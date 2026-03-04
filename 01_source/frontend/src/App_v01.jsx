import { useEffect, useMemo, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";

const API_CONFIG = {
  SP: {
    host: "localhost",
    port: 8000,            // gateway no host
    path: "/gateway/pagamento",
  },
  PT: {
    host: "localhost",
    port: 8000,            // gateway no host
    path: "/gateway/pagamento",
  },
};

function LockerPage({ defaultRegion }) {
  const location = useLocation();
  const navigate = useNavigate();

  const [region, setRegion] = useState(defaultRegion);
  const [payment, setPayment] = useState("PIX");
  const [value, setValue] = useState("");
  const [drawer, setDrawer] = useState("");
  const [response, setResponse] = useState("");

  // Se a rota mudar (/sp ou /pt), atualiza a região automaticamente
  useEffect(() => {
    setRegion(defaultRegion);
  }, [defaultRegion, location.pathname]);

  function getOrCreateDeviceFingerprint() {
    const key = "ellan_device_fp_v1";
    let fp = localStorage.getItem(key);
    if (!fp) {
      fp = crypto.randomUUID();
      localStorage.setItem(key, fp);
    }
    return fp;
  }

  function generateIdempotencyKey() {
    return crypto.randomUUID();
  }

  const buildUrl = (region) => {
    const config = API_CONFIG[region];
    if (!config) return null;
    const { host, port, path } = config;
    return `http://${host}:${port}${path}`;
  };

  const url = useMemo(() => buildUrl(region), [region]);

  const sendPayment = async () => {
    if (!drawer || Number(drawer) < 1 || Number(drawer) > 24) {
      setResponse("❌ Por favor, informe uma gaveta válida (1 a 24)");
      return;
    }
    if (!value || Number(value) <= 0) {
      setResponse("❌ Por favor, informe um valor válido");
      return;
    }
    if (!url) {
      setResponse(`❌ Região ${region} não configurada - sem endpoint`);
      return;
    }

    const deviceFp = getOrCreateDeviceFingerprint();
    const idemKey = generateIdempotencyKey();

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idemKey,
          "X-Device-Fingerprint": deviceFp,
        },
        body: JSON.stringify({
          regiao: region,
          metodo: payment,
          valor: parseFloat(value),
          porta: parseInt(drawer),
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        setResponse(`❌ HTTP ${res.status}\n\n${text}\n\n📍 Região: ${region}\n🔗 URL: ${url}`);
        return;
      }

      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (error) {
      setResponse(
        "❌ Erro ao conectar com Gateway\n\n" +
          (error?.message ? `message: ${error.message}\n` : "") +
          (error?.name ? `name: ${error.name}\n` : "") +
          `📍 Região: ${region}\n` +
          `🔗 URL: ${url}\n` +
          `🔑 Idempotency: ${idemKey}\n` +
          `📱 Device FP: ${deviceFp}\n` +
          `❌ Erro: ${error?.message || "Desconhecido"}\n` +
          `📌 Tipo: ${error?.name || "N/A"}`
      );
    }
  };

  // Quando muda o select, também muda a URL (/sp ou /pt)
  const onChangeRegion = (newRegion) => {
    setRegion(newRegion);
    navigate(newRegion === "SP" ? "/sp" : "/pt");
  };

  return (
    <div style={{ padding: 40, fontFamily: "Arial" }}>
      <h1>🏷️ ELLAN LAB LOCKER</h1>

      <nav style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <Link to="/sp">/sp</Link>
        <Link to="/pt">/pt</Link>
        <span style={{ opacity: 0.6 }}>Gateway: {url}</span>
      </nav>

      <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Selecionar a sua Região:</strong>
        </label>

        <div
          style={{
            marginTop: 10,
            padding: 8,
            backgroundColor: region === "SP" ? "#1b5883" : "#aa7828",
            borderRadius: 4,
            border: "1px solid #ddd",
            color: "white",
          }}
        >
          <strong>🌍 Região ativa:</strong>{" "}
          {region === "SP" ? "🇧🇷 Carapicuíba" : "🇵🇹 Maia"}
        </div>

        <select
          value={region}
          onChange={(e) => onChangeRegion(e.target.value)}
          style={{ padding: 8, width: 200 }}
        >
          <option value="SP">🇧🇷 Carapicuíba</option>
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
          fontSize: 16,
        }}
      >
        💰 Enviar Pagamento
      </button>

      <div style={{ marginTop: 30 }}>
        <strong>📋 Resposta do Backend:</strong>
        <pre
          style={{
            backgroundColor: "#5e5a5a",
            padding: 15,
            borderRadius: 4,
            border: "1px solid #ddd",
            marginTop: 10,
            overflow: "auto",
            color: "white",
          }}
        >
          {response}
        </pre>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/sp" replace />} />
      <Route path="/sp" element={<LockerPage defaultRegion="SP" />} />
      <Route path="/pt" element={<LockerPage defaultRegion="PT" />} />
      <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
    </Routes>
  );
}