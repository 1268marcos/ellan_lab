
========================
04/03/2026 - 17:35
========================

Padrão de Proxy no Vite (evitar CORS)

Quando o frontend (Vite, ex.: localhost:5173) chama APIs em outras portas (8000, 8201, 8202), o browser pode bloquear por CORS. A forma mais “blindada” é usar proxy do Vite, fazendo o frontend chamar rotas na mesma origem (/api/...) e o Vite encaminha para os serviços reais.

1) vite.config.js (proxy)

Crie/edite 01_source/frontend/vite.config.js:

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Gateway (host:8000) -> /api/gw/...
      "/api/gw": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gw/, ""),
      },

      // Backend SP (host:8201) -> /api/sp/...
      "/api/sp": {
        target: "http://localhost:8201",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sp/, ""),
      },

      // Backend PT (host:8202) -> /api/pt/...
      "/api/pt": {
        target: "http://localhost:8202",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pt/, ""),
      },
    },
  },
});
2) Como usar no código (sem portas “hardcoded”)

Em vez de chamar http://localhost:8000/... ou http://localhost:8202/..., use caminhos relativos:

Gateway:

fetch("/api/gw/gateway/pagamento", ...)

Backend SP:

fetch("/api/sp/locker/slots")

Backend PT:

fetch("/api/pt/locker/slots")

3) Testes rápidos do proxy

Com o frontend rodando (npm run dev):

curl -sS http://localhost:5173/api/pt/locker/slots | head
curl -sS -X POST http://localhost:5173/api/gw/gateway/pagamento \
  -H "Content-Type: application/json" \
  -d '{"regiao":"PT","metodo":"PIX","valor":100,"porta":1}'

Se responder, o proxy está funcionando e o frontend fica imune a CORS.

=====================
04/03/2026 - 09:00
=====================

Convenções de Rede e Portas (Padrão “Blindado”)

Este projeto usa Docker Compose com uma rede interna (container→container) e portas publicadas no host (host→container). Para evitar confusão e regressões, seguimos as regras abaixo.

1) Regra de Ouro: interno ≠ externo

Dentro do Docker (container→container):

Sempre use nome do serviço + porta interna fixa.

Exemplo: http://backend_sp:8000

Fora do Docker (host→container):

Sempre use localhost + porta publicada (fachada).

Exemplo: http://localhost:8201

Nunca use localhost para um container chamar outro container.

2) Porta interna padronizada

Todos os serviços HTTP devem escutar em uma porta interna previsível, preferencialmente:

Porta interna padrão (HTTP): 8000

Exceção aceitável: serviços com porta própria por clareza (ex.: order_pickup_service em 8003)

Importante: “porta publicada” do Compose não muda a porta interna do serviço; ela só expõe um caminho para o host.

3) Mapeamento oficial de portas (host “fachada”)
Serviço	Porta interna (Docker)	Porta externa (Host)	Acesso no Host
backend_sp	8000	8201	http://localhost:8201
backend_pt	8000	8202	http://localhost:8202
payment_gateway	8000	8000	http://localhost:8000
order_pickup_service	8003	8003	http://localhost:8003
4) URLs internas oficiais (para uso entre containers)

Use sempre:

BACKEND_SP_INTERNAL=http://backend_sp:8000

BACKEND_PT_INTERNAL=http://backend_pt:8000

MQTT_INTERNAL=mqtt_broker:1883

REDIS_INTERNAL=redis_central:6379

POSTGRES_INTERNAL=postgres_central:5432

Exemplos:

payment_gateway chama: http://backend_sp:8000

order_pickup_service chama: http://backend_pt:8000

5) Padrão de configuração (defaults no código)

Para reduzir erros quando alguém roda via Compose sem configurar nada:

Defaults no código devem apontar para o ambiente Docker (interno).

O host (externo) deve ser ativado apenas via env quando rodar fora do Compose.

Exemplo recomendado (defaults):

BACKEND_SP_BASE default → http://backend_sp:8000

BACKEND_PT_BASE default → http://backend_pt:8000

6) Healthcheck: sempre na porta interna

Healthchecks rodam dentro do container, então devem usar:

http://localhost:8000/health (ou a porta interna do serviço)

Nunca use localhost:8201 em healthcheck (isso é porta do host, não do container).

7) Teste de sanidade (anti-regressão)

Rodar para validar conectividade interna:

docker compose exec order_pickup_service sh -lc \
  "wget -qO- http://backend_sp:8000/health && echo SP_OK; \
   wget -qO- http://backend_pt:8000/health && echo PT_OK"

Se esse teste falhar, normalmente significa:

serviço não está ouvindo na porta interna esperada, ou

env foi configurado com porta “de host” dentro do Docker, ou

nome do serviço no Compose foi alterado.

8) Regra final (evitar 90% dos bugs de rede)

Containers sempre falam via service_name:porta_interna.
Host sempre fala via localhost:porta_publicada.