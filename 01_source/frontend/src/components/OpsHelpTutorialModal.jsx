import React, { useEffect, useMemo, useState } from "react";

function HelpButton({ onClick, label = "Abrir tutorial da página", hiddenByPreference = false }) {
  return (
    <div style={helpCtaWrapStyle}>
      <span style={hiddenByPreference ? helpBadgeMutedStyle : helpBadgeStyle}>Ajuda</span>
      <button
        type="button"
        aria-label={label}
        title={label}
        onClick={onClick}
        style={hiddenByPreference ? helpButtonMutedStyle : helpButtonStyle}
      >
        ?
      </button>
    </div>
  );
}

function TutorialModal({ open, onClose, title, subtitle, sections = [], ctaLabel, ctaHref, preferenceControl }) {
  const normalizedSections = useMemo(() => {
    return Array.isArray(sections) ? sections.filter((section) => section && Array.isArray(section.items)) : [];
  }, [sections]);

  useEffect(() => {
    if (!open) return undefined;
    function handleEscape(event) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div role="presentation" style={overlayStyle} onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label={title} style={modalStyle} onClick={(event) => event.stopPropagation()}>
        <div style={modalHeaderStyle}>
          <div>
            <h2 style={modalTitleStyle}>{title}</h2>
            {subtitle ? <p style={modalSubtitleStyle}>{subtitle}</p> : null}
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle} aria-label="Fechar tutorial">
            Fechar
          </button>
        </div>
        <div style={modalBodyStyle}>
          {normalizedSections.map((section) => (
            <section key={section.title} style={sectionStyle}>
              <h3 style={sectionTitleStyle}>{section.title}</h3>
              <ol style={sectionListStyle}>
                {section.items.map((item, idx) => (
                  <li key={`${section.title}-${idx}`} style={sectionItemStyle}>
                    {item}
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
        <div style={footerAreaStyle}>
          {preferenceControl}
          {ctaLabel && ctaHref ? (
            <a href={ctaHref} style={ctaLinkStyle}>
              {ctaLabel}
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function OpsHelpTutorialModal({
  title,
  subtitle,
  sections,
  ctaLabel,
  ctaHref,
  storageKey,
  userKey = "anonymous",
}) {
  const [open, setOpen] = useState(false);
  const preferenceStorageKey = useMemo(() => {
    const safeScope = String(storageKey || "default").trim() || "default";
    const safeUser = String(userKey || "anonymous").trim() || "anonymous";
    return `ops:tutorial:hidden:v1:${safeUser}:${safeScope}`;
  }, [storageKey, userKey]);
  const [hideAgain, setHideAgain] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(preferenceStorageKey);
      setHideAgain(saved === "1");
    } catch {
      setHideAgain(false);
    }
  }, [preferenceStorageKey]);

  function handlePreferenceChange(nextValue) {
    setHideAgain(Boolean(nextValue));
    try {
      if (nextValue) {
        window.localStorage.setItem(preferenceStorageKey, "1");
      } else {
        window.localStorage.removeItem(preferenceStorageKey);
      }
    } catch {
      // Ignore localStorage errors in restricted environments.
    }
  }

  return (
    <>
      <HelpButton
        onClick={() => setOpen(true)}
        hiddenByPreference={hideAgain}
        label={hideAgain ? "Abrir tutorial (marcado como não mostrar novamente)" : "Abrir tutorial da página"}
      />
      <TutorialModal
        open={open}
        onClose={() => setOpen(false)}
        title={title}
        subtitle={subtitle}
        sections={sections}
        ctaLabel={ctaLabel}
        ctaHref={ctaHref}
        preferenceControl={
          <label style={hideToggleStyle}>
            <input
              type="checkbox"
              checked={hideAgain}
              onChange={(event) => handlePreferenceChange(event.target.checked)}
            />{" "}
            Não mostrar novamente nesta página para este usuário
          </label>
        }
      />
    </>
  );
}

const helpButtonStyle = {
  width: 30,
  height: 30,
  borderRadius: 999,
  border: "1px solid rgba(125,211,252,0.7)",
  background: "rgba(14,116,144,0.2)",
  color: "#bae6fd",
  fontWeight: 900,
  cursor: "pointer",
  lineHeight: 1,
  fontSize: 16,
};

const helpButtonMutedStyle = {
  ...helpButtonStyle,
  border: "1px solid rgba(148,163,184,0.6)",
  background: "rgba(30,41,59,0.35)",
  color: "#cbd5e1",
};

const helpCtaWrapStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
};

const helpBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  border: "1px solid rgba(125,211,252,0.72)",
  background: "rgba(14,116,144,0.18)",
  color: "#bae6fd",
  fontSize: 11,
  fontWeight: 800,
  padding: "4px 8px",
  lineHeight: 1,
  letterSpacing: 0.2,
};

const helpBadgeMutedStyle = {
  ...helpBadgeStyle,
  border: "1px solid rgba(148,163,184,0.5)",
  background: "rgba(30,41,59,0.35)",
  color: "#cbd5e1",
};

const overlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(2, 6, 23, 0.72)",
  display: "grid",
  placeItems: "center",
  zIndex: 1300,
  padding: 16,
};

const modalStyle = {
  width: "min(760px, 100%)",
  maxHeight: "86vh",
  overflow: "auto",
  borderRadius: 14,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "#0b1220",
  color: "#e2e8f0",
  padding: 14,
  display: "grid",
  gap: 12,
};

const modalHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 10,
};

const modalTitleStyle = {
  margin: 0,
  fontSize: 18,
};

const modalSubtitleStyle = {
  margin: "6px 0 0",
  color: "#cbd5e1",
  fontSize: 13,
};

const closeButtonStyle = {
  border: "1px solid rgba(148,163,184,0.5)",
  background: "transparent",
  color: "#e2e8f0",
  borderRadius: 8,
  padding: "6px 10px",
  cursor: "pointer",
  fontWeight: 700,
};

const modalBodyStyle = {
  display: "grid",
  gap: 10,
};

const sectionStyle = {
  border: "1px solid rgba(148,163,184,0.28)",
  borderRadius: 10,
  background: "rgba(15,23,42,0.55)",
  padding: 10,
};

const sectionTitleStyle = {
  margin: "0 0 8px",
  fontSize: 13,
  color: "#bfdbfe",
};

const sectionListStyle = {
  margin: 0,
  paddingLeft: 18,
  display: "grid",
  gap: 4,
};

const sectionItemStyle = {
  fontSize: 13,
  color: "#e2e8f0",
};

const ctaLinkStyle = {
  color: "#93c5fd",
  textDecoration: "none",
  fontSize: 13,
  fontWeight: 700,
};

const footerAreaStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap",
};

const hideToggleStyle = {
  border: "1px solid rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.65)",
  color: "#e2e8f0",
  borderRadius: 10,
  padding: "8px 10px",
  fontSize: 12,
};
