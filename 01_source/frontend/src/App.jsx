import { useState } from "react";

const API_CONFIG = {
  SP: {
    host: "localhost",
    port: 8000,  // 👈 ALTERADO: 8101 → 8000      veja docker-compose.yml em BACKEND_SP
    path: "/gateway/pagamento"
  },
  PT: {
    host: "localhost",
    port: 8000,  // 👈 ALTERADO: 8102 → 8000 (ou mantenha 8102 se tiver outro backend)    veja docker-compose.yml em BACKEND_PT
    path: "/gateway/pagamento"
  }
};

export default function App() {
  const [region, setRegion] = useState("SP");
  const [payment, setPayment] = useState("PIX");
  const [value, setValue] = useState("");
  const [drawer, setDrawer] = useState("");
  const [response, setResponse] = useState("");

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

  const sendPayment = async () => {
    // Validações básicas
    if (!drawer || drawer < 1 || drawer > 24) {
      setResponse("❌ Por favor, informe uma gaveta válida (1 a 24)");
      return;
    }
    
    if (!value || value <= 0) {
      setResponse("❌ Por favor, informe um valor válido");
      return;
    }


    // const url = "http://localhost:8000/gateway/pagamento"; 

    // 🔥 MAPA DE ENDPOINTS POR REGIÃO
    // const endpoints = {
    //   SP: "http://localhost:8101/gateway/pagamento",
    //   PT: "http://localhost:8102/gateway/pagamento"
    // };
    // const url = endpoints[region];

    // 🔥🔥 CONSTRUIR URL DINAMICAMENTE
    const url = buildUrl(region);
    
    if (!url) {
      setResponse(`❌ Região ${region} não configurada ou definida - não possui endpoint configurado`);
      return;
    }

    try {
      // const res = await fetch(url, {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ regiao: region, metodo: payment, valor: parseFloat(value), porta: parseInt(drawer) }),
      // });

      const deviceFp = getOrCreateDeviceFingerprint();
      const idemKey = generateIdempotencyKey();

      // Opcional: log para debug
      // console.log(`🌍 Região: ${region} | URL: ${url}`);

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
        setResponse(`❌ HTTP ${res.status}\n\n${text} 📍 Região: ${region}\n🔗 URL: ${url}`);
        return;
      }
      
      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
      
    } catch (error) {
      // setResponse("Erro ao conectar com Gateway");
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

  return (
    <div style={{ padding: 40, fontFamily: "Arial" }}>
      <h1>🏷️ ELLAN LAB LOCKER</h1>

   <div style={{ marginBottom: 15 }}>
        <label style={{ display: "block", marginBottom: 5 }}>
          <strong>Selecionar a sua Região:</strong>
        </label>
        <div style={{ 
          marginTop: 10, 
          padding: 8, 
          backgroundColor: region === 'SP' ? '#1b5883' : '#aa7828',
          borderRadius: 4,
          border: '1px solid #ddd'
        }}>
          <strong>🌍 Região ativa:</strong> {region === 'SP' ? '🇧🇷 Carapicuíba (porta 8101)' : '🇵🇹 Maia (porta 8102)'}
        </div>
        <select 
          value={region} 
          onChange={(e) => setRegion(e.target.value)}
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
          marginTop: 10,
          overflow: "auto"
        }}>
          {response}
        </pre>
      </div>
    </div>
  );
}