#!/usr/bin/env python3
"""Generate a signed license key for Verity Trust Copilot."""
import argparse
import base64
import json
import time
import sys

from nacl.signing import SigningKey


def main():
    parser = argparse.ArgumentParser(description="Generate a Verity Trust Copilot license key")
    parser.add_argument("--org-id", required=True, help="Organization ID")
    parser.add_argument("--org-name", required=True, help="Organization name")
    parser.add_argument("--seats", type=int, required=True, help="Maximum seats")
    parser.add_argument("--email", required=True, help="Customer email")
    parser.add_argument("--expiry-days", type=int, default=365, help="Days until expiry (0 = never)")
    parser.add_argument("--private-key", help="Base64-encoded Ed25519 private key (32 bytes)")
    parser.add_argument("--generate-keys", action="store_true", help="Generate a new keypair and print it")

    args = parser.parse_args()

    if args.generate_keys:
        key = SigningKey.generate()
        private_b64 = base64.b64encode(key.encode()).decode()
        public_b64 = base64.b64encode(key.verify_key.encode()).decode()
        print(f"Private key (keep secret): {private_b64}")
        print(f"Public key  (set as LICENSE_PUBLIC_KEY): {public_b64}")
        return

    private_key_b64 = args.private_key or input("Enter private key (base64): ").strip()

    try:
        private_key_bytes = base64.b64decode(private_key_b64)
        signing_key = SigningKey(private_key_bytes)
    except Exception as e:
        print(f"Error: Invalid private key — {e}", file=sys.stderr)
        sys.exit(1)

    now = int(time.time())
    exp = now + (args.expiry_days * 86400) if args.expiry_days > 0 else None

    payload = {
        "org_id": args.org_id,
        "org_name": args.org_name,
        "max_seats": args.seats,
        "iat": now,
        "email": args.email,
    }
    if exp:
        payload["exp"] = exp

    payload_bytes = json.dumps(payload).encode()
    signature = signing_key.sign(payload_bytes).signature

    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode().rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    license_key = f"{payload_b64}.{sig_b64}"
    print(f"\nLicense key:\n{license_key}")

    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    print(f"Seats: {args.seats}")
    print(f"Expires: {'Never' if not exp else time.strftime('%Y-%m-%d', time.gmtime(exp))}")


if __name__ == "__main__":
    main()
