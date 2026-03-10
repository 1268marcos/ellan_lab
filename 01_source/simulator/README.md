# simulator

Simulador de hardware do locker para ambiente local/DEV.

## Papel deste serviço

Este componente simula o comportamento físico do locker:

- 24 portas/gavetas
- abertura de porta via MQTT
- comando de luz via MQTT
- heartbeat periódico
- injeção de falhas
- estados de porta para teste operacional

## O que este serviço NÃO é

Este serviço não é o dono do fluxo de negócio.

Ele não substitui:

- `order_pickup_service`
- `backend_sp`
- `backend_pt`
- `payment_gateway`

O fluxo oficial continua sendo:

1. `order_pickup_service` cria/confirma pedido
2. `backend_sp` ou `backend_pt` envia comando MQTT
3. `simulator` consome o comando e simula a porta

## Tópicos MQTT usados

### Comandos recebidos
- `locker/{REGION}/doors/cmd`
- `locker/{REGION}/doors/light/cmd`

### Eventos publicados
- `locker/{REGION}/doors/events`
- `locker/{REGION}/doors/heartbeat`

### Fallback opcional de DEV
- `locker/{REGION}/pagamento`

> Observação: `PAYMENT_TRIGGERS_OPEN=false` é o padrão recomendado.

## Variáveis de ambiente

- `MQTT_HOST` → host do broker MQTT
- `MQTT_PORT` → porta do broker MQTT
- `REGION` → `SP` ou `PT`
- `LOCKER_ID` → identificador do locker
- `FAILURE_RATE` → taxa de falha simulada
- `PAYMENT_TRIGGERS_OPEN` → fallback DEV para abrir via tópico de pagamento
- `DEBUG_LOGS` → habilita logs detalhados

## Estados simulados

Estados normais:
- `IDLE`
- `OPENING`
- `OPEN`
- `CLOSING`
- `CLOSED`

Estados de falha:
- `JAMMED`
- `SENSOR_ERROR`
- `POWER_FAIL`

## Uso esperado na FASE 3 — V

Este simulador é usado para validar:

- pagamento KIOSK aprovado
- comando de abertura da gaveta
- comando de luz
- falha de abertura
- falha de fechamento
- heartbeat do locker
- comportamento por região (`SP` / `PT`)

## Observações

- O simulador atual trabalha em nível de hardware/MQTT.
- Ele ainda não persiste inventário nem alocação.
- A alocação continua sendo responsabilidade do backend regional.