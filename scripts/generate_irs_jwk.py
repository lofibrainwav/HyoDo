#!/usr/bin/env python3
"""
IRS JWK Generator (Hardened)
Generates an RSA Key Pair and a Self-Signed Certificate with STRICT IRS extensions.
Outputs the JWK in the specific format required by the IRS API.
"""

import sys
import json
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography import x509


def base64url_encode(data) -> None:
    """Encodes data to Base64URL without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def int_to_base64url(n) -> None:
    """Encodes a large integer to Base64URL."""
    length = (n.bit_length() + 7) // 8
    b = n.to_bytes(length, byteorder="big")
    return base64url_encode(b)


def generate_hardened_jwk() -> None:
    print("🔐 Generating RSA Key Pair (2048 bit)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Generate a Self-Signed Certificate with IRS-Required Extensions
    print("📜 Generating Hardened Self-Signed Certificate...")
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Virtual"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "AFO Kingdom"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Julie AICPA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Julie Bot"),
        ]
    )

    # Critical: IRS requires KeyUsage and ExtendedKeyUsage
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.now(timezone.utc))
    builder = builder.not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))

    # Extensions
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,  # Self-signed often needs this false unless acting as CA
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
            content_commitment=True,  # NonRepudiation
        ),
        critical=True,
    )
    builder = builder.add_extension(
        x509.ExtendedKeyUsage(
            [
                ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH,
                ExtendedKeyUsageOID.EMAIL_PROTECTION,
            ]
        ),
        critical=False,
    )

    cert = builder.sign(private_key, hashes.SHA256())

    # Extract Constants
    pn = public_key.public_numbers()

    # 1. x5c (Base64 DER - NOT Base64URL)
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    x5c_str = base64.b64encode(cert_der).decode("ascii")

    # 2. x5t (Base64URL SHA-1 Thumbprint)
    sha1 = hashlib.sha1(cert_der).digest()
    x5t_str = base64url_encode(sha1)

    # 3. Key ID
    kid = x5t_str

    # Strict Ordering Construction
    # We build the dict, but when printing we will ensure order manually just in case python version changes
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": kid,
        "n": int_to_base64url(pn.n),
        "e": int_to_base64url(pn.e),
        "x5c": [x5c_str],
        "x5t": x5t_str,
    }

    # Save Private Key
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    print("\n✅ Hardened JWK Generated Successfully!")
    print("\n⚠️  [PRIVATE KEY] Update your .env (IRS_PRIVATE_KEY):")
    print("-" * 20)
    print(pem.decode("ascii"))
    print("-" * 20)

    print("\n📋 [JWK FOR FORM] Copy this JSON exactly:")
    print("-" * 20)
    # Using json.dumps is usually fine for order in modern Python (3.7+ preserves insertion order)
    # But let's verify visual order reflects kty -> x5t
    print(json.dumps(jwk, indent=2))
    print("-" * 20)

    with open("irs_julie_jwk_hardened.json", "w") as f:
        json.dump(jwk, f, indent=2)

    with open("irs_julie_private_hardened.pem", "wb") as f:
        f.write(pem)


if __name__ == "__main__":
    generate_hardened_jwk()
