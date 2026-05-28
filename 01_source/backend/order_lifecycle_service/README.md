# order_lifecycle_service

Serviço dedicado ao lifecycle operacional e analítico de pedidos do ELLAN Lab Locker.

## Responsabilidades iniciais
- deadlines explícitos
- timeout pré-pagamento
- eventos de domínio
- facts analíticos
- worker dedicado

## Tabelas iniciais
- lifecycle_deadlines
- domain_events
- analytics_facts

## Configuração — health score

Pesos do pickup health score (`compute_health`) são configuráveis via variável de ambiente:

```bash
HEALTH_SCORE_WEIGHTS="efficiency=0.35,reliability=0.25,risk=0.30,trend=0.10"
```

Regras de validação (na startup):

- Chaves obrigatórias: `efficiency`, `reliability`, `risk`, `trend`
- Cada peso entre `0.0` e `1.0`
- Soma dos pesos ≈ `1.0` (tolerância `0.01`)

Se a configuração for inválida, o serviço registra `health_score_weights_invalid_using_defaults` e usa o default:

`efficiency=0.40,reliability=0.20,risk=0.25,trend=0.15`