-- =========================================
-- PROCEDURES.SQL
-- =========================================

-- 1. Procedure: insert немесе update (UPSERT)
CREATE OR REPLACE PROCEDURE upsert_contact(p_name TEXT, p_phone TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM phonebook WHERE first_name = p_name
    ) THEN
        
        UPDATE phonebook
        SET phone_number = p_phone
        WHERE first_name = p_name;
        
        RAISE NOTICE 'User updated: %', p_name;
    ELSE
        
        INSERT INTO phonebook(first_name, phone_number)
        VALUES (p_name, p_phone);
        
        RAISE NOTICE 'User inserted: %', p_name;
    END IF;
END;
$$;




-- 2. Procedure: delete by name OR phone
CREATE OR REPLACE PROCEDURE delete_contact_proc(p_value TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM phonebook
    WHERE first_name = p_value
       OR phone_number = p_value;

    IF NOT FOUND THEN
        RAISE NOTICE 'No contact found';
    ELSE
        RAISE NOTICE 'Contact deleted';
    END IF;
END;
$$;




-- =========================================

--3. Procedure: bulk insert with validation

CREATE OR REPLACE PROCEDURE insert_many_users(
    names TEXT[],
    phones TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    i INT;
    invalid_data TEXT := '';
BEGIN
    FOR i IN 1..array_length(names, 1)
    LOOP
        -- Телефон тексеру (тек цифр және ұзындығы >= 10)
        IF phones[i] ~ '^[0-9]+$' AND length(phones[i]) >= 10 THEN
            
            INSERT INTO phonebook(first_name, phone_number)
            VALUES (names[i], phones[i])
            ON CONFLICT (phone_number) DO NOTHING;

        ELSE
            -- Қате деректерді жинау
            invalid_data := invalid_data || names[i] || ' (' || phones[i] || '), ';
        END IF;
    END LOOP;

    IF invalid_data <> '' THEN
        RAISE NOTICE 'Invalid data: %', invalid_data;
    ELSE
        RAISE NOTICE 'All users inserted successfully';
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error occurred: %', SQLERRM;
END;
$$;


