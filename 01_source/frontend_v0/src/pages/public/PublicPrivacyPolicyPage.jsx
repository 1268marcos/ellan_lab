
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toInternalLegalPrivacyPath } from "../../data/legalPrivacyDocuments";
import { LOCKER_PLAYER_GROUPS, playersSummaryForRegulation } from "../../data/lockerNetworkPlayers";

const PRIVACY_API = `${import.meta.env.VITE_PRIVACY_COMPLIANCE_ADMIN_BASE_URL || "/api/pca"}/v1/privacy-compliance-admin`;

const JURISDICTION_OPTIONS = [
  { code: "LGPD", label: "Brasil", subtitle: "LGPD · Lei 13.709/2018" },
  { code: "GDPR", label: "União Europeia", subtitle: "GDPR · Reg. UE 2016/679" },
  { code: "UKGDPR", label: "Reino Unido", subtitle: "UK GDPR · DPA 2018" },
  { code: "CCPA", label: "Califórnia (EUA)", subtitle: "CCPA / CPRA" },
  { code: "PIPEDA", label: "Canadá", subtitle: "PIPEDA" },
  { code: "APPI", label: "Japão", subtitle: "APPI" },
];

const RIGHTS_BY_CODE = {
  LGPD: [
    "Confirmar a existência de tratamento e acessar seus dados (Art. 18, I–II)",
    "Corrigir dados incompletos, inexatos ou desatualizados (Art. 18, III)",
    "Anonimizar, bloquear ou eliminar dados desnecessários (Art. 18, IV)",
    "Portabilidade a outro fornecedor (Art. 18, V)",
    "Eliminar dados tratados com consentimento (Art. 18, VI)",
    "Informação sobre compartilhamento e recusa de consentimento (Art. 18, VII–VIII)",
    "Revogar consentimento a qualquer momento (Art. 18, IX)",
  ],
  GDPR: [
    "Acesso aos dados pessoais (Art. 15)",
    "Retificação de dados inexatos (Art. 16)",
    "Apagamento / direito ao esquecimento (Art. 17)",
    "Limitação do tratamento (Art. 18)",
    "Portabilidade dos dados (Art. 20)",
    "Oposição ao tratamento (Art. 21)",
    "Retirar consentimento sem prejuízo da licitude anterior (Art. 7(3))",
  ],
  UKGDPR: [
    "Os mesmos direitos previstos no UK GDPR e Data Protection Act 2018",
    "Reclamação junto ao ICO (Information Commissioner's Office)",
    "Portabilidade e acesso mediante solicitação ao DPO UK",
  ],
  CCPA: [
    "Saber quais categorias de dados pessoais coletamos e finalidades",
    "Acessar dados específicos coletados sobre você",
    "Solicitar exclusão de dados pessoais (com exceções legais)",
    "Corrigir dados pessoais inexatos (CPRA)",
    "Opt-out de venda ou compartilhamento de dados pessoais",
    "Não ser discriminado por exercer seus direitos",
  ],
  PIPEDA: [
    "Acesso às informações pessoais que mantemos sobre você",
    "Correção de informações inexatas ou incompletas",
    "Retirada de consentimento quando aplicável",
    "Reclamação junto ao Office of the Privacy Commissioner of Canada",
  ],
  APPI: [
    "Solicitar divulgação de finalidade de utilização",
    "Acesso, retificação e exclusão de dados pessoais retidos",
    "Suspensão de utilização ou eliminação quando tratamento violar a lei",
  ],
};

const STATIC_PROCESSORS = [
  { name: "InPost / DPD / DHL", role: "Redes locker UE", regions: "EU/UK" },
  { name: "CTT / Worten / El Corte Inglés", role: "Lockers e PUDO PT/ES", regions: "PT, ES" },
  { name: "Magalu / Mercado Livre / Correios", role: "Hubs e lockers BR", regions: "Brasil" },
  { name: "Amazon Hub / USPS", role: "Hub lockers EUA", regions: "US" },
  { name: "Stripe / AWS / SendGrid", role: "Pagamentos, cloud, e-mail", regions: "Global" },
  { name: "Intelipost / Melhor Envio", role: "Agregadores logísticos BR", regions: "Brasil" },
];

function formatDate(iso) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString("pt-BR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return null;
  }
}

export default function PublicPrivacyPolicyPage() {
  const [regulations, setRegulations] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [processors, setProcessors] = useState([]);
  const [lockerNetworks, setLockerNetworks] = useState([]);
  const [lockerSummary, setLockerSummary] = useState("");
  const [selectedCode, setSelectedCode] = useState("LGPD");
  const [loading, setLoading] = useState(true);
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [regR, polR, procR] = await Promise.all([
          fetch(`${PRIVACY_API}/regulations`),
          fetch(`${PRIVACY_API}/policy-versions`),
          fetch(`${PRIVACY_API}/processors`),
        ]);
        if (cancelled) return;
        const regJ = regR.ok ? await regR.json().catch(() => ({ items: [] })) : { items: [] };
        const polJ = polR.ok ? await polR.json().catch(() => ({ items: [] })) : { items: [] };
        const procJ = procR.ok ? await procR.json().catch(() => ({ items: [] })) : { items: [] };
        setRegulations(regJ.items || []);
        setPolicies(polJ.items || []);
        setProcessors(procJ.items || []);
        setApiOnline(regR.ok || polR.ok);
      } catch {
        if (!cancelled) setApiOnline(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadNetworks() {
      try {
        const netR = await fetch(
          `${PRIVACY_API}/locker-networks?regulation_code=${encodeURIComponent(selectedCode)}`,
        );
        if (cancelled || !netR.ok) return;
        const netJ = await netR.json().catch(() => ({ items: [] }));
        setLockerNetworks(netJ.items || []);
        setLockerSummary(netJ.summary || playersSummaryForRegulation(selectedCode) || "");
      } catch {
        if (!cancelled) {
          setLockerSummary(playersSummaryForRegulation(selectedCode) || "");
        }
      }
    }
    void loadNetworks();
    return () => {
      cancelled = true;
    };
  }, [selectedCode]);

  const selectedRegulation = useMemo(
    () => regulations.find((r) => r.code === selectedCode) || null,
    [regulations, selectedCode],
  );

  const currentPolicy = useMemo(() => {
    if (!selectedRegulation) return null;
    const matches = policies.filter((p) => p.regulation_id === selectedRegulation.id);
    return matches.find((p) => p.is_current) || matches[0] || null;
  }, [policies, selectedRegulation]);

  const relevantProcessors = useMemo(() => {
    if (!processors.length) return STATIC_PROCESSORS;
    return processors
      .filter((p) => {
        try {
          const codes = JSON.parse(p.regulation_codes_json || "[]");
          return codes.includes(selectedCode);
        } catch {
          return true;
        }
      })
      .map((p) => ({
        name: p.name,
        role: p.processor_type || "Subprocessador",
        regions: p.country || "—",
      }));
  }, [processors, selectedCode]);

  const rights = RIGHTS_BY_CODE[selectedCode] || RIGHTS_BY_CODE.GDPR;
  const lastUpdated = formatDate(currentPolicy?.effective_at) || "23 de Maio de 2026";
  const policyVersion = currentPolicy?.version || "3.0";
  const dpoEmail = selectedRegulation?.dpo_email || "privacidade@ellan.pt";
  const authority = selectedRegulation?.supervisory_authority || "Autoridade competente";
  const retentionDays = selectedRegulation?.default_retention_days || 365;
  const responseSla = selectedRegulation?.response_sla_days || 30;
  const policyDocPath = currentPolicy ? toInternalLegalPrivacyPath(currentPolicy.content_url) : null;

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <header style={headerStyle}>
          <div style={headerContentStyle}>
            <span style={badgeStyle}>Política de Privacidade</span>
            <h1 style={titleStyle}>Como protegemos seus dados</h1>
            <p style={subtitleStyle}>
              Plataforma ELLAN Lab Locker — comércio e retirada em redes globais (InPost, DHL, Magalu,
              Mercado Livre, Amazon Hub e parceiros). Tratamos dados pessoais conforme o marco aplicável à
              sua jurisdição.
            </p>
            <div style={metaInfoStyle}>
              <span>Última atualização: {loading ? "…" : lastUpdated}</span>
              <span>Versão {loading ? "…" : policyVersion}</span>
              {apiOnline ? <span style={liveBadgeStyle}>Catálogo compliance sincronizado</span> : null}
            </div>
          </div>
        </header>

        <section style={jurisdictionBarStyle} aria-label="Selecionar jurisdição">
          <p style={jurisdictionHintStyle}>Selecione sua região para ver bases legais, DPO e versão da política:</p>
          <div style={jurisdictionTabsStyle}>
            {JURISDICTION_OPTIONS.map((opt) => (
              <button
                key={opt.code}
                type="button"
                onClick={() => setSelectedCode(opt.code)}
                style={{
                  ...jurisdictionTabStyle,
                  ...(selectedCode === opt.code ? jurisdictionTabActiveStyle : {}),
                }}
                aria-pressed={selectedCode === opt.code}
              >
                <strong>{opt.label}</strong>
                <span style={jurisdictionTabSubStyle}>{opt.subtitle}</span>
              </button>
            ))}
          </div>
        </section>

        {(lockerSummary || lockerNetworks.length > 0) && (
          <section style={playersBarStyle} aria-label="Redes locker do marco selecionado">
            <h3 style={playersTitleStyle}>Redes locker — {selectedCode}</h3>
            {lockerSummary ? <p style={playersSummaryStyle}>{lockerSummary}</p> : null}
            {lockerNetworks.length > 0 ? (
              <ul style={playersListStyle}>
                {lockerNetworks.map((n) => (
                  <li key={n.code}>
                    <strong>{n.name}</strong> ({n.network_type}) — {n.countries?.join(", ")}
                  </li>
                ))}
              </ul>
            ) : (
              <ul style={playersListStyle}>
                {LOCKER_PLAYER_GROUPS.map((g) => (
                  <li key={g.label}>
                    <strong>{g.label}:</strong> {g.players.join(", ")}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {currentPolicy ? (
          <div style={policyBannerStyle}>
            <strong>{currentPolicy.title}</strong>
            {currentPolicy.summary ? <p style={policySummaryStyle}>{currentPolicy.summary}</p> : null}
            {policyDocPath ? (
              <Link to={policyDocPath} style={policyLinkStyle}>
                Documento completo ({currentPolicy.version})
              </Link>
            ) : currentPolicy.content_url ? (
              <a href={currentPolicy.content_url} style={policyLinkStyle} target="_blank" rel="noopener noreferrer">
                Documento completo ({currentPolicy.version})
              </a>
            ) : null}
          </div>
        ) : null}

        <div style={contentStyle}>
          <nav style={indexStyle} aria-label="Navegação rápida">
            <h3 style={indexTitleStyle}>Navegação rápida</h3>
            <ul style={indexListStyle}>
              {[
                ["#escopo", "Escopo e controlador"],
                ["#coleta-dados", "Coleta de dados"],
                ["#bases-legais", "Bases legais e finalidades"],
                ["#compartilhamento", "Subprocessadores"],
                ["#retencao", "Retenção"],
                ["#seguranca", "Segurança"],
                ["#direitos", "Seus direitos"],
                ["#cookies", "Cookies"],
                ["#contato", "DPO e contato"],
              ].map(([href, label]) => (
                <li key={href}>
                  <a href={href}>{label}</a>
                </li>
              ))}
            </ul>
          </nav>

          <div style={sectionsStyle}>
            <section id="escopo" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>1. Escopo e controlador</h2>
              <p style={paragraphStyle}>
                Esta política aplica-se ao uso da plataforma ELLAN Lab Locker — compra de produtos, pagamento,
                alocação de compartimentos, retirada em locker físico, emissão fiscal e suporte ao cliente.
              </p>
              {selectedRegulation ? (
                <div style={infoBoxStyle}>
                  <strong>Marco aplicável:</strong> {selectedRegulation.name} ({selectedRegulation.jurisdiction}
                  ). {selectedRegulation.description}
                </div>
              ) : (
                <p style={paragraphStyle}>
                  Marco selecionado: <strong>{selectedCode}</strong>. Resposta a solicitações de titulares em até{" "}
                  {responseSla} dias úteis.
                </p>
              )}
            </section>

            <section id="coleta-dados" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>2. Coleta de dados</h2>
              <p style={paragraphStyle}>Coletamos apenas o necessário para operar lockers e cumprir obrigações legais:</p>
              <ul style={listStyle}>
                <li>
                  <strong>Identificação e contato:</strong> nome, e-mail, telefone, CPF/CNPJ ou documento equivalente
                </li>
                <li>
                  <strong>Pedido e retirada:</strong> histórico de compras, código/QR de retirada, locker escolhido,
                  timestamps de abertura de compartimento
                </li>
                <li>
                  <strong>Pagamento:</strong> dados tokenizados por parceiros certificados (não armazenamos PAN completo)
                </li>
                <li>
                  <strong>Localização:</strong> aproximada para sugerir lockers próximos (InPost, DHL Packstation, redes BR)
                </li>
                <li>
                  <strong>Telemetria do dispositivo:</strong> IP, navegador, kiosk — com base em consentimento quando exigido
                </li>
                <li>
                  <strong>Fiscal:</strong> dados para NF-e / fatura conforme jurisdição (ex.: Brasil)
                </li>
              </ul>
            </section>

            <section id="bases-legais" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>3. Bases legais e finalidades</h2>
              <ul style={listStyle}>
                <li>Execução de contrato — processar pedido, pagamento e retirada no locker</li>
                <li>Consentimento — marketing, analytics e cookies não essenciais (revogável a qualquer momento)</li>
                <li>Interesse legítimo — prevenção a fraude, segurança operacional e melhoria do serviço</li>
                <li>Obrigação legal — retenção fiscal, resposta a autoridades e ordens judiciais</li>
                {selectedCode === "CCPA" ? (
                  <li>
                    <strong>CCPA/CPRA:</strong> notice at collection; opt-out de venda/compartilhamento de dados pessoais
                  </li>
                ) : null}
              </ul>
            </section>

            <section id="compartilhamento" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>4. Subprocessadores e compartilhamento</h2>
              <p style={paragraphStyle}>
                Compartilhamos dados apenas para operar o serviço, sempre com contratos de proteção (DPA/SCC quando
                aplicável). <strong>Não vendemos</strong> dados pessoais.
              </p>
              <ul style={listStyle}>
                {relevantProcessors.map((p) => (
                  <li key={p.name}>
                    <strong>{p.name}</strong> — {p.role} ({p.regions})
                  </li>
                ))}
              </ul>
              <p style={paragraphStyle}>
                Operadoras de rede locker, marketplaces (Magalu, Mercado Livre, Amazon Hub) e transportadoras recebem
                dados mínimos para entrega e retirada.
              </p>
            </section>

            <section id="retencao" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>5. Retenção</h2>
              <p style={paragraphStyle}>
                Prazo padrão para dados operacionais de retirada: <strong>{retentionDays} dias</strong>, salvo
                obrigação legal distinta (ex.: fiscal). Logs de segurança e auditoria podem ser mantidos por período
                adicional proporcional.
              </p>
            </section>

            <section id="seguranca" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>6. Segurança</h2>
              <div style={gridStyle}>
                {[
                  ["Criptografia TLS", "Dados em trânsito protegidos ponta a ponta"],
                  ["Controle de acesso", "Princípio do menor privilégio em OPS e backends"],
                  ["Tokenização", "Pagamentos via PSP certificado PCI-DSS"],
                  ["Monitoramento", "Detecção de incidentes e resposta conforme GDPR Art. 33 / LGPD Art. 48"],
                ].map(([title, desc]) => (
                  <div key={title} style={securityCardStyle}>
                    <strong>{title}</strong>
                    <p style={securityCardDescStyle}>{desc}</p>
                  </div>
                ))}
              </div>
            </section>

            <section id="direitos" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>7. Seus direitos ({selectedCode})</h2>
              <ul style={listStyle}>
                {rights.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              {selectedCode === "CCPA" ? (
                <div style={warningBoxStyle}>
                  <strong>Do Not Sell or Share:</strong> californianos podem optar por não vender ou compartilhar dados
                  pessoais. Envie solicitação para {dpoEmail} com assunto &quot;CCPA Opt-Out&quot;.
                </div>
              ) : null}
              <div style={contactBoxStyle}>
                <strong>Exercer direitos:</strong>{" "}
                <a href={`mailto:${dpoEmail}?subject=DSAR%20${selectedCode}`} style={contactLinkStyle}>
                  {dpoEmail}
                </a>
                {" · "}
                <Link to="/suporte" style={contactLinkStyle}>
                  Central de suporte
                </Link>
                <p style={slaHintStyle}>
                  Prazo de resposta: até {responseSla} dias · Autoridade supervisora: {authority}
                </p>
              </div>
            </section>

            <section id="cookies" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>8. Cookies e tecnologias similares</h2>
              <ul style={listStyle}>
                <li>
                  <strong>Essenciais:</strong> sessão, carrinho, autenticação e preferências de locker
                </li>
                <li>
                  <strong>Desempenho:</strong> métricas agregadas de uso (com consentimento quando exigido)
                </li>
                <li>
                  <strong>Marketing:</strong> somente com opt-in explícito (GDPR/LGPD) ou conforme CCPA/CPRA
                </li>
              </ul>
              <p style={paragraphStyle}>Gerencie preferências no navegador ou revogue consentimento via suporte.</p>
            </section>

            <section id="contato" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>9. Encarregado de proteção de dados (DPO)</h2>
              <div style={contactInfoStyle}>
                <div>
                  <strong>E-mail:</strong>{" "}
                  <a href={`mailto:${dpoEmail}`} style={contactLinkStyle}>
                    {dpoEmail}
                  </a>
                </div>
                <div>
                  <strong>Privacidade geral:</strong>{" "}
                  <a href="mailto:privacidade@ellan.pt" style={contactLinkStyle}>
                    privacidade@ellan.pt
                  </a>
                </div>
                <div>
                  <strong>Telefone:</strong> +351 253 079 738 (PT) · +55 11 3000-0000 (BR)
                </div>
                <div>
                  <strong>Horário:</strong> segunda a sexta, 9h–18h (fuso local do DPO responsável)
                </div>
              </div>
            </section>
          </div>

          <div style={acceptanceBoxStyle}>
            <p style={acceptanceTextStyle}>
              Ao utilizar nossos serviços, você declara ter lido esta política. Alterações relevantes serão
              comunicadas por e-mail ou aviso na plataforma, com registro de versão ({policyVersion}).
            </p>
          </div>
        </div>

        <div style={navigationButtonsStyle}>
          <Link to="/legal/privacy" style={secondaryButtonStyle}>
            Documentos legais completos
          </Link>
          <Link to="/termos" style={secondaryButtonStyle}>
            Termos de Uso
          </Link>
          <Link to="/suporte" style={secondaryButtonStyle}>
            Suporte / DSAR
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            Voltar ao início
          </Link>
        </div>
      </div>

      <style>{`
        html { scroll-behavior: smooth; }
        @media (max-width: 768px) {
          .security-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </main>
  );
}

const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%)",
  padding: "var(--spacing-4) 0",
};

const containerStyle = {
  maxWidth: "1000px",
  margin: "0 auto",
  padding: "0 var(--spacing-4)",
};

const headerStyle = {
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  borderRadius: "var(--radius-2xl)",
  padding: "var(--spacing-8)",
  marginBottom: "var(--spacing-4)",
  color: "white",
  textAlign: "center",
};

const headerContentStyle = { maxWidth: "800px", margin: "0 auto" };

const badgeStyle = {
  display: "inline-block",
  padding: "var(--spacing-1) var(--spacing-3)",
  background: "rgba(255,255,255,0.2)",
  borderRadius: "var(--radius-full)",
  fontSize: "var(--font-size-sm)",
  fontWeight: 600,
  marginBottom: "var(--spacing-3)",
};

const titleStyle = {
  fontSize: "var(--font-size-4xl)",
  fontWeight: 800,
  marginBottom: "var(--spacing-3)",
  lineHeight: 1.2,
};

const subtitleStyle = {
  fontSize: "var(--font-size-lg)",
  opacity: 0.95,
  lineHeight: 1.6,
  marginBottom: "var(--spacing-4)",
};

const metaInfoStyle = {
  display: "flex",
  justifyContent: "center",
  gap: "var(--spacing-4)",
  fontSize: "var(--font-size-sm)",
  opacity: 0.9,
  flexWrap: "wrap",
};

const liveBadgeStyle = {
  background: "rgba(16,185,129,0.35)",
  padding: "2px 10px",
  borderRadius: "999px",
};

const jurisdictionBarStyle = {
  background: "white",
  borderRadius: "var(--radius-xl)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-4)",
  boxShadow: "var(--shadow-sm)",
};

const jurisdictionHintStyle = {
  margin: "0 0 var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  color: "#64748b",
};

const jurisdictionTabsStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
  gap: "var(--spacing-2)",
};

const jurisdictionTabStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  gap: 2,
  padding: "var(--spacing-2) var(--spacing-3)",
  border: "2px solid #e2e8f0",
  borderRadius: "var(--radius-md)",
  background: "#f8fafc",
  cursor: "pointer",
  textAlign: "left",
  fontSize: "var(--font-size-sm)",
  color: "#334155",
};

const jurisdictionTabActiveStyle = {
  borderColor: "#667eea",
  background: "#eef2ff",
  color: "#4338ca",
};

const jurisdictionTabSubStyle = {
  fontSize: "11px",
  opacity: 0.75,
  fontWeight: 400,
};

const playersBarStyle = {
  background: "#f0fdf4",
  border: "1px solid #bbf7d0",
  borderRadius: "var(--radius-xl)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-4)",
};

const playersTitleStyle = {
  margin: "0 0 var(--spacing-2)",
  fontSize: "var(--font-size-base)",
  fontWeight: 700,
  color: "#166534",
};

const playersSummaryStyle = {
  margin: "0 0 var(--spacing-2)",
  fontSize: "var(--font-size-sm)",
  color: "#15803d",
  lineHeight: 1.5,
};

const playersListStyle = {
  margin: 0,
  paddingLeft: "var(--spacing-4)",
  fontSize: "var(--font-size-sm)",
  color: "#14532d",
  lineHeight: 1.6,
};

const policyBannerStyle = {
  background: "#eef2ff",
  border: "1px solid #c7d2fe",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-4)",
};

const policySummaryStyle = {
  margin: "var(--spacing-2) 0",
  fontSize: "var(--font-size-sm)",
  color: "#475569",
};

const policyLinkStyle = {
  color: "#4338ca",
  fontWeight: 600,
  fontSize: "var(--font-size-sm)",
};

const contentStyle = {
  background: "white",
  borderRadius: "var(--radius-2xl)",
  padding: "var(--spacing-8)",
  marginBottom: "var(--spacing-6)",
  boxShadow: "var(--shadow-md)",
};

const indexStyle = {
  background: "#f7fafc",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-6)",
  border: "1px solid #e2e8f0",
};

const indexTitleStyle = {
  fontSize: "var(--font-size-base)",
  fontWeight: 700,
  marginBottom: "var(--spacing-2)",
  color: "#2d3748",
};

const indexListStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "var(--spacing-2)",
  listStyle: "none",
  padding: 0,
  margin: 0,
};

const sectionsStyle = { display: "grid", gap: "var(--spacing-6)" };
const sectionStyle = { scrollMarginTop: "var(--spacing-8)" };

const sectionTitleStyle = {
  fontSize: "var(--font-size-2xl)",
  fontWeight: 700,
  color: "#2d3748",
  marginBottom: "var(--spacing-3)",
  paddingBottom: "var(--spacing-2)",
  borderBottom: "2px solid #e2e8f0",
};

const paragraphStyle = {
  fontSize: "var(--font-size-base)",
  lineHeight: 1.6,
  color: "#4a5568",
  marginBottom: "var(--spacing-3)",
};

const listStyle = {
  margin: "var(--spacing-3) 0",
  paddingLeft: "var(--spacing-5)",
  fontSize: "var(--font-size-base)",
  lineHeight: 1.6,
  color: "#4a5568",
};

const infoBoxStyle = {
  background: "#fef3c7",
  borderLeft: "4px solid #f59e0b",
  padding: "var(--spacing-3)",
  borderRadius: "var(--radius-md)",
  marginTop: "var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  color: "#92400e",
};

const warningBoxStyle = {
  background: "#fff7ed",
  borderLeft: "4px solid #ea580c",
  padding: "var(--spacing-3)",
  borderRadius: "var(--radius-md)",
  marginTop: "var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  color: "#9a3412",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: "var(--spacing-3)",
  marginTop: "var(--spacing-3)",
};

const securityCardStyle = {
  padding: "var(--spacing-3)",
  background: "#f7fafc",
  borderRadius: "var(--radius-lg)",
  textAlign: "left",
};

const securityCardDescStyle = {
  margin: "6px 0 0",
  fontSize: "var(--font-size-sm)",
  color: "#64748b",
};

const contactBoxStyle = {
  background: "#e0f2fe",
  borderLeft: "4px solid #0284c7",
  padding: "var(--spacing-3)",
  borderRadius: "var(--radius-md)",
  marginTop: "var(--spacing-3)",
};

const contactLinkStyle = { color: "#0284c7", fontWeight: 600, textDecoration: "none" };
const slaHintStyle = { margin: "8px 0 0", fontSize: "var(--font-size-sm)", color: "#0369a1" };

const contactInfoStyle = {
  background: "#f7fafc",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginTop: "var(--spacing-3)",
  display: "grid",
  gap: "var(--spacing-2)",
};

const acceptanceBoxStyle = {
  marginTop: "var(--spacing-6)",
  padding: "var(--spacing-4)",
  background: "#f0fdf4",
  borderRadius: "var(--radius-lg)",
  border: "1px solid #bbf7d0",
  textAlign: "center",
};

const acceptanceTextStyle = { margin: 0, fontSize: "var(--font-size-sm)", color: "#166534" };

const navigationButtonsStyle = {
  display: "flex",
  gap: "var(--spacing-3)",
  justifyContent: "center",
  flexWrap: "wrap",
};

const primaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-6)",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  textDecoration: "none",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
  display: "inline-block",
};

const secondaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-6)",
  background: "white",
  color: "#667eea",
  textDecoration: "none",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
  border: "2px solid #667eea",
  display: "inline-block",
};
