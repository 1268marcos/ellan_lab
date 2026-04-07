ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'creditCard';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'debitCard';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'pix';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'boleto';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'apple_pay';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'google_pay';
ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'cash';