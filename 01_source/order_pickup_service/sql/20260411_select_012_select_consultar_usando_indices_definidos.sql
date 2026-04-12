-- Usando ix_capability_profile_region
SELECT * FROM public.capability_profile WHERE region_id = 1;

-- Usando ix_capability_profile_channel
SELECT * FROM public.capability_profile WHERE channel_id = 2;

-- Usando ix_capability_profile_context
SELECT * FROM public.capability_profile WHERE context_id = 4;

-- Usando ix_capability_profile_active
SELECT * FROM public.capability_profile WHERE is_active = TRUE;

-- Usando ix_capability_profile_priority
SELECT * FROM public.capability_profile WHERE priority >= 100;