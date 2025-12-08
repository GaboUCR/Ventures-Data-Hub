-- =========================================================
-- Esquema base para usuarios (admin Ace + dueños de compañía)
-- =========================================================

-- 1) Crear esquema y extensiones necesarias
CREATE SCHEMA IF NOT EXISTS core;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;    -- para tipo CITEXT (email case-insensitive)

-- 2) Tipos ENUM
-- Rol global del usuario (a nivel plataforma Ace)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'global_user_role' AND typnamespace = 'core'::regnamespace
    ) THEN
        CREATE TYPE core.global_user_role AS ENUM (
            'admin',         -- admin de Ace (ve todo el portfolio)
            'company_user'   -- dueño/miembro de una o varias compañías
        );
    END IF;
END $$;

-- Rol del usuario dentro de una compañía concreta
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'company_role' AND typnamespace = 'core'::regnamespace
    ) THEN
        CREATE TYPE core.company_role AS ENUM (
            'owner',     -- dueño / founder principal
            'admin',     -- permisos altos dentro de la compañía
            'member',    -- miembro normal
            'viewer'     -- solo lectura
        );
    END IF;
END $$;

-- 3) Tabla de usuarios (admins + dueños/miembros)
CREATE TABLE IF NOT EXISTS core.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,             -- o NULL si luego usas SSO
    full_name       TEXT NOT NULL,
    global_role     core.global_user_role NOT NULL DEFAULT 'company_user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4) Tabla de compañías (startups del portfolio)
CREATE TABLE IF NOT EXISTS core.companies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE,                      -- para URLs tipo /companies/finpay
    stage       TEXT,                             -- luego se puede cambiar a ENUM
    sector      TEXT,                             -- ej: 'Fintech', 'B2B SaaS'
    country     TEXT,
    website_url TEXT,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5) Tabla de memberships (relación usuario <-> compañía)
CREATE TABLE IF NOT EXISTS core.company_memberships (
    company_id        UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    user_id           UUID NOT NULL
        REFERENCES core.users(id) ON DELETE CASCADE,

    role              core.company_role NOT NULL DEFAULT 'owner',
    is_primary_owner  BOOLEAN NOT NULL DEFAULT FALSE,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, user_id)
);

-- 6) Índice único opcional para un solo owner principal por compañía
CREATE UNIQUE INDEX IF NOT EXISTS company_primary_owner_unique_idx
    ON core.company_memberships (company_id)
    WHERE is_primary_owner = TRUE;
