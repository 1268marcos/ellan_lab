import { useState } from "react";

async function getOrCreateDeviceFingerprint() {
  const key = "ellan_device_fp_v1";
  let fp = localStorage.getItem(key);
  if (!fp) {
    fp = crypto.randomUUID();
    localStorage.setItem(key, fp);
  }
  return fp;
}

async function generateIdempotencyKey() {
  return crypto.randomUUID();
}

async function canonicalPaymentPayload({ regiao, metodo, valor, porta }) {
  // Normaliza tipos e arredonda valor para evitar diferenças por "0.1 + 0.2"
  const v = Number(valor);
  const p = Number(porta);

  return {
    regiao: String(regiao).toUpperCase(),
    metodo: String(metodo).toUpperCase(),
    valor: Number.isFinite(v) ? Number(v.toFixed(2)) : v,
    porta: Number.isFinite(p) ? p : porta,
  };
}

async function sha256Hex(str) {
  const enc = new TextEncoder();
  const buf = await crypto.subtle.digest("SHA-256", enc.encode(str));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function getIdempotencyKeyForPayload(payload, ttlMs = 120_000) {
  const storeKey = "ellan_idem_cache_v1";
  const now = Date.now();

  const canonical = canonicalPaymentPayload(payload);
  const fingerprint = await sha256Hex(JSON.stringify(canonical));

  const raw = localStorage.getItem(storeKey);
  const cache = raw ? JSON.parse(raw) : {};

  const hit = cache[fingerprint];
  if (hit && hit.idemKey && typeof hit.ts === "number" && now - hit.ts <= ttlMs) {
    return { idemKey: hit.idemKey, cacheHit: true, fingerprint };
  }

  const idemKey = crypto.randomUUID();
  cache[fingerprint] = { idemKey, ts: now };

  // Limpeza leve (opcional): remove itens expirados
  for (const k of Object.keys(cache)) {
    if (now - cache[k].ts > ttlMs) delete cache[k];
  }

  localStorage.setItem(storeKey, JSON.stringify(cache));
  return { idemKey, cacheHit: false, fingerprint };
}

export default function App() {
  const [region, setRegion] = useState("SP");
  const [payment, setPayment] = useState("PIX");
  const [value, setValue] = useState("");
  const [drawer, setDrawer] = useState("");
  const [response, setResponse] = useState("");

  const sendPayment = async () => {
    // Validações básicas
    if (!drawer || drawer < 1 || drawer > 24) {
      setResponse("Por favor, informe uma gaveta válida (1 a 24)");
      return;
    }
    
    if (!value || value <= 0) {
      setResponse("Por favor, informe um valor válido");
      return;
    }

    const url = "http://localhost:8000/gateway/pagamento";

    const payload = {
      regiao: region,
      metodo: payment,
      valor: parseFloat(value),
      porta: parseInt(drawer),
    };

    const deviceFp = getOrCreateDeviceFingerprint();
    const { idemKey, cacheHit } = await getIdempotencyKeyForPayload(payload, 120_000);    

    try {
      const deviceFp = getOrCreateDeviceFingerprint();
      const idemKey = generateIdempotencyKey();

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idemKey, "X-Device-Fingerprint": deviceFp, },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setResponse(
        JSON.stringify(
          {
            http_status: res.status,
            idempotency: { key: idemKey, reused_within_2min: cacheHit },
            response: data,
          },
          null, 
          2
        )
      );
    } catch (error) {
      setResponse("Erro ao conectar com Gateway");
    }
  };

  return (
    <div style={{ padding: 40, fontFamily: "Arial" }}>
      <h1>🏷️ ELLAN LAB LOCKER</h1>

   <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Selecionar a sua Região:</strong>
        </label>
        <select 
          value={region} 
          onChange={(e) => setRegion(e.target.value)}
          style={{ padding: 8, width: 200 }}
        >
          <option value="SP">🇧🇷 São Paulo</option>
          <option value="PT">🇵🇹 Maia</option>
        </select>
      </div>

      <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Selecionar Método de Pagamento:</strong>
        </label>
        <select 
          value={payment} 
          onChange={(e) => setPayment(e.target.value)}
          style={{ padding: 8, width: 200 }}
        >
          <option value="PIX">💳 PIX</option>
          <option value="CARTAO">💳 Cartão</option>
          <option value="MBWAY">📱 MB Way</option>
          <option value="NFC">📱 Proximidade</option>
        </select>
      </div>

      <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Informe a Gaveta (1 a 24):</strong>
        </label>
        <input
          type="number"
          min="1"
          max="24"
          value={drawer}
          onChange={(e) => setDrawer(e.target.value)}
          placeholder="Digite o número da gaveta"
          style={{ padding: 8, width: 200 }}
        />
        <small style={{ display: "block", color: "#666", marginTop: 3 }}>
          Escolha uma gaveta disponível entre 1 e 24
        </small>
      </div>

      <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Informe o Valor:</strong>
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Digite o valor do pagamento"
          style={{ padding: 8, width: 200 }}
        />
      </div>

      <button
        onClick={sendPayment}
        style={{ 
          marginTop: 10, 
          padding: "10px 20px",
          backgroundColor: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: 4,
          cursor: "pointer",
          fontSize: 16
        }}
      >
        💰 Enviar Pagamento
      </button>


      <div style={{ marginTop: 30 }}>
        <strong>📋 Resposta do Backend:</strong>
        <pre style={{ 
          backgroundColor: "#5e5a5a", 
          padding: 15, 
          borderRadius: 4,
          border: "1px solid #ddd",
          marginTop: 10
        }}>
          {response}
        </pre>
      </div>
    </div>
  );
}