import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

function isDevBypassEnabled() {
  return String(import.meta.env.VITE_DEV_BYPASS_AUTH || "").toLowerCase() === "true";
}

function getAllowedRoleSet() {
  const raw =
    String(import.meta.env.VITE_BASE_CATALOG_ALLOWED_ROLES || "").trim() ||
    "LOCKER_SLOT_MANAGER,ADMIN";
  return new Set(
    raw
      .split(",")
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean)
  );
}

function userRolesFromProfile(user) {
  if (!user) return [];
  if (Array.isArray(user.roles)) return user.roles.map((item) => String(item));
  if (typeof user.role === "string") return [user.role];
  if (typeof user.category === "string") return [user.category];
  if (Array.isArray(user.categories)) return user.categories.map((item) => String(item));
  return [];
}

async function readJson(res) {
  return res.json().catch(() => ({}));
}

export default function DevBaseCatalogPage() {
  const { user, token } = useAuth();
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [overview, setOverview] = useState(null);
  const [enums, setEnums] = useState([]);
  const [tables, setTables] = useState([]);
  const [countries, setCountries] = useState([]);
  const [provinces, setProvinces] = useState([]);
  const [products, setProducts] = useState([]);
  const [lockerLocations, setLockerLocations] = useState([]);

  const [countryFilter, setCountryFilter] = useState("");
  const [provinceFilter, setProvinceFilter] = useState("");
  const [provinceCountryFilter, setProvinceCountryFilter] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [lockerLocationFilter, setLockerLocationFilter] = useState("");
  const [lockerLocationCountryFilter, setLockerLocationCountryFilter] = useState("");
  const [lockerLocationProvinceFilter, setLockerLocationProvinceFilter] = useState("");

  const [countryForm, setCountryForm] = useState({
    code: "",
    name: "",
    continent: "",
    default_currency: "",
    default_timezone: "",
    address_format: "",
    is_active: true,
  });
  const [provinceForm, setProvinceForm] = useState({
    code: "",
    name: "",
    country_code: "",
    province_code_original: "",
    region: "",
    timezone: "",
    is_active: true,
  });
  const [productForm, setProductForm] = useState({
    id: "",
    name: "",
    amount_cents: 0,
    currency: "BRL",
    description: "",
    is_active: true,
  });
  const [lockerLocationForm, setLockerLocationForm] = useState({
    external_id: "",
    province_code: "",
    city_name: "",
    district: "",
    postal_code: "",
    latitude: "",
    longitude: "",
    timezone: "",
    address_street: "",
    address_number: "",
    address_complement: "",
    is_active: true,
  });

  const allowedRoles = useMemo(() => getAllowedRoleSet(), []);
  const currentRoles = useMemo(() => userRolesFromProfile(user), [user]);
  const canAccess = useMemo(() => {
    if (isDevBypassEnabled()) return true;
    const normalized = currentRoles.map((item) => item.trim().toUpperCase());
    return normalized.some((role) => allowedRoles.has(role));
  }, [allowedRoles, currentRoles]);

  async function runRequest(url, options = {}) {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const mergedHeaders = {
        ...(options.headers || {}),
      };
      if (token) {
        mergedHeaders.Authorization = `Bearer ${token}`;
      }
      const res = await fetch(url, {
        ...options,
        headers: mergedHeaders,
      });
      const data = await readJson(res);
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }
      return data;
    } catch (e) {
      setError(String(e?.message || e));
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function loadOverview() {
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/overview`);
    if (data) setOverview(data);
  }

  async function loadEnums() {
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/enums`);
    if (data) setEnums(Array.isArray(data.items) ? data.items : []);
  }

  async function loadTables() {
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/tables`);
    if (data) setTables(Array.isArray(data.items) ? data.items : []);
  }

  async function loadCountries() {
    const q = countryFilter.trim();
    const data = await runRequest(
      `${ORDER_PICKUP_BASE}/dev-admin/base/countries?limit=500${q ? `&q=${encodeURIComponent(q)}` : ""}`
    );
    if (data) setCountries(Array.isArray(data.items) ? data.items : []);
  }

  async function loadProvinces() {
    const q = provinceFilter.trim();
    const cc = provinceCountryFilter.trim().toUpperCase();
    const data = await runRequest(
      `${ORDER_PICKUP_BASE}/dev-admin/base/provinces?limit=1000${q ? `&q=${encodeURIComponent(q)}` : ""}${cc ? `&country_code=${encodeURIComponent(cc)}` : ""}`
    );
    if (data) setProvinces(Array.isArray(data.items) ? data.items : []);
  }

  async function loadProducts() {
    const q = productFilter.trim();
    const data = await runRequest(
      `${ORDER_PICKUP_BASE}/dev-admin/base/products?limit=1000${q ? `&q=${encodeURIComponent(q)}` : ""}`
    );
    if (data) setProducts(Array.isArray(data.items) ? data.items : []);
  }

  async function loadLockerLocations() {
    const q = lockerLocationFilter.trim();
    const cc = lockerLocationCountryFilter.trim().toUpperCase();
    const pc = lockerLocationProvinceFilter.trim().toUpperCase();
    const data = await runRequest(
      `${ORDER_PICKUP_BASE}/dev-admin/base/locker-locations?limit=2000${q ? `&q=${encodeURIComponent(q)}` : ""}${cc ? `&country_code=${encodeURIComponent(cc)}` : ""}${pc ? `&province_code=${encodeURIComponent(pc)}` : ""}`
    );
    if (data) setLockerLocations(Array.isArray(data.items) ? data.items : []);
  }

  async function saveCountry() {
    const code = String(countryForm.code || "").trim().toUpperCase();
    if (code.length !== 2) {
      setError("country code deve ter 2 caracteres (ex: BR, PT).");
      return;
    }
    if (!countryForm.name.trim()) {
      setError("name é obrigatório.");
      return;
    }
    const payload = {
      name: countryForm.name.trim(),
      continent: countryForm.continent || null,
      default_currency: countryForm.default_currency || null,
      default_timezone: countryForm.default_timezone || null,
      address_format: countryForm.address_format || null,
      is_active: Boolean(countryForm.is_active),
      metadata_json: {},
    };
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/countries/${encodeURIComponent(code)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (data?.ok) {
      setMessage(`Country ${code} salvo com sucesso.`);
      await loadCountries();
    }
  }

  async function saveProvince() {
    const code = String(provinceForm.code || "").trim().toUpperCase();
    if (!code) {
      setError("province code é obrigatório (ex: BR-SP, PT-11).");
      return;
    }
    if (!provinceForm.name.trim()) {
      setError("name é obrigatório.");
      return;
    }
    const payload = {
      name: provinceForm.name.trim(),
      country_code: provinceForm.country_code ? provinceForm.country_code.trim().toUpperCase() : null,
      province_code_original: provinceForm.province_code_original ? provinceForm.province_code_original.trim().toUpperCase() : null,
      region: provinceForm.region ? provinceForm.region.trim().toUpperCase() : null,
      timezone: provinceForm.timezone || null,
      is_active: Boolean(provinceForm.is_active),
      metadata_json: {},
    };
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/provinces/${encodeURIComponent(code)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (data?.ok) {
      setMessage(`Province ${code} salva com sucesso.`);
      await loadProvinces();
    }
  }

  async function saveProduct() {
    const sku = String(productForm.id || "").trim();
    if (!sku) {
      setError("SKU id é obrigatório.");
      return;
    }
    if (!productForm.name.trim()) {
      setError("name é obrigatório.");
      return;
    }
    const payload = {
      name: productForm.name.trim(),
      description: productForm.description || null,
      amount_cents: Number(productForm.amount_cents || 0),
      currency: String(productForm.currency || "BRL").trim().toUpperCase(),
      is_active: Boolean(productForm.is_active),
      metadata_json: {},
    };
    const data = await runRequest(`${ORDER_PICKUP_BASE}/dev-admin/base/products/${encodeURIComponent(sku)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (data?.ok) {
      setMessage(`SKU ${sku} salvo com sucesso.`);
      await loadProducts();
    }
  }

  async function saveLockerLocation() {
    const externalId = String(lockerLocationForm.external_id || "").trim();
    if (!externalId) {
      setError("external_id (locker_id) é obrigatório.");
      return;
    }
    const latitudeRaw = String(lockerLocationForm.latitude || "").trim();
    const longitudeRaw = String(lockerLocationForm.longitude || "").trim();
    const hasLat = latitudeRaw !== "";
    const hasLng = longitudeRaw !== "";
    if ((hasLat && !hasLng) || (!hasLat && hasLng)) {
      setError("latitude e longitude devem ser informados juntos.");
      return;
    }
    const payload = {
      external_id: externalId,
      province_code: lockerLocationForm.province_code ? lockerLocationForm.province_code.trim().toUpperCase() : null,
      city_name: lockerLocationForm.city_name || null,
      district: lockerLocationForm.district || null,
      postal_code: lockerLocationForm.postal_code || null,
      latitude: hasLat ? Number(latitudeRaw) : null,
      longitude: hasLng ? Number(longitudeRaw) : null,
      timezone: lockerLocationForm.timezone || null,
      address_street: lockerLocationForm.address_street || null,
      address_number: lockerLocationForm.address_number || null,
      address_complement: lockerLocationForm.address_complement || null,
      operating_hours_json: {},
      metadata_json: {},
      is_active: Boolean(lockerLocationForm.is_active),
    };
    const data = await runRequest(
      `${ORDER_PICKUP_BASE}/dev-admin/base/locker-locations/${encodeURIComponent(externalId)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    if (data?.ok) {
      setMessage(`Locker location ${externalId} salva com sucesso.`);
      await loadLockerLocations();
    }
  }

  if (!canAccess) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <h1 style={{ marginTop: 0 }}>Ops — Base Catalog Management</h1>
          <div style={warningStyle}>
            Esta interface exige perfil autorizado. Ajuste <b>VITE_BASE_CATALOG_ALLOWED_ROLES</b> ou habilite
            <b> VITE_DEV_BYPASS_AUTH=true</b> no ambiente controlado.
          </div>
          <div style={summaryStyle}>
            <div><b>Perfis atuais:</b> {currentRoles.join(", ") || "-"}</div>
            <div><b>Perfis exigidos:</b> {Array.from(allowedRoles).join(", ")}</div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>Ops — Base Catalog Management</h1>
        <div style={warningStyle}>
          Gestão operacional de tabelas base do projeto (country/province/products) e leitura de enums/tabelas
          do schema público. Esta tela é exclusivamente para ambiente de desenvolvimento controlado com VITE_DEV_BYPASS_AUTH=true. Veja 02_docker/.env
        </div>

        <div style={tabRowStyle}>
          {[
            ["overview", "Overview"],
            ["countries", "Countries"],
            ["provinces", "Provinces"],
            ["locker_locations", "Locker Locations"],
            ["products", "SKUs"],
            ["enums", "Enums"],
            ["tables", "Tables"],
          ].map(([key, label]) => (
            <button
              key={key}
              style={tab === key ? buttonPrimaryStyle : buttonSecondaryStyle}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={toolbarStyle}>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadOverview}>Carregar overview</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadEnums}>Carregar enums</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadTables}>Carregar tables</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadCountries}>Carregar countries</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadProvinces}>Carregar provinces</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadLockerLocations}>Carregar locker locations</button>
          <button style={buttonSecondaryStyle} disabled={loading} onClick={loadProducts}>Carregar SKUs</button>
        </div>

        {message ? <div style={okStyle}>{message}</div> : null}
        {error ? <pre style={errorStyle}>{error}</pre> : null}
      </section>

      {tab === "overview" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Overview</h2>
          <pre style={jsonBoxStyle}>{JSON.stringify(overview || {}, null, 2)}</pre>
        </section>
      ) : null}

      {tab === "countries" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Countries</h2>
          <div style={gridStyle}>
            <input placeholder="Filtro (code/nome/continente)" style={inputStyle} value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)} />
            <button style={buttonSecondaryStyle} onClick={loadCountries} disabled={loading}>Buscar</button>
          </div>
          <div style={gridStyle}>
            <input placeholder="code (BR, PT...)" style={inputStyle} value={countryForm.code} onChange={(e) => setCountryForm((s) => ({ ...s, code: e.target.value }))} />
            <input placeholder="name" style={inputStyle} value={countryForm.name} onChange={(e) => setCountryForm((s) => ({ ...s, name: e.target.value }))} />
            <input placeholder="continent" style={inputStyle} value={countryForm.continent} onChange={(e) => setCountryForm((s) => ({ ...s, continent: e.target.value }))} />
            <input placeholder="default_currency" style={inputStyle} value={countryForm.default_currency} onChange={(e) => setCountryForm((s) => ({ ...s, default_currency: e.target.value }))} />
            <input placeholder="default_timezone" style={inputStyle} value={countryForm.default_timezone} onChange={(e) => setCountryForm((s) => ({ ...s, default_timezone: e.target.value }))} />
            <input placeholder="address_format" style={inputStyle} value={countryForm.address_format} onChange={(e) => setCountryForm((s) => ({ ...s, address_format: e.target.value }))} />
            <label style={checkStyle}><input type="checkbox" checked={countryForm.is_active} onChange={(e) => setCountryForm((s) => ({ ...s, is_active: e.target.checked }))} />ativo</label>
            <button style={buttonPrimaryStyle} onClick={saveCountry} disabled={loading}>Salvar country</button>
          </div>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead><tr><th style={thStyle}>Code</th><th style={thStyle}>Name</th><th style={thStyle}>Continent</th><th style={thStyle}>Currency</th><th style={thStyle}>Timezone</th><th style={thStyle}>Ativo</th></tr></thead>
              <tbody>
                {countries.map((row) => (
                  <tr key={row.id || row.code}>
                    <td style={tdStyle}>{row.code}</td><td style={tdStyle}>{row.name}</td><td style={tdStyle}>{row.continent || "-"}</td><td style={tdStyle}>{row.default_currency || "-"}</td><td style={tdStyle}>{row.default_timezone || "-"}</td><td style={tdStyle}>{String(row.is_active)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "provinces" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Provinces</h2>
          <div style={gridStyle}>
            <input placeholder="Filtro (code/nome/region)" style={inputStyle} value={provinceFilter} onChange={(e) => setProvinceFilter(e.target.value)} />
            <input placeholder="country_code (opcional)" style={inputStyle} value={provinceCountryFilter} onChange={(e) => setProvinceCountryFilter(e.target.value)} />
            <button style={buttonSecondaryStyle} onClick={loadProvinces} disabled={loading}>Buscar</button>
          </div>
          <div style={gridStyle}>
            <input placeholder="code (BR-SP, PT-11...)" style={inputStyle} value={provinceForm.code} onChange={(e) => setProvinceForm((s) => ({ ...s, code: e.target.value }))} />
            <input placeholder="name" style={inputStyle} value={provinceForm.name} onChange={(e) => setProvinceForm((s) => ({ ...s, name: e.target.value }))} />
            <input placeholder="country_code" style={inputStyle} value={provinceForm.country_code} onChange={(e) => setProvinceForm((s) => ({ ...s, country_code: e.target.value }))} />
            <input placeholder="province_code_original" style={inputStyle} value={provinceForm.province_code_original} onChange={(e) => setProvinceForm((s) => ({ ...s, province_code_original: e.target.value }))} />
            <input placeholder="region (legado/compat)" style={inputStyle} value={provinceForm.region} onChange={(e) => setProvinceForm((s) => ({ ...s, region: e.target.value }))} />
            <input placeholder="timezone" style={inputStyle} value={provinceForm.timezone} onChange={(e) => setProvinceForm((s) => ({ ...s, timezone: e.target.value }))} />
            <label style={checkStyle}><input type="checkbox" checked={provinceForm.is_active} onChange={(e) => setProvinceForm((s) => ({ ...s, is_active: e.target.checked }))} />ativo</label>
            <button style={buttonPrimaryStyle} onClick={saveProvince} disabled={loading}>Salvar province</button>
          </div>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead><tr><th style={thStyle}>Code</th><th style={thStyle}>Name</th><th style={thStyle}>Country</th><th style={thStyle}>Original</th><th style={thStyle}>Region</th><th style={thStyle}>Timezone</th><th style={thStyle}>Ativo</th></tr></thead>
              <tbody>
                {provinces.map((row) => (
                  <tr key={row.id || row.code}>
                    <td style={tdStyle}>{row.code}</td><td style={tdStyle}>{row.name}</td><td style={tdStyle}>{row.country_code || "-"}</td><td style={tdStyle}>{row.province_code_original || "-"}</td><td style={tdStyle}>{row.region || "-"}</td><td style={tdStyle}>{row.timezone || "-"}</td><td style={tdStyle}>{String(row.is_active)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "locker_locations" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Capability Locker Location (PostGIS-safe)</h2>
          <div style={gridStyle}>
            <input placeholder="Filtro (locker/cidade/bairro)" style={inputStyle} value={lockerLocationFilter} onChange={(e) => setLockerLocationFilter(e.target.value)} />
            <input placeholder="country_code (ex: BR, PT)" style={inputStyle} value={lockerLocationCountryFilter} onChange={(e) => setLockerLocationCountryFilter(e.target.value)} />
            <input placeholder="province_code (ex: BR-SP, PT-11)" style={inputStyle} value={lockerLocationProvinceFilter} onChange={(e) => setLockerLocationProvinceFilter(e.target.value)} />
            <button style={buttonSecondaryStyle} onClick={loadLockerLocations} disabled={loading}>Buscar</button>
          </div>
          <div style={gridStyle}>
            <input placeholder="external_id (locker_id)" style={inputStyle} value={lockerLocationForm.external_id} onChange={(e) => setLockerLocationForm((s) => ({ ...s, external_id: e.target.value }))} />
            <input placeholder="province_code" style={inputStyle} value={lockerLocationForm.province_code} onChange={(e) => setLockerLocationForm((s) => ({ ...s, province_code: e.target.value }))} />
            <input placeholder="city_name" style={inputStyle} value={lockerLocationForm.city_name} onChange={(e) => setLockerLocationForm((s) => ({ ...s, city_name: e.target.value }))} />
            <input placeholder="district" style={inputStyle} value={lockerLocationForm.district} onChange={(e) => setLockerLocationForm((s) => ({ ...s, district: e.target.value }))} />
            <input placeholder="postal_code" style={inputStyle} value={lockerLocationForm.postal_code} onChange={(e) => setLockerLocationForm((s) => ({ ...s, postal_code: e.target.value }))} />
            <input placeholder="latitude (-90..90)" style={inputStyle} value={lockerLocationForm.latitude} onChange={(e) => setLockerLocationForm((s) => ({ ...s, latitude: e.target.value }))} />
            <input placeholder="longitude (-180..180)" style={inputStyle} value={lockerLocationForm.longitude} onChange={(e) => setLockerLocationForm((s) => ({ ...s, longitude: e.target.value }))} />
            <input placeholder="timezone" style={inputStyle} value={lockerLocationForm.timezone} onChange={(e) => setLockerLocationForm((s) => ({ ...s, timezone: e.target.value }))} />
            <input placeholder="address_street" style={inputStyle} value={lockerLocationForm.address_street} onChange={(e) => setLockerLocationForm((s) => ({ ...s, address_street: e.target.value }))} />
            <input placeholder="address_number" style={inputStyle} value={lockerLocationForm.address_number} onChange={(e) => setLockerLocationForm((s) => ({ ...s, address_number: e.target.value }))} />
            <input placeholder="address_complement" style={inputStyle} value={lockerLocationForm.address_complement} onChange={(e) => setLockerLocationForm((s) => ({ ...s, address_complement: e.target.value }))} />
            <label style={checkStyle}><input type="checkbox" checked={lockerLocationForm.is_active} onChange={(e) => setLockerLocationForm((s) => ({ ...s, is_active: e.target.checked }))} />ativo</label>
            <button style={buttonPrimaryStyle} onClick={saveLockerLocation} disabled={loading}>Salvar locker location</button>
          </div>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Locker</th>
                  <th style={thStyle}>Province</th>
                  <th style={thStyle}>Country</th>
                  <th style={thStyle}>Cidade</th>
                  <th style={thStyle}>Coords</th>
                  <th style={thStyle}>Geom</th>
                </tr>
              </thead>
              <tbody>
                {lockerLocations.map((row) => (
                  <tr key={row.id || `${row.external_id}-${row.province_code || ""}`}>
                    <td style={tdStyle}>{row.external_id}</td>
                    <td style={tdStyle}>{row.province_code || "-"}</td>
                    <td style={tdStyle}>{row.country_code || "-"}</td>
                    <td style={tdStyle}>{row.city_name || "-"}</td>
                    <td style={tdStyle}>{row.latitude != null && row.longitude != null ? `${row.latitude}, ${row.longitude}` : "-"}</td>
                    <td style={tdStyle}>{row.geom_wkt || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "products" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Products / SKUs</h2>
          <div style={gridStyle}>
            <input placeholder="Filtro (sku/nome/descrição)" style={inputStyle} value={productFilter} onChange={(e) => setProductFilter(e.target.value)} />
            <button style={buttonSecondaryStyle} onClick={loadProducts} disabled={loading}>Buscar</button>
          </div>
          <div style={gridStyle}>
            <input placeholder="sku id" style={inputStyle} value={productForm.id} onChange={(e) => setProductForm((s) => ({ ...s, id: e.target.value }))} />
            <input placeholder="name" style={inputStyle} value={productForm.name} onChange={(e) => setProductForm((s) => ({ ...s, name: e.target.value }))} />
            <input placeholder="amount_cents" style={inputStyle} type="number" value={productForm.amount_cents} onChange={(e) => setProductForm((s) => ({ ...s, amount_cents: Number(e.target.value || 0) }))} />
            <input placeholder="currency" style={inputStyle} value={productForm.currency} onChange={(e) => setProductForm((s) => ({ ...s, currency: e.target.value }))} />
            <input placeholder="description" style={inputStyle} value={productForm.description} onChange={(e) => setProductForm((s) => ({ ...s, description: e.target.value }))} />
            <label style={checkStyle}><input type="checkbox" checked={productForm.is_active} onChange={(e) => setProductForm((s) => ({ ...s, is_active: e.target.checked }))} />ativo</label>
            <button style={buttonPrimaryStyle} onClick={saveProduct} disabled={loading}>Salvar SKU</button>
          </div>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead><tr><th style={thStyle}>SKU</th><th style={thStyle}>Name</th><th style={thStyle}>Preço</th><th style={thStyle}>Moeda</th><th style={thStyle}>Ativo</th></tr></thead>
              <tbody>
                {products.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td><td style={tdStyle}>{row.name}</td><td style={tdStyle}>{row.amount_cents}</td><td style={tdStyle}>{row.currency}</td><td style={tdStyle}>{String(row.is_active)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "enums" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Public Enums</h2>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead><tr><th style={thStyle}>Enum</th><th style={thStyle}>Values</th></tr></thead>
              <tbody>
                {enums.map((item) => (
                  <tr key={item.enum_name}>
                    <td style={tdStyle}>{item.enum_name}</td>
                    <td style={tdStyle}>{Array.isArray(item.values) ? item.values.join(", ") : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "tables" ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Public Tables</h2>
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead><tr><th style={thStyle}>Table</th><th style={thStyle}>Estimated Rows</th></tr></thead>
              <tbody>
                {tables.map((item) => (
                  <tr key={item.table_name}>
                    <td style={tdStyle}>{item.table_name}</td>
                    <td style={tdStyle}>{item.estimated_rows}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
  display: "grid",
  gap: 16,
};

const cardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const warningStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(199,146,0,0.14)",
  border: "1px solid rgba(199,146,0,0.30)",
  fontSize: 14,
};

const summaryStyle = {
  marginTop: 12,
  padding: 10,
  borderRadius: 10,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.08)",
};

const tabRowStyle = {
  marginTop: 12,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const toolbarStyle = {
  marginTop: 12,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const gridStyle = {
  marginTop: 12,
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 10,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const checkStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 14,
};

const buttonSecondaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "white",
  fontWeight: 600,
};

const buttonPrimaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(31,122,63,0.40)",
  background: "#1f7a3f",
  color: "white",
  fontWeight: 700,
};

const okStyle = {
  marginTop: 10,
  padding: 10,
  borderRadius: 10,
  background: "rgba(31,122,63,0.15)",
  border: "1px solid rgba(31,122,63,0.35)",
};

const errorStyle = {
  marginTop: 10,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
  whiteSpace: "pre-wrap",
};

const jsonBoxStyle = {
  marginTop: 8,
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12,
  padding: 12,
  overflow: "auto",
  maxHeight: 320,
};

const tableWrapperStyle = {
  overflowX: "auto",
  marginTop: 12,
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
};

const thStyle = {
  textAlign: "left",
  borderBottom: "1px solid rgba(255,255,255,0.18)",
  padding: "10px 8px",
  fontSize: 13,
};

const tdStyle = {
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  padding: "10px 8px",
  verticalAlign: "top",
};
