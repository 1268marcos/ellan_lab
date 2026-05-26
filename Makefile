# Raiz do Ellan Lab — alvos utilitários para desenvolvimento e CI.
.PHONY: test-collect test-payment-contract test-order-pickup-admin test-analytics-bi-admin e2e-payment-p0 e2e-payment-ui migrate-partner-admin-security migrate-partner-admin-security-sqlite

# pytest --collect-only em billing_fiscal_service, order_pickup_service e payment_gateway.
# Exige .venv + requirements.txt instalados em cada serviço (ver 07_tests/run_backend_test_collect.sh).
test-collect:
	@chmod +x 07_tests/run_backend_test_collect.sh
	@./07_tests/run_backend_test_collect.sh

# Contratos pagamento → runtime (gateway) e pickup → lifecycle (cancel prepayment).
test-payment-contract:
	@chmod +x 07_tests/run_payment_runtime_contract_tests.sh
	@./07_tests/run_payment_runtime_contract_tests.sh

test-order-pickup-admin:
	cd 01_source/order_pickup_admin_service && PYTHONPATH=. SEED_ON_START=false .venv/bin/pytest tests/ -q

test-analytics-bi-admin:
	cd 01_source/analytics_bi_admin_service && PYTHONPATH=. SEED_ON_START=false .venv/bin/pytest tests/ -q

# E2E pagamento (P2): POST /orders (dev bypass) → gateway /gateway/payment/create → payment-confirm.
# E2E_CREATE_ORDER_VIA=seed: allocate + psql seed (legado). E2E_SKIP_GATEWAY=1 omite o gateway.
# Pré-requisito: ./deploy/compose-minimal-stack.sh; pickup com DEV_BYPASS_AUTH=true em lab (env.e2e-minimal).
# Locker default SP-CARAPICUIBA-JDMARILU-LK-002; slots via GET /locker/slots (não fixo em 24).
e2e-payment-p0:
	@chmod +x 07_tests/e2e_payment_minimal_stack.sh
	@./07_tests/e2e_payment_minimal_stack.sh

# P3 — Playwright no checkout (smoke sem stack; fluxo DEV com E2E_PUBLIC_AUTH_TOKEN + stack).
# PLAYWRIGHT_START_VITE=0 se o Vite já estiver no ar em FRONTEND_BASE_URL.
e2e-payment-ui:
	@chmod +x 07_tests/e2e_payment_ui_playwright.sh
	@./07_tests/e2e_payment_ui_playwright.sh

migrate-partner-admin-security:
	@chmod +x 02_docker/postgres_central/ops/apply_partner_admin_security_migrations.sh
	@./02_docker/postgres_central/ops/apply_partner_admin_security_migrations.sh

migrate-partner-admin-security-sqlite:
	@chmod +x 01_source/partner_admin_service/scripts/apply_migrations.sh
	@./01_source/partner_admin_service/scripts/apply_migrations.sh
