-- schema.sql
-- Extended PhoneBook schema for TSIS 1
-- Run once to set up (or upgrade) the database.
-- Safe to re-run: uses IF NOT EXISTS / IF EXISTS guards.

-- ── 1. Groups ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Seed default groups
INSERT INTO groups (name) VALUES
    ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- ── 2. Contacts (base table from Practice 7, extended) ─────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100),
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add new columns to an existing table without dropping data
ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS email      VARCHAR(100),
    ADD COLUMN IF NOT EXISTS birthday   DATE,
    ADD COLUMN IF NOT EXISTS group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

-- Drop the old UNIQUE phone column if it was on contacts (Practice 7 schema)
-- (safe: phones now live in the phones table)
ALTER TABLE contacts DROP COLUMN IF EXISTS phone;

-- ── 3. Phones (1-to-many) ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) DEFAULT 'mobile'
                           CHECK (type IN ('home', 'work', 'mobile'))
);

CREATE UNIQUE INDEX IF NOT EXISTS phones_contact_phone_uidx
    ON phones (contact_id, phone);