import os
import re
import json
import openai
from dotenv import load_dotenv

load_dotenv()

ROLE_CONTEXT = {
    "CUSTOMER": """Та хүргэлтийн компанийн хэрэглэгч __NAME__ (__EMAIL__)-д туслах AI юм.
Хэрэглэгч зөвхөн өөрийн захиалга болон хүргэлтийн мэдээлэлд хандах эрхтэй.
DB query-д шаардлагатай бол хэрэглэгчийн email (__EMAIL__)-р шүүх.""",

    "SHOP": """Та хүргэлтийн компанийн түншлэгч __NAME__ дэлгүүрт (__EMAIL__) туслах AI юм.
Дэлгүүр өөрийн илгээсэн захиалга болон хүргэлтийн компанитай харилцааны мэдээлэлд хандах эрхтэй.
DB query-д шаардлагатай бол дэлгүүрийн email (__EMAIL__)-р шүүх.""",

    "EMPLOYEE": """Та хүргэлтийн компанийн ажилтан __NAME__ (__EMAIL__) юм.
Бүх хэрэглэгч, дэлгүүр, захиалгын мэдээлэлд хандах бүрэн эрхтэй. Ямар ч мэдээлэл харж болно.""",
}

ROUTER_PROMPT = """__ROLE_CONTEXT__

═══ ЧАТНЫ ТҮҮХ ═══
__HISTORY__

═══ ХЭРЭГЛЭГЧИЙН АСУУЛТ ═══
__QUESTION__

═══ ЧАДАМЖ СОНГОХ ДҮРЭМ ═══

▶ ORDER_REQUEST — хэрэглэгч ШИНЭ хүргэлт захиалах, өөрийн бараагаа илгээх/хүргүүлэх хүсэлт:
  - "бараагаа хүргүүлмээр байна", "та нараар дамжуулж явуулъя", "захиалга өгье"
  - "илгээмж явуулах", "хүргэлт захиалах", "бараа илгээх", "хүргэж өгөх үү"
  ⚠️ Энэ нь одоо байгаа өгөгдлийг ХАЙХ биш, ШИНЭ хүсэлт тул DB_QUERY БҮҮ сонго!

  Захиалга бүртгэхэд 5 мэдээлэл хэрэгтэй:
    item            — илгээх бараа/төрөл
    pickup_address  — авах хаяг
    dropoff_address — хүргэх хаяг
    recipient_name  — хүлээн авагчийн нэр
    recipient_phone — хүлээн авагчийн утас
  Чатны түүх + одоогийн мессежээс эдгээрийг цуглуул. Аль хэдийн өгсөнийг дахин БҮҮ асуу.
  • ДУТУУ бол: дутуу мэдээллийг эелдгээр асуугаад "order": null буцаа.
  • 5 мэдээлэл БҮГД бүрдсэн бол: баталгаажуулах хариу бичээд "order" объектыг бүрэн дүүргэж буцаа.

▶ DB_QUERY — одоо байгаа өгөгдлийг ХАЙХ/ХАРАХ дараах тохиолдолд ЗААВАЛ энийг сонго:
  - Тоо, статистик: "хэд байна", "нийт", "тоо", "орлого", "дүн"
  - Жагсаалт: "харуул", "жагсаа", "бүрийн", "бүгдийг"
  - Өгөгдөл: "захиалга", "бүтээгдэхүүн", "компани", "борлуулалт"

  DB Schema:
__SCHEMA__

  ⚠️ ЗААВАЛ МЭДЭХ ХОЛБООСУУД (JOIN):
  - fact_orders.customer_id → dim_customers.id   (компани/хэрэглэгчийн мэдээлэл)
  - fact_order_status.order_id → fact_orders.id  (захиалгын төлөв)
  - fact_order_status.driver_id → dim_drivers.id (жолоочийн мэдээлэл)
  - "компани" гэвэл → dim_customers.customer_name ашигла
  - "захиалга" гэвэл → fact_orders хүснэгт ашигла
  - "төлөв/статус" гэвэл → fact_order_status ашигла
  - WHERE-д is_current=true нэмэх (одоогийн өгөгдөл авах)

▶ RAG — ЗӨВХӨН журам/нөхцлийн асуулт:
  - "журам", "нөхцөл", "дүрэм", "гэрээ", "буцаалт боломжтой юу"
  Баримт:
__RAG_CONTENT__

▶ KNOWLEDGE — үйл ажиллагааны ЕРӨНХИЙ мэдлэг (тодорхой тоо БИШ):
  - "хүргэлт хэдэн ӨДӨРТ ирдэг", "төлбөр яаж хийх", "баталгаа хэд хоног"
  ⚠️ ХУГАЦААНЫ асуулт ("хэдэн ӨДӨР/udur/хоног/цаг/days хүргэдэг/ирдэг") → KNOWLEDGE!
  ⚠️ Харин ТООЛОХ асуулт ("хэдэн хүргэлт / нийт хүргэлт") → DB_QUERY!

▶ INTRO — мэндчилгээ, ерөнхий яриа:
  - "та хэн бэ", "сайн уу", "юу хийдэг вэ"

⚠️ ХЭЛ/БИЧЛЭГ: Хэрэглэгч кирилл, ЛАТИН (translit), эсвэл англиар бичиж болно.
   Үсгийн бичлэгээс үл хамааран УТГААР нь ангил. Жишээ латин→кирилл:
   "niit heden hvrgelt baina we" = "нийт хэдэн хүргэлт байна вэ" → DB_QUERY
   "zahialga", "hurgelt", "heden", "niit", "udur" = "захиалга", "хүргэлт", "хэдэн", "нийт", "өдөр"
⚠️ ТҮҮХЭНД БҮҮ АВТ: Чатны түүхэнд мэндчилгээ их давтагдсан байж болно.
   Гэхдээ ОДООГИЙН асуултын утгаар ангил — тоо/жагсаалт асуувал INTRO БИШ.
⚠️ "хэд/хэдэн/heden/хичнээн/тоо/нийт/niit" + захиалга/хүргэлт/харилцагч/гомдол/жолооч
   → ЗААВАЛ DB_QUERY! (ж: "нийт хэдэн хүргэлт", "аль дүүрэг хамгийн их захиалгатай")
⚠️ "бараагаа хүргүүлэх/илгээх/захиалга өгөх" гэвэл шинэ хүсэлт тул → ЗААВАЛ ORDER_REQUEST!

═══ БУЦААХ JSON ═══
DB_QUERY:
{"capability": "DB_QUERY", "sql": "<SELECT ... LIMIT 100>", "explanation": "<тайлбар>"}

ORDER_REQUEST (5 мэдээлэл бүгд бүрдсэн үед):
{"capability": "ORDER_REQUEST", "answer": "<баталгаажуулах хариу>", "order": {"item": "...", "pickup_address": "...", "dropoff_address": "...", "recipient_name": "...", "recipient_phone": "..."}}

Бусад (INTRO / KNOWLEDGE / RAG / дутуу ORDER_REQUEST):
{"capability": "INTRO", "answer": "<Монгол хариу>", "order": null}

Зөвхөн цэвэр JSON. Markdown үгүй."""

ANSWER_PROMPT = """Та хүргэлтийн компанийн AI туслах юм.
Хэрэглэгч "__QUESTION__" гэж асуусан.
SQL query-ийн үр дүн: __DATA__
Энгийн, ойлгомжтой Монгол хэлээр хариул. Тоонуудыг тодорхой дурд. Зөвхөн хариу текст."""


def route_and_respond(question, history, schema, rag_content="",
                      user_role="CUSTOMER", user_name="Хэрэглэгч", user_email=""):
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY тохируулагдаагүй.")

    client = openai.OpenAI(api_key=key)

    history_text = "\n".join([
        f"{'Хэрэглэгч' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in history[-6:]
    ]) if history else "Түүх байхгүй"

    rag_text     = rag_content[:800] if rag_content else "Холбогдох мэдлэг олдсонгүй"
    role_context = (ROLE_CONTEXT.get(user_role, ROLE_CONTEXT["CUSTOMER"])
                    .replace("__NAME__",  user_name)
                    .replace("__EMAIL__", user_email))

    prompt = (ROUTER_PROMPT
              .replace("__ROLE_CONTEXT__", role_context)
              .replace("__HISTORY__",      history_text)
              .replace("__QUESTION__",     question)
              .replace("__SCHEMA__",       schema)
              .replace("__RAG_CONTENT__",  rag_text))

    print(f"[LLM] Role=[{user_role}]  Түүх={len(history)}  RAG={'тийм' if rag_content else 'үгүй'}")
    print(f"[LLM] OpenAI gpt-4o-mini дуудаж байна (router)...")

    import time
    t0   = time.time()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,
    )
    ms  = int((time.time() - t0) * 1000)
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    print(f"[LLM] ✅ Router ({ms}ms): {raw[:120]}")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[LLM] ❌ JSON parse алдаа: {e}  raw={raw[:80]}")
        result = {"capability": "INTRO", "answer": "Уучлаарай, дахин оролдоно уу."}

    cap = result.get("capability", "?")
    print(f"[LLM] → [{cap}]" + (f"  SQL: {result.get('sql','')[:80]}" if cap == "DB_QUERY" else ""))
    return result


def generate_answer(question, data):
    key    = os.getenv("OPENAI_API_KEY", "")
    client = openai.OpenAI(api_key=key)

    from datetime import datetime, date
    def serialize(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    data_str = json.dumps(data[:5], ensure_ascii=False, default=serialize)
    prompt   = (ANSWER_PROMPT
                .replace("__QUESTION__", question)
                .replace("__DATA__",     data_str))

    import time
    t0   = time.time()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    ms     = int((time.time() - t0) * 1000)
    answer = resp.choices[0].message.content.strip()
    print(f"[LLM] ✅ Answer ({ms}ms): {answer[:80]}")
    return answer
