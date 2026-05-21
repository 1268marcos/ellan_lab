-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 11_rls_policies.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: invoices; Type: ROW SECURITY; Schema: public; Owner: admin
--


ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

--
-- Name: invoices invoices_partner_isolation; Type: POLICY; Schema: public; Owner: admin
--


CREATE POLICY invoices_partner_isolation ON public.invoices USING ((((tenant_id)::text = (public.get_current_tenant_id())::text) OR ((ecommerce_partner_id)::text = (public.get_current_partner_id())::text) OR ((public.get_current_user_role())::text = 'admin'::text)));


--
-- Name: order_items; Type: ROW SECURITY; Schema: public; Owner: admin
--


ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

--
-- Name: order_items order_items_partner_isolation; Type: POLICY; Schema: public; Owner: admin
--


CREATE POLICY order_items_partner_isolation ON public.order_items USING ((EXISTS ( SELECT 1
   FROM public.orders o
  WHERE (((o.id)::text = (order_items.order_id)::text) AND (((o.ecommerce_partner_id)::text = (public.get_current_partner_id())::text) OR ((public.get_current_user_role())::text = 'admin'::text))))));


--
-- Name: orders; Type: ROW SECURITY; Schema: public; Owner: admin
--


ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

--
-- Name: orders_partitioned; Type: ROW SECURITY; Schema: public; Owner: admin
--


ALTER TABLE public.orders_partitioned ENABLE ROW LEVEL SECURITY;

--
-- Name: orders orders_partner_isolation; Type: POLICY; Schema: public; Owner: admin
--


CREATE POLICY orders_partner_isolation ON public.orders USING ((((ecommerce_partner_id)::text = (public.get_current_partner_id())::text) OR ((public.get_current_user_role())::text = 'admin'::text) OR ((public.get_current_user_role())::text = 'ops'::text)));


--
-- Name: orders orders_tenant_isolation; Type: POLICY; Schema: public; Owner: admin
--


CREATE POLICY orders_tenant_isolation ON public.orders USING ((((tenant_id)::text = (public.get_current_tenant_id())::text) OR ((public.get_current_user_role())::text = 'admin'::text)));


--
-- Name: pickups; Type: ROW SECURITY; Schema: public; Owner: admin
--


ALTER TABLE public.pickups ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

