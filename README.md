# 🚚 Хүргэлтийн AI Туслах — Delivery AI Assistant

Хүргэлтийн компанид зориулсан Монгол хэлний AI чатбот. Байгалийн хэлний асуултыг SQL болгон хөрвүүлж өгөгдлийн сангаас мэдээлэл гарган авдаг.

---

## ✨ Үндсэн боломжууд

- 🔐 **Gmail-ээр нэвтрэх** — Google OAuth 2.0
- 👥 **3 төрлийн хэрэглэгч** — тус бүрд тохирсон мэдээлэл
- 🤖 **AI чат** — Монгол хэлний асуулт → SQL → хариу
- 📄 **RAG** — Журам, бодлогын баримт хайлт
- 📊 **Хүснэгт харуулах** — Query-н үр дүнг CSV татах

---

## 👤 Хэрэглэгчийн 3 төрөл

| Төрөл | Тайлбар | Хандах мэдээлэл |
|-------|---------|-----------------|
| 🚚 **Ажилтан** | Хүргэлтийн компанийн ажилтан | Бүх мэдээлэл |
| 📦 **Хэрэглэгч** | Бараа авч байгаа хүн | Өөрийн захиалга |
| 🏪 **Дэлгүүр** | Бараа илгээж байгаа online shop | Өөрийн хүргэлт |

---

## 🏗️ Системийн бүтэц

```
Frontend (Streamlit)
    ↓ HTTP
Backend (FastAPI)
    ├── Google OAuth → Нэвтрэлт
    ├── LLM Router → Чадамж сонгох (INTRO / KNOWLEDGE / DB_QUERY / RAG)
    ├── OpenAI GPT-4o-mini → SQL үүсгэх, хариу бичих
    ├── Neon PostgreSQL → Өгөгдлийн сан
    └── RAG → Баримт хайлт
```

---

## 🛠️ Технологийн стек

| Хэсэг | Технологи |
|-------|-----------|
| Frontend | Python, Streamlit |
| Backend | Python, FastAPI |
| Database | PostgreSQL (Neon Cloud) |
| AI | OpenAI GPT-4o-mini |
| Auth | Google OAuth 2.0, JWT |

---

## 🚀 Локал ажиллуулах

### 1. Repo clone хийх
```bash
git clone https://github.com/таны-username/capstone-delivery-ai.git
cd capstone-delivery-ai
```

### 2. Virtual environment үүсгэх
```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

### 3. Packages суулгах
```bash
pip install -r Backend/requirements.txt
```

### 4. Environment variables тохируулах
```bash
cp Backend/.env.example Backend/.env
# .env файлд өөрийн утгуудыг оруулна
```

### 5. Backend ажиллуулах
```bash
cd Backend
uvicorn main:app --reload --port 8000
```

### 6. Frontend ажиллуулах (шинэ terminal)
```bash
cd Frontend
streamlit run app.py
```

`http://localhost:8501` хаягаар нээнэ.

---

## ⚙️ Environment Variables

`Backend/.env.example` файлаас хуулж `.env` үүсгэнэ:

```env
PGHOST=...
PGDATABASE=...
PGUSER=...
PGPASSWORD=...

OPENAI_API_KEY=sk-...

GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...

JWT_SECRET=your-secret
SESSION_SECRET=your-secret
FRONTEND_URL=http://localhost:8501
```

---

## 📁 Файлын бүтэц

```
Capstone/
├── Backend/
│   ├── main.py          # FastAPI app, endpoints
│   ├── auth.py          # Google OAuth, JWT
│   ├── database.py      # PostgreSQL холболт
│   ├── db_users.py      # Хэрэглэгчийн DB функцүүд
│   ├── llm.py           # OpenAI, role-based prompts
│   ├── rag.py           # Баримт хайлт
│   ├── docs/            # RAG баримтууд
│   ├── requirements.txt
│   └── .env.example
├── Frontend/
│   └── app.py           # Streamlit UI
└── README.md
```

---

## 📖 AI Чадамжууд

| Чадамж | Тайлбар | Жишээ асуулт |
|--------|---------|--------------|
| 🤖 INTRO | Мэндчилгээ, танилцуулга | "Та хэн бэ?" |
| 📚 KNOWLEDGE | Ерөнхий мэдлэг | "Хүргэлт хэдэн өдөрт ирдэг?" |
| 🗄️ DB_QUERY | Өгөгдлийн сангаас хайх | "Нийт захиалга хэд байна?" |
| 📄 RAG | Журам, бодлогоос хайх | "Буцаалтын журам юу вэ?" |

---

## 👨‍💻 Хөгжүүлэгч

Capstone төсөл — 2026
