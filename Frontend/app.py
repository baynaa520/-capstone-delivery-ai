import os
import uuid
import requests
import streamlit as st
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8001")
ROLE_INFO = {
    "CUSTOMER": ("📦", "Бараа авах хэрэглэгч", "#63b3ed"),
    "SHOP":     ("🏪", "Online дэлгүүр",        "#68d391"),
    "EMPLOYEE": ("🚚", "Хүргэлтийн ажилтан",    "#f6ad55"),
}
CAP_INFO = {
    "INTRO":     ("🤖", "#63b3ed", "Ерөнхий"),
    "KNOWLEDGE": ("📚", "#68d391", "Мэдлэг"),
    "DB_QUERY":  ("🗄️", "#f6ad55", "DB Хайлт"),
    "RAG":       ("📄", "#fc8181", "Журам"),
}

st.set_page_config(page_title="Delivery AI", page_icon="🚚",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{ font-family:'DM Sans',sans-serif; }
.stApp{ background:#080b14; }
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0d1117 0%,#0a0f1a 100%) !important;
    border-right:1px solid rgba(99,179,237,0.12) !important;
}
[data-testid="stSidebar"] *{ color:rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stButton button{
    background:rgba(99,179,237,0.07) !important;
    border:1px solid rgba(99,179,237,0.18) !important;
    border-radius:8px !important; color:rgba(255,255,255,0.8) !important;
    font-size:.82rem !important; transition:all .2s !important;
}
[data-testid="stSidebar"] .stButton button:hover{
    background:rgba(99,179,237,0.18) !important;
    border-color:rgba(99,179,237,0.5) !important;
    color:#63b3ed !important; transform:translateX(3px) !important;
}
.hero{
    background:linear-gradient(135deg,#0d1117 0%,#111827 50%,#0f1e2e 100%);
    border:1px solid rgba(99,179,237,0.15); border-radius:16px;
    padding:2rem; margin-bottom:1.5rem; text-align:center;
}
.hero h1{ font-family:'Space Mono',monospace; color:#63b3ed; font-size:2rem; margin:0 0 .5rem; }
.hero p{ color:rgba(255,255,255,0.4); font-size:.9rem; margin:0; }
.role-card{
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
    border-radius:16px; padding:2rem 1.5rem; text-align:center;
    transition:all .25s; cursor:pointer;
}
.role-card:hover{ border-color:rgba(99,179,237,0.4); background:rgba(99,179,237,0.05); }
.role-icon{ font-size:3rem; margin-bottom:.8rem; }
.role-title{ font-size:1.1rem; font-weight:600; color:white; margin-bottom:.4rem; }
.role-desc{ font-size:.8rem; color:rgba(255,255,255,0.4); line-height:1.5; }
.cap-badge{
    display:inline-block; padding:.15rem .6rem; border-radius:20px;
    font-size:.7rem; font-weight:600; margin-bottom:.4rem; border:1px solid;
}
.answer-text{ font-size:1rem; color:rgba(255,255,255,0.92); line-height:1.8; }
.sql-box{
    background:#0d1117; border:1px solid rgba(99,179,237,0.2);
    border-left:3px solid #63b3ed; border-radius:0 8px 8px 0;
    padding:.8rem 1rem; font-family:'Space Mono',monospace;
    font-size:.75rem; color:#79c0ff; white-space:pre-wrap;
}
[data-testid="stChatMessage"]{ background:transparent !important; border:none !important; padding:.1rem 0 !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]){
    background:rgba(99,179,237,0.07) !important; border:1px solid rgba(99,179,237,0.15) !important;
    border-radius:12px !important; padding:.7rem 1rem !important; margin:.25rem 0 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]){
    background:rgba(255,255,255,0.02) !important; border:1px solid rgba(255,255,255,0.06) !important;
    border-radius:12px !important; padding:.7rem 1rem !important; margin:.25rem 0 !important;
}
[data-testid="stChatInput"]{ background:#0d1117 !important; border:1px solid rgba(99,179,237,0.25) !important; border-radius:12px !important; }
[data-testid="stChatInput"] textarea{ color:white !important; }
hr{ border-color:rgba(255,255,255,0.05) !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
for k, v in [("token",""),("user_name",""),("user_email",""),
              ("user_role",""),("needs_role",False),
              ("messages",[]),("session_id",""),("channel","web")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── OAuth callback хүлээн авах ────────────────────────────────
params = st.query_params
if "token" in params:
    st.session_state.token      = params["token"]
    st.session_state.needs_role = params.get("new_user","false") == "true"
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend"))
        from auth import decode_token
        u = decode_token(st.session_state.token)
        st.session_state.user_name  = u.get("name",  "")
        st.session_state.user_email = u.get("email", "")
        st.session_state.user_role  = u.get("role",  "") or ""
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()

if params.get("auth_error"):
    st.error("❌ Google нэвтрэлт амжилтгүй. Дахин оролдоно уу.")
    st.query_params.clear()


# ═══════════════════════════════════════════════════════════════
# ХУУДАС 1 — Нэвтрэх
# ═══════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
    <div class="hero" style="padding:4rem 2rem;">
        <h1>🚚 Delivery AI</h1>
        <p style="font-size:1rem;color:rgba(255,255,255,0.5);margin:.5rem 0 2rem;">
            Хүргэлтийн компанийн ухаалаг туслах
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <a href="{API_URL}/auth/google" target="_self" style="text-decoration:none;">
            <div style="display:flex;align-items:center;justify-content:center;gap:12px;
                        background:white;color:#333;border-radius:10px;padding:14px 24px;
                        font-size:1rem;font-weight:600;cursor:pointer;
                        box-shadow:0 2px 12px rgba(0,0,0,0.3);">
                <svg width="20" height="20" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Gmail-ээрээ нэвтрэх
            </div>
        </a>
        <div style="text-align:center;margin-top:2rem;color:rgba(255,255,255,0.25);font-size:.75rem;">
            Google OAuth 2.0 — аюулгүй нэвтрэлт
        </div>
        <div style="text-align:center;margin-top:.8rem;font-family:'Space Mono',monospace;
                    color:rgba(99,179,237,0.45);font-size:.7rem;">
            🔗 Backend: {API_URL}
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ХУУДАС 2 — Role сонгох
# ═══════════════════════════════════════════════════════════════
def show_role_selection():
    name = st.session_state.user_name or st.session_state.user_email
    st.markdown(f"""
    <div class="hero">
        <h1>Тавтай морил, {name}!</h1>
        <p>Та ямар хэрэглэгч вэ? Нэгийг сонгоно уу.</p>
    </div>
    """, unsafe_allow_html=True)

    ROLES = [
        ("CUSTOMER", "📦", "Бараа авч байгаа хэрэглэгч",
         "Захиалгын байдал шалгах\nХүргэлтийн мэдээлэл авах\nБуцаалт, гомдол гаргах"),
        ("SHOP", "🏪", "Бараа хүргүүлж байгаа\nOnline дэлгүүр",
         "Захиалгын менежмент\nХүргэлтийн компанитай харилцаа\nДэлгүүрийн статистик"),
        ("EMPLOYEE", "🚚", "Хүргэлтийн компанийн\nАжилтан",
         "Бүх мэдээлэлд хандах\nБүх хэрэглэгчийн захиалга\nСистем бүхэлд нь харах"),
    ]

    cols = st.columns(3)
    for col, (role, icon, title, desc) in zip(cols, ROLES):
        with col:
            st.markdown(f"""
            <div class="role-card">
                <div class="role-icon">{icon}</div>
                <div class="role-title">{title}</div>
                <div class="role-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{icon} Сонгох", key=f"role_{role}", use_container_width=True):
                try:
                    r = requests.patch(f"{API_URL}/auth/role",
                                       json={"token": st.session_state.token, "role": role},
                                       timeout=10)
                    if r.status_code == 200:
                        new_tok = r.json()["token"]
                        st.session_state.token      = new_tok
                        st.session_state.user_role  = role
                        st.session_state.needs_role = False
                        try:
                            import sys, os
                            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend"))
                            from auth import decode_token
                            u = decode_token(new_tok)
                            st.session_state.user_name  = u.get("name",  "")
                            st.session_state.user_email = u.get("email", "")
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error("Алдаа гарлаа")
                except Exception as e:
                    st.error(f"❌ {e}")


# ═══════════════════════════════════════════════════════════════
# ХУУДАС 3 — Чат
# ═══════════════════════════════════════════════════════════════
def show_chat():
    role = st.session_state.user_role
    role_icon, role_label, role_color = ROLE_INFO.get(role, ("🤖", "Хэрэглэгч", "#63b3ed"))

    with st.sidebar:
        st.markdown(f"""
        <div style='padding:.5rem 0 1rem;'>
            <div style='font-family:Space Mono,monospace;color:{role_color};font-size:1rem;font-weight:700;'>
                🚚 Delivery AI
            </div>
            <div style='margin-top:.5rem;padding:.4rem .7rem;border-radius:8px;
                        background:{role_color}18;border:1px solid {role_color}33;display:inline-block;'>
                <span style='color:{role_color};font-size:.8rem;font-weight:600;'>
                    {role_icon} {role_label}
                </span>
            </div>
            <div style='color:rgba(255,255,255,0.35);font-size:.7rem;margin-top:.3rem;'>
                {st.session_state.user_email}
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔌 Шалгах", use_container_width=True):
                try:
                    r = requests.get(f"{API_URL}/health", timeout=5)
                    st.success("✅ OK") if r.json().get("status") == "ok" else st.error("❌ DB")
                except Exception:
                    st.error("❌ Алдаа")
        with c2:
            if st.button("➕ Шинэ", use_container_width=True):
                try:
                    uid = ""
                    if st.session_state.token:
                        import sys, os
                        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend"))
                        from auth import decode_token
                        uid = decode_token(st.session_state.token).get("sub", "")
                    r = requests.post(f"{API_URL}/api/session",
                                      json={"user_id": uid, "channel": st.session_state.channel},
                                      timeout=5)
                    if r.status_code == 200:
                        st.session_state.session_id = r.json().get("session_id", "")
                except Exception:
                    st.session_state.session_id = ""
                st.session_state.messages = []
                st.rerun()

        st.divider()

        st.markdown("<div style='color:rgba(255,255,255,0.4);font-size:.72rem;margin-bottom:.3rem;'>📡 Channel</div>",
                    unsafe_allow_html=True)
        channels = ["web", "FB", "Telegram", "Instagram"]
        st.session_state.channel = st.selectbox(
            "channel", channels,
            index=channels.index(st.session_state.channel),
            label_visibility="collapsed"
        )

        st.divider()

        EXAMPLES = {
            "CUSTOMER": ["Миний захиалгын байдал ямар байна?",
                         "Хүргэлт хэдэн өдөрт ирдэг вэ?",
                         "Буцаалт хийж болох уу?",
                         "Захиалга цуцлах журам юу вэ?"],
            "SHOP":     ["Манай дэлгүүрийн захиалгын тоо харуул",
                         "Хүргэлтийн компанитай харилцааны журам",
                         "Хамгийн их захиалгатай бараа",
                         "Захиалгын нийт дүн хэд вэ?"],
            "EMPLOYEE": ["Нийт захиалга хэд байна?",
                         "Компани бүрийн захиалгын тоо",
                         "Бүтээгдэхүүн юу байна?",
                         "Нийт орлого хэд вэ?"],
        }
        examples = EXAMPLES.get(role, EXAMPLES["EMPLOYEE"])
        st.markdown("<div style='color:rgba(255,255,255,0.35);font-size:.7rem;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:.6rem;'>💡 Жишээ асуултууд</div>",
                    unsafe_allow_html=True)
        for ex in examples:
            if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
                st.session_state["prefill"] = ex
                st.rerun()

        st.divider()
        if st.button("🚪 Гарах", use_container_width=True):
            for k in ["token", "user_name", "user_email", "user_role", "messages", "session_id", "needs_role"]:
                st.session_state[k] = [] if k == "messages" else ""
            st.rerun()

    # Header
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0d1117,#111827,#0f1e2e);
                border:1px solid rgba(99,179,237,0.15);border-radius:16px;
                padding:1.2rem 2rem;margin-bottom:1.5rem;'>
        <div style='font-family:Space Mono,monospace;color:{role_color};font-size:1.4rem;font-weight:700;'>
            🚚 Delivery AI Assistant
        </div>
        <div style='color:rgba(255,255,255,0.35);font-size:.8rem;margin-top:.2rem;'>
            {role_icon} {role_label} — {st.session_state.user_name}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                cap = msg.get("capability", "INTRO")
                icon_, color_, label_ = CAP_INFO.get(cap, ("🤖", "#63b3ed", cap))
                st.markdown(
                    f'<div class="cap-badge" style="color:{color_};border-color:{color_}33;background:{color_}11;">'
                    f'{icon_} {label_}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-text">{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("sql"):
                    with st.expander("🔧 SQL харах"):
                        st.markdown(f'<div class="sql-box">{msg["sql"]}</div>', unsafe_allow_html=True)
                if msg.get("df") is not None and not msg["df"].empty and msg.get("show_table"):
                    with st.expander(f"📊 Өгөгдөл ({len(msg['df'])} мөр)"):
                        st.dataframe(msg["df"], use_container_width=True,
                                     height=min(300, 55 + len(msg["df"]) * 35))
                        st.download_button("⬇️ CSV", msg["df"].to_csv(index=False),
                                           "data.csv", "text/csv",
                                           key=f"dl_{msg.get('key', 0)}")

    # Input
    prefill  = st.session_state.pop("prefill", None)
    question = st.chat_input("Асуултаа бичнэ үү...") or prefill

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/message",
                        json={"message":    question,
                              "session_id": st.session_state.session_id,
                              "channel":    st.session_state.channel,
                              "token":      st.session_state.token},
                        timeout=40,
                    )
                    if resp.status_code == 200:
                        data       = resp.json()
                        st.session_state.session_id = data.get("session_id", "")
                        answer     = data.get("answer", "")
                        sql        = data.get("sql", "")
                        results    = data.get("results", [])
                        row_count  = data.get("row_count", 0)
                        capability = data.get("capability", "INTRO")
                        df         = pd.DataFrame(results) if results else pd.DataFrame()
                        show_table = capability == "DB_QUERY" and row_count > 1

                        icon_, color_, label_ = CAP_INFO.get(capability, ("🤖", "#63b3ed", capability))
                        st.markdown(
                            f'<div class="cap-badge" style="color:{color_};border-color:{color_}33;background:{color_}11;">'
                            f'{icon_} {label_}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="answer-text">{answer}</div>', unsafe_allow_html=True)

                        if sql:
                            with st.expander("🔧 SQL харах"):
                                st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)
                        if show_table and not df.empty:
                            with st.expander(f"📊 Өгөгдөл ({row_count} мөр)"):
                                st.dataframe(df, use_container_width=True,
                                             height=min(300, 55 + len(df) * 35))
                                st.download_button("⬇️ CSV татах", df.to_csv(index=False),
                                                   "data.csv", "text/csv",
                                                   key=f"dl_{len(st.session_state.messages)}")

                        st.session_state.messages.append({
                            "role":       "assistant",
                            "content":    answer,
                            "capability": capability,
                            "sql":        sql,
                            "df":         df,
                            "show_table": show_table,
                            "key":        len(st.session_state.messages),
                        })
                    else:
                        err = resp.json().get("detail", "Системийн алдаа.")
                        st.error(f"⚠️ {err}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend холбогдсонгүй!")
                except Exception as e:
                    st.error(f"⚠️ {e}")


# ═══════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════
if not st.session_state.token:
    show_login()
elif st.session_state.needs_role or not st.session_state.user_role:
    show_role_selection()
else:
    show_chat()
