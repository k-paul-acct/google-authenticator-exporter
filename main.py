import base64
import glob
import sys
from urllib.parse import parse_qs, urlparse

import pyotp
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode

import migration_pb2

# --- Configuration ---
# List any .txt filenames here that you want the script to ignore
IGNORE_TXT_FILES = {
    # add more filenames here as needed
}

# --- Constants & Maps ---
ALGO_MAP = {
    migration_pb2.MigrationPayload.ALGORITHM_UNSPECIFIED: "SHA1",
    migration_pb2.MigrationPayload.ALGORITHM_SHA1: "SHA1",
    migration_pb2.MigrationPayload.ALGORITHM_SHA256: "SHA256",
    migration_pb2.MigrationPayload.ALGORITHM_SHA512: "SHA512",
    migration_pb2.MigrationPayload.ALGORITHM_MD5: "MD5",
}

DIGITS_MAP = {
    migration_pb2.MigrationPayload.DIGIT_COUNT_UNSPECIFIED: 6,
    migration_pb2.MigrationPayload.DIGIT_COUNT_SIX: 6,
    migration_pb2.MigrationPayload.DIGIT_COUNT_EIGHT: 8,
}

TYPE_TOTP = migration_pb2.MigrationPayload.OTP_TYPE_TOTP
TYPE_HOTP = migration_pb2.MigrationPayload.OTP_TYPE_HOTP


# --- Helpers ---
def decode_migration_uri(uri: str):
    """Parse the otpauth-migration:// URI into a MigrationPayload."""
    parsed = urlparse(uri.strip())
    if parsed.scheme != "otpauth-migration":
        raise ValueError(f"Not a migration URI: {uri!r}")
    q = parse_qs(parsed.query)
    data_b64 = q.get("data")
    if not data_b64:
        raise ValueError(f"No data parameter in URI: {uri!r}")
    raw = base64.urlsafe_b64decode(data_b64[0] + "===")
    payload = migration_pb2.MigrationPayload()
    payload.ParseFromString(raw)
    return payload


def format_label(entry):
    return f"{entry.issuer} ({entry.name})" if entry.issuer else entry.name


def extract_qr_uri(image_path):
    """Read QR code(s) from the given image and return the first otpauth URI."""
    img = Image.open(image_path)
    decoded = qr_decode(img)
    for obj in decoded:
        text = obj.data.decode("utf-8")
        if text.startswith("otpauth-migration://"):
            return text
    raise RuntimeError(f"No otpauth-migration QR found in {image_path}")


# --- Main ---
def main():
    uris = []
    for fn in glob.glob("qrcodes/*.txt"):
        if fn in IGNORE_TXT_FILES:
            print(f"[i] Ignored file: {fn}", file=sys.stderr)
            continue
        with open(fn, encoding="utf-8") as f:
            uris.append(f.read().strip())

    for ext in ("png", "jpg", "jpeg"):
        for img in glob.glob(f"qrcodes/*.{ext}"):
            try:
                uri = extract_qr_uri(img)
                uris.append(uri)
            except Exception as e:
                print(f"[!] Skipped {img}: {e}", file=sys.stderr)

    if not uris:
        print("No migration URIs found in .txt or image files.", file=sys.stderr)
        sys.exit(1)

    for uri in uris:
        try:
            payload = decode_migration_uri(uri)
        except Exception as e:
            print(f"[!] Invalid URI: {e}", file=sys.stderr)
            continue

        for entry in payload.otp_parameters:
            label = format_label(entry)
            secret_b32 = base64.b32encode(entry.secret).decode("utf-8").rstrip("=")
            digits = DIGITS_MAP.get(entry.digits, 6)
            algo = ALGO_MAP.get(entry.algorithm, "SHA1")

            if entry.type == TYPE_HOTP:
                hotp = pyotp.HOTP(secret_b32, digits=digits, digest=algo)
                code = hotp.at(entry.counter)
            else:
                totp = pyotp.TOTP(secret_b32, digits=digits, interval=30, digest=algo)
                code = totp.now()

            print(f"{label}: {code}, secret: {secret_b32}")


if __name__ == "__main__":
    main()
