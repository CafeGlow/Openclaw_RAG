-- 1. Users Table: Stores profiles and the 8:30 AM alarm preference
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    name TEXT,
    skin_type TEXT,
    reminder_time TIME DEFAULT '08:30:00',
    onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Orders Table: Tracks the purchase funnel
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    gateway_order_id TEXT UNIQUE NOT NULL,
    product_flavor TEXT, -- 'Hazelnut', 'Pistachio', etc.
    amount_paise INTEGER,
    status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Habit Tracker Table: Tracks the 21-day "Dose" streak
CREATE TABLE IF NOT EXISTS habit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    log_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'pending', -- 'pending', 'completed'
    UNIQUE(user_id, log_date)
);

-- 4. Glow Audits Table: Stores image references for MedGemma analysis
CREATE TABLE IF NOT EXISTS glow_audits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    audit_day INTEGER, -- 1 or 21
    image_url TEXT,
    analysis_result JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);