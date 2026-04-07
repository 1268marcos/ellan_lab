SELECT
    cp.profile_code,
    pmc.code AS payment_method_code,
    pic.code AS payment_interface_code,
 

    cpmi.is_default,
    cpmi.is_active,
    cpmi.sort_order


 FROM capability_profile_method_interface cpmi

JOIN capability_profile_method cpm ON cpm.id = cpmi.profile_method_id


JOIN capability_profile cp ON cp.id = cpm.profile_id


JOIN payment_method_catalog pmc ON pmc.id = cpm.payment_method_id


JOIN payment_interface_catalog pic ON pic.id = cpmi.payment_interface_id


WHERE cp.id = 7
ORDER BY pmc.code, cpmi.sort_order, cpmi.id;