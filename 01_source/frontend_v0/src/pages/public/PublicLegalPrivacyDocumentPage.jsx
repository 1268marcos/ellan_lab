
import React from "react";
import { Link, useParams } from "react-router-dom";
import { getLegalPrivacyDocument, listLegalPrivacyDocuments } from "../../data/legalPrivacyDocuments";

function Block({ block }) {
  if (block.type === "p") return <p style={paragraphStyle}>{block.text}</p>;
  if (block.type === "ul") {
    return (
      <ul style={listStyle}>
        {block.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    );
  }
  if (block.type === "notice") {
    return <div style={noticeStyle}>{block.text}</div>;
  }
  return null;
}

export function PublicLegalPrivacyIndexPage() {
  const docs = listLegalPrivacyDocuments();

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <header style={headerStyle}>
          <span style={badgeStyle}>Documentos legais</span>
          <h1 style={titleStyle}>Políticas de privacidade por jurisdição</h1>
          <p style={subtitleStyle}>
            Textos completos versionados para GDPR, LGPD, CCPA, PIPEDA, APPI, PDPA e demais marcos.
          </p>
        </header>
        <div style={contentStyle}>
          <ul style={docListStyle}>
            {docs.map((doc) => (
              <li key={doc.slug} style={docItemStyle}>
                <Link to={`/legal/privacy/${doc.slug}`} style={docLinkStyle}>
                  <strong>{doc.title}</strong>
                  <span style={docMetaStyle}>
                    {doc.regulation} · v{doc.version} · {doc.jurisdiction}
                  </span>
                  {doc.summary ? <span style={docSummaryStyle}>{doc.summary}</span> : null}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div style={navStyle}>
          <Link to="/legal/privacy/players" style={secondaryButtonStyle}>
            Documentos por player
          </Link>
          <Link to="/privacidade" style={secondaryButtonStyle}>
            Resumo público
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            Início
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function PublicLegalPrivacyDocumentPage() {
  const { region, version } = useParams();
  const doc = getLegalPrivacyDocument(region, version);

  if (!doc) {
    return (
      <main style={pageStyle}>
        <div style={containerStyle}>
          <div style={contentStyle}>
            <h1 style={{ ...titleStyle, color: "#2d3748" }}>Documento não encontrado</h1>
            <p style={paragraphStyle}>
              Não existe política em <code>/legal/privacy/{region}/{version}</code>.
            </p>
            <Link to="/legal/privacy" style={primaryButtonStyle}>
              Ver índice de documentos
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main style={pageStyle} lang={doc.language === "pt" ? "pt-BR" : "en"}>
      <div style={containerStyle}>
        <header style={headerStyle}>
          <span style={badgeStyle}>{doc.regulation}</span>
          <h1 style={titleStyle}>{doc.title}</h1>
          {doc.summary ? <p style={subtitleStyle}>{doc.summary}</p> : null}
          <div style={metaInfoStyle}>
            <span>Versão {doc.version}</span>
            <span>{doc.jurisdiction}</span>
            <span>Vigência: {doc.effectiveDate}</span>
          </div>
        </header>

        <nav style={indexStyle} aria-label="Índice do documento">
          <h2 style={indexTitleStyle}>Índice</h2>
          <ul style={indexListStyle}>
            {doc.sections.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`}>{s.title}</a>
              </li>
            ))}
          </ul>
        </nav>

        <article style={contentStyle}>
          {doc.sections.map((s) => (
            <section key={s.id} id={s.id} style={sectionStyle}>
              <h2 style={sectionTitleStyle}>{s.title}</h2>
              {s.blocks.map((block, i) => (
                <Block key={`${s.id}-${i}`} block={block} />
              ))}
            </section>
          ))}

          <footer style={docFooterStyle}>
            <p style={paragraphStyle}>
              DPO / privacidade:{" "}
              <a href={`mailto:${doc.dpoEmail}`} style={inlineLinkStyle}>
                {doc.dpoEmail}
              </a>
            </p>
            <p style={footerNoteStyle}>
              Documento gerado para ELLAN Lab Locker · {doc.slug} · não constitui aconselhamento jurídico.
            </p>
          </footer>
        </article>

        <div style={navStyle}>
          <Link to="/legal/privacy" style={secondaryButtonStyle}>
            Todos os documentos
          </Link>
          <Link to="/privacidade" style={secondaryButtonStyle}>
            Resumo /privacidade
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            Início
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
  maxWidth: "900px",
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
  fontSize: "var(--font-size-3xl)",
  fontWeight: 800,
  marginBottom: "var(--spacing-3)",
  lineHeight: 1.2,
  color: "inherit",
};

const subtitleStyle = {
  fontSize: "var(--font-size-lg)",
  opacity: 0.95,
  lineHeight: 1.6,
  marginBottom: "var(--spacing-3)",
};

const metaInfoStyle = {
  display: "flex",
  justifyContent: "center",
  gap: "var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  opacity: 0.9,
  flexWrap: "wrap",
};

const indexStyle = {
  background: "white",
  borderRadius: "var(--radius-lg)",
  padding: "var(--spacing-4)",
  marginBottom: "var(--spacing-4)",
  boxShadow: "var(--shadow-sm)",
  border: "1px solid #e2e8f0",
};

const indexTitleStyle = {
  margin: "0 0 var(--spacing-2)",
  fontSize: "var(--font-size-base)",
  fontWeight: 700,
};

const indexListStyle = {
  margin: 0,
  paddingLeft: "var(--spacing-4)",
  lineHeight: 1.8,
  fontSize: "var(--font-size-sm)",
};

const contentStyle = {
  background: "white",
  borderRadius: "var(--radius-2xl)",
  padding: "var(--spacing-8)",
  marginBottom: "var(--spacing-6)",
  boxShadow: "var(--shadow-md)",
};

const sectionStyle = {
  scrollMarginTop: "var(--spacing-8)",
  marginBottom: "var(--spacing-6)",
  paddingBottom: "var(--spacing-4)",
  borderBottom: "1px solid #e2e8f0",
};

const sectionTitleStyle = {
  fontSize: "var(--font-size-xl)",
  fontWeight: 700,
  color: "#2d3748",
  marginBottom: "var(--spacing-3)",
};

const paragraphStyle = {
  fontSize: "var(--font-size-base)",
  lineHeight: 1.7,
  color: "#4a5568",
  marginBottom: "var(--spacing-3)",
};

const listStyle = {
  margin: "var(--spacing-2) 0 var(--spacing-3)",
  paddingLeft: "var(--spacing-5)",
  lineHeight: 1.7,
  color: "#4a5568",
};

const noticeStyle = {
  background: "#fef3c7",
  borderLeft: "4px solid #f59e0b",
  padding: "var(--spacing-3)",
  borderRadius: "var(--radius-md)",
  marginBottom: "var(--spacing-3)",
  fontSize: "var(--font-size-sm)",
  color: "#92400e",
};

const docFooterStyle = {
  marginTop: "var(--spacing-6)",
  paddingTop: "var(--spacing-4)",
  borderTop: "2px solid #e2e8f0",
};

const footerNoteStyle = {
  fontSize: "var(--font-size-sm)",
  color: "#64748b",
  margin: 0,
};

const inlineLinkStyle = { color: "#0284c7", fontWeight: 600 };

const navStyle = {
  display: "flex",
  gap: "var(--spacing-3)",
  justifyContent: "center",
  flexWrap: "wrap",
  marginBottom: "var(--spacing-6)",
};

const primaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-5)",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  textDecoration: "none",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
};

const secondaryButtonStyle = {
  padding: "var(--spacing-3) var(--spacing-5)",
  background: "white",
  color: "#667eea",
  textDecoration: "none",
  borderRadius: "var(--radius-md)",
  fontWeight: 600,
  border: "2px solid #667eea",
};

const docListStyle = { listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 12 };

const docItemStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: "var(--radius-lg)",
  overflow: "hidden",
};

const docLinkStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  padding: "var(--spacing-4)",
  textDecoration: "none",
  color: "#1e293b",
};

const docMetaStyle = { fontSize: "var(--font-size-sm)", color: "#64748b" };
const docSummaryStyle = { fontSize: "var(--font-size-sm)", color: "#475569", marginTop: 4 };
