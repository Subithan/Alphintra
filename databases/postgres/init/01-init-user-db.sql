-- Create the alphintra user and database
CREATE USER alphintra WITH PASSWORD 'alphintra123';
CREATE DATABASE alphintra OWNER alphintra;
GRANT ALL PRIVILEGES ON DATABASE alphintra TO alphintra;

-- Create additional databases
CREATE DATABASE auth_db OWNER alphintra;
CREATE DATABASE trading_db OWNER alphintra;
CREATE DATABASE strategy_db OWNER alphintra;

GRANT ALL PRIVILEGES ON DATABASE auth_db TO alphintra;
GRANT ALL PRIVILEGES ON DATABASE trading_db TO alphintra;
GRANT ALL PRIVILEGES ON DATABASE strategy_db TO alphintra;