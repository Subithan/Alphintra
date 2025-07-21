-- Path: Alphintra/src/backend/auth-service/src/main/resources/db/migration/V1__initial_schema.sql
-- Purpose: Flyway migration script for the initial schema, mirroring init_database.sql with KYC extensions.

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    phone_number VARCHAR(20),
    address TEXT,
    kyc_status VARCHAR(20) DEFAULT 'NOT_STARTED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kyc_documents (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    document_reference VARCHAR(255),
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_kyc_documents_user_id ON kyc_documents(user_id);

INSERT INTO roles (name) VALUES ('USER') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ADMIN') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('KYC_ADMIN') ON CONFLICT (name) DO NOTHING;

INSERT INTO users (username, email, password, kyc_status)
VALUES ('admin', 'admin@alphintra.com', '$2a$10$1eZ5h5f2g4v3k2j5n6m7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d2e3f', 'NOT_STARTED')
ON CONFLICT (username) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'ADMIN'
ON CONFLICT (user_id, role_id) DO NOTHING;




-- -- Path: Alphintra/src/backend/auth-service/src/main/resources/db/migration/V1__initial_schema.sql
-- -- Purpose: Flyway migration script for the initial schema, mirroring init_database.sql with KYC extensions.

-- CREATE TABLE IF NOT EXISTS users (
--     id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     password VARCHAR(255) NOT NULL,
--     first_name VARCHAR(50),
--     last_name VARCHAR(50),
--     date_of_birth DATE,
--     phone_number VARCHAR(20),
--     address TEXT,
--     kyc_status VARCHAR(20) DEFAULT 'NOT_STARTED',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS roles (
--     id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
--     name VARCHAR(50) NOT NULL UNIQUE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS user_roles (
--     user_id BIGINT NOT NULL,
--     role_id BIGINT NOT NULL,
--     PRIMARY KEY (user_id, role_id),
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
-- );

-- CREATE TABLE IF NOT EXISTS kyc_documents (
--     id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
--     user_id BIGINT NOT NULL,
--     document_type VARCHAR(50) NOT NULL,
--     document_reference VARCHAR(255),
--     status VARCHAR(20) DEFAULT 'PENDING',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );

-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
-- CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
-- CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
-- CREATE INDEX IF NOT EXISTS idx_kyc_documents_user_id ON kyc_documents(user_id);

-- INSERT INTO roles (name) VALUES ('USER') ON CONFLICT (name) DO NOTHING;
-- INSERT INTO roles (name) VALUES ('ADMIN') ON CONFLICT (name) DO NOTHING;
-- INSERT INTO roles (name) VALUES ('KYC_ADMIN') ON CONFLICT (name) DO NOTHING;

-- INSERT INTO users (username, email, password, kyc_status)
-- VALUES ('admin', 'admin@alphintra.com', '$2a$10$1eZ5h5f2g4v3k2j5n6m7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d2e3f', 'NOT_STARTED')
-- ON CONFLICT (username) DO NOTHING;

-- INSERT INTO user_roles (user_id, role_id)
-- SELECT u.id, r.id
-- FROM users u, roles r
-- WHERE u.username = 'admin' AND r.name = 'ADMIN'
-- ON CONFLICT (user_id, role_id) DO NOTHING;