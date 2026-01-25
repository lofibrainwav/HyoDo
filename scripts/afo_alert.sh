#!/usr/bin/env bash
# AFO Kingdom Alert System
# Usage: ./scripts/afo_alert.sh <level> <title> <message>
# Levels: info, warning, error, critical
# Requires: SLACK_WEBHOOK_URL or DISCORD_WEBHOOK_URL env var

set -euo pipefail
trap 'echo "❌ Alert failed at line $LINENO"; exit 1' ERR

LEVEL="${1:-info}"
TITLE="${2:-AFO Kingdom Alert}"
MESSAGE="${3:-No message provided}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Emoji mapping
case "$LEVEL" in
    info)     EMOJI="ℹ️"; COLOR="#2196F3" ;;
    warning)  EMOJI="⚠️"; COLOR="#FFC107" ;;
    error)    EMOJI="❌"; COLOR="#F44336" ;;
    critical) EMOJI="🚨"; COLOR="#B71C1C" ;;
    success)  EMOJI="✅"; COLOR="#4CAF50" ;;
    *)        EMOJI="📢"; COLOR="#9E9E9E" ;;
esac

echo "$EMOJI [$LEVEL] $TITLE: $MESSAGE"

# Slack Webhook
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    PAYLOAD=$(cat <<EOF
{
    "attachments": [{
        "color": "$COLOR",
        "title": "$EMOJI $TITLE",
        "text": "$MESSAGE",
        "footer": "AFO Kingdom Alert System",
        "ts": $(date +%s)
    }]
}
EOF
)
    curl -sS -X POST -H 'Content-type: application/json' \
        --data "$PAYLOAD" \
        "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || echo "⚠️ Slack send failed"
    echo "📤 Slack notification sent"
fi

# Discord Webhook
if [[ -n "${DISCORD_WEBHOOK_URL:-}" ]]; then
    PAYLOAD=$(cat <<EOF
{
    "embeds": [{
        "title": "$EMOJI $TITLE",
        "description": "$MESSAGE",
        "color": $(printf '%d' "0x${COLOR:1}"),
        "footer": {"text": "AFO Kingdom | $TIMESTAMP"}
    }]
}
EOF
)
    curl -sS -X POST -H 'Content-type: application/json' \
        --data "$PAYLOAD" \
        "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1 || echo "⚠️ Discord send failed"
    echo "📤 Discord notification sent"
fi

# Fallback: local log
if [[ -z "${SLACK_WEBHOOK_URL:-}" && -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
    mkdir -p artifacts/alerts
    echo "[$TIMESTAMP] [$LEVEL] $TITLE: $MESSAGE" >> artifacts/alerts/alert_log.txt
    echo "📝 Logged to artifacts/alerts/alert_log.txt (no webhook configured)"
fi
