# Google Authenticator Exporter

This project is a simple Python tool that lets you:

* **Import** your Google Authenticator export URIs (both `.txt` files and QR code images).
* **Decode** the Google "migration" protobuf payload into individual TOTP/HOTP accounts.
* **Print** each account's current one‑time code and its Base32 secret, ready to import into any other authenticator app.

This is ideal for migrating or backing up your two‑factor accounts in bulk, entirely offline and under your control.

## Features

* **Multi‑format input**: Read `otpauth-migration://…?data=` URIs from `.txt` files or directly scan QR code images.
* **Protocol buffers**: Uses your own `migration.proto` schema (generated via `protoc`) to parse Google's export payload.
* **TOTP & HOTP support**: Handles both time‑based (TOTP) and counter‑based (HOTP) OTPs.
* **Export-ready secrets**: Outputs Base32‑encoded secrets so you can re‑import into other apps.
* **Configurable ignores**: Skip any `.txt` exports you no longer want to process.
* **Directory‑scoped**: All inputs live in `qrcodes/`, keeping your workspace tidy.

## Prerequisites

1. **Python 3.7+**
2. **Protobuf compiler** (`protoc`) to generate Python bindings from `migration.proto`
3. **System QR library** (libzbar0)

## Installation & Setup

1. **Clone the repo**

   ```bash
   git clone git@github.com:k-paul-acct/google-authenticator-exporter.git
   cd google-authenticator-exporter
   ```
2. **Create & activate a virtualenv**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate

   # Install pip-tools into your virtualenv
   pip install pip-tools
   ```

3. **Generate protobuf bindings** (optional)

   ```bash
   protoc --python_out=. migration.proto
   ```

   This produces `migration_pb2.py` (used by `main.py`).

4. **Compile and install dependencies**

   ```bash
   # Pin your runtime deps
   pip-compile requirements.in
   pip-sync requirements.txt

   # Pin your dev deps (for testing/linting)
   pip-compile requirements-dev.in
   pip-sync requirements.txt requirements-dev.txt
   ```

   This ensures reproducible installs via \[pip‑tools].

## Usage

1. **Prepare your inputs**

   * Drop any `*.txt` files containing a single `otpauth-migration://…?data=` URI into `qrcodes/`.
   * Drop any screenshots/export QR codes (`*.png`, `*.jpg`, `*.jpeg`) into `qrcodes/`.

2. **Optionally configure ignores**

   Open `main.py` and adjust the `IGNORE_TXT_FILES` set to skip files you don’t want processed.

3. **Run the exporter**

   ```bash
   python main.py
   ```

   You’ll see lines like:

   ```
   GitHub (alice@example.com): 123456, secret: JBSWY3DPEHPK3PXP
   Google (alice@gmail.com): 654321, secret: KRSXG5DSMFZXI===
   ```
