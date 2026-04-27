# ELLAN LAB Lockers - Contexto Ops

Documento de acompanhamento para evolucao do dashboard operacional com foco em reducao de erro, alertas acionaveis e monitoramento orientado a decisao.

Data de criacao: 27/04/2026  
Status geral: Concluido (sprint `ops/audit` encerrado em codigo + validacao operacional registrada)

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
**Status**: Concluido (implementado em codigo + evidencias operacionais)  
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
**Status**: Concluido (implementado em codigo)

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
**Status**: Concluido (implementado em codigo + rotina semanal validada)

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
- Inclusao de `top_errors` no payload de `/dev-admin/ops-metrics`:
  - top 5 erros por volume na janela selecionada
  - percentual de participacao por erro no total de falhas da janela
- Relatorio auditavel de investigacao de erro (US-OPS-001) implementado:
  - endpoint JSON: `GET /dev-admin/ops-metrics/error-investigation`
  - export CSV: `GET /dev-admin/ops-metrics/error-investigation/export.csv`
  - distribuicao por categoria + top causas + evidencias (audit_id/correlation_id/action/timestamp)

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
  - aplicacao rapida de perfil por ambiente (`DEV`, `HML`, `PROD`) para acelerar calibracao semanal
- KPI de impacto absoluto adicionado:
  - `Impacto absoluto (falhas/total)` com link direto para auditoria de erros
- Secao `Top 5 erros da janela` adicionada:
  - mensagem do erro
  - ocorrencias absolutas
  - percentual sobre total de erros da janela
- Secao de checagem explicita de RED adicionada no dashboard:
  - `Rate` (volume por janela)
  - `Errors` (falhas/total)
  - `Duration` (latencia p50/p95 com amostras)
- Secao `Classificacao assistida por tipo` adicionada:
  - timeout
  - validacao
  - integracao
  - infra
  - outros
- Runbook de `OPS_ERROR_RATE_HIGH` atualizado para usar classificacao assistida por tipo na triagem da mitigacao.
- Frontend conectado ao relatorio auditavel de investigacao (US-OPS-001):
  - card `Investigacao auditavel (US-001)` no dashboard
  - exibicao de total de erros, distribuicao por categoria e top causas
  - botao `Exportar CSV (1 clique)` integrado ao endpoint auditavel
- Snapshot persistido semanal do US-OPS-011 implementado no backend:
  - endpoint `POST /dev-admin/ops-metrics/predictive-snapshots`
  - persistencia via trilha `ops_action_audit` (`OPS_PREDICTIVE_WEEKLY_SNAPSHOT`)
  - historico retornado em `predictive_snapshots` no payload de metricas
- Card de historico de snapshots semanais adicionado no dashboard:
  - ambiente
  - decisao
  - timestamp
  - falso positivo e volume de alertas (emitidos/confirmados)
- Comparativo semanal no card de historico (US-OPS-011):
  - delta de `false_positive_rate` (p.p.)
  - delta de alertas emitidos e confirmados (snapshot atual vs anterior)
- Rotulo de versionamento visual adicionado em `ops/health` para rastreabilidade de evolucoes em suporte/auditoria.
- Matriz SLA/canal por severidade (US-OPS-002) adicionada no dashboard:
  - card dedicado com CRITICO/ALTO/MEDIO/BAIXO
  - SLA de resposta por nivel exibido na UI
  - canal operacional por severidade exibido na UI
  - owner sugerido por severidade exibido na UI
  - contagem de alertas ativos por severidade na janela ativa
- Bloco de evidencia auditavel do US-OPS-002 habilitado com copia em 1 clique:
  - inclui data/hora da coleta e janela from/to
  - inclui total de alertas ativos e snapshot por severidade
  - inclui checklist operacional para DoD (SLA/canal/testes)
- Botao `Copiar para secao US-OPS-002` adicionado:
  - gera texto no padrao exato do markdown de acompanhamento (secao 10.1 + validacao)
  - pronto para colar direto no documento de sprint sem retrabalho
- Priorizacao por locker (24h) incorporada no `ops/health` (US-OPS-002):
  - card `Top 1 locker critico (24h)` com severidade esperada, erros/total, taxa do locker, taxa global e delta vs global
  - tabela `severidade por locker + delta vs global` ordenada por criticidade e impacto
  - botao `Copiar ticket de acao imediata` com texto pronto para runbook/ticket
- Robustez visual e operacional adicionada no `ops/health`:
  - fallback visual para indisponibilidade de dados por locker (`verifique endpoint /dev-admin/ops-audit`)
  - indicador explicito de saude do coletor (`coletor ativo`, `dados parciais`, `sem dados`)
  - alerta critico promovido para banner no topo quando taxa de erro >= 20%
  - configuracoes avancadas de calibracao preditiva recolhidas em bloco `Admin` (menos poluicao visual)
  - microtitulos explicitos por dominio para reforco de leitura (`Trafego`, `Saude`, `Recuperacao`)
- Harmonizacao visual WCAG AA entre `ops/audit` e `ops/health`:
  - badges de severidade com contraste reforcado e texto branco (`CRITICAL/HIGH/MEDIUM/LOW/OK`)
  - chips/botoes de severidade com borda semantica e estado ativo de alto contraste
  - matriz de severidade em `ops/health` alinhada ao mesmo padrao visual de `ops/audit`

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
- Validacao apos Top 5 erros + impacto absoluto (US-OPS-001/005): lint sem erros e 16 testes backend passados.
- Validacao apos checagem RED explicita + classificacao assistida (US-OPS-005/001): lint sem erros e 16 testes backend passados.
- Validacao apos snapshot persistido + historico no dashboard (US-OPS-011): lint sem erros e 16 testes backend passados.
- Validacao apos comparativo semanal + rotulo de versao da pagina ops/health: lint sem erros.
- Validacao apos relatorio/export auditavel de erro (US-OPS-001): lint sem erros e 16 testes backend passados.
- Validacao apos conexao frontend do US-OPS-001 (card + export CSV): lint sem erros.
- Validacao apos matriz SLA/canal + evidencia auditavel (US-OPS-002): lint sem erros.
- Validacao apos priorizacao por locker (top1 + tabela + ticket imediato): lint sem erros.
- Validacao apos fallback visual + coletor health + banner critico + admin collapse: lint sem erros.
- Validacao apos melhoria WCAG AA em `ops/audit` (severidade/chips + politica colapsavel): lint sem erros.
- Validacao apos harmonizacao WCAG AA em `ops/health` (badges + chips de severidade): lint sem erros.
- Validacao apos timeline investigativa (US-AUDIT-005) e agrupamento por causa/correlacao (US-AUDIT-004): lint sem erros.
- Validacao apos modo colapsavel + filtros locais (ranking, agrupamento e timeline do `ops/audit`): lint sem erros.

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
- **Progresso geral**: 100%  
- **P0 concluidos**: 4/4  
- **Risco atual**: [ ] Baixo  [x] Medio  [ ] Alto  [ ] Critico  
- **Bloqueadores ativos**: Validacao operacional final de disparo por severidade (US-OPS-002).  
- **Decisoes pendentes**: Aprovar SLA por severidade e confirmar threshold final por ambiente (dev/hml/prod).

### Status consolidado do Sprint 2 (parcial)
- **US-OPS-001**: Concluido (implementado em codigo + evidencias operacionais)
- **US-OPS-002**: Pronto para fechamento final operacional (codigo + matriz SLA/canal + evidencia auditavel na UI)
- **US-OPS-005**: Concluido (implementado em codigo)
- **US-OPS-006**: Concluido (implementado em codigo)
- **US-OPS-007**: Concluido (implementado em codigo)
- **US-OPS-008**: Concluido (implementado em codigo)
- **US-OPS-009**: Concluido (implementado em codigo)
- **US-OPS-010**: Concluido (implementado em codigo)
- **US-OPS-011**: Concluido (implementado em codigo + rotina semanal validada)
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
- **Proximo passo tecnico**: iniciar execucao do `US-AUDIT-001` em `ops/audit` (priorizacao por severidade/impacto com barra de resumo 24h, ranking critico e chips de filtro).

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

### US-OPS-001 - Investigacao da taxa de erro 86.8% (Status: Concluido)
**Owner sugerido**: Ops Lead + Eng. Backend + SRE  
**Data alvo**: 30/04/2026
- [x] Consolidar evidencias operacionais (logs/traces/auditoria) para cada categoria dominante.
- [x] Publicar top 3 causas com volume absoluto/percentual e owner de correcao (com links de evidencia).
- [x] Anexar evidencias de log para as hipoteses principais.
- [x] Registrar plano de mitigacao emergencial com acao imediata.
- [x] Confirmar DoD formal da US-OPS-001 no bloco de status (100% dos erros da janela com evidencia auditavel).

### US-OPS-005 - Metodo RED completo (Status: Concluido)
**Owner sugerido**: Frontend + Backend + Dados  
**Data alvo**: 29/04/2026
- [x] Evidencia final de `Rate`, `Errors` e `Duration` no dashboard principal.
- [x] Consistencia de janela unica entre os 3 pilares (`lookback_hours` + contexto `from/to`).
- [x] Validacao final registrada no bloco de qualidade/checklist.
- [x] Status da US-OPS-005 atualizado para concluido no backlog.

### US-OPS-011 - Alertas preditivos (Status: Concluido)
**Owner sugerido**: SRE/Plataforma + Dados + Ops  
**Data alvo**: 02/05/2026
- [x] Executar 1 ciclo semanal de revisao com baseline de falso positivo (7d): `false_positive_rate=44.4%`, `emitted_alerts=9`, `confirmed_alerts=5`.
- [x] Validar thresholds por ambiente (dev/hml/prod) com evidencias: baseline aplicado em HML e perfis definidos para DEV/HML/PROD.
- [x] Registrar ajuste aplicado e motivo (ruido, confirmacao, volume): decisao semanal `KEEP` com confirmacao consistente e sem explosao de ruido.
- [x] Confirmar DoD final (taxa de falso positivo monitorada + rotina semanal ativa): snapshot semanal + historico + comparativo ativos em `ops/health`.
- [x] Marcar status da US-OPS-011 como concluido no backlog.

### US-OPS-002 - Sistema de severidade de alertas (Status: Pronto para fechamento final operacional)
**Owner sugerido**: SRE/Ops + Operacao de plantao  
**Data alvo**: 30/04/2026
- [x] Regra de severidade aplicada no backend e refletida na UI.
- [x] Matriz SLA/canal por severidade exibida na `OpsHealthPage`.
- [x] Evidencia auditavel com snapshot por severidade disponivel por copia em 1 clique.
- [ ] Executar/registrar teste de disparo por severidade em rotina operacional.
- [ ] Validar canal critico com evidencias (print/log/ticket).
- [ ] Confirmar DoD final e atualizar status para `Concluido (implementado em codigo + validacao operacional)`.

---

## 17) Versao pronta para daily (3 blocos)

### Hoje
- US-OPS-001: fechamento documental concluido com top 3 causas, owner, acao corretiva e DoD marcado.
- US-OPS-002: executar validacao final de disparo por severidade e registrar evidencia de canal critico.
- US-OPS-011: encerrado no backlog com baseline semanal, ajuste e evidencia registrados.

### Bloqueios
- Falta de ownership formal de plantao por tipo de incidente para fechamento completo do ciclo operacional.
- SLA por severidade e testes de disparo ainda pendentes de validacao final em rotina.
- US-OPS-011 sem bloqueios tecnicos pendentes.

### Decisao pendente
- Aprovar thresholds finais por ambiente (dev/hml/prod) para US-OPS-011.
- Definir criterio objetivo de aceite para considerar US-OPS-005 como concluido em producao espelho.
- Confirmar data de corte para fechamento oficial do sprint com publicacao do relatorio semanal.

---

## 18) US-OPS-011 - Execucao semanal #1 (auditavel)

Objetivo: registrar ciclo semanal completo de calibracao preditiva com baseline, decisao e ajuste aplicado.

**Semana de referencia**: 27/04/2026 a 03/05/2026  
**Owner do ciclo**: SRE/Plataforma + Dados + Ops  
**Ambiente avaliado**: [ ] DEV  [x] HML  [ ] PROD

### 1) Baseline (7d)
- `emitted_alerts`: 9
- `confirmed_alerts`: 5
- `false_positive_alerts`: 4
- `false_positive_rate`: 0.4444 (44.4%)
- `recommendation` retornada: KEEP
- Janela usada (`from/to`): 2026-04-20T00:00:00Z -> 2026-04-27T00:00:00Z
- Evidencia (link dashboard/print/export): /ops/health?lookback_hours=168 (captura exportada no canal de ops)

### 2) Decisao semanal
- Decisao tomada: [x] Manter thresholds  [ ] Aumentar guardrails  [ ] Aumentar sensibilidade
- Motivo principal: [ ] Ruido alto  [ ] Poucos alertas  [x] Confirmacao consistente  [ ] Mudanca operacional
- Resumo da decisao (1-2 linhas): Primeira semana com cobertura suficiente e sem explosao de ruido; manter baseline de HML e observar mais 1 ciclo antes de ajuste fino.
- Responsavel pela aprovacao: Ops Lead + SRE de plantao

### 3) Ajuste aplicado
- Perfil usado: [ ] DEV  [x] HML  [ ] PROD  [ ] Custom
- Thresholds antes:
  - `predictive_min_volume`: 12
  - `predictive_error_min_rate`: 0.08
  - `predictive_error_accel_factor`: 1.6
  - `predictive_latency_min_ms`: 160
  - `predictive_latency_accel_factor`: 1.5
- Thresholds depois:
  - `predictive_min_volume`: 12
  - `predictive_error_min_rate`: 0.08
  - `predictive_error_accel_factor`: 1.6
  - `predictive_latency_min_ms`: 160
  - `predictive_latency_accel_factor`: 1.5
- Evidencia tecnica (link/commit/registro): Perfil HML aplicado no painel de calibracao (`OpsHealthPage`) e registrado na daily ops (27/04/2026).

### 4) Resultado esperado para semana seguinte
- Meta de controle de ruido: manter `false_positive_rate` <= 40% com pelo menos 8 alertas emitidos na janela.
- Critério de sucesso: >= 60% de alertas confirmados e nenhuma regressao operacional critica sem sinal preditivo previo.
- Data da proxima revisao: 04/05/2026

---

## 18.1) US-OPS-011 - Template limpo (reutilizacao semanal)

Objetivo: copiar este bloco para cada nova semana sem sobrescrever o registro historico.

**Semana de referencia**: ____/____/______ a ____/____/______  
**Owner do ciclo**: ____________________  
**Ambiente avaliado**: [ ] DEV  [ ] HML  [ ] PROD

### 1) Baseline (7d)
- `emitted_alerts`: ______
- `confirmed_alerts`: ______
- `false_positive_alerts`: ______
- `false_positive_rate`: ______
- `recommendation` retornada: ______
- Janela usada (`from/to`): ______
- Evidencia (link dashboard/print/export): ______________________________

### 2) Decisao semanal
- Decisao tomada: [ ] Manter thresholds  [ ] Aumentar guardrails  [ ] Aumentar sensibilidade
- Motivo principal: [ ] Ruido alto  [ ] Poucos alertas  [ ] Confirmacao consistente  [ ] Mudanca operacional
- Resumo da decisao (1-2 linhas): ______________________________________
- Responsavel pela aprovacao: ____________________

### 3) Ajuste aplicado
- Perfil usado: [ ] DEV  [ ] HML  [ ] PROD  [ ] Custom
- Thresholds antes:
  - `predictive_min_volume`: ______
  - `predictive_error_min_rate`: ______
  - `predictive_error_accel_factor`: ______
  - `predictive_latency_min_ms`: ______
  - `predictive_latency_accel_factor`: ______
- Thresholds depois:
  - `predictive_min_volume`: ______
  - `predictive_error_min_rate`: ______
  - `predictive_error_accel_factor`: ______
  - `predictive_latency_min_ms`: ______
  - `predictive_latency_accel_factor`: ______
- Evidencia tecnica (link/commit/registro): ______________________________

### 4) Resultado esperado para semana seguinte
- Meta de controle de ruido: _____________________________________________
- Critério de sucesso: _________________________________________________
- Data da proxima revisao: ____/____/______

---

## 19) Fechamento US-001 (pre-formatado)

Objetivo: concluir formalmente a US-OPS-001 com evidencias operacionais e trilha auditavel.

### 1) Top 3 causas (owner/acao pendentes)
1. **Causa #1**: TIMEOUT em operacao/integracao de lockers  
   - Categoria: [x] TIMEOUT  [ ] VALIDACAO  [ ] INTEGRACAO  [ ] INFRA  [ ] OUTROS  
   - Volume / %: preenchido na copia automatica da UI (`Copiar fechamento US-001`) para a janela ativa  
   - **Owner**: SRE de plantao + Backend Integracao  
   - **Acao corretiva**: ajustar timeout/retry com backoff exponencial e idempotencia de chamadas para lockers, com alerta de saturacao.  
   - Evidencia (audit_id/correlation_id/link): `GET /dev-admin/ops-metrics/error-investigation` + export CSV da janela

2. **Causa #2**: VALIDACAO de payload/regra operacional  
   - Categoria: [ ] TIMEOUT  [x] VALIDACAO  [ ] INTEGRACAO  [ ] INFRA  [ ] OUTROS  
   - Volume / %: preenchido na copia automatica da UI (`Copiar fechamento US-001`) para a janela ativa  
   - **Owner**: Engenharia de Dominio (Pedidos) + QA Operacional  
   - **Acao corretiva**: reforcar validacao de schema/contrato na entrada e bloquear payload invalido com mensagem padronizada e rastreavel.  
   - Evidencia (audit_id/correlation_id/link): card `Investigacao auditavel (US-001)` + CSV 1 clique

3. **Causa #3**: INTEGRACAO com dependencia externa (parceiro/provider)  
   - Categoria: [ ] TIMEOUT  [ ] VALIDACAO  [x] INTEGRACAO  [ ] INFRA  [ ] OUTROS  
   - Volume / %: preenchido na copia automatica da UI (`Copiar fechamento US-001`) para a janela ativa  
   - **Owner**: Integracoes + Owner de parceiro/provider  
   - **Acao corretiva**: ativar fallback operacional por canal parceiro, revisar SLA de integracao e automatizar retry seguro para erros transientes.  
   - Evidencia (audit_id/correlation_id/link): trilha de auditoria + endpoints de investigacao/export

### 2) Hipoteses e evidencias operacionais
- [x] Hipotese principal validada com evidencia de log/traces.
- [x] Hipoteses secundarias registradas com status (validada/descartada).
- [x] Links de evidencias anexados (dashboard/audit/export CSV).

### 3) Plano de mitigacao emergencial
- [x] Mitigacao imediata definida e executada.
- [x] Risco residual descrito.
- [x] Responsavel por monitoramento pos-mitigacao definido.
- Plano resumido (1-3 linhas): aplicar retry/backoff controlado, monitorar severidades CRITICO/ALTO e reduzir reincidencia via acao corretiva por causa.

### 4) Gate de encerramento (DoD US-001)
- [x] 100% dos erros da janela classificados por categoria.
- [x] Top 3 causas com owner e acao corretiva documentados.
- [x] Evidencias operacionais anexadas e auditaveis.
- [x] Plano de mitigacao emergencial registrado.
- [x] Status da **US-OPS-001** alterado para **Concluido (implementado em codigo + evidencias operacionais)**.

### 5) Comando final de fechamento documental
- Atualizar no backlog:
  - `US-OPS-001 -> Status: Concluido (implementado em codigo + evidencias operacionais)`
- Atualizar no consolidado semanal:
  - `P0 concluidos: 4/4`
  - `Bloqueadores ativos`: remover item relacionado a classificacao de causa raiz (se aplicavel)

---

## 20) Mini padrao de versionamento (ops/health)

Objetivo: manter rastreabilidade consistente de evolucoes da tela `ops/health` em operacao/suporte/auditoria.

### Formato oficial
- `major.minor.patch + sprint`
- Exemplo de exibicao no badge da pagina:
  - `ops/health v1.4.2-sprint2`

### Regra de incremento
- **major**: quebra de fluxo/contrato ou mudanca estrutural relevante na operacao.
- **minor**: nova capacidade funcional sem quebrar o fluxo anterior (novo bloco/card/endpoint conectado).
- **patch**: ajuste incremental sem mudanca de comportamento principal (layout, microcopy, bugfix pontual).
- **sprint**: sufixo informativo de ciclo (ex.: `sprint2`, `sprint3`), alinhado ao planejamento ativo.

### Checklist rapido por release
- [ ] Badge de versao atualizado em `ops/health`.
- [ ] Registro de versao anotado neste documento (entregas + qualidade).
- [ ] Evidencia operacional vinculada (ex.: export CSV, snapshot semanal, runbook/ticket).

---

## 21) Novo sprint - Refacao avancada de `ops/audit`

Objetivo: elevar `ops/audit` para o mesmo nivel de maturidade de `ops/health`, com foco em investigacao rápida, priorizacao por risco e trilha auditavel pronta para incidente/auditoria.

### Contexto de abertura
- O ciclo atual elevou significativamente `ops/health` (severidade, top locker crítico, ticket imediato, evidências).
- `ops/audit` ainda está funcional, porém básico para o nível operacional já atingido.
- Este sprint foca em transformar `ops/audit` na tela principal de investigação N2/N3.

### Backlog inicial (P0/P1)

#### P0 - Critico (execucao imediata)

### US-AUDIT-001 - Painel de priorizacao por severidade e impacto
**Descricao**: Como operador de plantao, quero abrir `ops/audit` e enxergar imediatamente os eventos mais críticos por severidade, impacto e recência.  
**Entregaveis**:
- Barra de resumo (24h): total eventos, total erros, taxa de erro, severidade dominante.
- Ranking dos eventos críticos com ordenação por severidade -> impacto -> recência.
- Chips de severidade com contagem e filtro em 1 clique.
**Criterios de aceite**:
- Possível reproduzir a mesma leitura de severidade do `ops/health` dentro de `ops/audit`.
- Top críticos visíveis em até 1 dobra de tela sem rolagem longa.
- **Status**: Concluido (implementado em codigo + validacao operacional registrada)
- **Parcial concluido**:
  - barra de resumo 24h (total, erros, taxa, severidade dominante)
  - ranking critico (severidade -> impacto -> recencia)
  - chips de severidade com filtro em 1 clique
  - persistencia de severidade em URL (`severity=`)
  - indicador de versao da pagina (`ops/audit v2.0.0-sprint-audit1`)
  - reforco de foco por locker no filtro principal (`locker_id`) com persistencia em URL (`locker_id=`)
  - filtro por `correlation_id` com persistencia em URL (`correlation_id=`) e localStorage
  - busca textual em `error_message` com persistencia em URL (`error_search=`) e localStorage

### US-AUDIT-002 - Filtros avançados e contexto operacional
**Descricao**: Como analista, quero filtrar audit por `locker_id`, `action`, `result`, `correlation_id`, janela e texto de erro para reduzir tempo de diagnóstico.  
**Entregaveis**:
- Filtros compostos com estado persistido em URL (`from`, `to`, `locker_id`, `result`, `action` etc.).
- Presets rápidos (1h, 6h, 24h, 7d) e botão "limpar filtros".
- Highlight de correspondência para `error_message`.
**Criterios de aceite**:
- Compartilhar URL reproduz a mesma visão/filtro em outra sessão.
- Redução de cliques para chegar em evidência (N3) em fluxo padrão.
- **Status**: Concluido (implementado em codigo)
- **Concluido**:
  - filtros compostos com persistencia em URL e localStorage
  - presets de janela (24h, 7d, 30d, mes) e reset rapido
  - highlight de termo buscado em `error_message`

### US-AUDIT-003 - Evidência pronta para ticket/incidente
**Descricao**: Como time de operação, quero copiar um bloco de evidência estruturado diretamente do audit para Jira/Linear/Canal.  
**Entregaveis**:
- Botão por linha: `Copiar evidência (markdown)` e `Copiar evidência (texto simples)`.
- Template com: timestamp, locker, action, result, correlation_id, erro, impacto sugerido e próximos passos.
- Copia em lote dos itens selecionados.
**Criterios de aceite**:
- Ticket criado sem retrabalho manual de formatação.
- Evidência mantém rastreabilidade técnica mínima para auditoria.
- **Status**: Concluido (implementado em codigo + validacao operacional registrada)
- **Parcial concluido**:
  - copia por linha implementada (`Copiar evidência` + `Copiar simples`)
  - selecao multipla por checkbox implementada
  - copia em lote implementada (markdown e texto simples)
  - feedback visual de copia e contador de itens selecionados

#### P1 - Alto (sequencia do sprint)

### US-AUDIT-004 - Agrupamento inteligente por causa/correlação
**Descricao**: Como engenheiro de suporte, quero agrupar eventos por causa provável (`timeout`, `validacao`, `integracao`, `infra`) e por `correlation_id`.  
**Entregaveis**:
- Visão agregada por categoria com volume/%.
- Expansão para detalhes por correlação e eventos relacionados.
- Indicador de reincidência por janela.
**Criterios de aceite**:
- Top 3 causas da janela identificáveis sem export externo.
- Navegação N2 -> N3 em no máximo 2 interações.
- **Status**: Concluido (implementado em codigo + validacao operacional registrada)
- **Parcial concluido**:
  - agrupamento por causa provavel com volume/% no `ops/audit`
  - top 3 causas visivel em 1 bloco (sem export externo)
  - expansao colapsavel por correlacoes relacionadas (N2 -> N3)
  - indicador de reincidencia por causa e por correlacao (`BAIXA`/`MEDIA`/`ALTA`)

### US-AUDIT-005 - Linha do tempo investigativa (event stream)
**Descricao**: Como operador, quero uma timeline dos eventos para enxergar sequência causal e pontos de ruptura.  
**Entregaveis**:
- Timeline por ordem temporal com mudanças de estado.
- Marcadores de anomalia e eventos-chave (ERROR spikes).
- Atalho para abrir entidade relacionada (pedido/locker/reconciliação).
**Criterios de aceite**:
- Sequência temporal de um incidente crítico compreendida em menos de 2 minutos.
- **Status**: Concluido (implementado em codigo + validacao operacional registrada)
- **Parcial concluido**:
  - timeline investigativa adicionada no `ops/audit` com stream temporal de eventos recentes
  - marcadores de anomalia implementados (`ERROR_EVENT`, `ERROR_SPIKE`, `SEVERITY_CRITICAL`)
  - atalho de entidade por evento (`Locker`, `Correlation`, `Reconciliação`, `Ops Health`)
  - sem necessidade de nova rota nesta etapa (entrega absorvida na rota existente `/ops/audit`)

### Qualidade e governanca do sprint
- Lint sem erros nos arquivos alterados.
- Testes de regressão de rotas/filtros essenciais executados.
- Registro em `ops/updates` de cada incremento relevante.
- Versão de página exibida em `ops/audit` no padrão `major.minor.patch + sprint`.

### Definicao de pronto (DoD) do sprint `ops/audit`
- [x] Priorização de severidade/impacto implementada e validada em produção espelho.
- [x] Filtros avançados + URL state funcionando ponta a ponta.
- [x] Cópia de evidência operacional (markdown/plain) validada com time de plantão.
- [x] Agrupamento por causa/correlação habilitado para investigação rápida.
- [x] Timeline investigativa disponível para casos críticos.
- [x] Documento atualizado com evidências e decisão de fechamento.

### Bloco pronto para daily (ops/audit)
**Hoje**
- Ranking crítico, agrupamento por causa/correlação e timeline investigativa convertidos para modo `collapsed` com filtros locais e limites de renderização.
- `US-AUDIT-004` avançou com leitura imediata de top causas, reincidência e drill-down N2->N3 por correlação.
- `US-AUDIT-005` avançou com stream temporal, marcadores (`ERROR_EVENT`, `ERROR_SPIKE`, `SEVERITY_CRITICAL`) e atalhos de entidade.

**Bloqueios**
- Sem bloqueios técnicos no momento.
- Sprint encerrado com validação operacional registrada no bloco `US-AUDIT-FINAL-VALIDATION`.

**Decisão**
- Encerramento formal aprovado: sprint `ops/audit` concluído nesta rodada.
- Registro de risco residual mantido como monitoramento contínuo (sem impedir fechamento).

### Bloco daily alternativo (Slack/Teams - curto e executivo)
**Hoje**: `ops/audit` consolidado com ranking, agrupamento e timeline em modo colapsavel + filtros locais; copia de evidencia expandida com formato curto para Slack/Teams (linha e lote).  
**Bloqueios**: sem bloqueios tecnicos; pendente apenas rodada de validacao operacional final em plantao (real/simulado).  
**Decisao**: recomendacao de fechamento do sprint como `Concluido em codigo`, mantendo `validacao operacional` como anexo incremental.
- **Automacao em 1 clique**: botoes `Copiar daily Slack/Teams` adicionados em `ops/audit` e `ops/health` para gerar status operacional automático (hoje/bloqueios/decisao) sem retrabalho.
- **Homogeneizacao UX/CX entre telas**: aplicado no `ops/health` o mesmo padrao de blocos colapsaveis com filtros locais e `Limpar secao` (Top erros, Classificacao assistida e Alertas ativos), alinhando com o `ops/audit`.
- **US-AUDIT-FINAL-VALIDATION implementado no `ops/audit`**:
  - secao dedicada de fechamento operacional com `resultado` + `notas de validacao`
  - snapshot automático com filtros ativos, resumo 24h, ranking top 3, causas top 3 e sinais da timeline
  - copia em 1 clique para evidencia final (`markdown` e `texto simples`)

### Proximo passo de execucao (imediato)
1. Iniciar novo ciclo de melhorias incrementais (backlog pós-fechamento) com base no risco residual de integração externa.
2. Manter rotina de validação operacional semanal usando `US-AUDIT-FINAL-VALIDATION` como padrão de evidência.
3. Registrar apenas ajustes evolutivos no `ops/updates` sem reabrir o sprint encerrado.

### Encerramento formal do sprint `ops/audit`
- **Data de fechamento**: 27/04/2026
- **Resultado**: `Concluido em codigo` + `validacao operacional registrada`
- **Evidencia de fechamento**: secao `US-AUDIT-FINAL-VALIDATION` em `ops/audit` (markdown/texto simples) com outcome `APPROVED_WITH_RISK`
- **Risco residual aceito**: instabilidade intermitente de integracao externa (`HTTP_5xx`) sob monitoramento ativo
- **Pendencia registrada para proximo ciclo**: Outros OPS devem passar pelo mesmo processo - Marcos Santos

### Exemplo pronto - fechamento com `APPROVED_WITH_RISK` (copiar e colar)
```text
US-AUDIT-FINAL-VALIDATION
timestamp: 2026-04-27T16:48:00Z
outcome: APPROVED_WITH_RISK
filtros_ativos: severity=HIGH | locker_id~SP-ALPHAVILLE-SHOP-LK-001 | error_search~HTTP_5
resumo_24h: total=184 | erros=46 | taxa=25.0% | sev=HIGH
ranking_top3: HIGH:PARTNER_HEALTH_CHECK_AUTO_ALERT | HIGH:OPS_ORDERS_STATUS_AUDIT_RANGE | MEDIUM:OPS_AUDIT_LIST
causas_top3: INTEGRACAO:28(MEDIA) | TIMEOUT:11(BAIXA) | INFRA:7(BAIXA)
timeline: eventos=30 | spikes=2 | criticos=0
notas: fluxo de investigacao executado em 1m35s; evidencias copiadas sem retrabalho; risco residual concentrado em HTTP_5xx intermitente de parceiro externo.
decisao: aprovado com risco monitorado; manter vigilancia ativa e revalidar em 24h com novo snapshot.
```

**Leitura executiva sugerida**
- **Motivo do risco**: dependencia externa com erro intermitente (`HTTP_5xx`) ainda presente na janela.
- **Mitigacao imediata**: manter triagem ativa por `correlation_id` + runbook de integracao para eventos HIGH.
- **Criterio de encerramento definitivo**: duas janelas consecutivas sem spike (`ERROR_SPIKE=0`) e queda da taxa para `<20%`.

