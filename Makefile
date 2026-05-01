# Raiz do Ellan Lab — alvos utilitários para desenvolvimento e CI.
.PHONY: test-collect test-payment-contract e2e-payment-p0

# pytest --collect-only em billing_fiscal_service, order_pickup_service e payment_gateway.
# Exige .venv + requirements.txt instalados em cada serviço (ver 07_tests/run_backend_test_collect.sh).
test-collect:
	@chmod +x 07_tests/run_backend_test_collect.sh
	@./07_tests/run_backend_test_collect.sh

# Contratos pagamento → runtime (gateway) e pickup → lifecycle (cancel prepayment).
test-payment-contract:
	@chmod +x 07_tests/run_payment_runtime_contract_tests.sh
	@./07_tests/run_payment_runtime_contract_tests.sh

# E2E pagamento: runtime → seed → gateway /gateway/payment/create (P1) → pickup payment-confirm.
# E2E_SKIP_GATEWAY=1 reproduz só o caminho sem gateway. Pré-requisito: ./deploy/compose-minimal-stack.sh
# Locker default SP-CARAPICUIBA-JDMARILU-LK-002; slots via GET /locker/slots (não fixo em 24).
e2e-payment-p0:
	@chmod +x 07_tests/e2e_payment_minimal_stack.sh
	@./07_tests/e2e_payment_minimal_stack.sh
