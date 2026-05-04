#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/ca" "$ROOT/services"
openssl genrsa -out "$ROOT/ca/ca.key" 2048
openssl req -x509 -new -nodes -key "$ROOT/ca/ca.key" -sha256 -days 3650 -subj "/CN=ellan-test-ca" -out "$ROOT/ca/ca.crt"
openssl genrsa -out "$ROOT/services/inventory.key" 2048
openssl req -new -key "$ROOT/services/inventory.key" -subj "/CN=inventory-service" -out "$ROOT/services/inventory.csr"
openssl x509 -req -in "$ROOT/services/inventory.csr" -CA "$ROOT/ca/ca.crt" -CAkey "$ROOT/ca/ca.key" -CAcreateserial -out "$ROOT/services/inventory.crt" -days 825 -sha256
rm -f "$ROOT/services/inventory.csr"
echo "Generated $ROOT/ca/ca.crt and $ROOT/services/inventory.crt"
