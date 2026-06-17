import os
import time
import traceback
import httpx
from database import (
    get_schema, run_query,
    get_session_by_user, create_session,
    save_message, get_messages, save_llm_log,
)
from llm import route_and_respond, generate_answer
from rag import search_docs


FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_VERIFY_TOKEN      = os.getenv("FB_VERIFY_TOKEN", "delivery_ai_verify")
GRAPH_URL            = "https://graph.facebook.com/v21.0/me/messages"


async def send_fb_message(recipient_id: str, text: str):
    if not FB_PAGE_ACCESS_TOKEN:
        print("[FB] ❌ FB_PAGE_ACCESS_TOKEN тохируулагдаагүй")
        return
    async with httpx.AsyncClient() as client:
        r = await client.post(
            GRAPH_URL,
            params={"access_token": FB_PAGE_ACCESS_TOKEN},
            json={
                "recipient":      {"id": recipient_id},
                "message":        {"text": text[:2000]},
                "messaging_type": "RESPONSE",
            },
            timeout=10,
        )
    if r.status_code != 200:
        print(f"[FB] ❌ Send алдаа {r.status_code}: {r.text[:120]}")
    else:
        print(f"[FB] ✅ Мессеж илгээгдлээ → {recipient_id}")


async def handle_fb_message(sender_id: str, text: str):
    print(f"[FB] ▶ sender={sender_id}  msg={text[:60]}")
    user_id    = f"fb_{sender_id}"
    user_role  = "CUSTOMER"
    user_name  = "Facebook хэрэглэгч"
    user_email = ""

    try:
        existing = get_session_by_user(user_id)
        sid      = existing["id"] if existing else create_session(user_id, "FB", text[:255])

        history   = get_messages(sid, limit=10)
        db_schema = get_schema()
        docs      = search_docs(text)

        t0         = time.time()
        llm        = route_and_respond(text, history, db_schema, docs,
                                       user_role, user_name, user_email)
        latency_ms = int((time.time() - t0) * 1000)
        capability = llm.get("capability", "INTRO")

        if capability == "DB_QUERY":
            sql = llm.get("sql", "")
            try:
                rows   = run_query(sql)
                answer = generate_answer(text, rows)
            except Exception as e:
                print(f"[FB] ❌ SQL алдаа: {e}")
                answer = "Уучлаарай, өгөгдлийг татахад алдаа гарлаа."
                rows   = []
        else:
            answer = llm.get("answer", "Уучлаарай, хариулж чадсангүй.")
            rows   = []

        save_message(sid, "user",      text)
        ai_mid = save_message(sid, "assistant", answer)
        save_llm_log(ai_mid, "gpt-4o-mini", 0, 0, latency_ms, capability.lower())

        print(f"[FB] [{capability}] {latency_ms}ms → {answer[:80]}")
        await send_fb_message(sender_id, answer)

    except Exception as e:
        print(f"[FB] ❌ handle алдаа: {e}")
        traceback.print_exc()
        await send_fb_message(sender_id, "Уучлаарай, алдаа гарлаа. Дахин оролдоно уу.")
