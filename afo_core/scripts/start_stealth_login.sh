#!/bin/bash

# Wrapper to start the Stealth Login process
# Usage: ./start_stealth_login.sh [service]

SERVICE=${1:-openai}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AFO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "👻 Starting Stealth Browser Bridge for: $SERVICE"
echo "   (This will open a Chromium window. Please log in manually.)"

# Run the python script
python3 "$AFO_ROOT/browser_auth/stealth_login.py" "$SERVICE"

echo "✅ If you saved a token, run 'source ./AFO/scripts/export_tokens.sh' to use it."
