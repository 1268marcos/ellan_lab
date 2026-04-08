-- Core table for product catalog management
CREATE TABLE public.products (
    -- Primary identifier, matches orders.sku_id and order_items.sku_id
    id VARCHAR(255) NOT NULL PRIMARY KEY,

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pricing (stored as cents to avoid floating point errors)
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
    
    -- Categorization (aligns with existing product_categories table)
    category_id VARCHAR(64) NULL, -- Foreign key to product_categories(id)
    
    -- Logistics & Dimensions (in millimeters and grams, standard in the backup)
    width_mm INTEGER,
    height_mm INTEGER,
    depth_mm INTEGER,
    weight_g INTEGER,
    
    -- Flags for business rules
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE,
    requires_id_check BOOLEAN NOT NULL DEFAULT FALSE,
    requires_signature BOOLEAN NOT NULL DEFAULT FALSE,
    is_hazardous BOOLEAN NOT NULL DEFAULT FALSE,
    is_fragile BOOLEAN NOT NULL DEFAULT FALSE,
    is_virtual BOOLEAN NOT NULL DEFAULT FALSE, -- For gift cards, tickets, etc.
    
    -- Metadata for flexible, schema-less data (as seen in other tables)
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for performance, following the pattern in your backup
CREATE INDEX idx_products_category ON public.products (category_id);
CREATE INDEX idx_products_is_active ON public.products (is_active);
CREATE INDEX idx_products_created_at ON public.products (created_at);

-- Add foreign key constraint for category
ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);

COMMENT ON TABLE public.products IS 'Central product catalog, aligning with sku_id used in orders and order_items.';
COMMENT ON COLUMN public.products.id IS 'SKU ID, matches orders.sku_id.';
COMMENT ON COLUMN public.products.amount_cents IS 'Price in cents to avoid floating point errors.';
COMMENT ON COLUMN public.products.metadata_json IS 'Flexible JSON field for additional product attributes.';
