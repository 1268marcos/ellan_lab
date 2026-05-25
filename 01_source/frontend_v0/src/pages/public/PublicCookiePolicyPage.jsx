
import React, { useState } from "react";
import { Link } from "react-router-dom";

const LAST_UPDATED = "25 de Maio de 2026";
const POLICY_VERSION = "1.0";

const COOKIE_CATEGORIES = [
  {
    id: "essenciais",
    prefKey: "essential",
    title: "Essenciais (necessários)",
    required: true,
    description:
      "Indispensáveis para login, sessão, carrinho, checkout, seleção de locker e segurança da conta. Não podem ser desativados sem impactar o serviço.",
    examples: ["ellan_session", "ellan_auth", "locker_selection", "csrf_token", "cookie_consent"],
  },
  {
    id: "funcionais",
    prefKey: "functional",
    title: "Funcionais",
    required: false,
    description: "Memorizam preferências de idioma, região (BR/PT), tema e último locker utilizado.",
    examples: ["locale", "region_pref", "ui_theme"],
  },
  {
    id: "desempenho",
    prefKey: "analytics",
    title: "Desempenho e analytics",
    required: false,
    description:
      "Métricas agregadas de uso da plataforma (páginas visitadas, erros, tempo de carregamento). Ativados apenas com consentimento quando exigido por lei.",
    examples: ["_ga", "_gid", "ellan_analytics"],
  },
  {
    id: "marketing",
    prefKey: "marketing",
    title: "Marketing",
    required: false,
    description:
      "Campanhas, remarketing e medição de conversão. Requer opt-in explícito (LGPD/GDPR) ou mecanismo de opt-out (CCPA/CPRA).",
    examples: ["ellan_mkt", "utm_persist"],
  },
];

const THIRD_PARTY = [
  { name: "Stripe", purpose: "Pagamentos PCI-DSS", cookies: "stripe.com / __stripe_*" },
  { name: "AWS / CloudFront", purpose: "CDN e disponibilidade", cookies: "cloudfront.net" },
  { name: "SendGrid", purpose: "E-mail transacional", cookies: "sendgrid.net" },
  { name: "Google Analytics", purpose: "Analytics (se consentido)", cookies: "_ga, _gid" },
];

const STORAGE_KEYS = {
  essential: "ellan_cookie_essential",
  functional: "ellan_cookie_functional",
  analytics: "ellan_cookie_analytics",
  marketing: "ellan_cookie_marketing",
};

function readPref(key) {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

function writePref(key, on) {
  try {
    localStorage.setItem(key, on ? "1" : "0");
  } catch {
    /* ignore */
  }
}

export default function PublicCookiePolicyPage() {
  const [prefs, setPrefs] = useState({
    essential: true,
    functional: readPref(STORAGE_KEYS.functional),
    analytics: readPref(STORAGE_KEYS.analytics),
    marketing: readPref(STORAGE_KEYS.marketing),
  });
  const [saved, setSaved] = useState(false);

  const setAll = (allowOptional) => {
    const next = {
      essential: true,
      functional: allowOptional,
      analytics: allowOptional,
      marketing: allowOptional,
    };
    setPrefs(next);
    writePref(STORAGE_KEYS.functional, next.functional);
    writePref(STORAGE_KEYS.analytics, next.analytics);
    writePref(STORAGE_KEYS.marketing, next.marketing);
    setSaved(true);
  };

  const toggle = (key) => {
    if (key === "essential") return;
    const next = { ...prefs, [key]: !prefs[key] };
    setPrefs(next);
    writePref(STORAGE_KEYS[key], next[key]);
    setSaved(true);
  };

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <header style={headerStyle}>
          <div style={headerContentStyle}>
            <span style={badgeStyle}>Política de Cookies</span>
            <h1 style={titleStyle}>Cookies e tecnologias similares</h1>
            <p style={subtitleStyle}>
              ELLAN Lab Locker utiliza cookies e armazenamento local para operar compras, retirada em lockers
              (InPost, Magalu, Mercado Livre, CTT e parceiros) e cumprir LGPD, GDPR e demais marcos aplicáveis.
            </p>
            <div style={metaInfoStyle}>
              <span>Última atualização: {LAST_UPDATED}</span>
              <span>Versão {POLICY_VERSION}</span>
            </div>
          </div>
        </header>

        <section style={consentBarStyle} aria-label="Gerir preferências de cookies">
          <h2 style={consentTitleStyle}>Centro de preferências</h2>
          <p style={consentHintStyle}>
            Escolha quais categorias opcionais autoriza. Cookies essenciais permanecem ativos para o funcionamento
            do site.
          </p>
          <div style={consentActionsStyle}>
            <button type="button" style={primaryBtnStyle} onClick={() => setAll(true)}>
              Aceitar todos
            </button>
            <button type="button" style={secondaryBtnStyle} onClick={() => setAll(false)}>
              Apenas essenciais
            </button>
          </div>
          {saved ? <p style={savedStyle}>Preferências guardadas neste navegador.</p> : null}
        </section>

        <div style={contentStyle}>
          <nav style={indexStyle} aria-label="Navegação rápida">
            <h3 style={indexTitleStyle}>Navegação rápida</h3>
            <ul style={indexListStyle}>
              {[
                ["#o-que-sao", "O que são cookies"],
                ["#categorias", "Categorias"],
                ["#terceiros", "Terceiros"],
                ["#gestao", "Como gerir"],
                ["#direitos", "Seus direitos"],
                ["#contato", "Contato"],
              ].map(([href, label]) => (
                <li key={href}>
                  <a href={href}>{label}</a>
                </li>
              ))}
            </ul>
          </nav>

          <div style={sectionsStyle}>
            <section id="o-que-sao" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>1. O que são cookies</h2>
              <p style={paragraphStyle}>
                Cookies são pequenos ficheiros armazenados no seu dispositivo quando visita o nosso site ou
                aplicação. Também usamos localStorage e sessionStorage para preferências e tokens de sessão,
                tratados com o mesmo nível de proteção descrito na{" "}
                <Link to="/privacidade" style={inlineLinkStyle}>
                  Política de Privacidade
                </Link>
                .
              </p>
            </section>

            <section id="categorias" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>2. Categorias de cookies</h2>
              {COOKIE_CATEGORIES.map((cat) => (
                <div key={cat.id} style={categoryCardStyle}>
                  <div style={categoryHeaderStyle}>
                    <h3 style={categoryTitleStyle}>{cat.title}</h3>
                    {cat.required ? (
                      <span style={requiredBadgeStyle}>Sempre ativo</span>
                    ) : (
                      <label style={toggleLabelStyle}>
                        <input
                          type="checkbox"
                          checked={prefs[cat.prefKey]}
                          onChange={() => toggle(cat.prefKey)}
                          disabled={cat.required}
                        />
                        {prefs[cat.prefKey] ? "Ativo" : "Inativo"}
                      </label>
                    )}
                  </div>
                  <p style={paragraphStyle}>{cat.description}</p>
                  <p style={examplesStyle}>
                    <strong>Exemplos:</strong> {cat.examples.join(", ")}
                  </p>
                </div>
              ))}
            </section>

            <section id="terceiros" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>3. Cookies de terceiros</h2>
              <p style={paragraphStyle}>
                Parceiros de pagamento, infraestrutura e redes locker podem definir cookies próprios quando
                redirecionamos ou incorporamos os seus serviços:
              </p>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Fornecedor</th>
                    <th style={thStyle}>Finalidade</th>
                    <th style={thStyle}>Cookies</th>
                  </tr>
                </thead>
                <tbody>
                  {THIRD_PARTY.map((row) => (
                    <tr key={row.name}>
                      <td style={tdStyle}>{row.name}</td>
                      <td style={tdStyle}>{row.purpose}</td>
                      <td style={tdStyle}>{row.cookies}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section id="gestao" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>4. Como gerir cookies</h2>
              <ul style={listStyle}>
                <li>Use o centro de preferências no topo desta página</li>
                <li>Configure o seu navegador para bloquear ou apagar cookies (Chrome, Firefox, Safari, Edge)</li>
                <li>Em dispositivos móveis, consulte as definições de privacidade do sistema</li>
                <li>Revogue consentimento a qualquer momento — não afeta a licitude do tratamento anterior</li>
              </ul>
              <div style={infoBoxStyle}>
                <strong>Nota:</strong> desativar cookies essenciais pode impedir login, checkout ou abertura de
                compartimento no locker.
              </div>
            </section>

            <section id="direitos" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>5. Seus direitos</h2>
              <p style={paragraphStyle}>
                Nos termos da LGPD, GDPR, UK GDPR, CCPA/CPRA e PIPEDA, pode solicitar informação sobre
                tratamento de dados, retificação, eliminação e oposição. Para exercer direitos relacionados a
                cookies e rastreamento:
              </p>
              <ul style={listStyle}>
                <li>E-mail: privacidade@ellan.pt</li>
                <li>
                  <Link to="/suporte" style={inlineLinkStyle}>
                    Central de Suporte / DSAR
                  </Link>
                </li>
                <li>
                  <Link to="/privacidade" style={inlineLinkStyle}>
                    Política de Privacidade completa
                  </Link>
                </li>
              </ul>
            </section>

            <section id="contato" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>6. Contacto do encarregado (DPO)</h2>
              <div style={contactInfoStyle}>
                <div>
                  <strong>E-mail:</strong>{" "}
                  <a href="mailto:privacidade@ellan.pt" style={contactLinkStyle}>
                    privacidade@ellan.pt
                  </a>
                </div>
                <div>
                  <strong>Horário:</strong> segunda a sexta, 9h–18h (Lisboa / São Paulo)
                </div>
              </div>
            </section>
          </div>

          <div style={acceptanceBoxStyle}>
            <p style={acceptanceTextStyle}>
              Ao continuar a navegar após configurar preferências, você concorda com esta política de cookies
              (versão {POLICY_VERSION}). Alterações serão publicadas nesta página.
            </p>
          </div>
        </div>

        <div style={navigationButtonsStyle}>
          <Link to="/privacidade" style={secondaryButtonStyle}>
            Política de Privacidade
          </Link>
          <Link to="/termos" style={secondaryButtonStyle}>
            Termos de Uso
          </Link>
          <Link to="/suporte" style={secondaryButtonStyle}>
            Suporte
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            Voltar ao início
          </Link>
        </div>
      </div>

      <style>{`html { scroll-behavior: smooth; }`}</style>
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
  background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
  borderRadius: "var(--radius-2xl)",
  padding: "var(--spacing-8)",
  marginBottom: "var(--spacing-6)",
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

const consentBarStyle = {
  background: "white",
  borderRadius: "var(--radius-xl)",
  padding: "var(--spacing-5)",
  marginBottom: "var(--spacing-4)",
  boxShadow: "var(--shadow-sm)",
  border: "1px solid #fde68a",
};

const consentTitleStyle = { margin: "0 0 var(--spacing-2)", fontSize: "var(--font-size-xl)", color: "#92400e" };
const consentHintStyle = { margin: "0 0 var(--spacing-3)", fontSize: "var(--font-size-sm)", color: "#64748b" };
const consentActionsStyle = { display: "flex", flexWrap: "wrap", gap: "var(--spacing-2)" };
const savedStyle = { margin: "var(--spacing-3) 0 0", fontSize: "var(--font-size-sm)", color: "#15803d" };

const primaryBtnStyle = {
  padding: "var(--spacing-2) var(--spacing-4)",
  background: "#d97706",
  color: "white",
  border: "none",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
  cursor: "pointer",
};

const secondaryBtnStyle = {
  padding: "var(--spacing-2) var(--spacing-4)",
  background: "#f8fafc",
  color: "#334155",
  border: "2px solid #e2e8f0",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
  cursor: "pointer",
};

const contentStyle = {
  background: "white",
  borderRadius: "var(--radius-2xl)",
  padding: "var(--spacing-8)",
  marginBottom: "var(--spacing-6)",
  boxShadow: "var(--shadow-md)",
};

const indexStyle = {
  background: "#fffbeb",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-6)",
  border: "1px solid #fde68a",
};

const indexTitleStyle = {
  fontSize: "var(--font-size-base)",
  fontWeight: 700,
  marginBottom: "var(--spacing-2)",
  color: "#78350f",
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
  borderBottom: "2px solid #fde68a",
};

const paragraphStyle = { fontSize: "var(--font-size-base)", lineHeight: 1.7, color: "#4a5568", marginBottom: "var(--spacing-3)" };
const listStyle = { paddingLeft: "var(--spacing-5)", lineHeight: 1.8, color: "#4a5568", marginBottom: "var(--spacing-3)" };
const inlineLinkStyle = { color: "#d97706", fontWeight: 600 };

const categoryCardStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-3)",
  background: "#fafafa",
};

const categoryHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  flexWrap: "wrap",
  gap: "var(--spacing-2)",
  marginBottom: "var(--spacing-2)",
};

const categoryTitleStyle = { margin: 0, fontSize: "var(--font-size-lg)", color: "#1e293b" };
const requiredBadgeStyle = {
  fontSize: "var(--font-size-xs)",
  background: "#fef3c7",
  color: "#92400e",
  padding: "2px 10px",
  borderRadius: "999px",
  fontWeight: 600,
};

const toggleLabelStyle = { fontSize: "var(--font-size-sm)", display: "flex", alignItems: "center", gap: 8, cursor: "pointer" };
const examplesStyle = { fontSize: "var(--font-size-sm)", color: "#64748b", margin: 0 };

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: "var(--font-size-sm)", marginTop: "var(--spacing-2)" };
const thStyle = { textAlign: "left", padding: "var(--spacing-2)", borderBottom: "2px solid #e2e8f0", color: "#334155" };
const tdStyle = { padding: "var(--spacing-2)", borderBottom: "1px solid #f1f5f9", color: "#475569" };

const infoBoxStyle = {
  background: "#fffbeb",
  border: "1px solid #fde68a",
  borderRadius: "var(--radius-md)",
  padding: "var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  color: "#78350f",
};

const contactInfoStyle = {
  background: "#f8fafc",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  display: "grid",
  gap: "var(--spacing-2)",
};

const contactLinkStyle = { color: "#d97706", fontWeight: 600 };

const acceptanceBoxStyle = {
  background: "#fffbeb",
  border: "2px solid #fde68a",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginTop: "var(--spacing-6)",
};

const acceptanceTextStyle = { margin: 0, fontSize: "var(--font-size-sm)", color: "#78350f", lineHeight: 1.6 };

const navigationButtonsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "var(--spacing-3)",
  justifyContent: "center",
  marginBottom: "var(--spacing-8)",
};

const secondaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-5)",
  background: "white",
  color: "#d97706",
  border: "2px solid #d97706",
  borderRadius: "var(--radius-lg)",
  textDecoration: "none",
  fontWeight: 600,
  fontSize: "var(--font-size-sm)",
};

const primaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-5)",
  background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
  color: "white",
  border: "none",
  borderRadius: "var(--radius-lg)",
  textDecoration: "none",
  fontWeight: 600,
  fontSize: "var(--font-size-sm)",
};
