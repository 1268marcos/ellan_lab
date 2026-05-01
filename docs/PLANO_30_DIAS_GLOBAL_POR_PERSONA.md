# ELLAN LAB - Plano de 30 dias por persona (Global + KIOSK Touch)

## Objetivo
Transformar o roadmap atual em execucao imediata orientada a:
- **escala global** (sem visao fixa por pais/regiao);
- **KIOSK como totem touch** para compra, retirada e alocacao de itens de parceiros;
- melhores praticas combinadas de **Engenharia de Software**, **UX/CX** e **Produto**.

## Premissas globais obrigatorias
- Arquitetura **global-first**: multi-pais, multi-moeda, multi-idioma, multi-fuso, requisitos fiscais configuraveis por jurisdicao.
- Contratos de API versionados e orientados a dominio (checkout, pickup, partners, ops, support).
- Observabilidade ponta a ponta com correlacao por `order_id`, `partner_id`, `kiosk_id`, `correlation_id`.
- Seguranca por padrao: principio de menor privilegio, segregacao de funcoes, trilha de auditoria e politicas CSP.
- Produto orientado a metricas por jornada (compra, retirada, alocacao, atendimento).

## Incorporacao de recomendacoes do `docs/caso_frontend.pdf`
Recomendacoes incorporadas e ajustadas para contexto global:

1. **Estilos inline -> sistema de estilos consistente**
   - Adotar **Tailwind** (rapidez e consistencia) ou **CSS Modules** (escopo local), com design tokens globais.
   - Motivo: escalabilidade visual, CSP mais forte, menor regressao e melhor manutencao.
   - Decisao: iniciar com estrategia hibrida orientada por dominio critico (checkout/kiosk/ops primeiro).

2. **Estado complexo -> store central**
   - Consolidar `currentOrder`, `payResp`, `pickupResp`, `syncStatus` em store (Zustand recomendado).
   - Motivo: fonte unica da verdade, menos race conditions, testes melhores e menor acoplamento.
   - Regra: `useReducer` para estados locais de formulario; store para estado de fluxo.

3. **Error Boundaries por dominio**
   - Aplicar boundaries em rotas/areas criticas (`checkout`, `kiosk`, `ops`, `my-orders`), nao apenas no App raiz.
   - Motivo: evitar tela branca, conter falhas e reduzir MTTR com observabilidade.

4. **TypeScript incremental (iniciar agora)**
   - Iniciar com `allowJs`, `checkJs`, `strict: false`, evoluindo para `strict: true` por etapas.
   - Prioridade de migracao: hooks criticos, store, contratos de API, paginas de checkout/kiosk/ops.

Esses quatro itens entram no plano como backlog tecnico transversal de P0/P1.

---

## Estrutura do plano (30 dias)

### Onda 1 (Dias 1-7) - Fundacao global e UX operacional
- Fechar contratos globais por dominio (checkout, pickup, partners, support).
- Definir arquitetura de estado frontend e padrao de estilos.
- Definir modelos de tela KIOSK touch v1.
- Instrumentar erro/telemetria minima em fluxos criticos.

### Onda 2 (Dias 8-18) - P0 de jornada do usuario + trilhas fiscal/contabil
- Entregar fluxos P0 de comprador online e comprador KIOSK.
- Entregar P0 de OPS e suporte para incidentes recorrentes.
- Estabilizar E2E principal de compra -> pagamento -> retirada/alocacao.
- Incluir trilha Fiscal e trilha Contabil (ELLAN LAB + partners) no escopo operacional de Sprint 2.

### Onda 3 (Dias 19-24) - Hardening e escala de parceiros
- Fechar P0 de parceiros e reconciliacao operacional.
- Endurecer seguranca, auditoria e recuperacao de falhas.
- Consolidar playbooks e treinamento curto para operacao.

### Onda 4 (Dias 25-30) - Readiness global e Go/No-Go
- Fechar P1 prioritarios por persona.
- Rodar regressao final, UAT de personas e checklist de rollout.
- Aprovar gate de producao por KPI e risco residual.

---

## Recomendacao atual — onde codar (checkpoint)

**Carimbo:** 2026-05-01 (atualização; último checkpoint completo 2026-04-30). Rever esta secao sempre que o comité mudar prioridade ou quando Fiscal/Contabil/Consolidado S2 cruzarem limiares do **gate v2**.

### Uma frase (foco dominante)
**Codar primeiro na Sprint 2**, na trilha **Fiscal + Contábil** (P0 e sequencia **D10–D18**), até aproximar o **gate v2** (Fiscal **≥50%**, Contábil **≥40%**, consolidado Sprint 2 **≥55%**, mais comprovação P0 em artefato de daily/ZIP). Em **paralelo seguro**, reservar **~25–35%** da capacidade de engenharia para **Sprint 1** (subir protótipos KIOSK **45% → ≥60%**, E2E assistido ou estilos checkout) para não perder o embalo da fundação FE/KIOSK.

### Por que esta ordem
| Se escolher… | Risco / beneficio |
| --- | --- |
| **Só Sprint 1** | Fundação e KIOSK avançam, mas **Sprint 3/4** continuam **congeladas** em net-new até o **gate v2**; Go/No-Go fica sem base financeira. |
| **Só Sprint 3 ou 4** | **Desalinhado** com a fase **A — Pré-gate** do plano: expansão antes do financeiro suficiente aumenta retrabalho e pressão no aceite. |
| **Sprint 2 dominante + fatia S1** | Maximiza **progresso no gargalo** (Fiscal **~28%**, Contábil ~15%, consolidado ~52% vs limiares v2) **sem** abandonar o **#1 capacidade FE** (Sprint 1 ~**61%**; meta **≥60%** cumprida no limiar; ver snapshots *(vii)*–*(viii)*). |

### Duas frentes (se houver duas pessoas)
| Frente | Sprint | O que codificar agora |
| --- | --- | --- |
| Negócio / integração fiscal-contábil | **Sprint 2** | Itens P0 da tabela **Backlog detalhado Sprint 2** e dias **D10–D18**; subir percentuais com evidência anexável ao daily. |
| Produto / FE capacidade | **Sprint 1** | **`/ops/kiosk-touch-models`** (protótipos **`[~]` ~64%** — smoke Playwright + cockpit), **E2E KIOSK fluxo completo** (compra→retirada ainda **`[ ]`**), ou **migração de estilos** checkout em fatias pequenas. |

### Uma pessoa (solo) — ritmo sugerido
1. **Uma unidade de trabalho Sprint 2** por ciclo (ex.: um P0 fiscal ou contábil com export ou trilha consultável).  
2. Em seguida **uma unidade Sprint 1** (ex.: incremento no cockpit KIOSK ou passo de E2E).  
3. Repetir até o **gate v2** PASS ou até o comité reordenar.

### Alocação numérica (codificação)
- **~65–75%** da capacidade de **codificação** na **Sprint 2** (trilha fiscal/contábil, consolidado rumo ao **gate v2**: Fiscal ≥50%, Contábil ≥40%, consolidado Sprint 2 ≥55%, comprovação P0).  
- **~25–35%** em **Sprint 1** (protótipos KIOSK, E2E assistido, estilos checkout) para sustentar a média do checklist Sprint 1 rumo a **≥60%** sem perder o desbloqueio de S3/S4.

### Evidência no repositório (checkpoint)
- **`FiscalGlobalPage.jsx`:** painel compacto **Sprint 2 — gate v2** com atalhos para `fiscal/management-daily`, `fiscal/accounting-close`, `fiscal/sprint2-finance-gate` e `fiscal/readiness-execution` (hub `fiscal/global`); lembrete textual do runbook `docs/runbooks/FISCAL_CATALOGO_SEM_UI_POR_PAIS.md`.  
- **`OpsKioskTouchModelsPage.tsx`:** checklist heurística **n≥8** com persistência em `localStorage`, **export JSON**, **recarregar definições** de modelos (`localStorage` merge por id), **`e2e/kiosk-touch-models.spec.ts`** (Playwright + mock `/public/auth/me*`, `VITE_ENABLE_OPS_ROUTES` no `webServer`).  
- **D11 — conciliação por `order_id` (Sprint 2):** `fiscalD11OrderIdRollup.js` + **`fiscalD11OrderIdRollup.test.js`** (Vitest); **`OpsFiscalProvidersPage.jsx`** — cartão *fila P0 por order_id*, export **`SPRINT2_D11_ORDER_ID_ROLLUP_*.json`**, handoff `localStorage` com `order_id_rollup`; **`FiscalManagementDailyPage.jsx`** — D12 com tabela + export + **`SPRINT2_D11_ORDER_ID_ROLLUP_*.json`** assinado no ZIP diário; **`FiscalAccountingClosePage.jsx`** — mesmo anexo **`SPRINT2_D11_ORDER_ID_ROLLUP_EXEC_*.json`** no ZIP executivo quando o lote D11 existir.
- **D12/D13 — handoff contábil e aceite (Sprint 2, paridade D11):** `fiscalSprint2D12D13Evidence.js` + **`fiscalSprint2D12D13Evidence.test.js`**; **`FiscalManagementDailyPage.jsx`** — export **`SPRINT2_D12_ACCOUNTING_HANDOFF_*.json`**, **`SPRINT2_D13_ACCOUNTING_ACCEPTANCE_*.json`** e anexos assinados **`SPRINT2_D12_*` / `SPRINT2_D13_*`** no pacote diário (.zip); **`FiscalAccountingClosePage.jsx`** — **`SPRINT2_D12_ACCOUNTING_HANDOFF_EXEC_*`** e **`SPRINT2_D13_ACCOUNTING_ACCEPTANCE_EXEC_*`** no ZIP executivo (com token + bloco P0-1b).
- **Checkout público (Sprint 1 — estilos, fatias 1–2):** **`src/styles/publicCheckoutChrome.css`** — passos, trust, spinners; hero; grelha; cartões resumo/pagamento; highlight SKU; formulário; `data-testid` **`public-checkout-summary-card`** / **`public-checkout-payment-card`**; sem inject de `@keyframes` no `document.head`.
- **`FiscalGlobalPage.jsx` (faixa Sprint 3):** atalhos **hardening** — `fiscal/slo-alerts`, `fiscal/incident-response`, `fiscal/sprint3-partner-audit`, `ops/quick-enablement`, `ops/reconciliation`.
- **`FiscalSprint3PartnerAuditPage.jsx`:** checklist de **handoff de sessão** (6 itens) + export JSON `SPRINT3_PARTNER_AUDIT_HANDOFF_SESSION_*`.
- **Sprint 2 / gate v2:** `fiscalSprint2FinanceGate.js` (chave `localStorage` + limiares); **`FiscalManagementDailyPage.jsx`** — cartão **espelho gate v2** + anexo ZIP `SPRINT2_GATE_V2_MIRROR_*`; **`FiscalAccountingClosePage.jsx`** — mesmo anexo no ZIP executivo (`*_EXEC_*`); **`FiscalSprint2FinanceGatePage.jsx`** — cockpit passa a usar o util partilhado; **`FiscalReadinessExecutionPage.jsx`** (`fiscal/readiness-execution`) — espelho na trilha FG-1, export JSON com `sprint2_gate_v2_mirror` + handoff texto alinhado; **`FiscalFg1GatePage.jsx`** (`fiscal/fg1-gate`) — **ponte FG-1 ↔ gate v2** (espelho + export `FG-1-FINAL-DECISION` com `sprint2_gate_v2_mirror`).

### O que nao fazer agora como foco principal
- **Não** abrir net-new grande em **Sprint 3** (hardening) ou **Sprint 4** (Go/No-Go) como substituto da subida Fiscal/Contábil/Consolidado enquanto a fase **A — Pré-gate** estiver ativa (ver tabela **Sprint ideal na sequência** na Sprint 2).

---

## Backlog por persona (P0/P1, dono, esforco, aceite)

## 1) Persona: Comprador ONLINE
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Checkout resiliente global (credito, erros acionaveis, fallback) | Eng Backend + Eng Frontend | 8 pts | Conversao checkout +5 p.p.; erros nao tratados <1%; fluxos validados em 3 moedas |
| P0 | Jornada transparente de pedido (status, invoice, notificacoes) | Produto + UX/CX + Frontend | 5 pts | Reducao >=30% em tickets de status; satisfacao pos-compra >= meta interna |
| P1 | Hardening de seguranca de conta (step-up em acao sensivel) | Security Eng + Backend | 3 pts | 100% das acoes sensiveis com politica aplicada e auditada |
| P1 | Experimentos UX de abandono por mercado/canal | Produto + UX Research | 3 pts | 2 experimentos ativos com leitura estatistica minima |

## 2) Persona: Comprador KIOSK (Totem Touch)
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Fluxo KIOSK proprio (compra, pagamento, abertura, retirada) | Eng Backend Kiosk + Eng Frontend Kiosk | 8 pts | Tempo p95 E2E <= 90s; taxa de conclusao assistida >=85% |
| P0 | Modelos de tela KIOSK v1 (Quick Buy, Guided Buy, Pickup Fast Lane, Partner Allocation) | Product Designer + UX Writer | 5 pts | 4 modelos navegaveis com testes moderados (n>=8) e ajustes aplicados |
| P1 | Recuperacao de erros no totem (timeout, slot indisponivel, falha pagamento) | UX/CX + Eng Orquestracao | 3 pts | 100% de erros criticos com rota de recuperacao clara |
| P1 | Localizacao global (idioma/microcopy/acessibilidade touch) | Produto + Localizacao + UX | 3 pts | Idiomas base habilitados sem truncamento; contraste e toque em conformidade |

## 3) Persona: Operadores de Sistema (OPS)
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Painel unificado global (pedidos, kiosk, parceiros, fiscal) | Plataforma + Produto OPS | 8 pts | MTTR -30%; 95% dos incidentes resolvidos com trilha por `order_id` |
| P0 | Runbooks por incidente + auditoria ponta a ponta | OPS Eng + Suporte N2 | 5 pts | Top 10 incidentes com runbook; 100% acoes criticas auditadas |
| P1 | Alertas por SLO com reducao de ruido | SRE + Data | 3 pts | Ruido de alerta -40%; cobertura de SLO >=90% |
| P1 | Enablement rapido de operadores | Produto OPS + Enablement | 2 pts | Onboarding operacional de novo operador <=2 dias |

## 4) Persona: Parceiros (todos os niveis)
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Contrato global de parceiro (API, SLA, faturamento, reconciliacao) | Produto Plataforma + Integracoes | 8 pts | Contrato versionado publicado; onboarding sem excecao para niveis alvo |
| P0 | Portal parceiro v1 (pedidos, repasses, disputas) | Frontend + Backend Parceiros | 5 pts | Operacao basica sem dependencia recorrente de suporte manual |
| P1 | Scorecard de performance por parceiro | Data + Operacoes | 3 pts | KPIs ativos: fill rate, SLA, cancelamento, disputa |
| P1 | Politica global de qualidade de catalogo de parceiros | Produto Catalogo + Parceiros | 3 pts | Erro critico de cadastro <2% no onboarding |

## 5) Persona: Equipes de Suporte (N1/N2/N3)
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Console de atendimento por jornada | Produto Suporte + Eng Ferramentas Internas | 8 pts | FCR +20%; TMA -25% |
| P0 | Playbooks e macros com auto-triagem | Suporte N2 + UX Conteudo | 5 pts | 80% dos casos recorrentes com fluxo padronizado |
| P1 | Base de conhecimento conectada a eventos do produto | Enablement + Data Eng | 3 pts | Sugestao automatica de artigo em 70% dos tickets elegiveis |
| P1 | Feedback loop suporte -> produto (quinzenal) | Produto + CX Ops | 2 pts | Top 5 dores do suporte sempre no backlog com owner |

---

## Workstream tecnico transversal (P0/P1)

## P0 (obrigatorio nos 30 dias)
| Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|
| Migracao inicial de estilos inline para base tokenizada (Tailwind/CSS Modules) | Frontend Platform | 8 pts | >=70% das telas criticas sem inline style novo |
| Store global de checkout/kiosk (Zustand) | Frontend Architecture | 5 pts | Estado critico unificado sem dessicronizacao conhecida |
| Error Boundaries por dominio + observabilidade | Frontend + SRE | 3 pts | Tela branca eliminada nas rotas criticas |
| Setup TypeScript incremental (allowJs/checkJs) + CI `tsc --noEmit` | Frontend Platform | 5 pts | Pipeline executa tipagem incremental sem bloquear sprint |

## P1 (imediatamente apos P0)
| Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|
| Evoluir TypeScript para `noImplicitAny` em modulos criticos | Frontend Platform | 3 pts | Cobertura tipada dos modulos criticos >=80% |
| Fortalecer CSP e politicas de seguranca de frontend | Security + Frontend | 3 pts | CSP sem excecoes perigosas em producao |

---

## KIOSK Touch - Modelos de tela (v1)

## Modelo A - Quick Buy
- Para compras rapidas e recorrentes.
- UX: poucos passos, CTA principal sempre visivel, foco em velocidade.

## Modelo B - Guided Buy
- Para novos usuarios ou carrinho mais complexo.
- UX: fluxo assistido, validações progressivas, linguagem simples.

## Modelo C - Pickup Fast Lane
- Para retirada por QR/codigo/manual.
- UX: entrada unica, confirmacao rapida, recuperacao de erro objetiva.

## Modelo D - Partner Allocation
- Para operacao de alocacao de itens de parceiros.
- UX: clareza de slot, lote, status e confirmacao com rastreabilidade.

## Requisitos de UX/CX para todos os modelos
- Alvo touch minimo de 44px.
- Contraste e legibilidade em ambiente com reflexo.
- Tempo de resposta visual imediato (feedback de clique/estado).
- Modo assistido para operacao de alto fluxo.
- Fallback claro em erro e tempo limite.

---

## Governanca de execucao (cadencia diaria)
- Daily de 20 minutos com owners de persona.
- Kanban unico com trilhas: Produto, UX/CX, Engenharia, Operacao.
- Politica de bloqueio: item P0 parado >24h entra em war room.
- Review quinzenal de UX com base em evidencias (nao opiniao).
- Gate Go/No-Go no dia 30 com aprovacao conjunta (Produto + Eng + Operacao).

## Definicao de pronto (DoD)
Um item so e considerado concluido quando tiver:
1. implementacao tecnica;
2. telemetria minima;
3. criterio de aceite medido;
4. runbook/checklist operacional;
5. comunicacao de mudanca para suporte/operacao.

---

## Riscos principais e mitigacao
- **Risco:** escopo global virar customizacao local ad-hoc.  
  **Mitigacao:** contratos configuraveis por jurisdicao e feature flags por capacidade.

- **Risco:** KIOSK copiar o fluxo online e perder semantica operacional.  
  **Mitigacao:** dominio proprio de KIOSK com estados e UX especificos.

- **Risco:** debito tecnico de frontend crescer durante entrega rapida.  
  **Mitigacao:** trilha transversal P0 (estilos, store, boundaries, TS incremental).

- **Risco:** operacao nao absorver novas capacidades.  
  **Mitigacao:** runbooks, treinamento rapido e console de suporte orientado a jornada.

---

## Entregaveis esperados ao final dos 30 dias
- Backlog P0 executado por persona.
- P1 prioritarios iniciados/completados conforme capacidade.
- KIOSK touch v1 operacional com 4 modelos de tela.
- Frontend com base tecnica reforcada (estilos, estado, erros, TS incremental).
- Operacao e suporte com runbooks e trilha de auditoria utilizaveis em producao.

---

## Tecnica de evolucao de sprint (mesmo padrao de acompanhamento)

## Legenda de status
- `[ ]` Nao iniciado
- `[~]` Em andamento
- `[x]` Concluido
- `[!]` Bloqueado / risco

## Ritual de evolucao (obrigatorio)
- Atualizar este documento com carimbo de data ao fim de cada dia util.
- Registrar por sprint: **o que entrou**, **o que saiu**, **riscos**, **decisao executiva**.
- Quando percentuais mudarem, atualizar também a subsecção **«Evolução percentual entre snapshots»** (Sprint 1 / Sprint 3) com **antes**, **depois** e **Δ** em pontos percentuais, para o comité ver tendência sem reabrir notas espalhadas.
- Em cada checkpoint de comité ou fim de sprint, rever e **atualizar o carimbo** na secção **«Recomendacao atual — onde codar»** (após **Estrutura do plano (30 dias)**) para refletir gate v2, média Sprint 1 e capacidade disponível.
- Nao mover item para `[x]` sem cumprir DoD (codigo + telemetria + aceite + runbook + comunicacao).

## Sprint 0 (Dias 1-2) - Baseline e setup de execucao
Objetivo: iniciar governanca e reduzir risco de desalinhamento.

Owner nominal unico da sprint:
- **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**

**Status geral Sprint 0:** `[x]` **Encerrado (escopo lab / governanca)** — 2026-04-30. Os itens abaixo fecham o *setup* de execucao; valores numericos de KPI em producao e contratos versionados para parceiros externos seguem evoluindo nas sprints seguintes com DoD de entrega de software.

Checklist:
- [x] Congelar baseline de KPI por persona (conversao, MTTR, FCR, abandono KIOSK). **Progresso: 100% (v0 documental)**
  - Owner: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**
  - Evidencia: tabela **Baseline KPI v0** no carimbo `### 2026-04-30 - Sprint 0 encerramento operacional` abaixo (fonte + meta; valores numericos iniciais quando houver pipeline de dados).
- [x] Publicar owners nominais por backlog P0/P1. **Progresso: 100%**
  - Owner: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**
  - Nota daily: ownership centralizado por decisao operacional (time unipessoal).
- [x] Criar board unico com swimlanes por persona + workstream transversal. **Progresso: 100% (v0)**
  - Owner: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**
  - Evidencia: este documento (tabela de sprints + backlog por persona + registro de entregas) + acompanhamento em `docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt` onde aplicavel.
- [x] Definir contratos globais minimos para checkout/kiosk/partners/ops/support. **Progresso: 100% (v0 referencial)**
  - Owner: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**
  - Evidencia: mapa **Contratos minimos v0** no mesmo carimbo (superficies e repos existentes no lab; exemplos de payload JSON nos cockpits fiscais/exports ja tratados como evidencia viva).

### 2026-04-30 - Sprint 0 encerramento operacional (lab)
Status geral: `[x]` Concluido (governanca + baseline v0; nao substitui medicao de producao nas sprints seguintes)

**Baseline KPI v0 (estrutura + fonte alvo; valores numericos TBD ate instrumentacao)**

| KPI (persona) | Fonte alvo no lab | Valor inicial v0 | Meta qualitativa Sprint 30 |
|---|---|---|---|
| Conversao checkout (ONLINE) | Funis em checkout + telemetria de erro | TBD | +5 p.p. vs baseline quando medido |
| MTTR incidente (OPS) | `ops/health`, pacotes diarios, runbooks | TBD | -30% vs baseline |
| FCR / TMA suporte (Suporte) | Console por jornada + macros | TBD | FCR +20%, TMA -25% (plano macro) |
| Abandono / throughput KIOSK (KIOSK) | E2E locker + modelos A-D Sprint 4 | TBD | p95 E2E <= 90s (plano) |

**Contratos minimos v0 (superficie + onde validar no repo)**

| Dominio | Contrato minimo (v0) | Onde ver / exemplificar |
|---|---|---|
| Checkout | Pedido + pagamento + estado `payResp` | `01_source/frontend` checkout + store Zustand Sprint 1 |
| KIOSK | Totem: compra, pagamento, pickup, alocacao | Rotas OPS kiosk + matriz Sprint 4 UAT 4 modelos |
| Partners | Onboarding + repasse + fiscal minimo | `billing_fiscal_service` + portal/agreements em backlog Sprint 2 |
| OPS | Painel + fiscal + health | `ops/health`, `fiscal/management-daily`, exports `ELLAN_FISCAL_DAILY_*` |
| Support | Jornada + playbook | `fiscal/incident-response`, ops triage |

Decisao executiva:
- Sprint 0 considerado **fechado para desbloquear foco** nas Sprints 1–4 ja em execucao; revisao de KPI real e contratos publicados para terceiros **nao reabre o Sprint 0 lab** — passam a constar no **Sprint 0b produção** (secao seguinte).

## Sprint 0b produção (contínuo / pós-lab) — **não misturar com Sprint 0 lab**
Objetivo: cumprir o que o Sprint 0 lab deixou como **TBD** ou **v0 referencial**, com **DoD de produto** (medição real, publicação, aceite).

**Status geral Sprint 0b:** `[ ]` **Não iniciado** — **~0%** (2026-04-30: apenas anotação de trilha; nenhum item fechado com evidência de produção).

Owner:
- **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**

Checklist (produção — evidência fora do “papel” do lab):
- [ ] **Baseline KPI com valores numericos** por persona (fonte de dados operacional definida + primeiro valor oficial + meta numerica revisada).
- [ ] **Contratos globais publicados** para consumo externo (ex.: OpenAPI/Swagger versionado, changelogs, SLA onde couber) — além do mapa v0 do Sprint 0 lab.
- [ ] **Board operacional** em ferramenta de execução (ou processo equivalente acordado) com WIP e dependencias — além deste `.md` como espelho de governanca.
- [ ] **Comunicação de mudança** para operacao/suporte nos marcos acima (registro de leitura ou treino minimo).

Nota de governanca:
- O ritual “nao mover para `[x]` sem DoD completo” aplica-se em prioridade ao **Sprint 0b** e às sprints de entrega; o **Sprint 0 lab** permanece excecao documentada como encerramento de setup.

## Sprint 1 (Dias 3-9) - Fundacao global + UX KIOSK v1
Objetivo: fechar arquitetura global e iniciar entrega de valor visivel.

Checklist:
- [~] Frontend: iniciar migracao de estilos (dominios checkout, kiosk, ops).
  - Progresso: **checkout público fatias 1–2** — `publicCheckoutChrome.css`: (1) passos, trust, spinners; (2) hero, grelha, cartões **Resumo**/**Pagamento**, highlight de produto, formulário, avisos, botões primário/secundário/DEV, caixas de erro; `data-testid` em resumo/pagamento; kiosk/ops em fatias seguintes.
- [x] Frontend: criar store central para `currentOrder`, `payResp`, `pickupResp`, `syncStatus`.
  - Progresso: **100%** (`useLockerSlotsSync` + **`LockerDashboardFirst.jsx`** leem/escrevem `syncStatus` na mesma `useCheckoutStore`; pedido/pagamento/pickup já consolidados)
- [x] Frontend: aplicar Error Boundaries por dominio critico.
  - Progresso: **100% no escopo Sprint 1** (boundaries por rota/feature critica + telemetria estruturada local com hook para Sentry)
- [~] Frontend: setup TS incremental (`allowJs`, `checkJs`, CI `tsc --noEmit`).
  - Progresso: **91%** (typecheck/build estáveis; gate no workflow; **strict-core** inclui locker-dashboard, `LockerDashboard`, `PickupHealthPanel`, `useOpsWindowPreset`, `OpsActionButton`, **`OpsKioskTouchModelsPage`**; meta **≥90%** no item; próximo: `checkJs` gradual ou mais páginas OPS)
- [~] Produto/UX: prototipos navegaveis dos 4 modelos de tela KIOSK touch.
  - Progresso: **64%** (cockpit **`/ops/kiosk-touch-models`**: modelos A–D + merge opcional em `localStorage`; checklist **n≥8** + export JSON; **smoke E2E** `e2e/kiosk-touch-models.spec.ts`; falta **testes moderados com utilizadores** n≥8 e refinamento visual para fechar **`[~]` → `[x]`**)
- [~] Eng/UX: validar fluxo KIOSK E2E assistido (compra -> pagamento -> abertura -> retirada/alocacao).
  - Progresso: **10%** (spec **OPS** `/ops/kiosk-touch-models` com auth mockada; smoke **`/comprar`** em `e2e/public-comprar-catalog.spec.ts`; checkout completo em `e2e/checkout-dev-full.spec.ts` com token opcional)

**Prioridade executiva (comité, 2026-04-30): Sprint 1 = `#1` em alocação de capacidade de engenharia de produto/FE**  
- **Objetivo:** média dos 6 itens **~61%** (ver **Metodo** *(viii)*); próximo ganho típico: **E2E** com mock `POST /public/orders/` (confirmar reserva) ou **fatia 3** de CSS (fundo página / painel fiscal). **Store e syncStatus: `[x]` 100%.** Catálogo→checkout + cartões + combo pagamento no E2E: **`[x]`** (`e2e/public-catalog-to-checkout.spec.ts`).  
- **Coexistência:** Sprint 2 mantém **prioridade #1 de negócio** (Fiscal + Contábil / D10–D18); alocação de **codificação** espelhada na secção **«Recomendacao atual — onde codar»**: **~65–75% Sprint 2** + **~25–35% Sprint 1** (não zero no financeiro até o comité rever).  
- **Ordem sugerida de ataque:** (1) **Store** — **`[x]`** → (2) **TS** — indicador **≥90%** + `OpsKioskTouchModelsPage` no strict-core → (3) **Protótipos KIOSK** — **`[~]`** cockpit `/ops/kiosk-touch-models` → (4) **E2E KIOSK assistido** → (5) **Migração de estilos** checkout.  
- **Onde codar em primeiro lugar (recomendação consolidada):** ver secção **«Recomendacao atual — onde codar»** acima do **Backlog por persona** — em síntese: **Sprint 2 dominante** (gate v2) + **fatia Sprint 1** para fechar **≥60%** na média dos seis itens.

## Sprint 2 (Dias 10-18) - P0 por persona em producao assistida + Fiscal/Contabil
Objetivo: colocar os P0 centrais para rodar com controle e incorporar trilhas financeiras operacionais (ELLAN LAB + partners).

**Diretriz executiva (comité):** **fechar o macro financeiro desta sprint (Fiscal + Contábil, P0 e trilha D10–D18 com evidência)** antes de **ampliar escopo** nas Sprints 3 e 4. OPS/Suporte já puxam percentuais altos; Fiscal (**~28%**) e Contábil (~15%) continuam o gargalo para **Go/No-Go** — absorver net-new em S3/S4 sem isso mantém o risco de aceite. **Critério numérico exato** e **sprint ideal na sequência** após o gate: ver subsecção **«Critério numérico “financeiro suficiente”»** abaixo. **Coexistência (2026-04-30):** com **Sprint 1** como `#1` de **capacidade FE**, reservar **throughput mínimo explícito** para P0 financeiro (não zero) até o comité rever a prioridade. **Codificação:** **~65–75% Sprint 2** (gate v2) + **~25–35% Sprint 1** — ver **«Recomendacao atual — onde codar»**.

**Recomendação de codificação (síntese):** esta sprint é o **foco dominante** para quem prioriza **desbloquear S3/S4** e o **Go/No-Go**; alinhar com a secção **«Recomendacao atual — onde codar»** e com o **gate v2** (Fiscal ≥50%, Contábil ≥40%, consolidado ≥55%).

Checklist:
- [ ] Comprador ONLINE: checkout resiliente + jornada de pedido transparente.
- [ ] Comprador KIOSK: fluxo proprio operacional com recuperacao de erro.
- [~] OPS: painel unificado + runbooks top incidentes.
  - Progresso: **88%** (lookup opcional no tracker antes da copia com `ticket_status`/`ticket_owner_lookup` no macro e export)
- [ ] Parceiros: contrato global versionado + portal parceiro v1.
- [~] Suporte: console por jornada + macros de triagem.
  - Progresso: **78%** (macros com validacao automatica de consistencia via lookup de ticket)
- [~] Fiscal (ELLAN LAB + partners): operacao fiscal assistida + governanca de emissores e conformidade.
  - Progresso: **28%** (D11: **rollup por `order_id`** + export/ZIP diário e executivo + Vitest no util; regressão de resync no host + trilha D10–D12/gaps; P0 conciliação por parceiro e aceite macro ainda em aberto)
- [~] Contabil (ELLAN LAB + partners): consolidacao contabil operacional + trilha de fechamento e evidencias.
  - Progresso: **15%** (aceite central D13-D18, exports, ZIP executivo; P0 reconciliacao receita/repasse ainda majoritariamente em backlog)

Evolucao consolidada Sprint 2 (apos ampliacao de escopo):
- **Antes da ampliacao (somente OPS/Suporte centrais): ~83% nas frentes ativas**
- **Agora (com Fiscal + Contabil no mesmo sprint): ~52% no consolidado do sprint**

#### Histórico — Gate **v1** (comité **2026-04-30**) *substituído*

| Métrica | Limiar v1 |
| --- | ---: |
| Fiscal (ELLAN LAB + partners) | ≥ 40% |
| Contábil (ELLAN LAB + partners) | ≥ 30% |

**Motivo da v2 (comité 2026-05-01):** endurecer trilhas fiscal/contábil antes de descongelar S3/S4 e acrescentar **terceiro limiar** no **consolidado macro da Sprint 2**, para evitar PASS com subidas só em OPS/Suporte enquanto comprador/parceiro/financeiro permanecem fracos.

#### Critério numérico «financeiro suficiente» — Sprint 2 (comité **v2**, **2026-05-01**) — **vigente**

Gate para **liberar expansão de escopo** nas Sprints 3 e 4. Percentuais alinhados à checklist Sprint 2, ao bloco **«Recalculo de evolucao Sprint 2»** e ao **consolidado** do mesmo sprint (atualizar valores neste doc a cada checkpoint).

| Métrica | Limiar v2 (cumulativo **AND**) | Referência snapshot (pré-gate) |
| --- | ---: | --- |
| **Fiscal** (ELLAN LAB + partners) | **≥ 50%** | ~28% |
| **Contábil** (ELLAN LAB + partners) | **≥ 40%** | ~15% |
| **Consolidado Sprint 2** (macro, todas as frentes do sprint) | **≥ 55%** | ~52% |

**Comprovação obrigatória (AND com os três limiares):** pelo menos **um** artefato anexável ao **daily** ou ao pacote ZIP equivalente (`fiscal/management-daily`, `fiscal/accounting-close`, ou export assinado já previsto no sprint) demonstrando avanço **P0** da trilha em foco no ciclo (ex.: conciliação pedido→documento / repasse ou fechamento D+0 com owner+ETA), na mesma janela de datas em que o comité declara o gate **PASS**. Os ZIPs de **`fiscal/management-daily`** e **`fiscal/accounting-close`** podem incluir **`SPRINT2_GATE_V2_MIRROR_ATTACH`** (espelho assinado dos percentuais e da nota P0 gravados em **`fiscal/sprint2-finance-gate`**, também visível no cockpit diário).

**Revisão de limiares:** próxima versão (**v3**) só com comité datado e motivo explícito neste `.md`.

#### Sprint ideal na sequência (após o gate **v2** «financeiro suficiente»)

| Fase | Condição | Sprint **ideal** dominante | O que muda na execução |
| --- | --- | --- | --- |
| **A — Pré-gate** | Fiscal **inferior a 50%** **ou** Contábil **inferior a 40%** **ou** consolidado **inferior a 55%** **ou** comprovação P0 em falta | **Sprint 2** (macro financeiro) | S3/S4: **sem net-new**; apenas paralelo seguro já definido na diretriz |
| **B — Pós-gate** | Os **três** limiares v2 **e** comprovação **PASS** | **Sprint 3** (hardening / confiabilidade) | **Próximo sprint ideal** para absorver **expansão de escopo** da própria Sprint 3 (itens `[ ]` / `[~]` do checklist S3 que estavam congelados por gating) |
| **C — Linha do plano 30 dias** | Sprint 3 em bom rumo após gate | **Sprint 4** (Go/No-Go global) | Sprint ideal para **matriz + UAT KIOSK + registo** com risco residual documentado; pressupõe trilha financeira e consolidado já acima do mínimo |

**Regra de ouro:** **Sprint 4** não é sprint ideal dominante para **novo** esforço de produto enquanto **B** não estiver declarado; caso contrário Go/No-Go permanece cosmeticamente avançado com base financeira fraca.

### Backlog detalhado Sprint 2 - Fiscal e Contabil (execucao imediata)

> **Referência operacional (catálogo global FG-0 / onda FG-1 sem UI por país):** [runbook](runbooks/FISCAL_CATALOGO_SEM_UI_POR_PAIS.md) — procedimentos (PR, fixtures, envelope) e evolução futura; escopo onda/adapters em `01_source/backend/billing_fiscal_service/app/config/fiscal_fg1_wave.py`.

#### Fiscal - ELLAN LAB
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Fechamento de governanca de emissores fiscais por pais/tenant | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 5 pts | Matriz de emissores ativa por jurisdicao critica; fallback fiscal definido; auditoria de alteracao habilitada |
| P0 | Conciliação fiscal operacional de pedidos (pedido -> emissao -> status fiscal) | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 8 pts | 100% dos pedidos de teste com trilha fiscal consultavel; divergencia sem status reduzida para <2% na janela de sprint |
| P1 | Painel de monitoramento fiscal com alertas de degradacao por provider | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 3 pts | Alertas por severidade ativos; evidencias de health check por provider no dashboard OPS |
| P1 | Playbook fiscal de contingencia por incidente recorrente | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 2 pts | Top incidentes fiscais com runbook publicado e validado em simulacao operacional |

#### Fiscal - Partners
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Contrato fiscal padrao para parceiros (campos obrigatorios + validacoes) | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 5 pts | Contrato fiscal versionado aplicado no onboarding parceiro sem bypass manual recorrente |
| P0 | Trilha de conciliacao fiscal por parceiro (settlement x documento fiscal) | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 8 pts | Divergencias fiscais por parceiro com classificacao e owner; SLA de tratativa definido |
| P1 | Score de conformidade fiscal por parceiro | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 3 pts | Scorecard com ranking de risco fiscal e filtro por periodo |
| P1 | Rotina de evidencias para dispute fiscal de parceiro | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 2 pts | Pacote de evidencias exportavel por caso de divergencia fiscal |

#### Contabil - ELLAN LAB
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Fechamento contabil operacional diario (D+0/D+1) com trilha auditavel | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 8 pts | Relatorio de fechamento diario gerado sem lacunas de evento critico; trilha por lote e responsavel |
| P0 | Reconciliacao contabil de receitas, estornos e creditos | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 8 pts | Divergencia contabil residual <2% na janela de validacao do sprint |
| P1 | Painel contabil de pendencias por severidade e aging | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 3 pts | Pendencias classificadas por aging com owner e ETA |
| P1 | Checklist de fechamento mensal pronto para handoff | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 2 pts | Checklist publicado e executado em simulacao de fechamento |

#### Contabil - Partners
| Prioridade | Item | Dono | Esforco | Criterio de aceite |
|---|---|---|---|---|
| P0 | Conciliação contabil de repasses por parceiro (pedido -> settlement -> lancamento) | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 8 pts | 100% dos parceiros prioritarios com trilha de repasse reconciliada no periodo |
| P0 | Governanca de provisoes e ajustes contabilizados por parceiro | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 5 pts | Ajustes com classificacao padronizada e aprovacao registrada por fluxo |
| P1 | Relatorio contabil por parceiro para handoff financeiro | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 3 pts | Export consolidado por parceiro com totais e divergencias |
| P1 | Regra de priorizacao de divergencia contabil por impacto financeiro | Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional | 2 pts | Fila contabil com ordenacao por impacto + SLA de tratativa |

Recalculo de evolucao Sprint 2 (apos detalhamento P0/P1 Fiscal+Contabil):
- **Consolidado Sprint 2 ajustado: ~52%** (D17 de governanca de aceites central concluido + estabilidade de regressao fiscal de resync validada; escopo macro ainda inclui integracao ampliada)
- **Fiscal (ELLAN LAB + partners): 28%** (endpoints admin fiscais + trilha D11 com evidência **rollup `order_id`** anexável ao daily/ZIP + regressão de resync no host)
- **Contabil (ELLAN LAB + partners): 15%** (trilha de aceite D13-D17 com API de retencao e alertas de divergencia prolongada)

#### Evolucao percentual dos sprints (snapshot consolidado)
Indicativos para acompanhamento executivo; sprints podem sobrepor-se no calendario real.

| Sprint | Janela (plano 30 dias) | Progresso indicativo | Nota breve |
| --- | --- | --- | --- |
| Sprint 0 (lab) | Dias 1-2 | **`[x]` ~100%** | Encerrado (lab): baseline KPI v0 + board neste doc + contratos referenciais v0 |
| **Sprint 0b (produção)** | Contínuo | **`[ ]` ~0%** | Ver secao **Sprint 0b produção**; separado do fecho lab |
| Sprint 1 | Dias 3-9 | **~61%** | **`#1` capacidade FE/KIOSK v1** — média 6 itens (ver **Metodo** *(viii)*); fundação ~**97%**; protótipos KIOSK **`[~]` ~64%**; E2E assistido **`[~]` 10%** |
| Sprint 2 | Dias 10-18 | **~52%** consolidado; Fiscal **~28%**; Contabil **~15%** | Trilha financeira D10-D18; OPS **~88%**, Suporte **~78%** no mesmo macro |
| Sprint 3 | Dias 19-24 | **~67%** | Média das seis frentes do checklist Sprint 3 (CSP 68, TS 96, auditoria 48, SLO 65, quick-enablement 100, P0-3 incidente 22); ver **Metodo** *(iv)* |
| Sprint 4 | Dias 25-30 | **~32%** | Média dos 4 itens do checklist Sprint 4 (24, 40, 28, 35) |

#### Painel percentual para decisão (snapshot 2026-04-30)
Percentuais acima **para decisão executiva** usam: Sprint 0 lab = conclusão checklist; **Sprint 0b = 0% até primeiro `[x]` com evidência de produção**; Sprint 1 = média simples dos seis itens do checklist da secao Sprint 1 (cada `[ ]` conta como 0%); Sprint 2 = consolidado já narrado no doc; Sprint 3 = média (68+96+48+65+100+22)/6 arredondada; Sprint 4 = média (24+40+28+35)/4 arredondada.

| Sprint | % execução (decisão) | Estado | Comentário útil para comité |
| --- | ---: | --- | --- |
| Sprint 0 lab | **100%** | `[x]` Fechado | Setup de governanca; **não** cobre KPI numerico nem contrato publicado externo |
| **Sprint 0b produção** | **0%** | `[ ]` Não iniciado | Próximo passo quando prioridade for “produção real” vs lab |
| Sprint 1 | **~61%** | `[~]` | **Prioridade `#1` capacidade**; store **`[x]`**; TS **≥90%**; KIOSK **`[~]`** `/ops/kiosk-touch-models` (n≥8 + export + smoke E2E); E2E **`/comprar`**; próximo: **estilos** ou **encadear checkout** |
| Sprint 2 | **~52%** | `[~]` | **Prioridade `#1` negócio** (Fiscal + Contábil / D10–D18); **coexiste** com S1 — throughput mínimo acordado |
| Sprint 3 | **~67%** | `[~]` | **Congelar net-new** até **gate v2** (Fiscal ≥50%, Contábil ≥40%, consolidado S2 ≥55%, comprovação P0 — secção Sprint 2); depois S3 = **sprint ideal** para expansão |
| Sprint 4 | **~32%** | `[~]` | **Sprint ideal** só na **fase C** pós-**gate v2**; até lá matriz/UAT sem expansão além do planeado |

#### Evolucao percentual entre snapshots (lab — 2026-04-30)

Tabela para o comité: **antes** = último snapshot neste documento antes da revisão por migração TS **ondas 5-6**; **depois** = após inclusão de `LockerDashboard.tsx`, barrel `features/locker-dashboard/index.ts` e `PickupHealthPanel.tsx` no `typecheck:strict-core`, com `npm run typecheck`, `typecheck:strict-core` e `build` verdes no frontend.

| Indicador | Antes | Depois | Δ |
| --- | ---: | ---: | ---: |
| Sprint 1 — média dos 6 itens do checklist | ~46% | **~47%** | **+1 p.p.** |
| Sprint 1 — só item «TS incremental» | 82% | **86%** | **+4 p.p.** |
| Sprint 1 — fundação FE isolada (média store+boundary+TS) | ~92% | **~93%** | **+1 p.p.** |
| Sprint 3 — item «TS módulos críticos / strict-core» | 93% | **94%** | **+1 p.p.** |
| Sprint 3 — média dos 6 itens do checklist | ~65% | **~65%** | **0 p.p.** *(arredondamento; cálculo bruto ~65,2%)* |

**Metodo (transparente):** *(i)* Tabela **«Evolução percentual entre snapshots»** acima (efeito **ondas 5-6**): média Sprint 1 com store a **94%** → (0 + 94 + 100 + 86 + 0 + 0) / 6 ≈ **47%**; fundação ≈ **93%**. *(ii)* Após **sync de slots** no Zustand: média Sprint 1 = (0 + **99** + 100 + 86 + 0 + 0) / 6 ≈ **47,5%**; fundação ≈ **95%**. *(iii)* Após **TS strict-core** (`useOpsWindowPreset`, `OpsActionButton`): média Sprint 1 = (0 + 99 + 100 + **90** + 0 + 0) / 6 ≈ **48,3%**; fundação = (99 + 100 + 90) / 3 ≈ **96%**; Sprint 3 item TS **95%**. *(iv)* **2026-04-30 (manhã):** store **`[x]`** (100%) + `LockerDashboardFirst` no mesmo `syncStatus`; protótipos KIOSK **45%**; TS item **91%** — média Sprint 1 = (0 + 100 + 100 + **91** + **45** + 0) / 6 = **56,0%** → **~56%**; fundação = (100 + 100 + 91) / 3 ≈ **97%**. Sprint 3 item TS **96%**; média S3 = (68 + 96 + 42 + 65 + 100 + 22) / 6 ≈ **65,5%** → **~66%**. *(v)* **2026-04-30 (checkpoint alocação S2/S1):** protótipos KIOSK **58%** (checklist n≥8 + export JSON em `/ops/kiosk-touch-models`); TS item **91%** — média Sprint 1 = (0 + 100 + 100 + **91** + **58** + 0) / 6 ≈ **58,2%** → **~58%**; fundação inalterada ≈ **97%**. **Alocação de codificação:** **~65–75%** Sprint 2 (gate v2) + **~25–35%** Sprint 1 — ver **«Recomendacao atual — onde codar»** e painel em **`FiscalGlobalPage.jsx`**. *(vi)* **2026-04-30 (Sprint 3 — handoff auditoria):** faixa Sprint 3 no hub `fiscal/global` + checklist de sessão (6 itens) e export JSON em `FiscalSprint3PartnerAuditPage.jsx`; item auditoria **48%**; média S3 = (68 + 96 + 48 + 65 + 100 + 22) / 6 ≈ **66,5%** → **~67%**. *(vii)* **2026-05-01 (Sprint 2 — D11 rollup `order_id`):** `fiscalD11OrderIdRollup.js` + Vitest; `OpsFiscalProvidersPage.jsx` + `FiscalManagementDailyPage.jsx` + `FiscalAccountingClosePage.jsx` (ZIP diário e executivo com `SPRINT2_D11_ORDER_ID_ROLLUP*`); checklist Fiscal Sprint 2 **26% → 28%**. *(viii)* **2026-05-01 (Sprint 1 — média ~60%):** protótipos KIOSK **58% → 64%** (recarregar definições + smoke `e2e/kiosk-touch-models.spec.ts`); item E2E assistido **0% → 10%** (`/ops/kiosk-touch-models` + **`/comprar`**); média bruta = (10 + 100 + 100 + 91 + 64 + 0) / 6 ≈ **60,8%** → painel **~61%**.

#### Snapshot incremental Sprint 1 — `syncStatus` de slots no Zustand (2026-04-30)

| Indicador | Antes (pós ondas 5-6) | Depois | Δ |
| --- | ---: | ---: | ---: |
| Item checklist «store central» | 94% | **99%** | **+5 p.p.** |
| Sprint 1 — média dos 6 itens | ~47% | **~48%** | **+1 p.p.** |
| Fundação FE isolada (store+boundary+TS) | ~93% | **~95%** | **+2 p.p.** |

**Evidência:** `useCheckoutStore.ts` (`CheckoutSlotsSyncBanner`, `setSyncStatus`) + `useLockerSlotsSync.ts` (leitura/escrita na store). **Atualização:** `LockerDashboardFirst.jsx` migrado para a mesma fonte (store), fechando duplicidade do banner de sync.

#### Snapshot incremental Sprint 1 / Sprint 3 — TS strict-core (`useOpsWindowPreset`, `OpsActionButton`)

| Indicador | Antes (pós store-sync Zustand) | Depois | Δ |
| --- | ---: | ---: | ---: |
| Item checklist «TS incremental» (Sprint 1) | 86% | **90%** | **+4 p.p.** |
| Fundação FE isolada (store+boundary+TS) | ~95% | **~96%** | **+1 p.p.** |
| Item checklist «TS módulos críticos» (Sprint 3) | 94% | **95%** | **+1 p.p.** |

**Evidência:** ficheiros migrados para `.ts`/`.tsx` com tipagem estrita; entradas novas em `tsconfig.strict-core.json`; `npm run typecheck` e `typecheck:strict-core` verdes.

#### Snapshot incremental Sprint 1 — store 100% + protótipos KIOSK v1

| Indicador | Antes | Depois | Δ |
| --- | ---: | ---: | ---: |
| Item checklist «store central» | 99% | **`[x]` 100%** | concluído |
| Item checklist «protótipos KIOSK» | 0% | **`[~]` 45%** | +45 p.p. |
| Rota OPS | — | **`/ops/kiosk-touch-models`** | cockpit v1 |

**Evidência:** `LockerDashboardFirst.jsx` usa `useCheckoutStore` para `syncStatus`/`setSyncStatus`; `OpsKioskTouchModelsPage.tsx` + `App.jsx` (lazy + `opsLinks` + rota com `withBoundary`).

#### Snapshot incremental Sprint 1 — checklist n≥8 + export JSON (KIOSK)

| Indicador | Antes | Depois | Δ |
| --- | ---: | ---: | ---: |
| Item checklist «protótipos KIOSK» | 45% | **`[~]` 58%** | +13 p.p. |
| Sprint 1 — média dos 6 itens | ~56% | **~58%** | +2 p.p. |

**Evidência:** `OpsKioskTouchModelsPage.tsx` (checklist heurística n≥8, `localStorage`, botão export JSON); `FiscalGlobalPage.jsx` (painel atalhos **gate v2** Sprint 2).

#### Snapshot incremental Sprint 1 — smoke E2E OPS KIOSK + cockpit (2026-05-01)

| Indicador | Antes | Depois | Δ |
| --- | ---: | ---: | ---: |
| Item checklist «protótipos KIOSK» | 58% | **`[~]` 64%** | **+6 p.p.** |
| Item checklist «E2E KIOSK assistido» | 0% | **`[~]` 10%** | +10 p.p. |
| Sprint 1 — média dos 6 itens | ~58% | **~61%** | **+3 p.p.** |

**Evidência:** `e2e/kiosk-touch-models.spec.ts`; `e2e/public-comprar-catalog.spec.ts`; `e2e/public-catalog-to-checkout.spec.ts` (catálogo → `/checkout`, query mínima, steps + cartões resumo/pagamento + combo método); `playwright.config.ts` (`VITE_ENABLE_OPS_ROUTES` no `webServer`); `OpsKioskTouchModelsPage.tsx` (`data-testid`, recarregar definições); `src/styles/publicCheckoutChrome.css` (estilos checkout fatias 1–2).

#### Snapshot incremental Sprint 2 — D11 evidência por `order_id` (2026-05-01)

| Indicador | Antes | Depois | Δ |
| --- | ---: | ---: | ---: |
| Fiscal (checklist Sprint 2) | 26% | **28%** | **+2 p.p.** |

**Evidência:** `fiscalD11OrderIdRollup.js` + `fiscalD11OrderIdRollup.test.js`; `OpsFiscalProvidersPage.jsx`; `FiscalManagementDailyPage.jsx` (payload + ZIP); `FiscalAccountingClosePage.jsx` (ZIP executivo `SPRINT2_D11_ORDER_ID_ROLLUP_EXEC_*`). **Extensão D12/D13 (mesmo padrão de nomeação assinada):** `fiscalSprint2D12D13Evidence.js` + testes Vitest; ZIP diário `SPRINT2_D12_ACCOUNTING_HANDOFF_*` e `SPRINT2_D13_ACCOUNTING_ACCEPTANCE_*`; ZIP executivo `*_EXEC_*` em `fiscal/accounting-close`.

#### Sequencia diaria Sprint 2 (D10-D18) - ordem de execucao e dependencias criticas
| Dia | Foco principal | Entregas alvo (P0 primeiro) | Dependencias criticas | Saida do dia |
|---|---|---|---|---|
| D10 | Fiscal ELLAN LAB - governanca de emissores | Fechar matriz pais/tenant/emissor e checklist GO/NO-GO operacional | Providers fiscais acessiveis; token interno; ambientes BR/PT validos | Matriz aprovada + evidencias de health e fallback |
| D11 | Fiscal ELLAN LAB - conciliacao fiscal pedido->documento | Validar trilha de emissao por pedido e classificar divergencias; **rollup por `order_id`** exportável/ZIP | Endpoint de consulta fiscal estavel; correlacao por `order_id` | Relatorio de divergencias fiscais com owner/ETA + artefato `SPRINT2_D11_ORDER_ID_ROLLUP*` |
| D12 | Fiscal Partners - contrato fiscal e onboarding | Aplicar contrato fiscal padrao no onboarding de parceiros | Campos obrigatorios mapeados; regras por jurisdicao definidas | Contrato versionado + checklist de onboarding fiscal |
| D13 | Fiscal Partners - conciliacao por parceiro | Fechar reconciliacao settlement x documento fiscal por parceiro prioritario | Dados de settlement disponiveis; IDs de parceiro consistentes | Painel de divergencia fiscal por parceiro |
| D14 | Contabil ELLAN LAB - fechamento operacional diario | Executar ciclo D+0/D+1 com trilha auditavel e evidencias | Janela de fechamento definida; eventos financeiros completos | Fechamento diario publicado com pendencias classificadas |
| D15 | Contabil ELLAN LAB - reconciliacao receita/estorno/credito | Consolidar divergencia contabil residual com plano de tratativa | Dados de pagamentos e estornos consolidados | Snapshot contabil com delta e plano de acao |
| D16 | Contabil Partners - repasses e provisoes | Reconciliar repasses por parceiro e classificar ajustes/provisoes | Lotes de repasse disponiveis; regras de aprovacao definidas | Fila contabil por parceiro com impacto e prioridade |
| D17 | Contabil ELLAN LAB - governanca do historico de aceites | Retencao/compactacao (poda) + alertas de divergencia prolongada entre snapshots | Historico D15 + compare estaveis; token interno | API `retention` + `divergence-health` + card em `fiscal/management-daily` |
| D18 | Aceite assistido Sprint 2 financeiro | Executar checklist final P0 e registrar riscos remanescentes P1 | Evidencias de D10-D17 completas; owners e ETAs atualizados | Sprint 2 financeiro pronto para transicao ao hardening |

Dependencias criticas transversais (Sprint 2 financeiro):
- Integridade de chaves de correlacao (`order_id`, `invoice_id`, `partner_id`, `batch_id`).
- Disponibilidade de endpoints fiscais/contabeis sem bloqueio de CORS/rede.
- Token interno e permissao operacional para rotas admin (`X-Internal-Token`).
- Rastreabilidade de ownership (owner + ETA + severidade) em toda divergencia.
- Rotina diaria de evidencia para handoff (texto + export estruturado).

## Sprint 3 (Dias 19-24) - Hardening e confiabilidade global
Objetivo: reduzir fragilidade operacional e risco de escala.

**Gating com Sprint 2:** novas frentes ou aumento de escopo nesta sprint ficam **atrás** do **gate v2** (**Fiscal ≥50%**, **Contábil ≥40%**, **consolidado S2 ≥55%**, comprovação P0 — subsecção na Sprint 2). Hardening já iniciado (CSP, TS, SLO, P0-1/P0-2/P0-3) segue em paralelo quando **não** roubar capacidade dos P0 financeiros.

Checklist:
- [~] Endurecer CSP e politicas de seguranca frontend.
  - Progresso: **68%** (meta CSP removida do `dist` no build — política só no gateway; exemplo Nginx em `02_docker/nginx/csp-frontend.example.conf`; JSON-LD externo; dev: plugin reabre `unsafe-inline` em `script-src`; `style-src` ainda com `unsafe-inline` no gateway até migração de estilos)
- [~] Evoluir tipagem TS em modulos criticos (`noImplicitAny` nesses modulos).
  - Progresso: **96%** (strict-core inclui locker-dashboard, `LockerDashboard`, `PickupHealthPanel`, `useOpsWindowPreset`, `OpsActionButton`, **`OpsKioskTouchModelsPage`**; utilitários OPS/data em páginas fiscais e `DevBaseCatalog` como antes)
- [~] Completar auditoria ponta a ponta em fluxos de alto impacto.
  - Progresso: **48%** (trilha E2E + rollup por parceiro em `fiscal/sprint3-partner-audit` + export slice; **checklist de handoff de sessão** (6 itens) com `localStorage` + export JSON dedicado; **faixa Sprint 3** no hub `fiscal/global`; falta cobertura ampliada em reconciliação real multi-parceiro e evidência de utilizadores nos dailies)
- [~] Consolidar scorecards de parceiros e alertas por SLO.
  - Progresso: **65%** (`fiscal/slo-alerts`: thresholds por janela + severidade + export auditável + recomendações automáticas + **registo P0-2** de decisões pós-recomendação em `localStorage`, export dedicado `SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS` e inclusão no JSON/ZIP do scorecard; falta calibragem operacional BR/PT com 3 decisões reais anexadas ao daily e scorecards de parceiros fora do núcleo fiscal)
- [x] Fechar treinamento rapido operacional (OPS/Suporte).
  - Cockpit `ops/quick-enablement`: checklist ~15min, handoff Slack, export JSON/ZIP assinados (`ELLAN_FISCAL_DAILY_*`, scope `SPRINT3_OPS_SUPPORT_QUICK_TRAINING`).

## Sprint 4 (Dias 25-30) - Go/No-Go global
Objetivo: consolidar aceite e readiness de rollout.

**Gating com Sprint 2:** decisão **Go/No-Go** só ganha credibilidade com **gate v2** cumprido (**Fiscal ≥50%**, **Contábil ≥40%**, **consolidado S2 ≥55%**, comprovação P0) e, na sequência do plano, **Sprint 3** estável como sprint ideal pós-gate. Evitar UAT/regressão “larga” como substituto do gate numérico.

Checklist:
- [~] Executar regressao funcional por persona.
  - Progresso: **24%** (matriz por persona + export ZIP; evidência pilotos + anexo automático no pacote diário/executivo)
- [~] Executar UAT de KIOSK touch para os 4 modelos.
  - Progresso: **40%** (cockpit `fiscal/sprint4-regression-matrix`: modelos A–D com notas; resumo Go/No-Go exportável; falta ciclos reais por turno anexados ao daily)
- [~] Validar SLO/KPI minimo de saida.
  - Progresso: **28%** (SLO fiscal + exports; baseline global por persona ainda em calibragem)
- [~] Registrar decisao Go/No-Go com riscos residuais e plano de mitigacao.
  - Progresso: **35%** (registro na matriz + JSON assinado dedicado `SPRINT4_GO_NO_GO_REGISTER_SUMMARY` no ZIP da página, no pacote diário quando há matriz em `localStorage`, e no ZIP de `fiscal/accounting-close` junto à matriz EXEC)

---

## Registro de evolucao (carimbos)

### 2026-04-30 - Baseline inicial
Status geral: `[~]` Em andamento

Resumo:
- Plano global por persona criado e estruturado para execucao imediata.
- Recomendacoes de frontend (`caso_frontend.pdf`) incorporadas como trilha transversal P0/P1.
- KIOSK definido como totem touch com 4 modelos de tela (compra, retirada e alocacao).
- Sprint 0 preenchido com owner nominal unico e progresso percentual por item para daily.

Decisao executiva do dia:
- Iniciar pelo **Sprint 0** com baseline de KPI, owners e board unico.
- Tratar backlog transversal de frontend como bloqueador positivo para escala global.
- Operacao segue com owner unico: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**.

Riscos imediatos:
- `[!]` Acumulo de papeis em owner unico pode reduzir throughput semanal.
- `[!]` Sem baseline de KPI finalizado, o gate de Go/No-Go perde objetividade.

Proximo checkpoint:
- ~~Publicar update de Sprint 0 com baseline fechado e contratos globais minimos documentados.~~ **Feito:** ver carimbo `### 2026-04-30 - Sprint 0 encerramento operacional (lab)`.

### 2026-04-30 - Inicio de codificacao Sprint 1
Status geral: `[~]` Em andamento

Resumo:
- Frontend recebeu **setup TypeScript incremental** (`tsconfig.json` + script `typecheck` em `package.json`).
- Criado **store central inicial** em Zustand (`src/store/useCheckoutStore.ts`) para estado critico de checkout/kiosk.
- Implementado **Error Boundary por dominio** e aplicado no roteamento principal (`src/components/DomainErrorBoundary.jsx` + `src/App.jsx`).
- Build de producao executado com sucesso no frontend.
- Aplicado **gate tecnico controlado** no typecheck incremental:
  - escopo inicial reduzido para arquivos TS/TSX novos;
  - `checkJs` desativado temporariamente para evitar ruído legado em `.jsx`;
  - `vite-env.d.ts` adicionado para compatibilidade de `import.meta.env`.

Decisao executiva do checkpoint:
- Continuar Sprint 1 focando na integracao real do store nos hooks de dashboard/checkout.
- Priorizar remocao gradual de estilos inline em dominios criticos (checkout, kiosk e ops).
- Manter gate tecnico controlado ate a trilha de migracao JS -> TS atingir cobertura suficiente para ampliar escopo.

Riscos imediatos:
- `[!]` Instalacao de dependencias via `npm install` falhou por conflito de peer de ESLint no ambiente atual.
- `[!]` Aviso de versao do Node abaixo do recomendado pelo Vite pode gerar instabilidade futura.

Proximo checkpoint:
- Integrar `useCheckoutStore` nos hooks de estado operacional e registrar impacto em consistencia de fluxo.

### 2026-04-30 - Expansao TS por dominio (checkout -> kiosk -> ops)
Status geral: `[~]` Em andamento

Resumo:
- Criados contratos tipados por dominio:
  - `src/features/checkout/types.ts`
  - `src/features/kiosk/types.ts`
  - `src/features/ops/types.ts`
- `useCheckoutStore.ts` passou a reutilizar tipos de `checkout`.
- `DomainErrorBoundary` migrado para `TSX` (`src/components/DomainErrorBoundary.tsx`), mantendo cobertura no roteamento principal.
- `typecheck` incremental e `build` executados com sucesso apos expansao.

Decisao executiva do checkpoint:
- Manter estrategia de contratos TS por dominio para reduzir risco de migracao.
- Proximo foco: aplicar os tipos no fluxo real dos hooks de checkout/kiosk antes de ampliar para OPS.

Riscos imediatos:
- `[!]` Build ainda alerta Node 20 na sessao do agente (ambiente Cursor), apesar do Node 22 instalado no host.
- `[!]` Fluxo principal ainda depende de hooks JS sem integracao plena ao store central.

Proximo checkpoint:
- Integrar `useCheckoutStore` em `useCurrentOrder` e `useOperationalPayment` com transicao controlada.

### 2026-04-30 - Integracao controlada do store nos hooks (bloco 1)
Status geral: `[~]` Em andamento

Resumo:
- `useCurrentOrder` passou a usar `useCheckoutStore` como fonte de verdade para `currentOrder`.
- `useOperationalPayment` passou a sincronizar `currentOrder` e `payResp` com o store, preservando API atual do hook.
- `setCurrentOrder` no store foi evoluido para aceitar valor direto e updater function (compativel com padrao React).
- Validacao tecnica concluida: `typecheck` e `build` verdes.

Decisao executiva do checkpoint:
- Manter transicao por blocos (sem big bang), preservando compatibilidade do controller e dos componentes atuais.
- Seguir no bloco 2 com integracao de pickup/orders ao store para consolidar fluxo completo.

Riscos imediatos:
- `[!]` Sessao do agente continua com Node 20 no build, apesar de host com Node 22.
- `[!]` `pickupResp` ainda local em hook de pickup (nao centralizado no store).

Proximo checkpoint:
- Integrar `useOperationalPickup` ao store e revisar `useLockerDashboardController` para reduzir estado duplicado.

### 2026-04-30 - Integracao controlada do store nos hooks (bloco 2)
Status geral: `[~]` Em andamento

Resumo:
- `useOperationalPickup` agora sincroniza `pickupResp` e `currentOrder` com `useCheckoutStore`.
- Hook de pickup passou a aceitar fallback seguro: props atuais ou estado central (transicao sem quebra).
- `useLockerDashboardController` simplificado para reduzir passagem redundante de estado ao pickup.
- Validacao tecnica concluida: `typecheck` e `build` verdes apos bloco 2.

Decisao executiva do checkpoint:
- Manter abordagem de compatibilidade retroativa nos hooks ate concluir consolidacao do fluxo de orders.
- Prosseguir para bloco 3 focando eliminacao de estado duplicado remanescente no controller/orders.

Riscos imediatos:
- `[!]` Sessao do agente segue em Node 20 para build local (aviso Vite), apesar de host com Node 22.
- `[!]` Ainda existe estado de resposta textual espalhado entre controller e hooks (etapa final de consolidacao pendente).

Proximo checkpoint:
- Integrar fluxo de orders ao store e remover duplicidade residual de respostas operacionais.

### 2026-04-30 - Integracao controlada do store nos hooks (bloco 3: orders/responses)
Status geral: `[~]` Em andamento

Resumo:
- `useCheckoutStore` evoluido para centralizar tambem `orderError`, `ordersLoading`, `ordersError`, `ordersData`.
- `useCurrentOrder` passou a usar `orderError` do store (reduzindo duplicidade de estado local).
- `useOperationalOrders` passou a usar `ordersLoading/ordersError/ordersData` do store, mantendo filtros/paginacao locais.
- Validacao tecnica concluida: `typecheck` e `build` verdes apos a consolidacao.

Decisao executiva do checkpoint:
- Considerar frente de consolidacao de store praticamente fechada (>90%), mantendo apenas hardening e limpeza residual.
- Preservar arquitetura hibrida temporaria (filtros/paginacao locais) para evitar regressao de UX no painel.

Riscos imediatos:
- `[!]` Sessao do agente segue em Node 20 para build local (aviso Vite), apesar de host com Node 22.
- `[!]` Necessidade de limpeza final de estados locais nao criticos no controller para reduzir complexidade cognitiva.

Proximo checkpoint:
- Hardening final: reduzir estados duplicados remanescentes no controller e preparar estabilizacao do `typecheck` no CI.

### 2026-04-30 - Hardening final + estabilizacao do typecheck no CI
Status geral: `[~]` Em andamento

Resumo:
- `useLockerDashboardController` recebeu hardening com `resetTransientFlowState` para centralizar limpeza de estado e reduzir duplicidade.
- Fluxos de troca de locker, selecao de slot e limpeza de selecao agora usam a mesma rotina de reset.
- Workflow de CI atualizado para Node 22 e passo explicito de `npm run typecheck` (smoke + regression).
- Validacao local concluida: `typecheck` e `build` verdes apos ajustes.

Decisao executiva do checkpoint:
- Considerar trilha de consolidacao de estado praticamente fechada (>90%) e mover foco para limpeza residual de baixo risco.
- Tratar `typecheck` como gate oficial do frontend no pipeline de regressao.

Riscos imediatos:
- `[!]` Gate de CI precisa de validacao em execucao remota (GitHub Actions) para confirmar estabilidade fim-a-fim.
- `[!]` Aviso de Node 20 persiste na sessao local do agente (ambiente Cursor), sem bloquear build.

Proximo checkpoint:
- Executar rodada remota de CI e registrar evidencias de estabilidade do gate de typecheck.

### 2026-04-30 - Tentativa de validacao remota do workflow (bloqueada por ambiente)
Status geral: `[!]` Bloqueado / risco

Resumo:
- Tentativa de disparo remoto via CLI GitHub (`gh workflow run "Sprint5 Item5 Regression"`) realizada.
- Evidencia coletada no terminal: `gh: command not found`.
- Validacao remota do gate de typecheck ficou bloqueada por ausencia do GitHub CLI no ambiente local.

Decisao executiva do checkpoint:
- Manter frente tecnica concluida localmente (build + typecheck verdes), com pendencia apenas de comprovacao remota.
- Tratar instalacao/autenticacao do `gh` como desbloqueador operacional imediato.

Riscos imediatos:
- `[!]` Sem execucao remota do workflow, falta evidencia final de estabilidade no ambiente GitHub Actions.

Proximo checkpoint:
- Instalar `gh`, autenticar (`gh auth login`) e executar `Sprint5 Item5 Regression`, registrando URL e resultado da run.

### 2026-04-30 - Nova tentativa de validacao remota (evidencia coletada)
Status geral: `[~]` Em andamento

Resumo:
- `gh` instalado e autenticado com sucesso no ambiente local.
- Disparo manual via `gh workflow run` bloqueado por permissao do token atual:
  - `HTTP 403: Resource not accessible by personal access token`.
- Evidencia remota coletada via listagem de runs recentes:
  - Workflow: `Sprint5 Item5 Regression`
  - Run ID: `25164702339`
  - Status: `failure`
  - Branch/evento: `main` / `push`
  - Falha principal no job `Sprint5 Item5 Smoke`, step `Install backend dependencies`.
- Causa observada no log do run:
  - `ERROR: Could not open requirements file: [Errno 2] No such file or directory: '01_source/order_pickup_service/requirements.txt'`

Decisao executiva do checkpoint:
- Frente de gate remoto segue parcialmente validada: pipeline executa, mas falha por problema de caminho/arquivo no ambiente remoto.
- Acao imediata: corrigir o step de dependencias backend no workflow para caminho resiliente.

Riscos imediatos:
- `[!]` Sem ajustar o passo de instalacao backend, o gate remoto nao confirma estabilidade fim-a-fim.
- `[!]` Token atual nao possui permissao para `workflow_dispatch` (disparo manual via CLI).

Proximo checkpoint:
- Ajustar workflow para validar caminho de `requirements.txt` antes de instalar e rerodar por push/manual.

### 2026-04-30 - Correcao de resiliencia no workflow CI (backend deps)
Status geral: `[x]` Concluido

Resumo:
- Workflow `Sprint5 Item5 Regression` ajustado para evitar falha de caminho no backend:
  - criacao de venv com `working-directory: 01_source/order_pickup_service`;
  - instalacao de dependencias usando caminho local (`requirements.txt`) no mesmo `working-directory`;
  - validacao explicita (`test -f requirements.txt`) com log de diagnostico em caso de ausencia.
- Ajuste aplicado nos dois jobs (`Smoke` e `Regression`).

Decisao executiva do checkpoint:
- Padrao de caminho absoluto no comando foi substituido por execucao contextual por diretório, reduzindo risco de inconsistencias em runner.
- Frente pronta para nova rodada de validacao remota.

Riscos imediatos:
- `[!]` Execucao remota ainda depende de push/manual rerun para comprovar efeito no GitHub Actions.
- `[!]` `workflow_dispatch` via CLI continua limitado pela permissao do token atual.

Proximo checkpoint:
- Rodar novamente a pipeline no remoto e registrar resultado final (run id + status) nesta secao.

### 2026-04-30 - Correcao raiz da falha remota (arquivo ignorado)
Status geral: `[x]` Concluido

Resumo:
- Nova analise da falha remota (`run_id: 25166200126`) confirmou que o `requirements.txt` nao estava disponivel no runner.
- Causa raiz identificada no repositorio:
  - regra global `*.txt` em `.gitignore` estava ignorando `01_source/order_pickup_service/requirements.txt`.
- Correcao aplicada:
  - adicionadas excecoes no `.gitignore`: `!**/requirements.txt` e `!**/requirements-*.txt`.
  - `requirements.txt` do `order_pickup_service` passou a ficar elegivel para versionamento.

Decisao executiva do checkpoint:
- Padrao de ignorar `*.txt` foi mantido, mas com excecoes explicitas para requisitos de build.
- Workflow remoto deve ser rerodado apos push dessa correcao para confirmar fechamento do gate.

Riscos imediatos:
- `[!]` Enquanto nao houver novo push com `requirements.txt` versionado, o workflow pode continuar falhando no mesmo ponto.

Proximo checkpoint:
- Commit/push de `.gitignore` + `01_source/order_pickup_service/requirements.txt` e nova execucao da Action.

### 2026-04-30 - Evidencia final de fechamento do gate remoto (sucesso)
Status geral: `[x]` Concluido

Resumo:
- Push aplicado com a correcao de rastreamento do `requirements.txt` (commit `da67fd1`).
- Workflow remoto executado com sucesso no GitHub Actions:
  - Workflow: `Sprint5 Item5 Regression`
  - Run ID: `25166340402`
  - Conclusao: `success`
  - URL: `https://github.com/1268marcos/ellan_lab/actions/runs/25166340402`
  - Commit (headSha): `da67fd1c341bc72e62fb01228f166db58e74717d`
  - Inicio/Fim (UTC): `2026-04-30T12:50:50Z` -> `2026-04-30T12:53:05Z`

Decisao executiva do checkpoint:
- Frente de estabilizacao do `typecheck` no CI e validacao remota do gate considerada **fechada com seguranca**.
- Prosseguir para as proximas prioridades de sprint sem bloqueio de pipeline nesta trilha.

Riscos imediatos:
- Sem riscos bloqueadores nesta frente.

Proximo checkpoint:
- Manter monitoramento passivo das proximas runs e abrir incidente apenas em regressao real.

## Snapshot para o daily de hoje (Sprint 0)
- Progresso Sprint 0: **`[x]` encerrado (lab)** — ver `### 2026-04-30 - Sprint 0 encerramento operacional (lab)`.
- Itens concluidos: **4/4** (checklist Sprint 0)
- Owner responsavel: **Marcos - Engenheiro de Software (Full Stack) e Responsavel por Produto/UX Operacional**
- Proximo foco: **Sprints 1–4** (execucao tecnica); baseline numerico de KPI quando instrumentacao estiver estavel.

## Fala de 60 segundos para daily (pronta para leitura) — pos-Sprint 0
"Sprint 0 do plano global por persona esta encerrado no escopo lab: owners, board neste documento, contratos referenciais v0 e baseline KPI v0 estruturado. O trabalho segue nas Sprints 1 a 4 com entregas de codigo e exports auditaveis; a medicao numerica de KPI passa a evoluir com a instrumentacao, sem reabrir Sprint 0."

---

## Registro claro de entregas (controle executivo)
Use esta estrutura para manter historico objetivo das entregas:

| Data | Sprint | Entrega | Status | Evidencia/Artefato | Proximo passo |
|---|---|---|---|---|---|
| 2026-04-30 | Sprint 0 | Plano global por persona em `.md` | `[x]` | `docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md` | Evoluir com checkpoints diarios |
| 2026-04-30 | Sprint 0 | Incorporacao das recomendacoes de frontend (caso_frontend) | `[x]` | Secao "Incorporacao de recomendacoes do docs/caso_frontend.pdf" | Executar trilha transversal P0 |
| 2026-04-30 | Sprint 0 | Owners nominais definidos (owner unico) | `[x]` | Secao Sprint 0 + snapshot daily | Manter ownership por item no board |
| 2026-04-30 | Sprint 0 | Board unico por persona + trilha transversal | `[x]` | Sprint 0 checklist + sprints neste `.md` | Manter registro de entregas |
| 2026-04-30 | Sprint 0 | Contratos globais minimos por dominio | `[x]` | Carimbo Sprint 0 — tabela Contratos v0 | Evoluir OpenAPI/publicacao por sprint |
| 2026-04-30 | Sprint 0 | Baseline de KPI por persona | `[x]` | Carimbo Sprint 0 — tabela Baseline KPI v0 | Preencher valores quando fontes estiverem prontas |
| 2026-04-30 | Sprint 0b produção | Trilha formal separada do Sprint 0 lab | `[ ]` | Secao **Sprint 0b produção** no plano | Executar checklist 0b com DoD de produto |
| 2026-04-30 | Sprint 1 | Prioridade `#1` capacidade (FE/KIOSK v1) | `[~]` | Secao Sprint 1 — bloco **Prioridade executiva** | Executar ordem: store 100% → TS (indicador ≥90% **feito**) → prototipos → E2E → estilos checkout |
| 2026-04-30 | Sprint 1 | Setup TypeScript incremental no frontend | `[~]` | `01_source/frontend/tsconfig.json`, `01_source/frontend/package.json` | Estabilizar typecheck no CI |
| 2026-04-30 | Sprint 1 | Gate tecnico controlado para typecheck incremental | `[x]` | `01_source/frontend/tsconfig.json`, `01_source/frontend/src/vite-env.d.ts` | Expandir escopo TS por dominio (checkout -> kiosk -> ops) |
| 2026-04-30 | Sprint 1 | Contratos TS por dominio (checkout, kiosk, ops) | `[x]` | `01_source/frontend/src/features/checkout/types.ts`, `01_source/frontend/src/features/kiosk/types.ts`, `01_source/frontend/src/features/ops/types.ts` | Tipar/adaptar hooks de fluxo com esses contratos |
| 2026-04-30 | Sprint 1 | DomainErrorBoundary migrado para TSX | `[x]` | `01_source/frontend/src/components/DomainErrorBoundary.tsx`, `01_source/frontend/src/App.jsx` | Instrumentar `onError` com telemetria (Sentry/OTel) |
| 2026-04-30 | Sprint 1 | Store central inicial (Zustand) | `[~]` | `01_source/frontend/src/store/useCheckoutStore.ts` | Integrar pickup/orders e remover estado duplicado residual |
| 2026-04-30 | Sprint 1 | Integracao do store em `useCurrentOrder` | `[x]` | `01_source/frontend/src/features/locker-dashboard/hooks/useCurrentOrder.js` | Consolidar mesma abordagem no pickup |
| 2026-04-30 | Sprint 1 | Integracao controlada do store em `useOperationalPayment` | `[x]` | `01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPayment.js` | `payResp` lido apenas do Zustand; alinhar `LockerDashboardFirst` legado se ainda em uso |
| 2026-04-30 | Sprint 1 | Integracao do store em `useOperationalPickup` | `[x]` | `01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPickup.js` | Consolidar fluxo de responses no estado central |
| 2026-04-30 | Sprint 1 | Reducao de estado duplicado no controller (pickup) | `[x]` | `01_source/frontend/src/features/locker-dashboard/hooks/useLockerDashboardController.js` | Repetir simplificacao para orders/responses |
| 2026-04-30 | Sprint 1 | Integracao de `orders/responses` ao store | `[x]` | `01_source/frontend/src/store/useCheckoutStore.ts`, `01_source/frontend/src/features/locker-dashboard/hooks/useCurrentOrder.js`, `01_source/frontend/src/features/locker-dashboard/hooks/useOperationalOrders.js` | Hardening final e limpeza residual de estado local |
| 2026-04-30 | Sprint 1 | Hardening no controller (reset centralizado de estado transitório) | `[x]` | `01_source/frontend/src/features/locker-dashboard/hooks/useLockerDashboardController.js` | Limpeza residual de duplicidade nao critica |
| 2026-04-30 | Sprint 1 | Estabilizacao do typecheck no CI (Node 22 + gate) | `[x]` | `.github/workflows/sprint5-item5-regression.yml` | Validar execucao remota do workflow |
| 2026-04-30 | Sprint 1 | Validacao remota do workflow no GitHub Actions | `[~]` | `gh run list` + `gh run view 25164702339 --log-failed` | Corrigir falha do step backend (`requirements.txt`) e rerodar |
| 2026-04-30 | Sprint 1 | Correcao de resiliencia no install backend do workflow | `[x]` | `.github/workflows/sprint5-item5-regression.yml` | Executar nova run remota e coletar evidencia final |
| 2026-04-30 | Sprint 1 | Correcao raiz de arquivo ignorado no CI (`requirements.txt`) | `[x]` | `.gitignore`, `01_source/order_pickup_service/requirements.txt` | Push + rerun para confirmar fechamento do gate |
| 2026-04-30 | Sprint 1 | Evidencia final do gate remoto (GitHub Actions) | `[x]` | Run `25166340402` (`success`) - https://github.com/1268marcos/ellan_lab/actions/runs/25166340402 | Monitoramento passivo nas proximas runs |
| 2026-04-30 | Sprint 1 | Error Boundary por dominio no roteamento | `[x]` | `01_source/frontend/src/components/DomainErrorBoundary.tsx`, `01_source/frontend/src/App.jsx` | Hardening incremental em rotas secundarias conforme necessidade |
| 2026-04-30 | Sprint 1 | Endpoint interno de ingestao de erro UI + envio frontend com fallback | `[x]` | `01_source/order_pickup_service/app/main.py`, `01_source/frontend/src/services/errorTelemetry.ts`, `01_source/frontend/src/App.jsx` | Evoluir armazenamento de UI errors para persistencia duravel |
| 2026-04-30 | Sprint 1 + Sprint 3 | Migracao TS ondas 5-6 (LockerDashboard + barrel locker-dashboard + PickupHealthPanel no strict-core) | `[x]` | `01_source/frontend/src/pages/LockerDashboard.tsx`, `01_source/frontend/src/features/locker-dashboard/index.ts`, `01_source/frontend/src/components/PickupHealthPanel.tsx`, `01_source/frontend/tsconfig.strict-core.json`; `npm run typecheck` + `typecheck:strict-core` + `build` | Proxima fatia: `PickupHealthPage` / `LockerDashboardFirst` ou ampliar strict-core por dominio |
| 2026-04-30 | Sprint 1 | Store: `syncStatus` de slots centralizado no Zustand | `[x]` | `01_source/frontend/src/store/useCheckoutStore.ts`, `01_source/frontend/src/features/locker-dashboard/hooks/useLockerSlotsSync.ts`; `typecheck` + `strict-core` + `build` | Alinhar `LockerDashboardFirst` ao store ou declarar 100% só fluxo TS |
| 2026-04-30 | Sprint 1 + Sprint 3 | TS strict-core: `useOpsWindowPreset` + `OpsActionButton` (meta ≥90% item Sprint 1) | `[x]` | `01_source/frontend/src/hooks/useOpsWindowPreset.ts`, `01_source/frontend/src/components/OpsActionButton.tsx`, `tsconfig.strict-core.json`; removidos `.js`/`.jsx` legados | Próximo: `checkJs` gradual, mais OPS em strict-core, ou `[x]` formal no item TS após comité |
| 2026-04-30 | Sprint 1 | Store 100%: `LockerDashboardFirst` usa `syncStatus` na Zustand | `[x]` | `01_source/frontend/src/pages/LockerDashboardFirst.jsx` + `useCheckoutStore` | Protótipos KIOSK + E2E |
| 2026-04-30 | Sprint 1 | Protótipos navegáveis KIOSK touch v1 (4 modelos) | `[~]` | `01_source/frontend/src/pages/OpsKioskTouchModelsPage.tsx`, rota `/ops/kiosk-touch-models`, `App.jsx` | n≥8 + subir % ou E2E assistido |

### 2026-04-30 - Expansao de Error Boundaries por feature critica
Status geral: `[x]` Concluido

Resumo:
- `App.jsx` evoluido de boundary global unico para boundaries por feature critica via helper `withBoundary`.
- Cobertura aplicada em rotas de maior risco operacional:
  - Checkout (`/checkout`);
  - Pedidos (`/meus-pedidos`, `/meus-pedidos/:orderId`);
  - OPS criticas (`/ops/sp`, `/ops/pt`, `/ops/sp/kiosk`, `/ops/pt/kiosk`, `/ops/reconciliation`, `/ops/audit`, `/ops/health`).
- Adicionado `onError` por dominio com log contextual (`domain` + `path`) para facilitar observabilidade.
- Chave por rota no boundary para reset seguro ao navegar entre telas.
- Validacao tecnica concluida: `typecheck` e `build` verdes.

Decisao executiva do checkpoint:
- Considerar o item de boundaries por feature critica concluido para Sprint 1.
- Manter evolucao futura como hardening opcional (estender para rotas OPS/fiscal restantes + envio de telemetria externa).

Riscos imediatos:
- `[!]` Observabilidade de erro ainda em `console.error` local; falta envio para Sentry/OTel para fechar ciclo de incidentes.

Proximo checkpoint:
- Integrar callback `onError` com pipeline real de telemetria e ampliar cobertura para rotas OPS/fiscal restantes conforme prioridade.

### 2026-04-30 - Evolucao da telemetria dos boundaries
Status geral: `[x]` Concluido

Resumo:
- Criado serviço `src/services/errorTelemetry.ts` para reporte estruturado de erro de UI.
- Evento de erro agora inclui: `eventId`, `domain`, `path`, `message`, `stack`, `componentStack`, `createdAt`.
- Persistencia local dos ultimos eventos em `localStorage` (`ellan_ui_error_events_v1`) para apoio operacional.
- Hook opcional de integracao com Sentry habilitado quando `window.Sentry` estiver presente.
- `App.jsx` passou a enviar erros dos boundaries para `reportUiErrorTelemetry` (em vez de `console.error` direto).

Decisao executiva do checkpoint:
- Sprint 1 encerra com boundaries por feature critica + telemetria padronizada no frontend.
- Evolucao futura fica focada em envio para backend/OTel e dashboards de erro por dominio.

Riscos imediatos:
- `[!]` Telemetria ainda sem envio ativo para backend central (apenas persistencia local + opcional Sentry).

Proximo checkpoint:
- Definir endpoint interno para ingestao de erro de UI e ligar pipeline observavel ponta a ponta.

### 2026-04-30 - Endpoint interno de ingestao + envio frontend com fallback
Status geral: `[x]` Concluido

Resumo:
- Backend (`order_pickup_service`) recebeu endpoint interno de ingestao:
  - `POST /internal/ui-errors` (protegido por `X-Internal-Token`);
  - validacao de payload e persistencia em buffer in-memory (`_ui_error_events`);
  - enriquecimento do endpoint `GET /internal/dev/errors` com `ui_count` e `ui_items`.
- Frontend passou a enviar evento de erro de UI para o endpoint interno via `errorTelemetry`:
  - envio best-effort para `${VITE_ORDER_PICKUP_BASE_URL}/internal/ui-errors`;
  - fallback preservado (persistencia local + `console` + opcional Sentry);
  - sem bloquear renderizacao em falha de rede/autorizacao.
- Validacao tecnica concluida: `typecheck` e `build` verdes.

Decisao executiva do checkpoint:
- Pipeline de telemetria de erro UI fechado no escopo Sprint 1 (ingestao interna + envio com fallback).
- Evolucao futura pode migrar de buffer in-memory para persistencia estruturada e dashboards operacionais.

Riscos imediatos:
- `[!]` Endpoint atual usa armazenamento em memoria (volatil em restart).
- `[!]` Envio depende de `VITE_INTERNAL_TOKEN` no frontend para autenticacao interna.

Proximo checkpoint:
- Evoluir para persistencia duravel de UI errors e visualizacao dedicada em painel OPS.

### 2026-04-30 - Sprint 2 (OPS) bloco inicial: painel unificado + runbook
Status geral: `[~]` Em andamento

Resumo:
- Entregue persistencia duravel de UI errors na tabela `ui_error_events` com fallback em memoria.
- Entregue endpoint paginado de consulta (`GET /dev-admin/ui-errors`) para consumo no painel.
- Entregue endpoint de resumo operacional (`GET /dev-admin/ui-errors/summary`) com top dominios/rotas/mensagens por janela.
- `ops/dev/errors` atualizado com secao de top incidentes e atalhos de runbook rapido por dominio.
- Registro publicado em `ops/updates`.

Decisao executiva do checkpoint:
- Sprint 2 (frente OPS) segue com foco em reduzir tempo de resposta a incidente via triagem guiada no proprio painel.

Riscos imediatos:
- `[!]` Mapeamento de runbook por dominio ainda inicial (checkout/kiosk/ops/global), pode exigir refinamento por rota real.
- `[!]` Suporte ainda sem macros de triagem copiaveis integradas ao painel.

Proximo checkpoint:
- Conectar runbooks a macros de triagem do suporte e gerar payload copiavel de incidente para handoff.

### 2026-04-30 - Sprint 2 (Suporte) macros de triagem copiaveis no OPS
Status geral: `[x]` Concluido

Resumo:
- `ops/dev/errors` recebeu bloco de **macros copiaveis** para suporte com 3 perfis:
  - INCIDENTE
  - MONITORAMENTO
  - ESCALACAO
- Cada macro sai preenchida com contexto operacional atual:
  - janela ativa (h),
  - total de eventos,
  - filtros aplicados (status/rota),
  - faixa paginada visivel,
  - top dominio/rota/mensagem quando disponivel.
- Copia com fallback para navegadores sem `navigator.clipboard`.
- Registro da evolucao publicado em `ops/updates`.

Decisao executiva do checkpoint:
- Fechada mais uma frente do Sprint 2 para suporte com padronizacao de handoff e triagem.

Riscos imediatos:
- `[!]` Macros ainda em formato texto unico (proximo passo pode incluir versoes por canal: Slack, ticket, incidente formal).

Proximo checkpoint:
- Integrar macros com IDs de incidente e owner/ETA para fechar ciclo de governanca operacional.

### 2026-04-30 - Sprint 2 (Governanca) macros com campos operacionais
Status geral: `[x]` Concluido

Resumo:
- Macros de triagem do `ops/dev/errors` evoluidas com campos operacionais obrigatorios:
  - `incident_id`
  - `owner`
  - `ETA`
  - `severidade` (CRITICAL/HIGH/MEDIUM/LOW)
- Os campos passam a compor automaticamente os 3 formatos de macro (INCIDENTE, MONITORAMENTO, ESCALACAO).
- Resultado: handoff mais auditavel com responsabilidade nominal e previsao de resolucao.
- Registro publicado em `ops/updates`.

Decisao executiva do checkpoint:
- Considerar trilha de governanca de triagem do Sprint 2 fechada no escopo de UI operacional.

Riscos imediatos:
- `[!]` Campos ainda manuais; proxima evolucao pode integrar preenchimento automatico por ticket externo.

Proximo checkpoint:
- Integrar `incident_id` com provedor de tickets e persistir historico de macros por usuario/turno.

### 2026-04-30 - Sprint 2 (Governanca) historico local de macros por turno
Status geral: `[x]` Concluido

Resumo:
- `ops/dev/errors` passou a registrar historico local dos ultimos 20 macros copiados.
- Cada item do historico guarda: `incident_id`, `owner`, `turno`, `ETA`, `severidade` e timestamp.
- Inclusa acao de **recopiar macro** para acelerar handoff e escalacao recorrente no plantao.
- `ops/updates` atualizado com `dateTime` (data + horario) nos novos lancamentos.

Decisao executiva do checkpoint:
- Governanca operacional de triagem avancou para trilha auditavel por turno sem depender de backend adicional.

Riscos imediatos:
- `[!]` Historico permanece local ao navegador; nao ha consolidacao central multiusuario.

Proximo checkpoint:
- Integrar `incident_id` com provedor de tickets e publicar sincronizacao opcional do historico.

### 2026-04-30 - Sprint 2 (Handoff) export rapido CSV/JSON
Status geral: `[x]` Concluido

Resumo:
- Historico local de macros no `ops/dev/errors` conectado com export rapido:
  - download CSV
  - download JSON
  - copia JSON para area de transferencia
- Entrega focada em anexar evidencias no handoff diario sem atrito.
- Registro publicado em `ops/updates` com data e horario.

Decisao executiva do checkpoint:
- Trilha operacional de handoff no Sprint 2 avancou para pacote pronto de evidencia (texto + arquivo).

Riscos imediatos:
- `[!]` Export permanece local e manual; ainda sem upload automatico para sistema externo.

Proximo checkpoint:
- Integrar `incident_id` com provedor de tickets e gerar link de referencia cruzada no proprio macro.

### 2026-04-30 - Sprint 2 (Governanca) validacao de ticket + link no macro
Status geral: `[x]` Concluido

Resumo:
- `incident_id` no `ops/dev/errors` passou a ter validacao por regex de padrao operacional.
- Quando valido, a tela mostra link rapido para abrir o ticket no tracker.
- `ticket_url` agora passa a integrar:
  - macro textual copiavel,
  - historico local de macros,
  - exportacoes CSV/JSON.
- Registro publicado em `ops/updates` com horario.

Decisao executiva do checkpoint:
- Trilha de governanca do Sprint 2 avancou com rastreabilidade direta incidente -> ticket.

Riscos imediatos:
- `[!]` Link de tracker usa base configuravel por ENV; ambientes sem configuracao padrao devem ajustar `VITE_INCIDENT_TRACKER_BASE_URL`.

Proximo checkpoint:
- Integrar lookup do ticket no tracker (status/owner) para validacao automatica antes da copia da macro.

### 2026-04-30 - Sprint 2 (Governanca) lookup opcional antes da copia
Status geral: `[x]` Concluido

Resumo:
- `ops/dev/errors` agora pode consultar o tracker (lookup opcional) para obter status e owner do ticket.
- A cópia de macro passou a executar esse lookup e incluir:
  - `ticket_status`
  - `ticket_owner_lookup`
  - `ticket_checked_at`
- Campos também entram no histórico local e nos exports CSV/JSON.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Governanca operacional ganhou validação semiautomática de consistência incidente-ticket no ato da triagem.

Riscos imediatos:
- `[!]` Lookup depende de disponibilidade e limites do tracker externo.

Proximo checkpoint:
- Adicionar fallback configurável de autenticação para tracker (token) em ambiente de produção.

### 2026-04-30 - Sprint 3 (Hardening) CSP frontend base
Status geral: `[~]` Em andamento

Resumo:
- Aplicada política CSP base no `frontend/index.html` com restrições de origem e `connect-src` explícito.
- Incluídas políticas adicionais de segurança no documento:
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Content-Type-Options: nosniff`
- Atualização registrada em `ops/updates` com data e horário.

Decisao executiva do checkpoint:
- Sprint 3 iniciado com hardening incremental sem bloquear os fluxos atuais de operação.

Riscos imediatos:
- `[!]` CSP ainda permite `unsafe-inline` em script/style para compatibilidade atual; reduzir permissões exige migração adicional.

Proximo checkpoint:
- Evoluir CSP para reduzir `unsafe-inline` e mover para headers no backend/gateway por ambiente.

### 2026-04-30 - Sprint 3 (Hardening) CSP reforçada — serviços locais + HMR + Permissions-Policy
Status geral: `[~]` Em andamento

Resumo:
- `connect-src` ampliado para billing fiscal **8020**, lifecycle **8010**, runtime **8200**, espelhos **127.0.0.1** e WebSockets **Vite** (5173/5174/4173) para não quebrar HMR em dev.
- Novas diretivas: `frame-src 'none'`, `worker-src 'self'`, `manifest-src 'self'`, `media-src` alinhado a imagens.
- `Permissions-Policy` restritiva (câmera, micro, geolocalização, payment, USB, FLoC).
- `preconnect` para `localhost:8020` no `index.html`.

Decisao executiva do checkpoint:
- Sprint 3 avança no primeiro eixo do checklist (CSP) sem exigir nonce/sha imediato; produção futura continua recomendada via gateway com CSP por ambiente.

Proximo checkpoint:
- Servir CSP por **header** no reverse proxy em produção (remover ou alinhar meta CSP) e planear redução de `unsafe-inline` em `style-src` (tokens/CSS modules).

### 2026-04-30 - Sprint 3 (Hardening) script-src sem unsafe-inline no artefacto de build
Status geral: `[~]` Em andamento

Resumo:
- JSON-LD movido para `public/seo/local-business.json` e referenciado com `<script type="application/ld+json" src="...">`.
- Meta CSP no `index.html` com `script-src 'self'` (sem `unsafe-inline`) no bundle de produção.
- Plugin `ellanCspIndexHtml` em `vite.config.js` reintroduz `unsafe-inline` em `script-src` no **serve** e **remove a meta CSP inteira** no **build** (política só no gateway).

Decisao executiva do checkpoint:
- Produção ganha superfície de ataque menor em scripts inline; desenvolvimento local permanece fluido.

Proximo checkpoint:
- Header CSP por ambiente no gateway e estratégia para `style-src` (design tokens + menos `style={{}}`).

### 2026-04-30 - Sprint 3 (Hardening) CSP só no gateway — meta removida do dist
Status geral: `[~]` Em andamento

Resumo:
- Build do frontend emite `dist/index.html` **sem** meta `Content-Security-Policy`; política canónica em `01_source/frontend/ellan-frontend-csp.mjs` (reutilizada na meta em dev, no header de `vite preview` e no exemplo Nginx `02_docker/nginx/csp-frontend.example.conf` com `map` + `add_header`).

#### Avaliacao critica da proposta (meta vs gateway + plano de estilos)
- **Acerto central**: CSP por **header** em produção é mais auditável e evita duplicar política com meta; retirar a meta do artefacto `dist` alinha com essa arquitetura.
- **Ajuste ao snippet genérico**: injetar no dev só `default-src 'self'; script-src 'self' 'unsafe-inline'` **apagaria** `connect-src` e outras diretivas úteis. Neste repo a meta completa vive no `index.html`; o plugin só acrescenta `unsafe-inline` em `script-src` no serve e remove a meta no build.
- **`vite preview`**: serve `dist` sem meta até existir gateway com header — tratar como pré-produção ou proxy local com a mesma CSP.
- **Relatórios de violação**: preferir **Reporting API** moderna em vez de depender só de `report-uri` legado.
- **CSS-in-JS**: Styled/Emotion podem injetar `<style>` dinâmico — podem manter exigência de `unsafe-inline` ou exigir nonces/hashes dedicados; o plano por **variáveis CSS + classes** continua adequado ao código atual com `style={{}}`.
- **ESLint `react/no-inline-styles`**: requer `eslint-plugin-react`; convém introduzir como **warn** por etapa para não bloquear o CI num único PR.

### 2026-04-30 - Sprint 3 (Type Safety) util OPS data/hora Brasil no strict-core
Status geral: `[~]` Em andamento

Resumo:
- Novo `src/utils/opsDateTimeFormat.ts` (`pt-BR` + `America/Sao_Paulo`) incluído no gate `typecheck:strict-core`.
- `ops/updates` passa a formatar entradas da timeline com esse util para consistência auditável para operadores no Brasil (sem depender só do fuso do SO).

### 2026-04-30 - Sprint 3 (Type Safety) gate strict-core incremental
Status geral: `[~]` Em andamento

Resumo:
- Criado `tsconfig.strict-core.json` com regras estritas para módulos críticos:
  - `strict: true`
  - `noImplicitAny: true`
  - `strictNullChecks: true`
- Novo script: `npm run typecheck:strict-core`.
- CI atualizado para executar o gate estrito junto do typecheck incremental.
- Registro publicado em `ops/updates` com data e horário.

Decisao executiva do checkpoint:
- Evolução de tipagem avançada de forma incremental e controlada, sem big bang no legado JS.

Riscos imediatos:
- `[!]` Cobertura estrita ainda limitada a núcleo crítico; expansão gradual continua necessária.

Proximo checkpoint:
- Expandir strict-core para mais módulos OPS críticos de leitura/triagem sem quebrar fluxo atual.

### 2026-04-30 - Sprint 3 (Type Safety) expansão para OPS triage governance
Status geral: `[~]` Em andamento

Resumo:
- Extraído módulo TS dedicado `features/ops/triageGovernance.ts` com:
  - normalização/validação de `incident_id`,
  - contrato tipado para contexto de macro,
  - builder de macro de triagem.
- `OpsDevErrorsPage` passou a consumir o módulo tipado.
- Gate `strict-core` expandido para incluir o novo módulo OPS crítico.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Sprint 3 segue com expansão controlada da tipagem em camadas de governança operacional, sem migração em massa de páginas JSX.

Riscos imediatos:
- `[!]` Página OPS principal ainda em JSX; tipagem total da view continua como etapa posterior.

Proximo checkpoint:
- Extrair mais blocos críticos de `ops/dev/errors` para módulos TS (lookup e histórico/export) e manter a página como orquestradora.

### 2026-04-30 - Sprint 3 (Type Safety) lookup + histórico/export em módulos TS
Status geral: `[~]` Em andamento

Resumo:
- Criados módulos TS dedicados:
  - `features/ops/ticketLookup.ts`
  - `features/ops/macroHistory.ts`
- `OpsDevErrorsPage` passou a consumir os módulos e ficou mais orquestradora.
- `strict-core` expandido para cobrir ambos os novos módulos.
- Registro publicado em `ops/updates` com data e horário.

Decisao executiva do checkpoint:
- A expansão de tipagem segue por fatias de risco operacional, mantendo estabilidade da UI e do fluxo de sprint.

Riscos imediatos:
- `[!]` UI principal ainda em JSX; próxima etapa pode migrar para TSX quando o núcleo estiver consolidado.

Proximo checkpoint:
- Extrair camada de persistência de draft/estado de triagem para módulo TS reutilizável e preparar migração gradual para TSX.

### 2026-04-30 - Sprint 3 (Type Safety) draft de triagem em módulo TS
Status geral: `[~]` Em andamento

Resumo:
- Extraída persistência de draft para `features/ops/triageDraft.ts` com:
  - `INITIAL_TRIAGE_DRAFT`
  - `loadTriageDraftFromStorage`
  - `saveTriageDraftToStorage`
- `OpsDevErrorsPage` atualizado para consumir o módulo e reduzir lógica inline de armazenamento.
- `strict-core` expandido para cobrir o novo módulo TS.
- Registro publicado em `ops/updates` com data e horário.

Decisao executiva do checkpoint:
- Migração gradual para TSX foi preparada por desacoplamento de estado/persistência sem alterar o fluxo operacional da página.

Riscos imediatos:
- `[~]` Tipagem TSX do corpo principal em andamento; ainda há espaço para endurecer tipos de payloads remotos e estilos inline em próximas fatias.

Proximo checkpoint:
- Migrar o corpo principal para TSX e remover ponte `.jsx`.

### 2026-04-30 - Sprint 3 (Type Safety) entrada TSX da OpsDevErrorsPage
Status geral: `[~]` Em andamento

Resumo:
- Criado `OpsDevErrorsPage.tsx` como entrypoint TSX da página.
- `App.jsx` atualizado para resolver explicitamente a rota via arquivo TSX.
- Gate `strict-core` atualizado para incluir o entrypoint TSX.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Migração para TSX segue sem ruptura, preservando fluxo operacional enquanto a tipagem avança por blocos.

Riscos imediatos:
- `[x]` Ponte `.jsx` aposentada após migração do corpo para `OpsDevErrorsPageBody.tsx`.

Proximo checkpoint:
- Endurecer tipos de integração (payloads de APIs e estruturas de estilos) para reduzir casts e preparar inclusão total no gate estrito.

### 2026-04-30 - Sprint 3 (Type Safety) corpo TSX da OpsDevErrorsPage + aposentadoria da ponte .jsx
Status geral: `[~]` Em andamento

Resumo:
- Corpo de `OpsDevErrorsPage.jsx` migrado para `OpsDevErrorsPageBody.tsx` com tipagem incremental de estado e handlers críticos.
- `OpsDevErrorsPage.tsx` passou a exportar diretamente o corpo TSX.
- Arquivos de ponte `.jsx` removidos para eliminar a dependência transitória.
- Gate `strict-core` expandido para incluir `OpsDevErrorsPageBody.tsx` e `OpsDevErrorsPage.tsx`.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Conversão para TSX foi concluída em fatia controlada, preservando comportamento operacional e abrindo espaço para endurecimento de tipos finos sem big bang.

Riscos imediatos:
- `[~]` Ainda há espaço para tipar alguns contratos de componentes JSX legados fora do escopo do bloco atual.

Proximo checkpoint:
- Endurecer tipagem de contratos legados (componentes JSX compartilhados) para reduzir necessidade de shims no strict-core.

### 2026-04-30 - Sprint 3 (Type Safety) unions estritas para erros backend (detail variants)
Status geral: `[~]` Em andamento

Resumo:
- `OpsDevErrorsPageBody.tsx` atualizado com union tipado para payloads de erro backend (`detail` em string, objeto e lista de itens).
- Parsing de erro consolidado em funções tipadas (`readBackendDetailMessage` + `parseError`) para reduzir fallback genérico.
- Tratamento de mensagens `message`/`error` normalizado sem casts amplos no fluxo principal.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Endurecimento focado em contratos de erro críticos, mantendo compatibilidade com variantes reais do backend sem aumentar acoplamento.

Riscos imediatos:
- `[~]` Parte da superfície legada JSX ainda requer contratos progressivos para reduzir acoplamento a declarations de compatibilidade.

Proximo checkpoint:
- Avançar na substituição gradual de declarations por módulos TS/TSX nativos nos componentes mais usados em OPS.

### 2026-04-30 - Sprint 3 (Type Safety) tipagem mínima de AuthContext + cartões/título OPS
Status geral: `[~]` Em andamento

Resumo:
- Criadas camadas tipadas para encapsular legado JSX sem ampliar superfície no page body:
  - `useAuthTyped` com contrato mínimo de contexto (`token`/`user`/`loading`);
  - `OpsTrendKpiCardTyped` com props mínimas (`label`, `value`, `trend`, `showTrend`, `baseStyle`);
  - `OpsPageTitleHeaderTyped` com props mínimas (`title`, `subtitle`, `children`).
- `OpsDevErrorsPageBody.tsx` passou a consumir wrappers tipados em vez de importar módulos JSX diretamente.
- `tsconfig.strict-core.json` atualizado para incluir wrappers tipados e remover dependência do arquivo de shim dedicado.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Endurecer primeiro os contratos realmente usados no fluxo OPS permite subir qualidade de tipo sem ruptura e sem big bang em componentes legados.

Riscos imediatos:
- `[~]` `AuthContext` ainda legado em JSX e consumido via camada tipada; demais componentes críticos desse bloco já migrados para TSX.

Proximo checkpoint:
- Avaliar migração incremental de `AuthContext` para TSX ou typing nativo do módulo para remover camada de compatibilidade restante.

### 2026-04-30 - Sprint 3 (Type Safety) migração nativa de OpsPageTitleHeader e OpsTrendKpiCard
Status geral: `[~]` Em andamento

Resumo:
- `OpsPageTitleHeader.jsx` migrado para `OpsPageTitleHeader.tsx` com tipagem de props e estilos.
- `OpsTrendKpiCard.jsx` migrado para `OpsTrendKpiCard.tsx` com tipos de props (`TrendDirection`, `OpsTrendKpiCardProps`) e utilitário tipado.
- `OpsDevErrorsPageBody.tsx` atualizado para consumir os componentes TSX nativos diretamente.
- Wrappers temporários `OpsPageTitleHeaderTyped.tsx` e `OpsTrendKpiCardTyped.tsx` removidos (eliminando `@ts-ignore` residuais desse bloco).
- `strict-core` atualizado para os arquivos TSX finais e registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Migração dos componentes-base mais usados em OPS foi priorizada para reduzir dívida de tipagem sem interromper o fluxo de entrega incremental.

Riscos imediatos:
- `[~]` Restam módulos legados JS/JSX fora do núcleo OPS crítico imediato (tokens utilitários e botões auxiliares) a serem migrados por prioridade.

Proximo checkpoint:
- Expandir migração incremental de módulos utilitários JS/JSX com maior reuso no fluxo OPS.

### 2026-04-30 - Sprint 3 (Type Safety) AuthContext migrado para TSX e remoção da última camada OPS
Status geral: `[~]` Em andamento

Resumo:
- `AuthContext.jsx` migrado para `AuthContext.tsx` com contratos tipados de contexto, roles e respostas de autenticação.
- `OpsDevErrorsPageBody.tsx` voltou a consumir `useAuth` diretamente do contexto tipado.
- Wrapper `useAuthTyped` removido, eliminando a última camada de compatibilidade específica do fluxo OPS.
- `strict-core` atualizado para incluir `AuthContext.tsx` e manter declarations apenas para módulos legados ainda não migrados.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- Encerrar a compatibilidade transitória do contexto no fluxo OPS aumenta previsibilidade de tipos sem bloquear evolução gradual do restante do frontend legado.

Riscos imediatos:
- `[~]` Ainda há módulos legados compartilhados no frontend geral, mas os utilitários críticos do fluxo OPS já avançaram para TS/TSX.

Proximo checkpoint:
- Continuar remoção incremental de declarations de compatibilidade restantes com migração dos módulos compartilhados de maior reuso.

### 2026-04-30 - Sprint 3 (Type Safety) migração de opsVisualTokens + OpsRouteHelpButton
Status geral: `[~]` Em andamento

Resumo:
- `opsVisualTokens.js` migrado para `opsVisualTokens.ts` com tipagem explícita de `TrendDirection`, `TrendToken` e retornos de estilos.
- `OpsRouteHelpButton.jsx` migrado para `OpsRouteHelpButton.tsx` com tipagem do fluxo de tutorial e chave de usuário.
- `strict-core` atualizado para incluir os novos módulos TS/TSX.
- `opsLegacyModules.d.ts` reduzido removendo declarations de compatibilidade para `opsVisualTokens` e `OpsRouteHelpButton`.
- Registro publicado em `ops/updates` com horário.

Decisao executiva do checkpoint:
- A migração dos utilitários de suporte visual e ajuda operacional reduz dívida de tipagem sem impactar o fluxo funcional das páginas OPS.

Riscos imediatos:
- `[~]` Declarations ainda permanecem para alguns módulos JS legados (ex.: `services/authApi`, `opsTutorialContent`, `OpsHelpTutorialModal`) e devem cair por fatias.

Proximo checkpoint:
- Tipar/migrar `opsTutorialContent` e `OpsHelpTutorialModal` para reduzir mais a camada de compatibilidade no strict-core.

### 2026-04-30 - Replanejamento executivo: Sprint 2 com Fiscal + Contabil (ELLAN LAB + partners)
Status geral: `[~]` Em andamento

Resumo:
- Sprint 2 ampliado para incluir duas frentes explícitas:
  - **Fiscal** (ELLAN LAB + partners);
  - **Contabil** (ELLAN LAB + partners).
- Cronograma recalibrado para acomodar escopo sem romper os 30 dias:
  - Onda 2: dias 8-18;
  - Onda 3: dias 19-24;
  - Onda 4: dias 25-30.
- Sprint 2 atualizado para dias **10-18** com objetivo revisado.

Recalculo de evolucao:
- Consolidado Sprint 2 antes da ampliacao (frentes ativas OPS/Suporte): **~83%**.
- Consolidado Sprint 2 apos incluir Fiscal + Contabil: **~50%** (referencia macro; ver atualizacao pos-D17 abaixo).
- Trilhas adicionadas:
  - Fiscal: **22%**;
  - Contabil: **10%**.

Decisao executiva do checkpoint:
- Priorizar fechamento operacional de Fiscal e Contabil dentro do Sprint 2 para reduzir risco de Go/No-Go financeiro.

Riscos imediatos:
- `[!]` Inclusao de novas trilhas reduz throughput disponivel para hardening de Sprint 3 caso nao haja fatiamento rigoroso.

Proximo checkpoint:
- Detalhar backlog P0/P1 de Fiscal e Contabil por persona operacional (ELLAN LAB e partners) com aceite mensuravel.

### 2026-04-30 - Sprint 2 detalhado: backlog P0/P1 Fiscal e Contabil por persona operacional
Status geral: `[~]` Em andamento

Resumo:
- Backlog Sprint 2 detalhado para quatro frentes:
  - Fiscal ELLAN LAB
  - Fiscal Partners
  - Contabil ELLAN LAB
  - Contabil Partners
- Cada item agora possui dono nominal, esforço em pontos e critério de aceite mensurável.
- Estrutura pronta para execução imediata e acompanhamento diário.

Recalculo de evolucao:
- Consolidado Sprint 2 recalculado de **~50%** para **~46%** apos granularizacao completa de escopo (baseline historica).
- Fiscal (ELLAN LAB + partners): **20%**.
- Contabil (ELLAN LAB + partners): **9%**.
- Atualizacao pos-D17 (governanca de aceites): consolidado **~50%**, Fiscal **22%**, Contabil **15%** (ver secao Sprint 2 no topo deste documento).

Decisao executiva do checkpoint:
- Sprint 2 passa a operar com trilha financeira completa (fiscal + contabil) com governança explícita para ELLAN LAB e partners.

Riscos imediatos:
- `[!]` Escopo financeiro detalhado aumenta carga de execução no sprint e exige priorização rígida de P0.

Proximo checkpoint:
- Iniciar execução dos P0 financeiros com evidência diária (conciliação fiscal e fechamento contábil operacional).

### 2026-04-30 - Sprint 2 execução iniciada (D10) com tracker operacional fiscal
Status geral: `[~]` Em andamento

Resumo:
- Sequência diária D10-D18 publicada no plano com ordem de execução e dependências críticas.
- Iniciada codificação do D10 na tela `ops/fiscal/providers` com checklist persistente (localStorage) para governança de execução.
- Adicionada ação de cópia de resumo D10 para handoff operacional com progresso, status BR/PT e checklist.

Decisao executiva do checkpoint:
- Execução financeira do Sprint 2 passa a operar com cadência diária explícita e evidência padronizada por dia.

Riscos imediatos:
- `[~]` Tracker D10 é local ao navegador; consolidação multiusuário ainda depende de etapa posterior.

Proximo checkpoint:
- Implementar D11 com trilha de divergências fiscais por pedido/parceiro e export de evidências por lote.

### 2026-04-30 - Sprint 2 execução D11 iniciada (trilha de divergências fiscais + export por lote)
Status geral: `[~]` Em andamento

Resumo:
- Implementada trilha D11 em `ops/fiscal/providers` com consulta de divergências fiscais (`/admin/fiscal/gaps`) e filtros operacionais por `order_id`, `partner_id`, `batch_id` e status.
- Adicionado export rápido por lote em CSV/JSON para handoff diário e rastreabilidade operacional.
- Criado endpoint de seed controlado `POST /admin/fiscal/gaps/seed` para geração de massa de teste com metadados de `partner_id` e `batch_id`.

Decisao executiva do checkpoint:
- D11 passa a operar com evidência exportável por lote, reduzindo tempo de triagem e bloqueios por falta de massa de teste.

Riscos imediatos:
- `[~]` Seed atual é voltado a ambiente de operação/teste e deve permanecer protegido por token interno.

Proximo checkpoint:
- Evoluir D12 com handoff contábil diário e reconciliação de fechamento com dependências fiscais consumindo o lote D11.

### 2026-04-30 - Sprint 2 execução D12 iniciada (handoff contábil diário conectado ao lote D11)
Status geral: `[~]` Em andamento

Resumo:
- Publicação operacional do lote D11 adicionada em `ops/fiscal/providers` via persistência local (`ellan_ops_fiscal_d11_handoff_v1`) com resumo por severidade, parceiros e batches.
- `fiscal/management-daily` passou a consumir esse lote D11 e exibir card de handoff contábil diário com recarga manual do snapshot.
- Payloads de handoff diário (`JSON` e `ZIP`) agora incluem bloco `d11_fiscal_gap_handoff` para rastreabilidade de fechamento contábil.

Decisao executiva do checkpoint:
- D12 reduz fricção entre triagem fiscal e fechamento contábil, conectando evidência operacional D11 diretamente no pacote diário de governança.

Riscos imediatos:
- `[~]` Integração baseada em localStorage é adequada para operação assistida local, porém consolidação multiusuário requer backend compartilhado em etapa posterior.

Proximo checkpoint:
- Evoluir D13 com trilha de aceite contábil por owner/ETA e checklist de pendências críticas alimentado automaticamente pelos gaps D11.

### 2026-04-30 - Sprint 2 execução D13 iniciada (aceite contábil por owner/ETA + checklist crítico automático)
Status geral: `[~]` Em andamento

Resumo:
- Fluxo de aceite contábil diário em `fiscal/management-daily` evoluído com campo explícito de `ETA` além do `owner` já existente.
- Checklist crítico D13 agora é gerado automaticamente a partir do snapshot D11 (itens com severidade `ERROR/WARN`), com marcação de progresso por item.
- Export de aprovação/pacote diário passa a incluir bloco estruturado `d13_critical_checklist` (owner, ETA, total, concluídos e itens).

Decisao executiva do checkpoint:
- D13 fecha a governança operacional entre fiscal e contábil com trilha objetiva de responsabilização (`owner`) e compromisso temporal (`ETA`) baseada em risco real do lote D11.

Riscos imediatos:
- `[~]` Como o checklist D13 é persistido localmente por navegador, o uso distribuído por múltiplos analistas ainda exige sincronização central no backend.

Proximo checkpoint:
- Evoluir D14 com consolidação centralizada do aceite D13 (owner/ETA/checklist) para visão multiusuário e trilha auditável compartilhada.

### 2026-04-30 - Sprint 2 execução D14 iniciada (consolidação central multiusuário do aceite D13)
Status geral: `[~]` Em andamento

Resumo:
- Backend fiscal agora expõe consolidação central do aceite contábil com `POST /admin/fiscal/accounting-approvals` e `GET /admin/fiscal/accounting-approvals/latest`.
- `fiscal/management-daily` passou a salvar o aceite D13 no backend (owner/ETA/checklist crítico) e também carregar o último snapshot central para operação multiusuário.
- Modelo D14 mantém fallback local, mas prioriza trilha central para governança compartilhada e continuidade entre analistas/turnos.

Decisao executiva do checkpoint:
- D14 eleva o fluxo de aceite de modo single-browser para modo colaborativo, reduzindo perda de contexto e melhorando auditoria operacional entre fiscal e contábil.

Riscos imediatos:
- `[~]` Estrutura central atual é minimalista (snapshot latest + histórico simples); políticas avançadas de conflito/versionamento ficam para etapa posterior.

Proximo checkpoint:
- Evoluir D15 com trilha de histórico paginada por período/owner/status e comparação entre snapshots de aceite.

### 2026-04-30 - Sprint 2 execução D15 iniciada (histórico paginado + comparação de snapshots de aceite)
Status geral: `[~]` Em andamento

Resumo:
- Backend D15 adiciona listagem paginada de aceites centrais com filtros por `owner`, `status` e `período` (`date_from/date_to`) em `GET /admin/fiscal/accounting-approvals`.
- Backend D15 inclui comparação entre snapshots (`GET /admin/fiscal/accounting-approvals/compare`) com diff objetivo de campos críticos (owner/status/eta/progresso checklist).
- `fiscal/management-daily` agora exibe painel histórico paginado, aplicação de filtros operacionais e bloco visual de comparação entre snapshots para governança diária.

Decisao executiva do checkpoint:
- D15 transforma o aceite central em trilha auditável consultável, reduzindo análise manual e acelerando revisão de mudanças entre turnos.

Riscos imediatos:
- `[~]` Diff atual cobre campos essenciais de governança; comparação semântica avançada de checklist permanece como evolução incremental.

Proximo checkpoint:
- Evoluir D16 com export consolidado do histórico filtrado (CSV/JSON) e evidência comparativa anexável no handoff executivo.

### 2026-04-30 - Sprint 2 execução D16 concluída (export consolidado + diff no handoff executivo)
Status geral: `[x]` Concluído no escopo D16

Resumo:
- Utilitário frontend `fiscalAccountingApprovalsHistory` consolida todas as páginas do endpoint `GET /admin/fiscal/accounting-approvals` respeitando filtros (`owner`, `status`, `date_from`, `date_to`) para export único em JSON ou CSV.
- `fiscal/management-daily` ganhou botões de export D16 e o pacote ZIP diário inclui automaticamente histórico consolidado (filtros da tela) + diff assinado (`compare` mais recente vs anterior).
- `fiscal/accounting-close` (handoff executivo) anexa ao ZIP auditável histórico consolidado dos últimos 30 dias e o mesmo diff D16, com fallback de erro documentado se o billing não estiver acessível.

Decisao executiva do checkpoint:
- D16 fecha o ciclo evidência → export → anexo executivo sem passos manuais adicionais, alinhando operação diária e comitê de fechamento.

Riscos imediatos:
- `[~]` Consolidação paginada assume limite máximo de 200 por página no backend; volumes muito grandes exigem janela de datas mais estreita ou evolução server-side dedicada.

Proximo checkpoint:
- D17: retenção/compactação e alertas de divergência prolongada (entregue na sequência).

### 2026-04-30 - Sprint 2 execução D17 concluída (retenção/compactação + alertas de divergência prolongada)
Status geral: `[x]` Concluído no escopo D17 (trilha de aceite central)

Resumo:
- Backend fiscal: `GET /admin/fiscal/accounting-approvals/divergence-health` analisa uma janela de snapshots recentes e sinaliza quando o mesmo diff de governança se repete em várias bordas consecutivas (divergência prolongada).
- Backend fiscal: `POST /admin/fiscal/accounting-approvals/retention` com `dry_run` remove snapshots mais antigos que um cutoff em dias, respeitando `keep_minimum` de linhas na tabela (compactação por poda controlada).
- `fiscal/management-daily` exibe card D17 com alerta visual, resumo de bordas e ações de dry-run / execução de retenção.
- Progresso Sprint 2 atualizado no topo deste documento: consolidado **~52%**, Fiscal **28%**, Contabil **15%**.

Decisao executiva do checkpoint:
- D17 reduz risco de crescimento desordenado do histórico e chama atenção para estagnação de divergências entre snapshots antes que virem surpresa em fechamento.

Riscos imediatos:
- `[~]` Retenção é irreversível na poda executada; operação deve usar sempre dry-run em produção assistida até playbook formal.

Proximo checkpoint:
- D18: checklist final Sprint 2 financeiro e registro de riscos P1 remanescentes; evoluir integração macro fiscal+contábil por parceiro conforme capacidade da sprint.

### 2026-04-30 - Sprint 2 execução D18 concluída (checklist + carimbo humano + ZIP)
Status geral: `[x]` Concluído no escopo D18 (MVP operacional + revisão registrada)

Resumo:
- Conteúdo D18 versionado em `01_source/frontend/src/utils/fiscalSprint2D18Content.js` (itens de checklist alinhados a D10–D17 + transição; payload reutilizável por rota).
- `fiscal/management-daily` ganhou card **D18** com checkboxes, tabela de 5 linhas para riscos P1, persistência local (`fiscal_management_daily:sprint2_d18_closeout_v1`), export/cópia JSON com `scope: SPRINT2_D18_FINANCE_CLOSEOUT` e inclusão assinada no **pacote diário .zip**.
- **Carimbo de revisão humana:** após preencher revisor (obrigatório) e nota opcional, ação **Carimbar closeout D18** grava `certification` no mesmo storage; o payload JSON/ZIP passa a incluir `closeout_certification` (`certified_at`, `certified_by`, `note`). Checklist incompleto exige confirmação explícita. **Revogar carimbo** limpa a certificação. O ZIP de `fiscal/accounting-close` reutiliza o mesmo bloco via `loadD18CloseoutFromStorage`.
- `fiscal/accounting-close` anexa o mesmo closeout ao **ZIP executivo** (`D18_EXEC_SPRINT2_CLOSEOUT`, `scope: SPRINT2_D18_EXEC_FINANCE_CLOSEOUT`), lendo o estado gravado em management-daily.

Checklist mínimo (espelho do código):
| id | Item |
|---|---|
| d10 | Governança D10 (matriz/providers): evidência revisada ou N/A documentado |
| d11 | Lote D11 publicado em ops/fiscal/providers e refletido no handoff diário |
| d12 | Handoff D12 contábil conectado ao snapshot D11 no pacote diário |
| d13_d14 | Aceite D13/D14: owner/ETA/checklist e persistência central quando em uso |
| d15 | Histórico D15: amostra de compare validada para turno ou justificativa registrada |
| d16 | Export D16 / ZIP diário ou executivo exercido ou motivo de não-exercício anotado |
| d17 | D17: dry-run de retenção ou justificativa de volume; divergência prolongada tratada ou escalada |
| transition | Comunicação do próximo foco acordada com o time: se **gate v2** **não** PASS (Fiscal ≥50%, Contábil ≥40%, consolidado S2 ≥55%, comprovação P0) → manter S2 dominante + S3 paralelo; se PASS → **Sprint 3** como sprint ideal (hardening), depois **Sprint 4** (Go/No-Go) |

Template P1 (cinco linhas no UI): colunas **Risco/tema**, **Owner**, **ETA**, **Impacto se não tratar** — exportadas em `p1_risks_remaining` no JSON D18.

Decisao executiva do checkpoint:
- D18 desbloqueia “aceite assistido” com artefato único reutilizável em comitê e handoff, sem depender de documento externo obrigatório nesta fase.

Proximo checkpoint:
- ~~Marcar D18 como concluído após revisão humana do JSON/ZIP~~ **Feito:** carimbo operacional na UI + `closeout_certification` nos artefatos. **Próximo foco (diretriz comité):** subir **P0 Fiscal + P0 Contábil** e o **consolidado S2** até **gate v2 (comité 2026-05-01): Fiscal ≥50%, Contábil ≥40%, consolidado ≥55%** + comprovação P0 no daily/ZIP (ver Sprint 2); até lá Sprint 3 só **paralelo seguro**, **sem net-new**; após gate, **Sprint 3** = sprint ideal dominante para expansão de hardening.

#### Recomendação de priorização (pós-D17) — **atualizada (comité)**

- **D18 (carimbo + artefatos)** permanece a evidência formal de closeout da trilha D10–D18; não substitui **P0 Fiscal / P0 Contábil** ainda em aberto nas tabelas da Sprint 2.
- **Prioridade #1:** **fechar o macro financeiro da Sprint 2** (Fiscal + Contábil: conciliação pedido→documento, repasses, evidências no daily/ZIP) **antes** de empurrar **net-new** nas Sprints 3 e 4. Sem isso, **Go/No-Go fica arriscado** (OPS/Suporte já altos; financeiro puxa a média para baixo).
- **Sprint 3:** manter **hardening já em curso** (CSP, TS, SLO, P0-1/P0-2/P0-3, quick-enablement) em **paralelo seguro** — desde que **não** consuma a capacidade dos P0 financeiros; **congelar net-new** até **gate v2** (**Fiscal ≥50%**, **Contábil ≥40%**, **consolidado S2 ≥55%**, comprovação P0 — comité **2026-05-01**). **Após o gate:** Sprint 3 torna-se o **sprint ideal** para expansão de escopo de hardening.
- **Sprint 4:** **sem ampliar** além do planeado até o mesmo gate v2; **sprint ideal** para Go/No-Go pleno na **fase C** (após S3 estável pós-gate), não antes.
- **Integração macro fiscal+contábil por parceiro** (longo prazo): continuar **P1/P2 pós–Go/No-Go** ou fatiar quando o throughput da Onda 2 estiver no limite; não competir com os P0 financeiros na mesma janela curta.

### 2026-04-30 - Direcionamento executivo: hardening (Sprint 3) **com gating financeiro Sprint 2**
Status geral: `[~]` Em andamento

Resumo:
- **Sprint 3** continua como camada de **confiabilidade** (CSP, TS, auditoria, SLO, incidente) **sem** ser tratada como “próximo saco de escopo” enquanto **Fiscal (~28%)** e **Contábil (~15%)** da Sprint 2 não subirem com evidência operacional.
- Regressão fiscal com PostgreSQL no host e `ELL_USE_LOCAL_DOCKER_PG=1` (`127.0.0.1:5435`) permanecem suporte à **trilha financeira**, não substituto do fecho P0.
- Efeito no plano: **menor risco de Go/No-Go cosmético**; hardening avança onde já existe fio, sem desviar donos dos P0 financeiros.

Atualização de progresso:
- **Sprint 2:** **~52%** consolidado (Fiscal **~28%**, Contábil **~15%**) — **foco comité até subir**.
- **Sprint 3:** **~67%** (média checklist; ver painel) — **sem net-new** até **gate v2** (Fiscal ≥50%, Contábil ≥40%, consolidado ≥55% + comprovação; comité **2026-05-01**); depois **sprint ideal** para expansão.
- **Sprint 4:** **~32%** — sprint ideal **dominante** só na **fase C** da sequência pós-gate (ver Sprint 2).
- **Sprint 0b produção:** **~0%** (`[ ]` — ver secao dedicada; separado do Sprint 0 lab).

Foco imediato **compatível** com a diretriz (paralelo seguro):
- Completar **auditoria ponta a ponta** onde reforça **pedido → emissão → reconciliação → handoff** (alinhado ao financeiro S2).
- Consolidar scorecards/SLO **Fiscal/OPS** sem novos domínios.
- Treino rápido / P0-3: **manutenção** do já entregue, sem novo escopo de produto.

### 2026-04-30 - Bloco de execução Sprint 3 (checklist curto P0)
Status geral: `[~]` Em andamento

Objetivo do bloco:
- Executar uma fatia curta e mensurável de hardening com impacto direto em confiabilidade operacional.

Checklist P0 (curto, com aceite e % inicial):
- [~] **P0-1 Auditoria ponta a ponta dos fluxos críticos (pedido -> emissão -> reconciliação -> handoff).**  
  - Critério de aceite: trilha auditável com `order_id`, `invoice_id`, `partner_id`, `batch_id` em 100% dos cenários de teste definidos para Sprint 3.  
  - Progresso atual: **48%** (alinhado ao item «auditoria ponta a ponta» do checklist Sprint 3 neste `.md`).
- [~] **P0-2 Scorecards e alertas SLO para Fiscal/OPS consolidados no painel.**  
  - Critério de aceite: dashboard com KPIs mínimos (`erro fiscal`, `latência`, `divergência prolongada`, `tempo de tratativa`) e alertas ativos por severidade.  
  - Progresso atual: **65%** (UI + export para ≥3 decisões pós-recomendação no sprint).
- [~] **P0-3 Treinamento operacional rápido + checklist de resposta a incidente.**  
  - Critério de aceite: runbook enxuto publicado, checklist aplicado em simulação assistida e evidência registrada no handoff diário.  
  - Progresso atual: **22%**.

Decisao executiva do bloco:
- Manter foco em 3 P0 de alto impacto para fechar Sprint 3 com ganho de confiabilidade antes de ampliar escopo P1.

Proximo checkpoint:
- Reavaliar este bloco ao fim do próximo ciclo diário e atualizar percentuais com base em evidência (dashboard, logs e runbook executado).

### Template diário Sprint 3 (preenchimento em 2 minutos)
Use o bloco abaixo diariamente para atualizar os 3 P0 com evidência objetiva e impedimento explícito.

| Data | P0 | % anterior | % novo | Evidência (1 linha) | Impedimento (se houver) | Próxima ação (24h) |
|---|---|---:|---:|---|---|---|
| AAAA-MM-DD | P0-1 Auditoria ponta a ponta | 42 | 42 | Ex.: trilha E2E + export de handoff no cockpit fiscal | Ex.: reconciliação por parceiro ainda fora do pacote único | Ex.: fechar 1 caso PT com IDs correlacionados e anexar evidência |
| AAAA-MM-DD | P0-2 Scorecards + alertas SLO | 55 | 65 | Ex.: `fiscal/slo-alerts` + ficheiro `SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS` no ZIP | Ex.: calibragem BR/PT com falsos positivos | Ex.: anexar 3 decisões reais ao daily |
| AAAA-MM-DD | P0-3 Treinamento + checklist incidente | 22 | 22 | Ex.: checklist D18 + handoff ZIP/JSON | Ex.: simulação assistida ainda não executada com evidência | Ex.: rodar simulação curta e anexar no daily |

### 2026-04-30 - Sprint 3 iniciada imediatamente (primeiro update diário)
Status geral: `[~]` Em andamento

Atualização rápida dos P0:
- **P0-1 Auditoria ponta a ponta** — `%`: **35 -> 42**
  - Evidência: consolidação do fluxo fiscal de resync com PostgreSQL no host validada em regressão (`contingency_resync_regression`).
  - Impedimento: falta fechar trilha completa com reconciliação por parceiro no mesmo pacote de evidência.
  - Próxima ação (24h): anexar evidência cruzada pedido->emissão->reconciliação no handoff diário.
- **P0-2 Scorecards + alertas SLO** — `%`: **30 -> 55 -> 65**
  - Evidência: `fiscal/slo-alerts` evoluído para calibração por janela (`24H`, `7D`, `30D`) + recomendações automáticas de ajuste (heurística por país/parceiro + checagem de cobertura da trilha E2E), versionado em `sprint3-v3-auto-recs`, com inclusão no export (`alerts.auto_adjustment_recommendations`) e correção de reload ao trocar período. **P0-2b:** registo local de decisões pós-recomendação (`SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS`, util `fiscalSprint3SloPostRecDecisions.js`), resumo `last_3` / `timeline` no scorecard JSON e ficheiro dedicado no ZIP SLO.
  - Impedimento: falta calibrar pesos/heurísticas com operação real (evitar falsos positivos) e consolidar playbook de “quando endurecer vs quando investigar”.
  - Próxima ação (24h): rodar 1 turno de validação assistida e registrar 3 casos reais (BR/PT) com decisão tomada a partir das recomendações (usar o bloco P0-2 na página).
- **P0-3 Treinamento + checklist incidente** — `%`: **20 -> 22**
  - Evidência: checklist de closeout D18 e fluxo de handoff já operacionalizados com artefatos JSON/ZIP.
  - Impedimento: falta simulação curta dedicada de incidente para Sprint 3 com carimbo de execução.
  - Próxima ação (24h): executar simulação assistida de 15-20 min e registrar resultado no daily.

### 2026-04-30 - Avanço dos próximos 2 sprints (Sprint 3 + Sprint 4)
Status geral: `[~]` Em andamento

Resumo:
- **Sprint 3** avança para fechamento operacional do hardening fiscal/OPS com artefatos auditáveis (SLO + trilha E2E no cockpit).
- **Sprint 4** entra em modo **paralelo seguro**: preparação de regressão/UAT e KPI mínimo de saída, sem bloquear o fechamento da Sprint 3.

Atualização de progresso (snapshot consolidado):
- **Sprint 3:** **~67%** (item auditoria 48%; média das seis frentes — secção Sprint 3 e **Metodo** *(vi)* no painel percentual)
- **Sprint 4:** **~32%**

Decisão executiva:
- Tratar Sprint 4 como **pré-produção assistida**: só aumenta ritmo quando Sprint 3 registrar evidência diária dos 3 P0 (template de 2 minutos).

Próximo checkpoint:
- Sprint 3: fechar P0-3 com simulação assistida + evidência anexada.
- Sprint 4: publicar matriz mínima de regressão por persona + 1 rodada piloto registrada.

### 2026-04-30 — Microajuste: handoff único (ZIP) alinhado ao plano
- **Pacote diário** (`fiscal/management-daily` e `ops/health`): quando houver dados no browser e token interno onde aplicável, o `.zip` consolida **P0-1b** (E2E + fatia por parceiro), **Sprint 4** (matriz + histórico de pilotos, com limite de tamanho) e **carimbo P0-3** (`SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH`, de `fiscal/incident-response`).
- **Pacote executivo** (`fiscal/accounting-close`): o `.zip` de fechamento inclui o mesmo trio quando aplicável — **P0-1b** com token + D11 em `localStorage`; matriz Sprint 4 já como `EXEC`; **pilotos** Sprint 4 em ficheiro dedicado sem duplicar a matriz; **P0-3** como no diário. Objetivo: um ficheiro de handoff por export, sem refinar o gate além do resumo já existente.

### Modelo de lancamento diario (copiar e preencher)
| Data | Sprint | Entrega | Status | Evidencia/Artefato | Proximo passo |
|---|---|---|---|---|---|
| AAAA-MM-DD | Sprint X | Nome objetivo da entrega | `[ ]`/`[~]`/`[x]`/`[!]` | Link de doc, PR, tela ou log | Acao seguinte com prazo |

### 2026-04-30 - Sprint 3: treinamento rapido OPS/Suporte (checklist plano)
Status geral: `[x]` Concluido (item plano)

Resumo:
- Entregue cockpit `ops/quick-enablement` com checklist curto, persistencia local, export JSON/ZIP assinados (`SPRINT3_OPS_SUPPORT_QUICK_TRAINING`, prefixo `ELLAN_FISCAL_DAILY`) e handoff Slack.
- Integracao leve: atalho em `ops/health` (FG-1) e link no runbook P0-3 (`fiscalSprint3IncidentRunbook.js`).

Decisao executiva:
- Tratar treinamento rapido como **habilitacao minima** antes de ampliar UAT KIOSK (Sprint 4). **Revisão comité (2026-04-30):** prioridade global de **capacidade** passa a **Sprint 1** (fundação + KIOSK v1); **Sprint 4** (UAT / Go-No-Go) fica em **paralelo seguro** sem roubar o plano de ataque da Sprint 1.

### 2026-04-30 - Comité: prioridade Sprint 1 (capacidade FE / KIOSK v1)
Status geral: `[~]` Em execucao (decisao de alocacao)

Resumo:
- Sprint 1 declarada **`#1` em capacidade** de engenharia de produto/FE: ver bloco **Prioridade executiva** na secao Sprint 1 (meta **~58%** → **≥60%**; ordem: store **`[x]`** → TS → protótipos **`[~]`** → E2E → estilos checkout). **Paralelo:** alocação **~65–75% codificação Sprint 2** (gate v2) + **~25–35% Sprint 1** — ver **«Recomendacao atual — onde codar»**.
- Painel de decisao e tabela de sprints atualizados: Sprint 1 vs Sprint 2 (**`#1` negócio** financeiro) passam a distinguir-se explicitamente.
- Registro de entregas: linha dedicada à decisao de prioridade Sprint 1.

Decisao executiva:
- **Nao** suspender Sprint 2 fiscal/contabil; **garantir throughput minimo** ao macro financeiro enquanto a Sprint 1 consome a maior fatia da capacidade.

### 2026-04-30 - Sprint 1: `syncStatus` de slots no store (Zustand)
Status geral: `[~]` Em andamento (item store checklist)

Resumo:
- O campo `syncStatus` em `useCheckoutStore` deixou de ser um tri-state morto (`idle`/`syncing`/`stale`) e passou a refletir o **banner** `{ ok, msg }` usado na UI do locker dashboard.
- `useLockerSlotsSync` grava e lê esse estado na store, eliminando duplicidade **no fluxo** `LockerDashboard` (TS).

Decisao executiva:
- **Atualizado:** `LockerDashboardFirst` passou a usar o mesmo `syncStatus` na store — ver carimbo **«store 100% + KIOSK v1»** no fim do registro.

### 2026-04-30 - Sprint 1 / Sprint 3: TS strict-core `useOpsWindowPreset` + `OpsActionButton` (meta ≥90%)
Status geral: `[~]` Em andamento (item TS Sprint 1 no limiar do comité; Sprint 3 acompanhada)

Resumo:
- Migrados **`useOpsWindowPreset.js` → `useOpsWindowPreset.ts`** e **`OpsActionButton.jsx` → `OpsActionButton.tsx`** com tipos explícitos (`UseOpsWindowPresetParams`, `OpsActionButtonProps`, variantes do botão).
- Inclusão no **`tsconfig.strict-core.json`**; `npm run typecheck` e `typecheck:strict-core` verdes.
- Item checklist **«TS incremental»** Sprint 1 reportado a **90%** (meta **≥90%** cumprida no indicador); desde então **91%** com `OpsKioskTouchModelsPage` no strict-core (ver **Metodo** *(iv)*).

Decisao executiva:
- Comité pode marcar **`[~]` → `[x]`** no item TS quando validar DoD além do gate (ex.: execução remota CI estável + amostra `checkJs` se for política). Próximo incremento técnico sugerido: mais módulos OPS reutilizados pelo locker/checkout ou `PickupHealthPage` por fatias.

### 2026-04-30 - Sprint 1: store 100% (`LockerDashboardFirst`) + protótipos KIOSK `/ops/kiosk-touch-models`
Status geral: `[~]` Sprint 1 (store **`[x]`**; protótipos **`[~]`**)

Resumo:
- **`LockerDashboardFirst.jsx`:** removido `useState` local de `syncStatus`; leitura/escrita via **`useCheckoutStore`** (mesmo contrato que `useLockerSlotsSync`).
- **Protótipos KIOSK v1:** nova página **`OpsKioskTouchModelsPage.tsx`**, rota **`/ops/kiosk-touch-models`**, entrada em **`opsLinks`** (Visão Geral) e lazy em **`App.jsx`** com `withBoundary("ops", …)`.
- **`tsconfig.strict-core.json`:** incluído `OpsKioskTouchModelsPage.tsx`; gates `typecheck` / `strict-core` / `build` verdes.

Decisao executiva:
- Subir protótipos **58% → ≥60%** com **testes moderados com utilizadores** (n≥8) e/ou refinamento visual; heurística n≥8 + export JSON cobre evidência leve até essa sessão. Próximo na ordem: **E2E KIOSK assistido** ou **estilos checkout**. Manter **~65–75%** da codificação na **Sprint 2** (gate v2) conforme **«Recomendacao atual — onde codar»**.

### 2026-04-30 - Sprint 2: painel gate v2 em `fiscal/global` + Sprint 1: checklist n≥8 em `/ops/kiosk-touch-models`
Status geral: `[~]` Sprint 1 / Sprint 2 (sem alteração de gate numérico)

Resumo:
- **`FiscalGlobalPage.jsx`:** faixa **Sprint 2 — trilha fiscal / contábil (gate v2)** com atalhos para rotas de evidência, lembrete do runbook **`docs/runbooks/FISCAL_CATALOGO_SEM_UI_POR_PAIS.md`** e texto de alocação **~65–75%** / **~25–35%**.
- **`OpsKioskTouchModelsPage.tsx`:** checklist **n≥8** (persistência local + export JSON) e bump de versão da página.
- **`PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`:** subsecções **Alocação numérica** e **Evidência no repositório** na secção **«Recomendacao atual — onde codar»**; **Metodo** *(v)*; snapshot incremental KIOSK; média Sprint 1 **~58%**.

Decisao executiva:
- Tratar o painel em **`fiscal/global`** como **ponto de entrada diário** para D10–D18 até o PASS do gate v2; anexar exports da checklist KIOSK aos dailies quando o comité pedir evidência Sprint 1.

### 2026-04-30 - Sprint 3: faixa hardening em `fiscal/global` + handoff de sessão em `fiscal/sprint3-partner-audit`
Status geral: `[~]` Sprint 3 (paralelo seguro; **sem net-new** fora do plano)

Resumo:
- **`FiscalGlobalPage.jsx`:** faixa **Sprint 3 — hardening** com atalhos SLO, incidente, partner-audit, quick-enablement, reconciliação OPS; texto de **paralelo seguro** até gate v2.
- **`FiscalSprint3PartnerAuditPage.jsx`:** checklist **handoff de sessão** (6 itens, `localStorage`) + export **`SPRINT3_PARTNER_AUDIT_HANDOFF_SESSION_*.json`**.
- **`PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`:** item «auditoria ponta a ponta» **42% → 48%**; média Sprint 3 **~66% → ~67%**; **Metodo** *(vi)*; painéis de decisão e P0-1 alinhados.

Decisao executiva:
- Usar o export de handoff nos dailies quando fechar ciclo E2E + parceiro na mesma sessão; manter disciplina de **não roubar** capacidade dos P0 financeiros da Sprint 2.

### 2026-04-30 - Sprint 2: espelho gate v2 no daily + anexo ZIP (trilha fiscal/contábil)
Status geral: `[~]` Sprint 2 (evidência operacional; percentuais de referência do doc inalterados até comité)

Resumo:
- **`fiscalSprint2FinanceGate.js`:** chave `localStorage`, limiares v2, `load` + `summarize` para reutilização.
- **`FiscalSprint2FinanceGatePage.jsx`:** passa a depender do util (**v1.0.1**).
- **`FiscalManagementDailyPage.jsx`:** cartão **Sprint 2 — gate v2 (espelho)** + atalhos **sprint2-finance-gate** e **accounting-close**; pacote diário inclui **`SPRINT2_GATE_V2_MIRROR_ATTACH`** quando há estado gravado.
- **`FiscalAccountingClosePage.jsx`:** ZIP executivo inclui o mesmo espelho (**ficheiro `*_SPRINT2_GATE_V2_MIRROR_EXEC_*`**).
- **`PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`:** comprovação P0 gate v2 + bloco **Evidência no repositório** atualizados.

Decisao executiva:
- O comité continua a **atualizar manualmente** os percentuais no cockpit até haver leitura automática de backend; o **espelho + ZIP** amarra a comprovação P0 ao **mesmo** objeto de estado que o export `SPRINT2_FINANCE_GATE_V2`.

### 2026-04-30 - Trilha FG-1 readiness: gate v2 no board `fiscal/readiness-execution`
Status geral: `[~]` Sprint 2 (encadeamento operacional)

Resumo:
- **`FiscalReadinessExecutionPage.jsx`:** atalhos **management-daily**, **sprint2-finance-gate**, **accounting-close**; cartão **espelho gate v2**; **export JSON** (`sprint2_gate_v2_mirror` + limiares); **«Copiar resumo handoff»** com linha Sprint 2.
- **`PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`:** bullet **Evidência no repositório** atualizado.

Decisao executiva:
- Tratar o export `fg1_readiness_execution_latest_*.json` como evidência única que liga **execução por país** ao **gate financeiro v2** no mesmo artefato, para daily único quando aplicável.

### 2026-04-30 - FG-1 gate: ponte explícita para gate financeiro Sprint 2 (v2)
Status geral: `[~]` Sprint 2 (clareza GO técnico vs GO financeiro)

Resumo:
- **`FiscalFg1GatePage.jsx`:** atalhos **sprint2-finance-gate** e **management-daily**; cartão **ponte FG-1 ↔ gate v2**; export **`fg1_final_decision_latest_*.json`** passa a incluir `sprint2_gate_v2_mirror` e limiares.

Decisao executiva:
- Operadores distinguem **FG-1 GO** (stub/coverage) de **PASS v2** (macro fiscal/contábil); o JSON único reduz ambiguidade no handoff.

### 2026-05-01 - Sprint 2: D11 rollup `order_id` + D12/D13 `SPRINT2_*` + Sprint 1: E2E KIOSK / comprar / checkout
Status geral: `[~]` Sprint 2 / Sprint 1 (evidência incremental; **sem** alteração declarada do gate v2 numérico até leitura do comité)

Resumo:
- **D11:** agregação **`fiscalD11OrderIdRollup.js`** (Vitest), cartão e export em **`OpsFiscalProvidersPage.jsx`**, handoff `localStorage` com `order_id_rollup`; **`FiscalManagementDailyPage.jsx`** (tabela, export, resumo no payload + ficheiro assinado no ZIP diário); **`FiscalAccountingClosePage.jsx`** — paridade no ZIP executivo (`SPRINT2_D11_ORDER_ID_ROLLUP_EXEC_*`).
- **D12/D13:** util **`fiscalSprint2D12D13Evidence.js`** (Vitest); exports dedicados e anexos SHA-256 no pacote diário (**`SPRINT2_D12_ACCOUNTING_HANDOFF_*`**, **`SPRINT2_D13_ACCOUNTING_ACCEPTANCE_*`**) e no ZIP executivo (**`*_EXEC_*`**) em alinhamento com o padrão D11.
- **Sprint 1:** **`e2e/kiosk-touch-models.spec.ts`** (mock `/public/auth/me*`), **`playwright.config.ts`**; **`e2e/public-comprar-catalog.spec.ts`** — smoke **`/comprar`**; **`e2e/public-catalog-to-checkout.spec.ts`** — **`/comprar` → `/checkout`** com query mínima (`locker_id`, `sku_id`, `slot`), mocks gateway/runtime e auth pickup.
- **Plano:** carimbo **«Recomendacao atual»** 2026-05-01; **Metodo** *(vii)*–*(viii)*; snapshots incrementais; Fiscal checklist **28%**; média Sprint 1 **~61%** (E2E checkout registado no snapshot Sprint 1).

Decisao executiva:
- **Feito (A — encadeamento checkout):** **`e2e/public-catalog-to-checkout.spec.ts`** cobre catálogo → checkout com query mínima (Playwright).
- **Feito (B — D12/D13):** artefactos **`SPRINT2_D12_*`** / **`SPRINT2_D13_*`** exportáveis e no ZIP diário/executivo, no mesmo padrão de evidência assinada do D11.
- **Feito (Sprint 1 — estilos checkout, fatias 1–2):** `publicCheckoutChrome.css` cobre topo + **cartões Resumo/Pagamento** + CTAs; E2E reforça cartões e combo de pagamento.
- **Próxima trilha recomendada (solo):** Sprint 1 — E2E com mock **`POST`** order pickup + assert **«Confirmar reserva»** / estado processando; ou **fatia 3** de CSS (fundos de página / `FiscalProfileCheckoutPanel`); Sprint 2 — D14+ conforme sequência D10–D18.
