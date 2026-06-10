import os
import re

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

# DB асуултад хамааралтай үгс — эдгээр байвал RAG хайхгүй
DB_KEYWORDS = {
    "хэд", "нийт", "тоо", "жагсаа", "харуул", "орлого", "дүн",
    "хэдэн", "бүрийн", "статистик", "хамгийн", "дундаж", "rank",
    "бүтээгдэхүүн", "захиалга", "компани", "борлуулалт",
}

# RAG-т хамааралтай үгс — эдгээр байвал хайна
RAG_KEYWORDS = {
    "журам", "нөхцөл", "дүрэм", "гэрээ", "баталгаа", "буцаалт",
    "цуцлах", "төлбөр", "хүргэлт", "хугацаа", "боломжтой",
}


def search_docs(query, top_k=3):
    if not os.path.exists(DOCS_DIR):
        return ""

    q_lower = query.lower()
    words   = set(re.findall(r'\w+', q_lower))

    # DB асуулт бол RAG буцаахгүй
    db_hits  = words & DB_KEYWORDS
    rag_hits = words & RAG_KEYWORDS

    if db_hits and not rag_hits:
        print(f"[RAG] DB асуулт ({db_hits}) → RAG алгасав")
        return ""

    scored = []
    for fname in os.listdir(DOCS_DIR):
        if not fname.endswith(('.txt', '.md')):
            continue
        with open(os.path.join(DOCS_DIR, fname), encoding='utf-8') as f:
            content = f.read()
        for para in re.split(r'\n{2,}', content):
            para = para.strip()
            if not para:
                continue
            score = sum(1 for w in words if w in para.lower())
            if score > 0:
                scored.append((score, para))

    scored.sort(key=lambda x: -x[0])
    result = "\n\n".join(p for _, p in scored[:top_k])
    if result:
        print(f"[RAG] {len(scored)} параграф олдлоо, шилдэг {top_k}-г буцааж байна")
    return result
