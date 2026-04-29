# FISCAL GLOBAL - Plano de Sprints (Q2/Q3 2026)

## Objetivo

Transformar as diretrizes de fiscalidade multipaís em execução incremental no ELLAN LAB, preservando:

- contrato canônico único,
- separação Port & Adapter,
- rollout controlado por feature flag,
- observabilidade e rollback por país.

---

## Premissas de Execução

- Stub e Real devem cumprir o mesmo contrato de domínio.
- Mudança de `FISCAL_MODE` ou feature flags não pode exigir refatoração de regra de negócio.
- Cada novo país entra em 3 níveis:
  - Nível 1: Stub + contrato + cenários obrigatórios.
  - Nível 2: Integração real homologação (gate técnico).
  - Nível 3: Go-live controlado (gate operacional).

---

## Backlog Estruturado por Camada

## FG-0 - Foundation Global (obrigatório antes dos países)

- Catálogo fiscal global por país/região (`authority`, `document_type`, `protocol`, `timezone`, `currency`, `id_rules`).
- Matriz de cenários obrigatórios por operação (`authorize/cancel/correct/status`) com mapeamento canônico.
- Convenção de fixtures por país + versionamento de especificação fiscal.
- Métricas padrão de stub/real por provider e região.
- Checklist padrão Stub -> Real (credencial, homologação, gate técnico, gate operacional, rollback).

DoD FG-0:
- estrutura global publicada em `docs`;
- endpoints/cenários de stub padronizados por contrato;
- playbook único reutilizável por país.

## FG-1 - Stub Global Multipaís (onda 1)

Países/autoridades prioritárias com base no material recebido:

- EUA federal (IRS MeF),
- Austrália (ATO),
- Polônia (KSeF),
- Canadá federal (CRA),
- França (DGFiP/Chorus Pro).

Escopo:
- adicionar adaptadores stub por país;
- adicionar fixtures mínimos por operação;
- adicionar cenários regionais críticos (rejeição de regra, timeout, not found, deadline).

DoD FG-1:
- cada autoridade da onda 1 com stub funcional;
- cenários obrigatórios implementados;
- logs estruturados e métricas expostas.

## FG-2 - Regionalidade Profunda (onda 2)

- EUA state-level: Califórnia (CDTFA), Texas (Comptroller), NY DTF.
- Canadá regional: Quebec (Revenu Quebec).
- Tailândia (RD).
- Alemanha (XRechnung/Peppol).

Escopo:
- regras regionais específicas (headers/parametrização por estado/região);
- validações de identificadores fiscais locais;
- cenários operacionais por região.

DoD FG-2:
- seleção regional por parâmetro explícito;
- fallback regional validado;
- documentação operacional de cada regionalidade.

## FG-3 - Go/No-Go Global no OPS

- Estender painel OPS para visão multipaís:
  - gate por país/região,
  - semáforo por severidade,
  - ações rápidas (gate/rollback),
  - drill-down por seção.
- Reusar padrão já consolidado BR/PT como baseline.

DoD FG-3:
- painel multipaís com escopo explícito;
- comandos operacionais por país;
- runbook/playbook globais atualizados.

## FG-4 - Homologação Real (por ondas)

Ordem recomendada:
1. IRS (EUA)
2. ATO (AU)
3. KSeF (PL)
4. CRA (CA)
5. Chorus Pro (FR)

Para cada país:
- credenciais homologação ativas;
- gate técnico com `GO`;
- janela de 30 min sem `CRITICAL`;
- rollback real validado por flag.

DoD FG-4:
- país promovido de `[~]` para `[x]` com evidência de gate + janela + rollback.

---

## Modelo de Sprint (2 semanas)

- Semana 1:
  - contrato + stub + fixtures + cenários + métricas.
- Semana 2:
  - OPS + runbook/playbook + gate técnico + hardening.

Entrega por sprint:
- implementação,
- operação,
- evidência no acompanhamento.

---

## Critérios de Saída da Rodada Global

- FG-0 a FG-3 concluídos em pelo menos 1 onda multipaís.
- Pelo menos 1 novo país fora BR/PT em `[x]` no fluxo real homologado.
- Operação capaz de executar gate/rollback por país sem dependência direta de dev.

---

## Notas de Qualidade dos documentos recebidos

- O documento ampliado está consistente para planejamento, mas possui um ajuste de marcação HTML na seção de glossário (tag de tabela iniciada/fechada de forma inconsistente). Isso não impede uso como referência de sprint, mas vale corrigir para publicação oficial.
