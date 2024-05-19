CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'Qq12345';
SELECT pg_create_physical_replication_slot('replication_slot');


CREATE TABLE phones(
        id_phone SERIAL PRIMARY KEY,
        phone VARCHAR(30)
);
CREATE TABLE emails(
        id_email SERIAL PRIMARY KEY,
        email VARCHAR(255)
);
