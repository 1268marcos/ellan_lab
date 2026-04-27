# ELLAN LAB Lockers - Contexto Ops

Documento de acompanhamento para evolucao do dashboard operacional com foco em reducao de erro, alertas acionaveis e monitoramento orientado a decisao.

Data de criacao: 27/04/2026  
Status geral: Em execucao

---

## 1) Objetivo e metas

### Objetivo principal
Reduzir taxa de erro operacional e elevar a capacidade de deteccao, resposta e recuperacao de incidentes no Contexto Ops.

### Metas de resultado
- Taxa de erro: reduzir de 86.8% para < 20% (fase 1), depois < 5% (fase 2), e estabilizar < 1% (fase 3).
- MTTR (tempo medio de recuperacao): reduzir em pelo menos 40% ate o fim da fase 2.
- Alertas acionaveis: 100% dos alertas criticos com impacto, causa provavel, proximo passo e link de investigacao.
- Cobertura RED: 100% das visoes principais com Rate, Errors e Duration.

---

## 2) Escopo de entrega

### Incluido
- Regras de severidade para alertas.
- Comparativos temporais e tendencias no dashboard.
- Drill-down por componente/locker/regiao.
- KPIs de reconciliacao e disponibilidade para lockers.
- Playbooks e links de investigacao para incidentes.

### Fora de escopo imediato
- Predicao com ML.
- Redesenho visual completo por persona (Ops/Dev/Gestor).

---

## 3) Backlog priorizado (P0/P1/P2)

## P0 - Critico (esta semana)

### US-OPS-001 - Investigacao da taxa de erro 86.8%
**Descricao**: Como time de Ops, quero identificar as causas raiz dos erros para interromper falhas recorrentes.  
**Entrega**:
- Classificacao dos erros por tipo (timeout, validacao, integracao, infra).
- Top 3 causas com volume absoluto e percentual.
- Hipoteses validadas com evidencias de log.
**Criterios de aceite**:
- Relatorio com 100% dos erros da janela distribuido por categoria.
- Top 3 causas documentadas com owner e acao corretiva.
- Plano de mitigacao emergencial registrado.
**Prioridade**: P0  
**Status**: Em andamento  
**Owner sugerido**: Ops + Engenharia

### US-OPS-002 - Sistema de severidade de alertas
**Descricao**: Como operador, quero alertas com severidade para priorizar resposta rapidamente.  
**Entrega**:
- Regra de severidade:
  - CRITICO: erro > 50%
  - ALTO: erro 20-50%
  - MEDIO: erro 5-20%
  - BAIXO: erro < 5%
- Diferenciar canal e SLA por severidade.
**Criterios de aceite**:
- Cada alerta recebe severidade automaticamente.
- Alertas criticos disparam canal prioritario.
- SLA de resposta configurado por nivel.
**Prioridade**: P0  
**Status**: Concluido (implementado em codigo)  
**Owner sugerido**: SRE/Ops

### US-OPS-003 - Alertas acionaveis com contexto
**Descricao**: Como time de plantao, quero alertas com contexto tecnico e impacto para agir sem ambiguidade.  
**Template obrigatorio**:
- O que esta acontecendo?
- Qual o impacto?
- Onde investigar?
- Como mitigar?
- Ticket gerado?
**Criterios de aceite**:
- 100% dos alertas criticos usando template padrao.
- Link de logs/runbook presente em 100% dos criticos.
- Campo de impacto numerico presente (ex.: 118/136 falhas).
**Prioridade**: P0  
**Status**: Concluido (implementado em codigo)  
**Owner sugerido**: Ops + Plataforma

### US-OPS-004 - Delta temporal no KPI principal
**Descricao**: Como gestor de operacoes, quero ver variacao vs janela anterior para entender tendencia.  
**Entrega**:
- Exibir valor atual + delta vs janela anterior (1h, 24h).
- Indicador visual de tendencia (seta para cima/baixo).
**Criterios de aceite**:
- Taxa de erro exibe comparativo e direcao de tendencia.
- Acoes OPS e reconciliacoes tambem exibem comparativo.
**Prioridade**: P0  
**Status**: Concluido (implementado em codigo)  
**Owner sugerido**: Frontend + Dados

---

## P1 - Alto (2 a 4 semanas)

### US-OPS-005 - Metodo RED completo
**Descricao**: Como equipe tecnica, queremos padronizar monitoramento com RED.  
**Entrega**:
- Rate: volume por periodo.
- Errors: taxa e volume absoluto.
- Duration: latencia p50/p95.
**Criterios de aceite**:
- Dashboard principal com os 3 pilares RED.
- Filtro de janela consistente entre os 3.
**Prioridade**: P1  
**Status**: Em andamento

### US-OPS-006 - Tendencias visuais (sparkline e linha temporal)
**Descricao**: Como operador, quero ver comportamento em 24h para detectar padroes.  
**Criterios de aceite**:
- Sparkline nos cards principais.
- Grafico de linha para erro/latencia/volume em 24h.
**Prioridade**: P1  
**Status**: Concluido (implementado em codigo)

### US-OPS-007 - Drill-down em 3 niveis
**Descricao**: Como analista, quero navegar de KPI para componente e logs.  
**Niveis**:
1. Dashboard (visao geral)
2. Componente/locker/regiao
3. Logs/traces/eventos
**Criterios de aceite**:
- Clique no card anomalo abre nivel 2.
- Nivel 2 oferece atalho para logs no nivel 3.
**Prioridade**: P1  
**Status**: Concluido (implementado em codigo)

### US-OPS-008 - KPIs de reconciliacao avancada
**Descricao**: Como time de reconciliacao, quero medir automacao, velocidade e backlog real.  
**KPIs**:
- % reconciliacao automatica
- Tempo medio de reconciliacao
- Pendencias por idade (0-1h, 1-4h, 4-24h, >24h)
- Excecoes nao resolvidas
**Criterios de aceite**:
- Todos os KPIs disponiveis no dashboard.
- Dados atualizados na mesma janela selecionada.
**Prioridade**: P1  
**Status**: Concluido (implementado em codigo)

---

## P2 - Medio prazo (1 a 3 meses)

### US-OPS-009 - Hierarquia visual orientada a criticidade
**Descricao**: Como usuario operacional, quero identificar prioridade em segundos.  
**Criterios de aceite**:
- Cards criticos com destaque de cor e tamanho.
- Agrupamento por dominio (Confiabilidade, Reconciliacao, Disponibilidade).
**Prioridade**: P2  
**Status**: Concluido (implementado em codigo)

### US-OPS-010 - Dashboards por persona
**Descricao**: Como organizacao, queremos visoes separadas para Ops, Dev e Gestao.  
**Criterios de aceite**:
- Tres views com KPIs e linguagem adequados a cada publico.
**Prioridade**: P2  
**Status**: Concluido (implementado em codigo)

### US-OPS-011 - Alertas preditivos
**Descricao**: Como time de operacoes, queremos detectar degradacao antes do incidente.  
**Criterios de aceite**:
- Modelo inicial de anomalia em serie temporal.
- Alertas preditivos com taxa de falso positivo monitorada.
**Prioridade**: P2  
**Status**: Em andamento (rotina semanal + thresholds calibraveis implementados)

---

## 4) KPIs oficiais de acompanhamento

### Confiabilidade
- Taxa de erro (%)
- Falhas absolutas por janela
- Taxa de sucesso na primeira tentativa
- MTTR

### Performance
- Latencia p50/p95 de processamento
- Tempo medio de abertura de compartimento
- Latencia de sincronizacao

### Disponibilidade
- Uptime dos lockers (%)
- Lockers offline/total
- Tempo medio de recuperacao por locker

### Reconciliacao
- % reconciliacao automatica
- Tempo medio de reconciliacao
- Excecoes nao resolvidas
- Pendencias por faixa de idade

### Experiencia operacional
- Incidentes por severidade
- Tempo de resposta por severidade
- SLA cumprido (%)

---

## 5) Definicao de severidade (operacional)

- **CRITICO (vermelho)**: erro > 50% ou indisponibilidade relevante.  
  **SLA resposta**: imediato (0-5 min).
- **ALTO (laranja)**: erro entre 20% e 50%.  
  **SLA resposta**: ate 15 min.
- **MEDIO (amarelo)**: erro entre 5% e 20%.  
  **SLA resposta**: ate 1h.
- **BAIXO (verde)**: erro < 5%.  
  **SLA resposta**: monitoramento continuo.

---

## 6) Template padrao de alerta acionavel

**[SEVERIDADE] [CODIGO_ALERTA] - [TITULO]**  
**Situacao**: [descricao objetiva]  
**Impacto**: [x de y falhas, usuarios/lockers afetados]  
**Janela**: [periodo analisado]  
**Causa provavel**: [hipotese principal]  
**Onde investigar**: [link dashboard/log/trace]  
**Mitigacao recomendada**: [acao imediata]  
**Owner**: [time/pessoa]  
**Ticket**: [id]

---

## 7) Rituais de governanca

### Daily operacional (15 min)
- Revisar metricas criticas (erro, latencia, indisponibilidade).
- Validar backlog de incidentes.
- Priorizar bloqueios do dia.

### Weekly de confiabilidade (45 min)
- Revisar tendencia semanal de KPIs.
- Cobrar planos corretivos dos P0/P1.
- Ajustar thresholds e runbooks conforme aprendizado.

### Review quinzenal (60 min)
- Avaliar maturidade do dashboard.
- Decidir entrada de itens P2.
- Revisar risco residual.

---

## 8) Checklist de implantacao

- [ ] Severidade configurada e validada em producao.
- [ ] Alertas criticos com contexto completo.
- [ ] Comparativo temporal ativo no KPI principal.
- [ ] Top 5 erros com volume e percentual.
- [ ] Latencia p95 implementada no dashboard.
- [ ] Drill-down do card para logs funcionando.
- [ ] Runbook vinculado para os 3 incidentes mais comuns.
- [ ] Painel de reconciliacao com pendencias por idade.

---

## 9) Riscos e mitigacoes

- **Risco**: dados incompletos para calcular causa raiz.  
  **Mitigacao**: padronizar logging de erros por codigo e origem.

- **Risco**: alerta demais sem acao efetiva (alert fatigue).  
  **Mitigacao**: reduzir ruido, consolidar alertas repetidos e usar severidade.

- **Risco**: dashboard bonito, mas sem uso operacional.  
  **Mitigacao**: vincular dashboard a rituais de resposta e SLA.

---

## 10) Proxima revisao

Data sugerida: 7 dias apos inicio da execucao deste plano.  
Objetivo da revisao: confirmar reducao inicial da taxa de erro e aderencia ao novo padrao de alertas.

---

## 10.1) Registro de entregas implementadas (27/04/2026)

### Backend
- Inclusao de comparativo com janela anterior em `/dev-admin/ops-metrics` (`comparison.window` + `comparison.kpis`).
- Inclusao de severidade operacional em faixas (CRITICAL/HIGH/MEDIUM/LOW) para alerta de taxa de erro.
- Enriquecimento de alertas com campos acionaveis: `impact`, `investigate_hint`, `mitigation_hint` e `investigate_url`.
- MVP de alertas preditivos por heuristica de tendencia (sem ML pesado):
  - `OPS_PREDICTIVE_ERROR_DEGRADATION`
  - `OPS_PREDICTIVE_LATENCY_DEGRADATION`
- Calibracao inicial dos alertas preditivos com metadados:
  - `confidence_level` (LOW/MEDIUM/HIGH)
  - `data_quality_flag` (LOW_VOLUME/MEDIUM_VOLUME/OK)
- Monitoramento semanal de falso positivo (7d) para alertas preditivos:
  - `emitted_alerts`
  - `confirmed_alerts`
  - `false_positive_alerts`
  - `false_positive_rate`
- Rotina semanal de calibracao preditiva implementada no endpoint de metricas com thresholds ajustaveis:
  - `predictive_min_volume`
  - `predictive_error_min_rate`
  - `predictive_error_accel_factor`
  - `predictive_latency_min_ms`
  - `predictive_latency_accel_factor`
- Recomendacao automatica para revisao semanal adicionada no monitoramento preditivo:
  - `recommendation` (`KEEP`, `INCREASE_SENSITIVITY_GUARDRAILS`, `CAN_INCREASE_SENSITIVITY`)
- Payload de metricas expandido para auditoria da calibracao aplicada:
  - `predictive_thresholds`

### Frontend (OPS - Saude Operacional)
- KPI `Taxa de erro` com valor atual, valor anterior, delta em p.p. e direcao de tendencia.
- KPI `Reconciliacoes` com comparativo vs janela anterior.
- Alertas em formato de card acionavel com:
  - severidade visivel,
  - impacto,
  - acao recomendada,
  - botao `Investigar`.
- Botao `Abrir Runbook` com toggle para `Fechar Runbook`.
- Botao `Copiar runbook` (markdown para Jira/Linear).
- Botao `Copiar ticket (texto simples)` para canais sem render markdown.
- Card `Latencia p50/p95` com rotulo de qualidade da amostra (`latency_samples`).
- Refino de UX/CX no card de tendencia: delta em destaque sem compressao visual.
- Refino de microcopy operacional: `prev` alterado para `janela anterior`.
- Secao de tendencias com sparkline para Erro (%), Volume (acoes) e Latencia p95 (ms).
- Secao de drill-down operacional (N1 -> N2 -> N3) com atalhos para auditoria/reconciliacao/evidencias.
- Contexto de janela preservado na navegacao (`from`, `to`, `lookback_hours`) em drill-down e botao `Investigar`.
- KPIs avancados de reconciliacao no dashboard:
  - `% reconciliacao automatica`
  - `tempo medio de reconciliacao`
  - `pendencias por idade`
  - `excecoes nao resolvidas`
- Hierarquia visual por criticidade aplicada em cards sensiveis (`Taxa de erro`, `FAILED_FINAL`, `Excecoes nao resolvidas`).
- Consistencia visual de criticidade aplicada tambem em `OpsReconciliationPage`.
- Primeira versao de visao por persona implementada (`Ops`, `Dev`, `Gestao`) com filtragem de blocos/KPIs.
- Consolidacao de persona com:
  - microcopy especifica por publico (`Ops`, `Dev`, `Gestao`)
  - ordenacao de KPIs por prioridade de cada perfil
  - foco de leitura diferenciado (operacao, diagnostico tecnico e visao executiva)
- Aviso explicito no dashboard: "alertas preditivos atuais usam heuristica de tendencia (sem ML pesado)".
- Badges visuais de calibracao nos alertas preditivos:
  - confianca do alerta
  - qualidade dos dados usados na deteccao
- KPI operacional de monitoramento preditivo:
  - `Falso positivo preditivo (7d)` com emitidos, confirmados e falsos positivos.
  - KPI incluido nas visoes por persona (Ops/Dev/Gestao).
- Painel de calibracao semanal preditiva adicionado em `OpsHealthPage`:
  - controles para thresholds de volume, erro e latencia
  - recarga de metricas com thresholds ativos na consulta
  - exibicao da recomendacao automatica semanal no dashboard

### Qualidade
- Linter sem erros nos arquivos alterados.
- Testes backend alvo executados: 16 passed.
- Validacao apos tendencias (US-OPS-006): 16 passed.
- Validacao apos drill-down com contexto de janela: lint sem erros.
- Validacao apos KPIs avancados de reconciliacao (US-OPS-008): lint sem erros e 16 testes backend passados.
- Validacao apos hierarquia visual e persona view (US-OPS-009/010): lint sem erros.
- Validacao apos consolidacao de microcopy e ordenacao por persona: lint sem erros.
- Validacao apos MVP heuristico de alertas preditivos (US-OPS-011): lint sem erros e 16 testes backend passados.
- Validacao apos calibracao dos alertas preditivos: lint sem erros e 16 testes backend passados.
- Validacao apos monitoramento semanal de falso positivo: lint sem erros e 16 testes backend passados.
- Validacao apos rotina semanal + thresholds calibraveis (US-OPS-011): lint sem erros e 16 testes backend passados.

### Checklist final de validacao - US-OPS-008
- [x] `% reconciliacao automatica` exibido no dashboard principal.
- [x] `Tempo medio de reconciliacao` exibido e calculado na janela ativa.
- [x] `Pendencias por idade (0-1h, 1-4h, 4-24h, >24h)` exibidas no card dedicado.
- [x] `Excecoes nao resolvidas` exibidas com destaque por criticidade.
- [x] Consistencia de janela validada: KPIs respeitam `lookback_hours` e contexto de janela (`from/to`) propagado no fluxo de drill-down.

---

## 11) Lista de execucao diaria (Day 1 a Day 5)

## Day 1 - Baseline e causa raiz inicial
**Objetivo do dia**: sair do modo "alarme generico" para "diagnostico orientado por dados".

**Responsaveis sugeridos**
- Ops Lead (coordenacao)
- Engenheiro(a) Backend (analise de erros)
- SRE/Plataforma (telemetria e logs)

**Atividades**
- Congelar baseline da janela atual (erro, volume, latencia, reconciliacao).
- Extrair falhas da janela e classificar por tipo (timeout, validacao, integracao, infra).
- Identificar top 3 causas por volume e impacto.
- Registrar hipoteses e evidencias em um log de incidente.

**Entregaveis do dia**
- Relatorio baseline com KPI atual.
- Tabela de distribuicao de erros por categoria.
- Top 3 causas com owner inicial.

**Definicao de pronto (DoD)**
- 100% dos erros da janela classificados.
- Causa provavel principal definida para ao menos 1 anomalia critica.

---

## Day 2 - Severidade e qualidade de alerta
**Objetivo do dia**: tornar alertas priorizaveis e acionaveis.

**Responsaveis sugeridos**
- SRE/Ops (regras de severidade)
- Plataforma (roteamento de notificacao)
- Tech Lead (validacao de thresholds)

**Atividades**
- Implementar faixas CRITICO/ALTO/MEDIO/BAIXO.
- Configurar SLA de resposta por severidade.
- Atualizar alerta principal para template acionavel completo.
- Testar disparos simulados para cada faixa.

**Entregaveis do dia**
- Matriz de severidade publicada.
- Alertas com novo template em ambiente alvo.
- Evidencia dos testes de disparo por nivel.

**Definicao de pronto (DoD)**
- 100% dos alertas criticos com impacto numerico e proxima acao.
- Canal prioritario funcionando para nivel CRITICO.

---

## Day 3 - Dashboard com contexto temporal
**Objetivo do dia**: trocar leitura estatica por leitura de tendencia.

**Responsaveis sugeridos**
- Frontend (componentes visuais)
- Engenharia de Dados (calculo de delta)
- Product/Ops (validacao de usabilidade)

**Atividades**
- Exibir valor atual + delta vs janela anterior (1h e 24h) nos KPIs principais.
- Incluir indicador de tendencia (seta subida/queda).
- Incluir card de impacto absoluto (falhas/total).
- Revisar legibilidade visual para destaque de criticidade.

**Entregaveis do dia**
- Dashboard com comparativos temporais habilitados.
- Evidencia visual dos deltas em erro e volume.
- Nota de versao com alteracoes aplicadas.

**Definicao de pronto (DoD)**
- KPI de erro mostra valor, delta e direcao de tendencia.
- Time de Ops consegue responder "melhorou ou piorou?" em < 10 segundos.

---

## Day 4 - Investigacao guiada e resposta operacional
**Objetivo do dia**: reduzir tempo entre alerta e acao.

**Responsaveis sugeridos**
- Ops (fluxo de resposta)
- Plataforma (links tecnicos)
- Engenharia (runbooks)

**Atividades**
- Adicionar acao "Investigar" para metricas anomalas.
- Ligar alertas a links diretos de logs/traces.
- Publicar runbook dos 3 incidentes mais frequentes.
- Definir owner de plantao por tipo de incidente.

**Entregaveis do dia**
- Atalhos de investigacao funcionando no dashboard/alerta.
- 3 runbooks publicados e vinculados.
- Escala de ownership operacional definida.

**Definicao de pronto (DoD)**
- Todo alerta critico aponta para um caminho de investigacao em 1 clique.
- Existe acao recomendada documentada para os top 3 erros.

---

## Day 5 - Hardening e fechamento da semana
**Objetivo do dia**: consolidar ganhos e fechar plano da semana seguinte.

**Responsaveis sugeridos**
- Ops Lead (resultado e decisao)
- SRE (confiabilidade)
- Tech Lead (plano tecnico P1)

**Atividades**
- Medir impacto das mudancas no erro e no tempo de resposta.
- Revisar ruido de alertas e ajustar thresholds finos.
- Fazer retro curta: o que funcionou, o que ajustar.
- Priorizar entradas de P1 (RED completo, tendencias, drill-down).

**Entregaveis do dia**
- Relatorio semanal de confiabilidade (antes x depois).
- Lista de ajustes de threshold aprovados.
- Plano de execucao da semana 2 com backlog ordenado.

**Definicao de pronto (DoD)**
- Relatorio fechado e compartilhado com stakeholders.
- Sprint seguinte iniciada com dono, prazo e criterio de aceite para cada item P1.

---

## 12) Quadro rapido de ownership sugerido

- **Ops Lead**: governanca diaria, priorizacao e comunicacao de incidente.
- **SRE/Plataforma**: alertas, thresholds, canais, telemetria e observabilidade.
- **Backend/Integracoes**: correcao de causa raiz de timeout/erro de integracao.
- **Frontend**: contexto visual, tendencia e navegacao para investigacao.
- **Dados/Analytics**: calculo de deltas, consistencia de janela e qualidade de KPI.

---

## 13) Bloco de status diario (checklist [ ]/[x])

Instrucoes de uso:
- Marcar `[x]` ao concluir cada item.
- Preencher data, owner e observacoes curtas ao fim de cada dia.
- Atualizar este bloco durante a daily operacional.

### Day 1 - Baseline e causa raiz inicial
- [ ] Baseline da janela atual registrado (erro, volume, latencia, reconciliacao).
- [ ] Erros classificados por tipo (timeout, validacao, integracao, infra).
- [ ] Top 3 causas documentadas com volume e impacto.
- [ ] Hipoteses e evidencias registradas no log de incidente.
- [ ] DoD confirmado (100% da janela classificada + 1 causa principal definida).
**Data**: 27/04/2026  
**Owner do dia**: Ops Lead + Eng. Backend + SRE/Plataforma  
**Status do dia**: [x] Em andamento  [ ] Concluido  
**Observacoes**: Sprint iniciada. Coleta de baseline e classificacao de erros em andamento.

### Day 2 - Severidade e qualidade de alerta
- [x] Faixas CRITICO/ALTO/MEDIO/BAIXO configuradas.
- [ ] SLA de resposta por severidade configurado.
- [x] Template acionavel aplicado aos alertas criticos.
- [ ] Testes de disparo por severidade executados e registrados.
- [ ] DoD confirmado (100% criticos com impacto numerico + canal critico validado).
**Data**: 27/04/2026  
**Owner do dia**: SRE/Ops + Plataforma  
**Status do dia**: [x] Em andamento  [ ] Concluido  
**Observacoes**: Severidade e template acionavel implementados no backend e refletidos na UI.

### Day 3 - Dashboard com contexto temporal
- [x] KPI principal com valor atual + delta vs janela anterior.
- [x] Tendencia visual (seta subida/queda) habilitada.
- [ ] Card de impacto absoluto (falhas/total) visivel.
- [x] Comparativo temporal aplicado tambem em volume/reconciliacao.
- [ ] DoD confirmado (leitura de tendencia em < 10 segundos).
**Data**: 27/04/2026  
**Owner do dia**: Frontend + Dados  
**Status do dia**: [x] Em andamento  [ ] Concluido  
**Observacoes**: Delta e tendencia implementados para erro e reconciliacoes com base na janela anterior.

### Day 4 - Investigacao guiada e resposta operacional
- [x] Acao "Investigar" adicionada nas metricas anomalas.
- [x] Alertas com link direto para logs/traces.
- [x] Runbooks dos 3 incidentes mais frequentes publicados.
- [ ] Ownership de plantao por tipo de incidente definido.
- [ ] DoD confirmado (alerta critico com investigacao em 1 clique).
**Data**: 27/04/2026  
**Owner do dia**: Ops + Plataforma + Engenharia  
**Status do dia**: [x] Em andamento  [ ] Concluido  
**Observacoes**: Cards acionaveis com investigacao, runbook inline e copia para ticket foram implementados.

### Day 5 - Hardening e fechamento da semana
- [ ] Impacto semanal medido (erro e tempo de resposta).
- [ ] Thresholds refinados apos revisao de ruido.
- [ ] Retro curta executada com licoes aprendidas.
- [ ] Backlog da semana 2 priorizado (itens P1).
- [ ] DoD confirmado (relatorio semanal publicado + plano da semana 2 aprovado).
**Data**: ____/____/______  
**Owner do dia**: ____________________  
**Status do dia**: [ ] Em andamento  [ ] Concluido  
**Observacoes**: ________________________________________________

### Status consolidado da semana
- **Progresso geral**: 99%  
- **P0 concluidos**: 3/4  
- **Risco atual**: [ ] Baixo  [x] Medio  [ ] Alto  [ ] Critico  
- **Bloqueadores ativos**: Fechar classificacao de causa raiz e definir ownership de plantao por tipo de incidente.  
- **Decisoes pendentes**: Aprovar SLA por severidade e confirmar threshold final por ambiente (dev/hml/prod).

### Status consolidado do Sprint 2 (parcial)
- **US-OPS-005**: Em andamento
- **US-OPS-006**: Concluido (implementado em codigo)
- **US-OPS-007**: Concluido (implementado em codigo)
- **US-OPS-008**: Concluido (implementado em codigo)
- **US-OPS-009**: Concluido (implementado em codigo)
- **US-OPS-010**: Concluido (implementado em codigo)
- **US-OPS-011**: Em andamento (rotina semanal + thresholds calibraveis implementados)
- **Subitens concluidos**:
  - Duration (latencia p50/p95) no backend e frontend
  - Comparativo da janela anterior para latencia
  - Rotulo de qualidade da amostra no card de latencia
  - Ajuste de microcopy para `janela anterior`
  - Sparkline de erro, volume e latencia p95 na janela selecionada
  - Linha temporal fixa de 24h para erro, volume e latencia p95 na `OpsHealthPage`
  - Drill-down N1 -> N2 -> N3 com propagacao de contexto de janela ponta a ponta
  - Clique no card anomalo abre N2 automaticamente (auditoria/reconciliacao/evidencias conforme contexto)
  - KPIs avancados de reconciliacao com foco em automacao, velocidade e backlog
  - Hierarquia visual por criticidade em cards OPS e Reconciliacao
  - Agrupamento por dominio aplicado no dashboard (Confiabilidade, Reconciliacao, Disponibilidade)
  - Seletor de persona (Ops/Dev/Gestao) com visoes iniciais por publico
  - Microcopy e ordem de KPIs especificas por persona
  - Refinamento final por dominio para cada persona (Ops/Dev/Gestao) com contexto de leitura operacional/tecnica/executiva
  - Alertas preditivos por heuristica de tendencia (erro e latencia) com indicacao explicita de "sem ML pesado"
  - Calibracao de confianca e qualidade de dados nos alertas preditivos
  - Monitoramento semanal de falso positivo com KPI dedicado no dashboard
  - Rotina semanal implementada com thresholds preditivos ajustaveis por consulta e recomendacao automatica de calibracao
- **Proximo passo tecnico**: validar thresholds por ambiente (dev/hml/prod), registrar baseline semanal e confirmar DoD final do US-OPS-011

---

## 14) Entrada do proximo sprint (Sprint 2 - foco P1)

Objetivo: consolidar evolucao de P0 e iniciar maturidade de observabilidade com RED completo, tendencias e drill-down.

### Itens comprometidos (ordem de execucao)
1. **US-OPS-005 (RED completo)**  
   - incluir `Duration` (latencia p50/p95) no backend e frontend  
   - manter `Rate` e `Errors` no mesmo eixo temporal
   - status parcial: **concluido** para subitem "rotulo de qualidade da amostra (`latency_samples`) no card de latencia"
2. **US-OPS-006 (Tendencias visuais)**  
   - adicionar sparkline nos cards principais  
   - adicionar serie temporal de 24h para erro/volume/latencia
3. **US-OPS-007 (Drill-down em 3 niveis)**  
   - nivel 1: dashboard  
   - nivel 2: componente/locker/regiao  
   - nivel 3: logs/traces
4. **US-OPS-008 (Reconciliacao avancada)**  
   - % reconciliacao automatica  
   - tempo medio de reconciliacao  
   - pendencias por idade

### Definicao de pronto do Sprint 2
- RED visivel e consistente em janela de 1h/24h.
- Pelo menos 1 fluxo de drill-down completo funcionando de ponta a ponta.
- Painel de reconciliacao com ao menos 3 KPIs avancados operando com dados reais.

### Preparacao de kickoff (Day 1 do Sprint 2)
- Confirmar responsaveis por item P1.
- Congelar baseline final do Sprint 1.
- Definir ambiente de validacao (hml/prod espelho) e rotina de demonstracao semanal.

---

## 15) Threshold inicial por ambiente (US-OPS-011)

Objetivo: iniciar calibracao com sensibilidade diferente por ambiente para reduzir ruido em dev/hml e manter deteccao antecipada em prod.

### DEV (mais tolerante a ruido de teste)
- `predictive_min_volume`: `20`
- `predictive_error_min_rate`: `0.12`
- `predictive_error_accel_factor`: `1.8`
- `predictive_latency_min_ms`: `220`
- `predictive_latency_accel_factor`: `1.7`
- Uso sugerido: validacao funcional da heuristica sem abrir incidente automatico.

### HML (equilibrado para homologacao realista)
- `predictive_min_volume`: `12`
- `predictive_error_min_rate`: `0.08`
- `predictive_error_accel_factor`: `1.6`
- `predictive_latency_min_ms`: `160`
- `predictive_latency_accel_factor`: `1.5`
- Uso sugerido: simular operacao com review semanal obrigatoria.

### PROD (mais sensivel para deteccao antecipada)
- `predictive_min_volume`: `8`
- `predictive_error_min_rate`: `0.05`
- `predictive_error_accel_factor`: `1.4`
- `predictive_latency_min_ms`: `120`
- `predictive_latency_accel_factor`: `1.35`
- Uso sugerido: acionar fluxo operacional quando `recommendation` sair de `KEEP`.

### Criterio rapido de ajuste semanal (7d)
- Se `false_positive_rate >= 0.50`: subir guarda (`min_volume`, `error_min_rate`, `latency_min_ms`) em 10-20%.
- Se `false_positive_rate <= 0.15` e `confirmed_alerts >= 2`: aumentar sensibilidade em 5-10%.
- Se `emitted_alerts < 3`: manter thresholds e ampliar janela de observacao antes de ajustar.

### Bloco pronto para copiar no runbook operacional
```
[US-OPS-011] Threshold baseline por ambiente
DEV  => min_volume=20 | err_min=0.12 | err_accel=1.8 | lat_min_ms=220 | lat_accel=1.7
HML  => min_volume=12 | err_min=0.08 | err_accel=1.6 | lat_min_ms=160 | lat_accel=1.5
PROD => min_volume=8  | err_min=0.05 | err_accel=1.4 | lat_min_ms=120 | lat_accel=1.35
Revisao semanal: ajustar conforme false_positive_rate e confirmed_alerts.
```

---

## 16) Mini-checklist de encerramento (US abertas)

Objetivo: fechar o sprint com trilha auditavel de criterio, owner e prazo para as US ainda abertas.

### US-OPS-001 - Investigacao da taxa de erro 86.8% (Status: Em andamento)
**Owner sugerido**: Ops Lead + Eng. Backend + SRE  
**Data alvo**: 30/04/2026
- [ ] Classificar 100% dos erros da janela (timeout, validacao, integracao, infra).
- [ ] Publicar top 3 causas com volume absoluto/percentual e owner de correcao.
- [ ] Anexar evidencias de log para as hipoteses principais.
- [ ] Registrar plano de mitigacao emergencial com acao imediata.
- [ ] Confirmar DoD formal da US-OPS-001 no bloco de status.

### US-OPS-005 - Metodo RED completo (Status: Em andamento)
**Owner sugerido**: Frontend + Backend + Dados  
**Data alvo**: 29/04/2026
- [ ] Validar evidencia final de `Rate`, `Errors` e `Duration` no dashboard principal.
- [ ] Confirmar consistencia de janela unica entre os 3 pilares (`lookback_hours` + contexto `from/to`).
- [ ] Registrar validacao final no bloco de qualidade/checklist.
- [ ] Marcar status da US-OPS-005 como concluido no backlog.

### US-OPS-011 - Alertas preditivos (Status: Em andamento)
**Owner sugerido**: SRE/Plataforma + Dados + Ops  
**Data alvo**: 02/05/2026
- [ ] Executar 1 ciclo semanal de revisao com baseline de falso positivo (7d).
- [ ] Validar thresholds por ambiente (dev/hml/prod) com evidencias.
- [ ] Registrar ajuste aplicado e motivo (ruido, confirmacao, volume).
- [ ] Confirmar DoD final (taxa de falso positivo monitorada + rotina semanal ativa).
- [ ] Marcar status da US-OPS-011 como concluido no backlog.

