#!/bin/bash
set -e

echo "=== Executando todos os smokes MVP ==="
./smoke-app-campo.sh
./smoke-noc.sh
./smoke-suporte.sh
./smoke-fiscal.sh
echo "=== Todos os smokes passaram ==="
