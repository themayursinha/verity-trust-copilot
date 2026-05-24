#!/usr/bin/env bash
set -euo pipefail

mkdir -p secrets
openssl genrsa -out secrets/jwt_private.pem 2048
openssl rsa -in secrets/jwt_private.pem -pubout -out secrets/jwt_public.pem
chmod 600 secrets/jwt_private.pem
echo "JWT RSA keys generated in secrets/"
