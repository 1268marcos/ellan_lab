# backend/runtime

Runtime operacional multi-locker da plataforma ELLAN.

## Objetivo
Unificar a lógica operacional antes duplicada em backend_sp/backend_pt
em um único serviço multi-locker, multi-região e preparado para SaaS.

## Princípios
- `X-Locker-Id` como identidade operacional principal
- sem `MACHINE_ID` fixo por processo como regra principal
- sem suposição de 24 slots fixos
- ONLINE e KIOSK devem refletir o mesmo estado operacional