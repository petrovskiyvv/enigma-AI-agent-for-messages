-- init.sql
-- Idempotent schema + seeds. Safe to run on every docker compose up.

BEGIN;

-- --- TICKETS ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tickets (
  id              BIGSERIAL PRIMARY KEY,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  full_name       TEXT,
  facility        TEXT,
  phone           TEXT,
  email           TEXT,
  device_numbers  TEXT,
  device_type     TEXT,
  emotional_tone  TEXT,
  category        TEXT,
  issue_summary   TEXT,
  original_text   TEXT,
  ai_response     TEXT,
  status          TEXT NOT NULL DEFAULT 'Новое'
);

-- --- TELEGRAM CHANNELS ------------------------------------------------------
CREATE TABLE IF NOT EXISTS telegram_channels (
  chat_id       BIGINT PRIMARY KEY,
  type          TEXT NOT NULL,
  title         TEXT,
  registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  active        BOOLEAN NOT NULL DEFAULT TRUE
);

-- --- TELEGRAM LINK TOKENS ---------------------------------------------------
CREATE TABLE IF NOT EXISTS telegram_link_tokens (
  token       UUID PRIMARY KEY,
  expires_at  TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ
);

-- --- TELEGRAM TICKET BINDINGS ----------------------------------------------
CREATE TABLE IF NOT EXISTS telegram_ticket_bindings (
  ticket_id                  INTEGER PRIMARY KEY REFERENCES tickets(id) ON DELETE CASCADE,
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  base_text                  TEXT,
  channel_chat_id            BIGINT,
  channel_message_id         BIGINT,
  discussion_chat_id         BIGINT,
  discussion_root_message_id BIGINT,
  timeline_message_id        BIGINT,
  assignee                   TEXT
);

-- --- TICKET EVENTS ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS ticket_events (
  id        BIGSERIAL PRIMARY KEY,
  ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  ts        TIMESTAMPTZ NOT NULL DEFAULT now(),
  type      TEXT NOT NULL,
  "by"      TEXT,
  prev      TEXT
);

-- Prevent duplicates if init.sql is executed repeatedly
CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_events_dedupe
  ON ticket_events (ticket_id, ts, type);

-- --- SEEDS -----------------------------------------------------------------
-- Demo tickets (formerly in-memory). Use fixed IDs for compatibility.
INSERT INTO tickets (
  id, created_at, full_name, facility, phone, email,
  device_numbers, device_type, emotional_tone, category,
  issue_summary, original_text, ai_response, status
) VALUES
  (1, now() - interval '2 days', 'Иванов Иван', 'Склад №1', '+7 900 000-00-01', 'ivanov@example.com',
   'A-1001', 'сканер', 'Нейтраль', 'hardware',
   'Не включается сканер', 'Сканер A-1001 не включается после замены батареи', 'Проверьте контакты батареи и попробуйте другую батарею.', 'Новое'),
  (2, now() - interval '1 day', 'Петров Пётр', 'Офис', '+7 900 000-00-02', 'petrov@example.com',
   'P-2002', 'принтер', 'Негатив', 'hardware',
   'Принтер зажевывает бумагу', 'Принтер P-2002 постоянно зажёвывает бумагу на входе', 'Проверьте ролики подачи и наличие посторонних предметов. Очистите тракт.', 'Закрыто'),
  (3, now() - interval '3 hours', 'Сидорова Анна', 'Торговый зал', '+7 900 000-00-03', 'sidorova@example.com',
   'T-3003', 'терминал', 'Нейтраль', 'software',
   'Терминал не выходит в сеть', 'Терминал T-3003 не подключается к Wi-Fi после обновления', 'Проверьте настройки Wi-Fi и перезагрузите устройство. При необходимости откатите обновление.', 'В работе')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ticket_events (ticket_id, ts, type, "by", prev)
VALUES
  (1, now() - interval '2 days', 'created', NULL, NULL),
  (2, now() - interval '1 day', 'created', NULL, NULL),
  (3, now() - interval '3 hours', 'created', NULL, NULL)
ON CONFLICT (ticket_id, ts, type) DO NOTHING;

SELECT setval(
  pg_get_serial_sequence('tickets','id'),
  (SELECT COALESCE(MAX(id), 1) FROM tickets),
  true
);

COMMIT;