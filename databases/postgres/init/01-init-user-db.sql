-- Create the alphintra user and database
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'alphintra') THEN
      CREATE USER alphintra WITH PASSWORD 'alphintra123';
   END IF;
END
$$;

SELECT 'CREATE DATABASE alphintra OWNER alphintra'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'alphintra')\gexec

SELECT 'CREATE DATABASE auth_db OWNER alphintra'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec

SELECT 'CREATE DATABASE trading_db OWNER alphintra'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_db')\gexec

SELECT 'CREATE DATABASE strategy_db OWNER alphintra'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'strategy_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE alphintra TO alphintra;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO alphintra;
GRANT ALL PRIVILEGES ON DATABASE trading_db TO alphintra;
GRANT ALL PRIVILEGES ON DATABASE strategy_db TO alphintra;