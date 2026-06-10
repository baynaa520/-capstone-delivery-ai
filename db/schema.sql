-- ============================================================
--  Capstone – Online Shop Database
--  Neon PostgreSQL
-- ============================================================

-- Companies (Компаниуд)
CREATE TABLE IF NOT EXISTS companies (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100),
    phone      VARCHAR(20),
    address    TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products (Бүтээгдэхүүн)
CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    price       NUMERIC(12,2) NOT NULL,
    stock       INT DEFAULT 0,
    category    VARCHAR(80),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Orders (Захиалга)
CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,
    company_id    INT REFERENCES companies(id),
    total_amount  NUMERIC(14,2),
    status        VARCHAR(30) DEFAULT 'pending',  -- pending / confirmed / shipped / delivered / cancelled
    ordered_at    TIMESTAMP DEFAULT NOW(),
    delivered_at  TIMESTAMP
);

-- Order Items (Захиалгын дэлгэрэнгүй)
CREATE TABLE IF NOT EXISTS order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity   INT NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL
);

-- ── Sample Data ─────────────────────────────────────────────

INSERT INTO companies (name, email, phone, address) VALUES
    ('Монгол Трейд ХХК',   'info@mongoltrade.mn',  '7711-0001', 'Улаанбаатар, СБД 1-р хороо'),
    ('Говь Экспорт ХХК',   'order@goviexport.mn',  '7711-0002', 'Улаанбаатар, БЗД 5-р хороо'),
    ('Номин Дистрибьютор', 'noming@nomin.mn',       '7711-0003', 'Улаанбаатар, ХУД 3-р хороо'),
    ('Стар Ложистик ХХК',  'logistics@star.mn',     '7711-0004', 'Дархан хот'),
    ('Эрдэнэт Трейд',      'trade@erdenet.mn',      '7711-0005', 'Эрдэнэт хот')
ON CONFLICT DO NOTHING;

INSERT INTO products (name, description, price, stock, category) VALUES
    ('Зурагт 55"',        'Samsung 4K QLED телевиз',          1850000, 25, 'Электроник'),
    ('Зөөврийн компьютер','Lenovo ThinkPad 14", i5, 16GB RAM', 3200000, 12, 'Электроник'),
    ('Гар утас',          'iPhone 15 128GB',                   2900000, 40, 'Электроник'),
    ('Хөргөгч',           'LG 350L хоёр хаалгатай',            1450000, 18, 'Ахуйн техник'),
    ('Угаалгын машин',    'Samsung 7кг автомат',                980000, 22, 'Ахуйн техник'),
    ('Гал тогооны иж',    'Bosch зуух + хийн плита',           1200000, 15, 'Ахуйн техник'),
    ('Офисын сандал',     'Ergonomic chair, хар',               450000, 50, 'Тавилга'),
    ('Бичгийн ширээ',     '160x80 L-shape ширээ',               380000, 30, 'Тавилга'),
    ('Принтер',           'HP LaserJet Pro',                    620000, 20, 'Оффис'),
    ('Проектор',          'Epson 3500 lm',                     1100000, 8,  'Оффис')
ON CONFLICT DO NOTHING;

INSERT INTO orders (company_id, total_amount, status, ordered_at, delivered_at) VALUES
    (1, 7250000,  'delivered',  '2026-04-01', '2026-04-05'),
    (1, 3200000,  'delivered',  '2026-04-10', '2026-04-14'),
    (2, 5800000,  'shipped',    '2026-04-15', NULL),
    (3, 1960000,  'confirmed',  '2026-04-20', NULL),
    (3, 9600000,  'delivered',  '2026-03-05', '2026-03-10'),
    (4, 2400000,  'pending',    '2026-05-01', NULL),
    (4, 4350000,  'delivered',  '2026-03-20', '2026-03-25'),
    (5, 760000,   'cancelled',  '2026-04-25', NULL),
    (5, 3300000,  'delivered',  '2026-05-05', '2026-05-08'),
    (2, 1100000,  'confirmed',  '2026-05-10', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 2, 1850000), (1, 9, 3, 620000),   -- Зурагт x2, Принтер x3 (→7250000? ойролцоо)
    (2, 2, 1, 3200000),                        -- Laptop x1
    (3, 3, 2, 2900000),                        -- Утас x2
    (4, 5, 2, 980000),                         -- Угаалгын машин x2
    (5, 2, 3, 3200000),                        -- Laptop x3
    (6, 8, 3, 380000), (6, 7, 3, 450000),     -- Ширээ, сандал x3
    (7, 4, 3, 1450000),                        -- Хөргөгч x3
    (8, 6, 1, 760000),                         -- Иж x1
    (9, 10, 3, 1100000),                       -- Проектор x3
    (10, 10, 1, 1100000)                       -- Проектор x1
ON CONFLICT DO NOTHING;