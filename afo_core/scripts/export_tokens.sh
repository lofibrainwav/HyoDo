#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AFO_ROOT="$(dirname "$SCRIPT_DIR")"

# Execute the python script and eval the output
# We use eval to apply the exports to the current shell if sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced
    eval "$(python3 "$SCRIPT_DIR/export_keys.py")"
    echo "✅ Tokens exported to environment."
else
    # Script is being executed
    echo "⚠️  This script should be sourced to apply variables to your shell:"
    echo "   source $0"
    echo ""
    echo "Preview of exports:"
    python3 "$SCRIPT_DIR/export_keys.py"
fi
