CREATE TABLE IF NOT EXISTS tickets (
    id             SERIAL PRIMARY KEY,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    full_name      VARCHAR(255),
    facility       VARCHAR(255),
    phone          VARCHAR(50),
    email          VARCHAR(255),
    device_numbers TEXT,
    device_type    VARCHAR(255),
    emotional_tone VARCHAR(50)  CHECK (emotional_tone IN ('Позитив', 'Нейтрально', 'Негатив')),
    category       VARCHAR(100) DEFAULT 'Общий вопрос',
    issue_summary  TEXT,
    original_text  TEXT,
    ai_response    TEXT,
    status         VARCHAR(50)  DEFAULT 'Новое' CHECK (status IN ('Новое', 'В работе', 'Закрыто'))
);

CREATE INDEX IF NOT EXISTS idx_tickets_status         ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_emotional_tone ON tickets(emotional_tone);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at     ON tickets(created_at DESC);
