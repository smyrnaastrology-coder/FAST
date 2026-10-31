-- Apply only after backing up the existing system and reviewing DB permissions.
-- This table is for Holavon accounts, not standalone Horary credit balances.
CREATE TABLE IF NOT EXISTS holavon_horary_quota (
    user_id TEXT PRIMARY KEY,
    free_used INTEGER NOT NULL DEFAULT 0 CHECK (free_used >= 0),
    pro_day DATE,
    pro_used INTEGER NOT NULL DEFAULT 0 CHECK (pro_used >= 0)
);

-- Reservation IDs prevent a retried request from spending the same quota
-- twice. This stores no question text or answer.
CREATE TABLE IF NOT EXISTS holavon_horary_reservations (
    user_id TEXT NOT NULL REFERENCES holavon_horary_quota(user_id),
    request_id UUID NOT NULL,
    quota_type TEXT NOT NULL CHECK (quota_type IN ('free', 'pro')),
    quota_day DATE NOT NULL,
    remaining INTEGER NOT NULL CHECK (remaining >= 0),
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, request_id)
);
ALTER TABLE holavon_horary_reservations ADD COLUMN IF NOT EXISTS completed BOOLEAN NOT NULL DEFAULT FALSE;

-- The application backend connects as its own database role; client-side
-- PostgREST roles must not read or modify counters directly.
ALTER TABLE holavon_horary_quota ENABLE ROW LEVEL SECURITY;
ALTER TABLE holavon_horary_reservations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE holavon_horary_quota FROM PUBLIC;
REVOKE ALL ON TABLE holavon_horary_reservations FROM PUBLIC;
