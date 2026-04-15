-- =========================================
-- FUNCTIONS.SQL
-- =========================================

-- 1. Function: search contacts by pattern
-- name / phone арқылы іздеу
CREATE OR REPLACE FUNCTION search_contacts(pattern TEXT)
RETURNS TABLE(
    id INT,
    first_name TEXT,
    phone_number TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM phonebook
    WHERE first_name ILIKE '%' || pattern || '%'
       OR phone_number LIKE pattern || '%';
END;
$$;


-- Қолдану:
-- SELECT * FROM search_contacts('8701');


-- =========================================

-- 2. Function: pagination (LIMIT + OFFSET)
CREATE OR REPLACE FUNCTION get_contacts_paginated(limit_val INT, offset_val INT)
RETURNS TABLE(
    id INT,
    first_name TEXT,
    phone_number TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM phonebook
    ORDER BY id
    LIMIT limit_val OFFSET offset_val;
END;
$$;


-- Қолдану:
-- SELECT * FROM get_contacts_paginated(5, 0);