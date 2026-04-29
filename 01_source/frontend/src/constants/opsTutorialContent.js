export const OPS_TUTORIALS_BY_PATH = {
  "/ops/audit": {
    title: "Tutorial rápido - ops/audit",
    subtitle: "Guia de plantão para investigação, priorização e evidência operacional.",
    sections: [
      {
        title: "1) Objetivo da tela",
        items: [
          "Investigar eventos operacionais com foco em resultado, severidade e rastreabilidade.",
          "Acompanhar inconsistências de status e evolução das falhas por período.",
        ],
      },
      {
        title: "2) Fluxo recomendado de uso",
        items: [
          "Comece por filtros de escopo (order_id, locker_id, correlation_id) e clique em Consultar auditoria.",
          "Use chips de severidade para priorizar CRITICAL e HIGH no plantão.",
          "Abra Ranking, Agrupamento por causa e Timeline para achar padrão de recorrência.",
          "Copie evidências individuais ou em lote para registrar no handoff.",
        ],
      },
      {
        title: "3) Dicas rápidas",
        items: [
          "Use Resetar filtros para voltar ao padrão de plantão (24h).",
          "Se houver incidente, copie o daily Slack/Teams para comunicação imediata.",
          "Antes de encerrar turno, gere o bloco US-AUDIT-FINAL-VALIDATION.",
        ],
      },
    ],
  },
  "/ops/health": {
    title: "Tutorial rápido - ops/health",
    subtitle: "Guia operacional para leitura de saúde, alertas e ação imediata.",
    sections: [
      {
        title: "1) Objetivo da tela",
        items: [
          "Monitorar saúde operacional por janela de tempo com foco em erro, latência e backlog.",
          "Apoiar decisão rápida de plantão por persona (Ops, Dev, Gestão).",
        ],
      },
      {
        title: "2) Fluxo recomendado de uso",
        items: [
          "Defina Persona e Janela (h), depois clique em Atualizar.",
          "Comece pelos KPIs de topo e pelos alertas com maior severidade.",
          "Use o link de investigação de cada alerta para aprofundar no ops/audit ou reconciliação.",
          "Se necessário, ajuste calibração preditiva e salve snapshot semanal.",
        ],
      },
      {
        title: "3) Dicas rápidas",
        items: [
          "Presets de janela aceleram leitura de tendência (24h, 48h, 7d).",
          "Copiar daily Slack/Teams ajuda no handoff sem perder contexto.",
          "Sempre validar volume da amostra antes de concluir melhora ou piora.",
        ],
      },
    ],
  },
  "/ops/reconciliation": {
    title: "Tutorial rápido - ops/reconciliation",
    subtitle: "Guia operacional para reconciliação manual e validação de recuperação.",
    sections: [
      {
        title: "1) Objetivo da tela",
        items: [
          "Executar reconciliação manual de pedidos com inconsistência de crédito/slot após falhas parciais.",
          "Acompanhar saúde operacional e alertas no mesmo fluxo de decisão.",
        ],
      },
      {
        title: "2) Fluxo recomendado de uso",
        items: [
          "Revise o bloco Saúde Operacional e os alertas ativos antes de agir.",
          "Informe o order_id e clique em Executar reconciliação.",
          "Confira o resultado e o objeto compensation para validar recuperação.",
          "Use o histórico local para repetir pedidos recentes com rapidez.",
        ],
      },
      {
        title: "3) Dicas rápidas",
        items: [
          "Se houver muitos casos, priorize pedidos ligados a alertas críticos.",
          "Alterne presets (24h, 48h, 7d) para entender tendência antes de atuar.",
          "Após ação manual, valide no ops/audit para confirmar estabilização.",
        ],
      },
    ],
  },
  "/ops/analytics/pickup": {
    title: "Tutorial rápido - ops/analytics/pickup",
    subtitle: "Leitura orientada do Pickup Health Dashboard por entidade e região.",
    sections: [
      {
        title: "1) Objetivo da tela",
        items: [
          "Priorizar risco operacional de retirada por entidade (lockers, fluxos e filas).",
          "Identificar rapidamente blocos em alerta/critico e direcionar resposta.",
        ],
      },
      {
        title: "2) Fluxo recomendado de uso",
        items: [
          "Escolha Entidade e Região para refletir o contexto do turno.",
          "Ajuste janela de tendência e limite do ranking para destacar os maiores riscos.",
          "Comece pelos cards de status (Atenção, Alerta, Crítico) e entre no detalhe dos itens com pior sinal.",
        ],
      },
      {
        title: "3) Dicas rápidas",
        items: [
          "Use presets curtos (1d/3d) para incidentes em andamento e longos (14d/30d) para tendência.",
          "Quando o risco persistir, correlacione com /ops/health e /ops/audit para evidência.",
          "Registre decisão e owner no handoff para garantir continuidade no próximo turno.",
        ],
      },
    ],
  },
  "/ops/updates": {
    title: "Tutorial rápido - ops/updates",
    subtitle: "Registro operacional de mudanças e comunicação de sprint.",
    sections: [
      {
        title: "1) Objetivo da tela",
        items: ["Concentrar histórico de entregas OPS com contexto funcional e técnico."],
      },
      {
        title: "2) Fluxo recomendado de uso",
        items: [
          "Leia primeiro os itens mais recentes e valide impacto na rota afetada.",
          "Use o link direto do card para abrir rapidamente a tela de operação relacionada.",
        ],
      },
      {
        title: "3) Dicas rápidas",
        items: ["Antes de handoff, registre mudança com escopo, evidência e rota principal."],
      },
    ],
  },
  "/ops/dev/errors": {
    title: "Tutorial rápido - ops/dev/errors",
    subtitle: "Triagem operacional de erros 4xx/5xx e sinais de regressão.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Detectar erro recorrente e priorizar atuação de suporte/engenharia."] },
      {
        title: "2) Fluxo recomendado de uso",
        items: ["Filtre por severidade/endpoint, agrupe padrões e valide aumento de volume no período."],
      },
      { title: "3) Dicas rápidas", items: ["Correlacione com /ops/health e /ops/audit para fechar diagnóstico."] },
    ],
  },
  "/ops/fiscal/providers": {
    title: "Tutorial rápido - ops/fiscal/providers",
    subtitle: "Saúde dos providers fiscais e decisão GO/NO-GO por país.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar disponibilidade fiscal e risco de emissão em BR/PT."] },
      {
        title: "2) Fluxo recomendado de uso",
        items: ["Revise status atual, rode rechecagem e valide critérios de GO/NO-GO antes de habilitar flags."],
      },
      { title: "3) Dicas rápidas", items: ["Documente decisão operacional e janela aplicada no handoff."] },
    ],
  },
  "/ops/partners/dashboard": {
    title: "Tutorial rápido - ops/partners/dashboard",
    subtitle: "Visão geral operacional de parceiros e desempenho agregado.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Priorizar parceiros com maior impacto operacional/financeiro."] },
      { title: "2) Fluxo recomendado de uso", items: ["Analise KPIs de topo, destaque outliers e abra drill-down de reconciliação."] },
      { title: "3) Dicas rápidas", items: ["Use janela consistente ao comparar parceiros no mesmo turno."] },
    ],
  },
  "/ops/partners/financials-service-areas": {
    title: "Tutorial rápido - ops/partners/financials-service-areas",
    subtitle: "Operação de settlement e cobertura por área de serviço.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Gerir geração/aprovação de settlement e expansão/ajuste de cobertura."] },
      { title: "2) Fluxo recomendado de uso", items: ["Valide performance, execute lote financeiro e confirme consistência da service area."] },
      { title: "3) Dicas rápidas", items: ["Priorize parceiros com divergência financeira e SLA degradado."] },
    ],
  },
  "/ops/partners/reconciliation-dashboard": {
    title: "Tutorial rápido - ops/partners/reconciliation-dashboard",
    subtitle: "Conciliação de divergências de settlement por parceiro.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Identificar e reduzir divergências relevantes de conciliação."] },
      { title: "2) Fluxo recomendado de uso", items: ["Ordene por impacto, investigue causa e acompanhe resolução por status."] },
      { title: "3) Dicas rápidas", items: ["Registre owner e ETA para cada divergência crítica."] },
    ],
  },
  "/ops/partners/billing-monitor": {
    title: "Tutorial rápido - ops/partners/billing-monitor",
    subtitle: "Monitoramento de billing e invoice de parceiros.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Prevenir atraso/falha no ciclo de cobrança dos parceiros."] },
      { title: "2) Fluxo recomendado de uso", items: ["Filtre por parceiro/período, valide pendências e confirme status de emissão."] },
      { title: "3) Dicas rápidas", items: ["Escalone inconsistência com impacto de fechamento financeiro."] },
    ],
  },
  "/ops/partners/hypertables": {
    title: "Tutorial rápido - ops/partners/hypertables",
    subtitle: "Saúde de hypertables/policies para dados de parceiros.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Garantir retenção, compressão e performance de séries temporais." ] },
      { title: "2) Fluxo recomendado de uso", items: ["Revise status de policies, identifique falhas e execute correção orientada."] },
      { title: "3) Dicas rápidas", items: ["Acompanhe crescimento de storage e jobs com falha recorrente."] },
    ],
  },
  "/ops/logistics/dashboard": {
    title: "Tutorial rápido - ops/logistics/dashboard",
    subtitle: "Painel macro da operação logística.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Visualizar carga operacional e gargalos logísticos do turno."] },
      { title: "2) Fluxo recomendado de uso", items: ["Comece pelos KPIs críticos e aprofunde em manifests/returns quando houver desvio."] },
      { title: "3) Dicas rápidas", items: ["Use mesma janela para comparação consistente entre áreas."] },
    ],
  },
  "/ops/logistics/manifests": {
    title: "Tutorial rápido - ops/logistics/manifests",
    subtitle: "Gestão operacional de manifestos e evidências.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Monitorar execução de manifestos e remover bloqueios operacionais."] },
      { title: "2) Fluxo recomendado de uso", items: ["Filtre pendências por status/tempo, aplique ação e confirme atualização no pipeline."] },
      { title: "3) Dicas rápidas", items: ["Mantenha evidência de execução para auditoria do turno."] },
    ],
  },
  "/ops/logistics/manifests-overview": {
    title: "Tutorial rápido - ops/logistics/manifests-overview",
    subtitle: "Visão consolidada de manifestos por janela operacional.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar volume, atraso e saúde global de manifestos."] },
      { title: "2) Fluxo recomendado de uso", items: ["Compare períodos, destaque anomalias e direcione investigação para a fila detalhada."] },
      { title: "3) Dicas rápidas", items: ["Use insights da visão geral para priorizar execução no D2/D3."] },
    ],
  },
  "/ops/logistics/returns": {
    title: "Tutorial rápido - ops/logistics/returns",
    subtitle: "Fila operacional de return-requests.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Reduzir backlog de devoluções com prioridade por impacto e SLA."] },
      { title: "2) Fluxo recomendado de uso", items: ["Filtre por status/idade, execute quick actions e confirme mudança de estado."] },
      { title: "3) Dicas rápidas", items: ["Faça handoff com lista explícita de pendências críticas."] },
    ],
  },
  "/ops/products/catalog": {
    title: "Tutorial rápido - ops/products/catalog",
    subtitle: "Operação de catálogo e qualidade de dados de produto.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Garantir consistência de cadastro, disponibilidade e dados essenciais."] },
      { title: "2) Fluxo recomendado de uso", items: ["Valide filtros de integridade, corrija pendências e reavalie sinais de risco."] },
      { title: "3) Dicas rápidas", items: ["Priorize itens com impacto direto em venda e fulfillment."] },
    ],
  },
  "/ops/products/assets": {
    title: "Tutorial rápido - ops/products/assets",
    subtitle: "Gestão operacional de mídia e barcode de produtos.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Assegurar que ativos essenciais estejam completos e válidos."] },
      { title: "2) Fluxo recomendado de uso", items: ["Localize item pendente, aplique ajuste e confirme validação pós-atualização."] },
      { title: "3) Dicas rápidas", items: ["Trate primeiro ativos bloqueantes de publicação/expedição."] },
    ],
  },
  "/ops/products/pricing-fiscal": {
    title: "Tutorial rápido - ops/products/pricing-fiscal",
    subtitle: "Operação de preço e regras fiscais de produto.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Evitar divergência de preço/fiscal entre catálogo e emissão."] },
      { title: "2) Fluxo recomendado de uso", items: ["Valide preço base, regra fiscal e impacto por região antes de publicar."] },
      { title: "3) Dicas rápidas", items: ["Registre mudança com justificativa para rastreabilidade."] },
    ],
  },
  "/ops/products/inventory-health": {
    title: "Tutorial rápido - ops/products/inventory-health",
    subtitle: "Saúde de estoque e sinalização de inconsistências.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Detectar desbalanceamento de estoque e prevenir ruptura operacional."] },
      { title: "2) Fluxo recomendado de uso", items: ["Monitore indicadores de risco, aprofunde por item e execute correção orientada."] },
      { title: "3) Dicas rápidas", items: ["Cruze com pedidos pendentes para priorização real de impacto."] },
    ],
  },
  "/ops/integration/outbox-replay": {
    title: "Tutorial rápido - ops/integration/outbox-replay",
    subtitle: "Replay operacional de eventos de integração.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Recuperar eventos não processados sem gerar duplicidade indevida."] },
      { title: "2) Fluxo recomendado de uso", items: ["Selecione lote, execute replay controlado e valide retorno no audit/health."] },
      { title: "3) Dicas rápidas", items: ["Evite reprocessamento massivo sem delimitar janela e escopo."] },
    ],
  },
  "/ops/integration/orders-fiscal": {
    title: "Tutorial rápido - ops/integration/orders-fiscal",
    subtitle: "Diagnóstico por order_id no fluxo integração + fiscal.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Rastrear ponta a ponta eventos e estado fiscal do pedido."] },
      { title: "2) Fluxo recomendado de uso", items: ["Informe order_id, avalie trilha de eventos e confirme consistência de status."] },
      { title: "3) Dicas rápidas", items: ["Anexe evidência do order_id no incidente/handoff."] },
    ],
  },
  "/ops/integration/orders-partner-lookup": {
    title: "Tutorial rápido - ops/integration/orders-partner-lookup",
    subtitle: "Lookup operacional por referência de parceiro.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Localizar rapidamente ordens por chave externa de parceiro."] },
      { title: "2) Fluxo recomendado de uso", items: ["Pesquise referência, valide correspondência e confirme estado operacional/fiscal."] },
      { title: "3) Dicas rápidas", items: ["Use correlação de IDs para reduzir retrabalho de suporte."] },
    ],
  },
  "/ops/auth/policy": {
    title: "Tutorial rápido - ops/auth/policy",
    subtitle: "Referência de política de autorização operacional.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Validar permissões exigidas antes de executar ações sensíveis."] },
      { title: "2) Fluxo recomendado de uso", items: ["Consulte papel/regra, compare com caso real e confirme aderência."] },
      { title: "3) Dicas rápidas", items: ["Sempre relacione decisão ao princípio de menor privilégio."] },
    ],
  },
  "/ops/auth/policy/versioning": {
    title: "Tutorial rápido - ops/auth/policy/versioning",
    subtitle: "Histórico e governança de versões de política OPS.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Entender evolução de regra e impacto por versão publicada."] },
      { title: "2) Fluxo recomendado de uso", items: ["Localize versão ativa, compare mudanças e comunique impacto operacional."] },
      { title: "3) Dicas rápidas", items: ["Use referência de versão no handoff para evitar ambiguidade."] },
    ],
  },
  "/ops/dev/reset": {
    title: "Tutorial rápido - ops/dev/reset",
    subtitle: "Ferramenta de reset para suporte técnico controlado.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Aplicar reset operacional em contexto de troubleshooting."] },
      { title: "2) Fluxo recomendado de uso", items: ["Confirme escopo/ambiente, execute reset e valide efeito pós-ação."] },
      { title: "3) Dicas rápidas", items: ["Evite execução sem evidência do problema e plano de rollback."] },
    ],
  },
  "/ops/dev/slots": {
    title: "Tutorial rápido - ops/dev/slots",
    subtitle: "Alocação e ajuste técnico de slots.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Ajustar distribuição técnica de slots para recuperação operacional."] },
      { title: "2) Fluxo recomendado de uso", items: ["Valide disponibilidade, aplique mudança e monitore impacto imediato."] },
      { title: "3) Dicas rápidas", items: ["Registre alteração para facilitar auditoria e reversão."] },
    ],
  },
  "/ops/dev/base": {
    title: "Tutorial rápido - ops/dev/base",
    subtitle: "Gestão técnica de base (tabelas/enums) para suporte OPS.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Executar manutenção controlada de dados estruturais de apoio."] },
      { title: "2) Fluxo recomendado de uso", items: ["Revise impacto, aplique alteração mínima e valide saúde pós-execução."] },
      { title: "3) Dicas rápidas", items: ["Preferir janelas controladas para mudanças estruturais."] },
    ],
  },
  "/ops/sp": {
    title: "Tutorial rápido - ops/sp",
    subtitle: "Operação regional SP no dashboard principal.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar operação de lockers da região SP."] },
      { title: "2) Fluxo recomendado de uso", items: ["Monitore filas/slots/pagamentos e trate bloqueios prioritários."] },
      { title: "3) Dicas rápidas", items: ["Escalone para dashboards especializados quando necessário."] },
    ],
  },
  "/ops/pt": {
    title: "Tutorial rápido - ops/pt",
    subtitle: "Operação regional PT no dashboard principal.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar operação de lockers da região PT."] },
      { title: "2) Fluxo recomendado de uso", items: ["Monitore saúde de retirada, filas e status de operação diária."] },
      { title: "3) Dicas rápidas", items: ["Padronize janela para comparar com SP em análises cruzadas."] },
    ],
  },
  "/ops/00": {
    title: "Tutorial rápido - ops/00",
    subtitle: "Ambiente operacional base para laboratório/controlado.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Executar validações operacionais em contexto controlado."] },
      { title: "2) Fluxo recomendado de uso", items: ["Teste fluxo fim-a-fim, valide métricas e documente observações."] },
      { title: "3) Dicas rápidas", items: ["Não confundir evidência de laboratório com produção."] },
    ],
  },
  "/ops/sp/kiosk": {
    title: "Tutorial rápido - ops/sp/kiosk",
    subtitle: "Operação kiosk SP.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar operação kiosk em SP e mitigar falhas de atendimento."] },
      { title: "2) Fluxo recomendado de uso", items: ["Revise estado atual do kiosk, execute ação e confirme recuperação."] },
      { title: "3) Dicas rápidas", items: ["Registre horário e impacto percebido ao aplicar correção."] },
    ],
  },
  "/ops/pt/kiosk": {
    title: "Tutorial rápido - ops/pt/kiosk",
    subtitle: "Operação kiosk PT.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Acompanhar operação kiosk em PT com foco em continuidade."] },
      { title: "2) Fluxo recomendado de uso", items: ["Identifique bloqueio, aplique ação de recuperação e valide retorno de serviço."] },
      { title: "3) Dicas rápidas", items: ["Escalone rapidamente falha repetitiva para engenharia."] },
    ],
  },
  "/ops/00/kiosk": {
    title: "Tutorial rápido - ops/00/kiosk",
    subtitle: "Kiosk em ambiente base/controlado.",
    sections: [
      { title: "1) Objetivo da tela", items: ["Validar comportamento kiosk em cenário controlado."] },
      { title: "2) Fluxo recomendado de uso", items: ["Execute teste guiado e confirme resposta esperada dos componentes."] },
      { title: "3) Dicas rápidas", items: ["Mantenha rastreio de cenário/teste para reprodução posterior."] },
    ],
  },
};

export const OPS_TUTORIALS_BY_GROUP = {
  "Visão Geral": {
    title: "Tutorial OPS - Visão Geral",
    subtitle: "Painéis de visão macro para acompanhamento operacional diário.",
    sections: [
      { title: "Objetivo da área", items: ["Acompanhar situação geral por região/tenant e identificar desvio inicial."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Valide KPIs centrais da janela atual e compare com o comportamento esperado.",
          "Ao detectar anomalia, avance para a rota especializada do domínio afetado.",
        ],
      },
      { title: "Saída esperada", items: ["Registrar sinal de risco e direcionar investigação para dashboard específico."] },
    ],
  },
  Dashboards: {
    title: "Tutorial OPS - Dashboards",
    subtitle: "Leitura rápida de saúde, auditoria e reconciliação para plantão.",
    sections: [
      { title: "Objetivo da área", items: ["Detectar incidentes, priorizar severidade e orientar ação imediata."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Comece por janela/filtros, destaque erros críticos e valide tendência do período.",
          "Use links cruzados entre dashboards para confirmar causa raiz.",
        ],
      },
      { title: "Saída esperada", items: ["Comunicação de status e evidência de decisão operacional."] },
    ],
  },
  "Logística": {
    title: "Tutorial OPS - Logística",
    subtitle: "Operação de manifestos, returns e acompanhamento de SLA.",
    sections: [
      { title: "Objetivo da área", items: ["Manter fluxo logístico estável, reduzindo backlog e violações de prazo."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Priorize itens por idade/criticidade e execute quick actions de normalização.",
          "Valide evolução após ação e faça handoff com lista de pendências abertas.",
        ],
      },
      { title: "Saída esperada", items: ["Fila tratada por prioridade com evidências de execução e próximos passos."] },
    ],
  },
  "Produtos & Fiscal": {
    title: "Tutorial OPS - Produtos & Fiscal",
    subtitle: "Governança de catálogo, preços, estoque e conformidade fiscal.",
    sections: [
      { title: "Objetivo da área", items: ["Garantir consistência de dados de produto e operação fiscal por país."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Verifique integridade de cadastro, pricing e sinais de inconsistência de estoque.",
          "Quando houver risco fiscal, valide providers/gates antes de avançar mudanças.",
        ],
      },
      { title: "Saída esperada", items: ["Ajustes seguros aplicados com rastreabilidade operacional."] },
    ],
  },
  "Integrações": {
    title: "Tutorial OPS - Integrações",
    subtitle: "Tratamento de outbox, replays e trilhas de integração por pedido.",
    sections: [
      { title: "Objetivo da área", items: ["Restabelecer fluxo de eventos e reduzir falhas de integração recorrentes."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Identifique lotes afetados, execute replay controlado e acompanhe retorno.",
          "Correlacione com audit/health para validar impacto e estabilização.",
        ],
      },
      { title: "Saída esperada", items: ["Pipeline de eventos normalizado com registro de causa e mitigação."] },
    ],
  },
  Partners: {
    title: "Tutorial OPS - Partners",
    subtitle: "Operação de performance, reconciliação e monitoramento financeiro de parceiros.",
    sections: [
      { title: "Objetivo da área", items: ["Assegurar previsibilidade de settlement, billing e cobertura operacional."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Priorize divergências relevantes por impacto financeiro e recorrência.",
          "Valide consistência entre dashboard, reconciliação e monitor de cobrança.",
        ],
      },
      { title: "Saída esperada", items: ["Pendências priorizadas com plano de correção e owner definido."] },
    ],
  },
  "Políticas": {
    title: "Tutorial OPS - Políticas",
    subtitle: "Referência de autorização e versionamento para governança de acesso.",
    sections: [
      { title: "Objetivo da área", items: ["Conferir regras de acesso e políticas vigentes antes de mudanças operacionais."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Valide escopo por perfil e confirme aderência às diretrizes publicadas.",
          "Use versão/política como base para decisões de suporte e auditoria.",
        ],
      },
      { title: "Saída esperada", items: ["Decisão documentada com referência explícita de política."] },
    ],
  },
  Dev: {
    title: "Tutorial OPS - Dev",
    subtitle: "Ferramentas operacionais de suporte técnico e manutenção controlada.",
    sections: [
      { title: "Objetivo da área", items: ["Executar ações de diagnóstico e manutenção sem comprometer operação."] },
      {
        title: "Fluxo recomendado",
        items: [
          "Confirme ambiente/escopo antes de executar resets, ajustes ou cargas de apoio.",
          "Após ação, valide efeito colateral nos dashboards operacionais.",
        ],
      },
      { title: "Saída esperada", items: ["Intervenção concluída com evidência e impacto controlado."] },
    ],
  },
};

export function resolveOpsTutorial(currentOpsPath, currentOpsLink) {
  const byGroup = OPS_TUTORIALS_BY_GROUP[currentOpsLink?.group || ""];
  if (OPS_TUTORIALS_BY_PATH[currentOpsPath]) {
    return OPS_TUTORIALS_BY_PATH[currentOpsPath];
  }
  if (byGroup) return byGroup;
  return {
    title: `Tutorial rápido - ${currentOpsPath}`,
    subtitle: currentOpsLink?.aria || "Guia rápido para navegação e operação da página atual.",
    sections: [
      {
        title: "Objetivo da tela",
        items: [currentOpsLink?.aria || "Executar a operação desta rota com segurança e rastreabilidade."],
      },
      {
        title: "Fluxo sugerido",
        items: [
          "Revise filtros/controles principais, execute a ação e valide o resultado retornado.",
          "Registre evidência operacional quando houver impacto em atendimento ou plantão.",
        ],
      },
      { title: "Próximo passo", items: ["Se necessário, use /ops/updates para contexto de mudanças recentes."] },
    ],
  };
}
