# 🛍️ Capstone – AI Order Assistant

**Workflow:** Байгалийн хэлний асуулт → OpenAI SQL үүсгэнэ → Neon PostgreSQL-с өгөгдөл татна → Streamlit UI харуулна

---

## 📁 Файлын бүтэц

```
Capstone/
├── README.md
├── .gitignore
├── db/
│   └── schema.sql          ← Бүх хүснэгт + sample өгөгдөл
├── backend/
│   ├── main.py             ← FastAPI app (гол логик)
│   ├── database.py         ← PostgreSQL холболт & query
│   ├── llm.py              ← OpenAI API: SQL үүсгэх & хариу бичих
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── app.py              ← Streamlit UI (workflow харуулсан)
```

---

## ⚙️ Тохируулга

### 1. Backend хавтас руу орж .env файл үүсгэх
```bash
cd backend
copy .env.example .env       # Windows
```

`.env` файлд дараах утгуудыг оруулна:
```env
PGHOST=ep-icy-silence-aq70iajz.c-8.us-east-1.aws.neon.tech
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=npg_4yXJFPikOV2u
OPENAI_API_KEY=sk-тань_key_энд
```

### 2. Package суулгах
```bash
pip install -r requirements.txt
```

---

## 🚀 Ажиллуулах

**Terminal 1 — FastAPI backend:**
```bash
cd backend
uvicorn main:app --reload
```
→ http://localhost:8000  
→ http://localhost:8000/docs  (Swagger UI)

**Terminal 2 — Streamlit frontend:**
```bash
cd frontend
streamlit run app.py
```
→ http://localhost:8501

---

## 🔄 Workflow диаграм

```
Хэрэглэгч асуулт бичнэ (Streamlit)
         ↓
POST /ask  →  FastAPI (main.py)
         ↓
database.py  →  Neon DB-с schema уншина
         ↓
llm.py  →  OpenAI gpt-4o-mini  →  SQL үүсгэнэ
         ↓
database.py  →  Neon DB-д SQL ажиллуулна
         ↓
JSON хариу  →  Streamlit хүснэгтээр харуулна
```

---

## 📡 API Endpoints

| Method | Endpoint  | Тайлбар                         |
|--------|-----------|---------------------------------|
| GET    | `/`       | Health check                    |
| GET    | `/health` | DB холболт шалгах               |
| GET    | `/schema` | DB-ийн бүтэц харах              |
| POST   | `/ask`    | Асуулт → SQL → Өгөгдөл буцаах  |

---

## 🗄️ DB Schema

| Хүснэгт      | Тайлбар                   |
|--------------|---------------------------|
| `companies`  | Захиалга өгдөг компаниуд  |
| `products`   | Бүтээгдэхүүн              |
| `orders`     | Захиалгууд                |
| `order_items`| Захиалгын дэлгэрэнгүй    |