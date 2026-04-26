-- procedures.sql
-- PL/pgSQL stored procedures and functions for TSIS 1
-- (Procedures from Practice 8 are NOT repeated here)

-- ── 1. add_phone ───────────────────────────────────────────────────────────
-- Adds a new phone number to an existing contact looked up by name.
-- If multiple contacts share the name the first match (by id) is used.
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Resolve contact by first_name (case-insensitive, partial match)
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  first_name ILIKE p_contact_name
        OR last_name  ILIKE p_contact_name
        OR (first_name || ' ' || COALESCE(last_name, '')) ILIKE p_contact_name
    ORDER  BY id
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Use home, work, or mobile.', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type)
    ON CONFLICT (contact_id, phone) DO NOTHING;

    RAISE NOTICE 'Phone % (%) added to contact id=%.', p_phone, p_type, v_contact_id;
END;
$$;


-- ── 2. move_to_group ──────────────────────────────────────────────────────
-- Moves a contact to a group; creates the group if it does not exist.
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Ensure group exists (create if missing)
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    -- Resolve contact
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  first_name ILIKE p_contact_name
        OR last_name  ILIKE p_contact_name
        OR (first_name || ' ' || COALESCE(last_name, '')) ILIKE p_contact_name
    ORDER  BY id
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact id=% moved to group "%".', v_contact_id, p_group_name;
END;
$$;


-- ── 3. search_contacts ────────────────────────────────────────────────────
-- Extended full-text search across: first_name, last_name, email, all phones.
-- Returns a set of contact rows (with one row per contact even if multi-phone).
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id         INTEGER,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.first_name,
        c.last_name,
        c.email,
        c.birthday,
        g.name AS group_name
    FROM   contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE  c.first_name ILIKE '%' || p_query || '%'
        OR c.last_name  ILIKE '%' || p_query || '%'
        OR c.email      ILIKE '%' || p_query || '%'
        OR ph.phone     ILIKE '%' || p_query || '%'
    ORDER  BY c.first_name, c.last_name;
END;
$$;


-- ── 4. paginated_contacts (reused from Practice 8, kept here for reference) ─
-- Already created in Practice 8; included as a comment so schema.sql + 
-- procedures.sql together form a complete self-contained deployment.
--
-- CREATE OR REPLACE FUNCTION paginated_contacts(p_limit INT, p_offset INT)
-- RETURNS TABLE (...) ...