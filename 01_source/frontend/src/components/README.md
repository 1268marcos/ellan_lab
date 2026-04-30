# OPS UI Components - Quick Index

Guia curto para acelerar adoção dos componentes-base da camada OPS.

## Componentes base

- `OpsActionButton.tsx`
  - Botão padrão OPS com variantes visuais:
    - `primary`
    - `secondary`
    - `warn`
    - `copy`
  - Uso rápido:
    - `<OpsActionButton variant="primary">Executar</OpsActionButton>`
    - `<OpsActionButton variant="copy">Copiar evidência</OpsActionButton>`

- `OpsScenarioPresets.jsx`
  - Grupo de presets coloridos por cenário:
    - `success` (verde)
    - `warn` (âmbar)
    - `error` (vermelho)
  - Uso rápido:
    - `<OpsScenarioPresets items={[{ id: "ok", tone: "success", label: "Preset verde", onClick: fn }]} />`

- `OpsTrendKpiCard.jsx`
  - Card KPI com destaque de tendência (`up`, `down`, `stable`).
  - Inclui helper `resolveTrendByDelta(delta)`.

## Tela de referência (uso combinado)

- `src/pages/OpsLogisticsReturnsPage.jsx`
  - Exemplo completo com:
    - filtros operacionais
    - `OpsScenarioPresets`
    - `OpsActionButton`
    - chips e painel técnico para handoff

## Regra prática de adoção

- Ao criar nova página OPS:
  1) comece por `OpsActionButton` para ações
  2) use `OpsScenarioPresets` para presets operacionais
  3) use `OpsTrendKpiCard` quando houver comparação temporal/KPI
  4) evite estilos inline duplicados para manter consistência
