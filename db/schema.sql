-- ============================================================
--  Capstone – Delivery AI Assistant
--  Neon PostgreSQL — БОДИТ production schema
--
--  ⚠️ Энэ файл нь жинхэнэ өгөгдлийн сангийн бүтцийг баримтжуулна.
--     AI-н DB_QUERY чадамж (Backend/llm.py) эдгээр хүснэгтийг
--     дараах JOIN-уудаар хайдаг:
--       fact_orders.customer_id      → dim_customers.id
--       fact_order_status.order_id   → fact_orders.id
--       fact_order_status.driver_id  → dim_drivers.id
--     Бүх dim_/fact_ хүснэгт SCD2 (is_current/effective_date/expiry_date)
--     загвартай тул query-д ЗААВАЛ  WHERE is_current = true  нэмнэ.
-- ============================================================


-- ── Хэмжээст хүснэгтүүд (dimensions, SCD2) ──────────────────

-- Харилцагч / компани (Хэрэглэгч, дэлгүүр)
CREATE TABLE IF NOT EXISTS dim_customers (
    id              UUID PRIMARY KEY,
    customer_name   VARCHAR,
    registry_number VARCHAR,
    phone_number    VARCHAR,
    email           VARCHAR,
    created_at      TIMESTAMP DEFAULT NOW(),
    -- SCD2
    is_current      BOOLEAN DEFAULT TRUE,
    effective_date  TIMESTAMP,
    expiry_date     TIMESTAMP
);

-- Жолооч (хүргэлтийн ажилтан)
CREATE TABLE IF NOT EXISTS dim_drivers (
    id              UUID PRIMARY KEY,
    firstname       VARCHAR,
    lastname        VARCHAR,
    registry_number VARCHAR,
    phone_number    VARCHAR,
    email           VARCHAR,
    birthday        DATE,
    plate_number    VARCHAR,
    bank_account    VARCHAR,
    created_at      TIMESTAMP DEFAULT NOW(),
    -- SCD2
    is_current      BOOLEAN DEFAULT TRUE,
    effective_date  TIMESTAMP,
    expiry_date     TIMESTAMP
);


-- ── Баримтат хүснэгтүүд (facts, SCD2) ───────────────────────

-- Захиалга / хүргэлт
CREATE TABLE IF NOT EXISTS fact_orders (
    id                    UUID PRIMARY KEY,
    customer_id           UUID REFERENCES dim_customers(id),  -- → dim_customers.id
    delivery_phone_number VARCHAR,
    hot_aimag             VARCHAR,        -- хот/аймаг
    sum_duureg            VARCHAR,        -- сум/дүүрэг
    address               TEXT,
    products              JSONB,          -- захиалгын барааны жагсаалт (JSON)
    is_prepaid            BOOLEAN,
    customer_fee          NUMERIC,        -- харилцагчаас авах төлбөр
    delivery_fee          NUMERIC,        -- хүргэлтийн төлбөр
    created_at            TIMESTAMP DEFAULT NOW(),
    -- SCD2
    is_current            BOOLEAN DEFAULT TRUE,
    effective_date        TIMESTAMP,
    expiry_date           TIMESTAMP
);

-- Захиалгын төлөв (статусын түүх)
CREATE TABLE IF NOT EXISTS fact_order_status (
    id             UUID PRIMARY KEY,
    order_id       UUID REFERENCES fact_orders(id),   -- → fact_orders.id
    driver_id      UUID REFERENCES dim_drivers(id),   -- → dim_drivers.id
    status         VARCHAR,    -- pending / picked / shipped / delivered / cancelled ...
    note           TEXT,
    created_at     TIMESTAMP DEFAULT NOW(),
    -- SCD2
    is_current     BOOLEAN DEFAULT TRUE,
    effective_date TIMESTAMP,
    expiry_date    TIMESTAMP
);

-- Гомдол / санал хүсэлт
CREATE TABLE IF NOT EXISTS complaints (
    id              TEXT PRIMARY KEY,
    agency          TEXT,
    content         TEXT,
    source_text     TEXT,
    status_text     TEXT,
    type_text       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_at_unix BIGINT
);


-- ── Аппликейшн / чатын хүснэгтүүд ───────────────────────────
--  (Эдгээрийг Backend-ийн init функцууд автоматаар үүсгэдэг:
--   db_users.init_users_table, database.init_delivery_requests_table)

-- Google OAuth-аар нэвтэрсэн хэрэглэгчид
CREATE TABLE IF NOT EXISTS app_users (
    id         VARCHAR(36)  PRIMARY KEY,
    google_id  VARCHAR(255) UNIQUE,
    email      VARCHAR(255) UNIQUE NOT NULL,
    name       VARCHAR(255),
    role       VARCHAR(20),     -- CUSTOMER / SHOP / EMPLOYEE
    created_at TIMESTAMP DEFAULT NOW()
);

-- Чатаар бүртгэгдсэн шинэ хүргэлтийн хүсэлт (ORDER_REQUEST)
CREATE TABLE IF NOT EXISTS baynaa.delivery_requests (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(255),
    session_id      VARCHAR(36),
    item            TEXT,
    pickup_address  TEXT,
    dropoff_address TEXT,
    recipient_name  VARCHAR(255),
    recipient_phone VARCHAR(50),
    status          VARCHAR(30) DEFAULT 'NEW',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Чатын session-ууд
CREATE TABLE IF NOT EXISTS baynaa.sessions (
    id         VARCHAR(36) PRIMARY KEY,
    user_id    VARCHAR(255),
    title      TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    msg_count  INT DEFAULT 0
);

-- Чатын мессежүүд
CREATE TABLE IF NOT EXISTS baynaa.messages (
    id          VARCHAR(36) PRIMARY KEY,
    session_id  VARCHAR(36) REFERENCES baynaa.sessions(id),
    role        VARCHAR(20),    -- user / assistant
    content     TEXT,
    token_count INT DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- LLM дуудлагын лог (хяналт / зардал)
CREATE TABLE IF NOT EXISTS baynaa.llm_logs (
    id                VARCHAR(36) PRIMARY KEY,
    message_id        VARCHAR(36),
    model             VARCHAR(50),
    prompt_tokens     INT,
    completion_tokens INT,
    cost_usd          NUMERIC(12,8),
    latency_ms        INT,
    use_case          VARCHAR(30)
);
