#!/usr/bin/env python3
"""
IRS Certificate Converter
Converts a purchased Certificate (PFX/P12 or PEM) into an IRS-compliant JWK.
Usage: python3 convert_cert_to_jwk.py <cert_path> <password_if_pfx>
"""

import base64
import getpass
import hashlib
import json
import sys

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12


def base64url_encode(data) -> None:
    """Encodes data to Base64URL without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def int_to_base64url(n) -> None:
    """Encodes a large integer to Base64URL."""
    length = (n.bit_length() + 7) // 8
    b = n.to_bytes(length, byteorder="big")
    return base64url_encode(b)


def load_cert_and_key(path, password=None) -> None:
    with open(path, "rb") as f:
        data = f.read()

    # Try PKCS#12 (PFX) first
    if path.lower().endswith((".pfx", ".p12")):
        print("🔓 Attempting to unlock PKCS#12 container...")
        if password is None:
            password = getpass.getpass("Enter PFX Password: ")

        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            data, password.encode() if password else None
        )
        return private_key, certificate, additional_certs

    # Try PEM
    print("🔓 Attempting to read PEM file...")
    try:
        # Assuming PEM contains both or just cert?
        # Usually need strict separation. Let's try loading Cert first.
        certificate = x509.load_pem_x509_certificate(data)
        # Try loading key
        try:
            private_key = serialization.load_pem_private_key(
                data, password=password.encode() if password else None
            )
        except:
            print(
                "⚠️ Could not load private key from same file. Assuming Key is handled separately or not needed for x5c extraction."
            )
            private_key = None

        return private_key, certificate, []
    except Exception as e:
        print(f"❌ Failed to load PEM: {e}")
        sys.exit(1)


def convert_to_jwk(cert_path, password=None) -> None:
    print(f"📂 Processing: {cert_path}")

    private_key, cert, chain = load_cert_and_key(cert_path, password)

    if not isinstance(private_key, rsa.RSAPrivateKey):
        print("❌ Private Key is NOT RSA. IRS requires RSA.")
        # Continue anyway to show public parts? No, strict fail.
        if private_key is None:
            print(
                "❌ Private Key missing. Cannot generate full JWK (n, e required from Key numbers, though present in Cert)."
            )
            # Actually we can get public numbers from Cert
        else:
            sys.exit(1)

    # Get Public Numbers
    if private_key:
        public_key = private_key.public_key()
    else:
        public_key = cert.public_key()

    if not isinstance(public_key, rsa.RSAPublicKey):
        print("❌ Certificate Public Key is NOT RSA.")
        sys.exit(1)

    pn = public_key.public_numbers()

    # 1. x5c Construction
    # IRS requires the Main Cert first, then intermediates.
    # We'll put the main cert, then any additional certs found in PFX.
    full_chain = [cert] + (chain if chain else [])

    x5c_list = []
    for c in full_chain:
        der = c.public_bytes(serialization.Encoding.DER)
        b64 = base64.b64encode(der).decode("ascii")
        x5c_list.append(b64)

    # 2. x5t (Thumbprint of Main Cert)
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    sha1 = hashlib.sha1(cert_der).digest()
    x5t_str = base64url_encode(sha1)

    # 3. Kid
    kid = x5t_str

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": kid,
        "n": int_to_base64url(pn.n),
        "e": int_to_base64url(pn.e),
        "x5c": x5c_list,
        "x5t": x5t_str,
    }

    print("\n✅ JWK Conversion Successful!")
    print("-" * 20)
    print(json.dumps(jwk, indent=2))
    print("-" * 20)

    # Save
    out_file = cert_path + ".jwk.json"
    with open(out_file, "w") as f:
        json.dump(jwk, f, indent=2)
    print(f"💾 Saved to: {out_file}")

    if private_key:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        key_file = cert_path + ".private.pem"
        with open(key_file, "wb") as f:
            f.write(pem)
        print(f"🔑 Private Key extracted to: {key_file} (KEEP SAFE)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_cert_to_jwk.py <cert_path.pfx> [password]")
        sys.exit(1)

    path = sys.argv[1]
    pw = sys.argv[2] if len(sys.argv) > 2 else None
    convert_to_jwk(path, pw)
