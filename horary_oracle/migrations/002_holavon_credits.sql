-- Purchased Horary credits live next to the free/Pro allowance but are a
-- separate, non-expiring wallet. A question first spends the daily allowance
-- and only then one purchased credit.
ALTER TABLE holavon_horary_quota
    ADD COLUMN IF NOT EXISTS credit_balance INTEGER NOT NULL DEFAULT 0
    CHECK (credit_balance >= 0);

-- Reservations may now be paid for by a purchased credit too.
ALTER TABLE holavon_horary_reservations
    DROP CONSTRAINT IF EXISTS holavon_horary_reservations_quota_type_check;
ALTER TABLE holavon_horary_reservations
    ADD CONSTRAINT holavon_horary_reservations_quota_type_check
    CHECK (quota_type IN ('free', 'pro', 'credit'));

-- Idempotent credit ledger. transaction_id comes from the store
-- (RevenueCat/Play) and must never grant the same purchase twice.
CREATE TABLE IF NOT EXISTS holavon_horary_credit_ledger (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),
    source TEXT NOT NULL DEFAULT 'revenuecat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS holavon_horary_credit_ledger_user_idx
    ON holavon_horary_credit_ledger (user_id, created_at DESC);

-- Only the application backend role may touch the wallet or its ledger.
ALTER TABLE holavon_horary_credit_ledger ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE holavon_horary_credit_ledger FROM PUBLIC;
