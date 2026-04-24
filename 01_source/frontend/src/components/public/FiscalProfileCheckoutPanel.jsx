// Painel guiado: perfil fiscal mínimo (PUT /public/auth/me/fiscal-profile)

import React, { useEffect, useMemo, useState } from "react";
import { upsertPublicFiscalProfile } from "../../services/authApi";

const labelStyle = { display: "block", fontWeight: 600, marginBottom: 6, color: "#0f172a" };
const inputStyle = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #cbd5e1",
  fontSize: 14,
  boxSizing: "border-box",
};
const gridStyle = { display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" };
const noticeStyle = {
  background: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: 10,
  padding: 12,
  marginBottom: 14,
  fontSize: 13,
  color: "#334155",
};

export default function FiscalProfileCheckoutPanel({ token, user, fiscalCountry, onSaved }) {
  const docTypeDefault = fiscalCountry === "PT" ? "NIF" : "CPF";
  const [taxCountry, setTaxCountry] = useState(fiscalCountry);
  const [taxDocumentType, setTaxDocumentType] = useState(docTypeDefault);
  const [taxDocumentValue, setTaxDocumentValue] = useState("");
  const [fiscalEmail, setFiscalEmail] = useState("");
  const [fiscalPhone, setFiscalPhone] = useState("");
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [city, setCity] = useState("");
  const [stateField, setStateField] = useState("");
  const [postal, setPostal] = useState("");
  const [addrCountry, setAddrCountry] = useState(fiscalCountry);
  const [consent, setConsent] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setTaxCountry(fiscalCountry);
    setTaxDocumentType(fiscalCountry === "PT" ? "NIF" : "CPF");
    setAddrCountry(fiscalCountry);
  }, [fiscalCountry]);

  useEffect(() => {
    if (!user) return;
    setFiscalEmail(user.fiscal_email || user.email || "");
    setFiscalPhone(user.fiscal_phone || user.phone || "");
    setTaxDocumentValue(user.tax_document_value || "");
    setLine1(user.fiscal_address_line1 || "");
    setLine2(user.fiscal_address_line2 || "");
    setCity(user.fiscal_address_city || "");
    setStateField(user.fiscal_address_state || "");
    setPostal(user.fiscal_address_postal_code || "");
    if (user.tax_country) setTaxCountry(String(user.tax_country).toUpperCase());
    if (user.tax_document_type) setTaxDocumentType(String(user.tax_document_type).toUpperCase());
    if (user.fiscal_address_country) setAddrCountry(String(user.fiscal_address_country).toUpperCase());
    setConsent(Boolean(user.fiscal_data_consent));
  }, [user]);

  const pct = useMemo(() => Number(user?.fiscal_profile_completeness ?? 0), [user]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await upsertPublicFiscalProfile(token, {
        tax_country: taxCountry,
        tax_document_type: taxDocumentType,
        tax_document_value: taxDocumentValue,
        fiscal_email: fiscalEmail,
        fiscal_phone: fiscalPhone || null,
        fiscal_address_line1: line1,
        fiscal_address_line2: line2 || null,
        fiscal_address_city: city,
        fiscal_address_state: stateField,
        fiscal_address_postal_code: postal,
        fiscal_address_country: addrCountry,
        fiscal_data_consent: consent,
      });
      if (typeof onSaved === "function") await onSaved();
    } catch (err) {
      setError(err?.message || "Não foi possível salvar o perfil fiscal.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ marginTop: 16, marginBottom: 8 }}>
      <h3 style={{ margin: "0 0 8px 0", fontSize: 16, color: "#0f172a" }}>Nota fiscal — dados do destinatário</h3>
      <div style={noticeStyle}>
        <strong>Completude: {pct}%</strong>
        <p style={{ margin: "8px 0 0 0" }}>
          Para emissão em ambiente com provedor fiscal real, é obrigatório perfil completo (documento, endereço e
          consentimento). Em modo stub de laboratório isso não bloqueia testes.
        </p>
      </div>

      {error ? (
        <div style={{ color: "#b91c1c", marginBottom: 10, fontSize: 13 }}>{error}</div>
      ) : null}

      <form onSubmit={handleSubmit}>
        <div style={gridStyle}>
          <label style={labelStyle}>
            País fiscal
            <select value={taxCountry} onChange={(e) => setTaxCountry(e.target.value)} style={inputStyle}>
              <option value="BR">Brasil</option>
              <option value="PT">Portugal</option>
            </select>
          </label>
          <label style={labelStyle}>
            Documento
            <select value={taxDocumentType} onChange={(e) => setTaxDocumentType(e.target.value)} style={inputStyle}>
              {taxCountry === "PT" ? <option value="NIF">NIF</option> : <option value="CPF">CPF</option>}
            </select>
          </label>
        </div>

        <label style={{ ...labelStyle, marginTop: 4 }}>
          {taxDocumentType === "NIF" ? "NIF (9 dígitos)" : "CPF (11 dígitos)"}
          <input value={taxDocumentValue} onChange={(e) => setTaxDocumentValue(e.target.value)} style={inputStyle} />
        </label>

        <div style={gridStyle}>
          <label style={labelStyle}>
            E-mail da nota
            <input
              type="email"
              value={fiscalEmail}
              onChange={(e) => setFiscalEmail(e.target.value)}
              style={inputStyle}
              required
            />
          </label>
          <label style={labelStyle}>
            Telefone (opcional)
            <input value={fiscalPhone} onChange={(e) => setFiscalPhone(e.target.value)} style={inputStyle} />
          </label>
        </div>

        <label style={labelStyle}>
          Logradouro e número
          <input value={line1} onChange={(e) => setLine1(e.target.value)} style={inputStyle} required />
        </label>
        <label style={labelStyle}>
          Complemento (opcional)
          <input value={line2} onChange={(e) => setLine2(e.target.value)} style={inputStyle} />
        </label>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Cidade
            <input value={city} onChange={(e) => setCity(e.target.value)} style={inputStyle} required />
          </label>
          <label style={labelStyle}>
            {taxCountry === "BR" ? "UF" : "Distrito / região"}
            <input value={stateField} onChange={(e) => setStateField(e.target.value)} style={inputStyle} required />
          </label>
        </div>

        <div style={gridStyle}>
          <label style={labelStyle}>
            {taxCountry === "BR" ? "CEP" : "Código postal"}
            <input value={postal} onChange={(e) => setPostal(e.target.value)} style={inputStyle} required />
          </label>
          <label style={labelStyle}>
            País do endereço
            <select value={addrCountry} onChange={(e) => setAddrCountry(e.target.value)} style={inputStyle}>
              <option value="BR">BR</option>
              <option value="PT">PT</option>
            </select>
          </label>
        </div>

        <label style={{ ...labelStyle, display: "flex", alignItems: "flex-start", gap: 8, marginTop: 10 }}>
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 3 }} />
          <span>Autorizo o uso destes dados para emissão e entrega de documentos fiscais conforme a legislação aplicável.</span>
        </label>

        <button
          type="submit"
          disabled={saving || !consent}
          style={{
            marginTop: 14,
            width: "100%",
            padding: "12px 16px",
            borderRadius: 10,
            border: "none",
            background: saving ? "#94a3b8" : "#0f766e",
            color: "#fff",
            fontWeight: 700,
            cursor: saving ? "default" : "pointer",
          }}
        >
          {saving ? "Salvando perfil fiscal…" : "Salvar perfil fiscal e continuar"}
        </button>
      </form>
    </div>
  );
}
