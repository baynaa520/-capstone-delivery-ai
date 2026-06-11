import os
import time
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from database import (
    get_schema, run_query, check_connection,
    get_session_by_user, create_session,
    save_message, get_messages, save_llm_log,
)
from db_users import init_users_table, get_or_create_user, update_user_role
from llm import route_and_respond, generate_answer
from rag import search_docs
from auth import create_token, decode_token, SESSION_SECRET, FRONTEND_URL

app = FastAPI(title="Delivery AI Assistant")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET,
                   same_site="lax", https_only=True)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.on_event("startup")
async def startup():
    init_users_table()
    print("[APP] ✅ Startup дууслаа")


# ── Auth endpoints ────────────────────────────────────────────

@app.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = str(request.base_url).rstrip("/") + "/auth/callback"
    print(f"[AUTH] Google redirect → {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def _exchange_code_manually(request: Request) -> dict:
    # Session cookie алдагдсан үед (cross-site redirect) authlib-ийн state
    # шалгалт унадаг тул code-ийг Google-тэй шууд солилцоно.
    import httpx
    code         = request.query_params.get("code", "")
    redirect_uri = str(request.base_url).rstrip("/") + "/auth/callback"
    async with httpx.AsyncClient() as client:
        r = await client.post("https://oauth2.googleapis.com/token", data={
            "code":          code,
            "client_id":     os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code",
        })
        r.raise_for_status()
        access_token = r.json()["access_token"]
        ui = await client.get("https://openidconnect.googleapis.com/v1/userinfo",
                              headers={"Authorization": f"Bearer {access_token}"})
        ui.raise_for_status()
        return ui.json()


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        try:
            token     = await oauth.google.authorize_access_token(request)
            user_info = token.get("userinfo") or {}
        except Exception as e:
            print(f"[AUTH] ⚠️ State шалгалт унав ({e}) — code-оор шууд солилцоно")
            user_info = await _exchange_code_manually(request)
        google_id = user_info.get("sub", "")
        email     = user_info.get("email", "")
        name      = user_info.get("name", email.split("@")[0])

        print(f"[AUTH] Google callback: {email}")
        user    = get_or_create_user(google_id, email, name)
        is_new  = not user.get("role")
        jwt_tok = create_token(user["id"], email, name, user.get("role"))

        redirect_url = f"{FRONTEND_URL}?token={jwt_tok}&new_user={'true' if is_new else 'false'}"
        return RedirectResponse(redirect_url)

    except Exception as e:
        print(f"[AUTH] ❌ Callback алдаа: {e}")
        traceback.print_exc()
        return RedirectResponse(f"{FRONTEND_URL}?auth_error=true")


class RoleRequest(BaseModel):
    token: str
    role:  str


@app.patch("/auth/role")
def set_role(body: RoleRequest):
    if body.role not in ("CUSTOMER", "SHOP", "EMPLOYEE"):
        raise HTTPException(400, "Role буруу байна")
    user_data = decode_token(body.token)
    update_user_role(user_data["sub"], body.role)
    new_token = create_token(user_data["sub"], user_data["email"],
                             user_data["name"], body.role)
    print(f"[AUTH] ✅ {user_data['email']} → {body.role}")
    return {"token": new_token}


# ── Health ────────────────────────────────────────────────────

@app.get("/health")
def health():
    ok = check_connection()
    print(f"[HEALTH] {'✅ OK' if ok else '❌ FAILED'}")
    return {"status": "ok" if ok else "error"}


# ── Session endpoints ─────────────────────────────────────────

class SessionRequest(BaseModel):
    user_id: str
    channel: str = "web"


@app.post("/api/session")
def new_session(body: SessionRequest):
    sid = create_session(body.user_id, body.channel, "New Chat")
    return {"session_id": sid}


@app.get("/api/session/{session_id}")
def session_history(session_id: str, limit: int = 50):
    return {"messages": get_messages(session_id, limit)}


# ── Main message endpoint ─────────────────────────────────────

class MessageRequest(BaseModel):
    message:    str
    session_id: str = ""
    channel:    str = "web"
    token:      str = ""


@app.post("/api/message")
def api_message(body: MessageRequest):
    user_id    = "anonymous"
    user_role  = "CUSTOMER"
    user_name  = "Хэрэглэгч"
    user_email = ""

    if body.token:
        try:
            u          = decode_token(body.token)
            user_id    = u.get("sub",   user_id)
            user_role  = u.get("role",  user_role) or "CUSTOMER"
            user_name  = u.get("name",  user_name)
            user_email = u.get("email", user_email)
        except Exception as e:
            print(f"[API] Token decode алдаа: {e}")

    print(f"\n{'='*55}")
    print(f"[API] ▶  {user_email or user_id[:8]}  [{user_role}]")
    print(f"[API]    {body.message[:80]}")
    print(f"{'='*55}")

    try:
        t0 = time.time()

        if body.session_id:
            sid = body.session_id
        else:
            existing = get_session_by_user(user_id)
            sid = existing["id"] if existing else create_session(
                user_id, body.channel, body.message[:255]
            )
        print(f"[API] 1. session={sid[:8]}...")

        history = get_messages(sid, limit=10)
        print(f"[API] 2. Түүх={len(history)} мессеж")

        db_schema = get_schema()
        docs      = search_docs(body.message)
        print(f"[API] 3. Schema={len(db_schema)}  RAG={'тийм' if docs else 'үгүй'}")

        llm        = route_and_respond(body.message, history, db_schema, docs,
                                       user_role, user_name, user_email)
        latency_ms = int((time.time() - t0) * 1000)
        capability = llm.get("capability", "INTRO")
        print(f"[API] 4. [{capability}]  {latency_ms}ms")

        if capability == "DB_QUERY":
            sql = llm.get("sql", "")
            print(f"[API] 5. SQL: {sql[:120]}")
            try:
                rows   = run_query(sql)
                answer = generate_answer(body.message, rows)
            except Exception as sql_err:
                print(f"[API] 5. ❌ SQL алдаа: {sql_err}")
                answer = "Уучлаарай, өгөгдлийг татахад алдаа гарлаа."
                rows   = []
        else:
            sql    = ""
            rows   = []
            answer = llm.get("answer", "Уучлаарай, хариулж чадсангүй.")
            print(f"[API] 5. Хариу: {answer[:80]}")

        save_message(sid, "user",      body.message)
        ai_mid = save_message(sid, "assistant", answer)
        save_llm_log(ai_mid, "gpt-4o-mini", 0, 0, latency_ms, capability.lower())
        print(f"[API] ✅ Дууслаа {int((time.time()-t0)*1000)}ms\n")

        return {
            "session_id": sid,
            "capability": capability,
            "answer":     answer,
            "sql":        sql,
            "results":    rows,
            "row_count":  len(rows),
        }

    except Exception as e:
        print(f"[API] ❌ АЛДАА: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Системийн алдаа гарлаа.")
