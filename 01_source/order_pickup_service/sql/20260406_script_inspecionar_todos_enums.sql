DO $$
DECLARE
    enum_rec RECORD;
    enum_val TEXT;
BEGIN
    FOR enum_rec IN 
        SELECT typname 
        FROM pg_type 
        WHERE typtype = 'e' 
          AND typnamespace = 'public'::regnamespace
        ORDER BY typname
    LOOP
        RAISE NOTICE '----- ENUM: % -----', enum_rec.typname;
        FOR enum_val IN 
            EXECUTE format('SELECT unnest(enum_range(NULL::%I))', enum_rec.typname)
        LOOP
            RAISE NOTICE '  %', enum_val;
        END LOOP;
    END LOOP;
END $$;