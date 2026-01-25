#!/bin/bash
EMAIL="bigbananamusic@gmail.com"
KEY="60653be292b5ecb225f02a672b628b759752e"
ACCOUNT_ID="ad3a31d2ccfea3d3a26c28a1c0924edb"
TUNNEL_ID="f88a3b8d-e235-4e55-9a97-84ae03f6f4fc"

# 1. Check Status
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels/$TUNNEL_ID"      -H "X-Auth-Email: $EMAIL"      -H "X-Auth-Key: $KEY"      -H "Content-Type: application/json" > status.json

# 2. Update Config (Try 'caddy' service name)
read -r -d '' BODY <<EOM
{
  "config": {
    "ingress": [
      {
        "hostname": "*.brnestrm.com",
        "service": "http://caddy:80"
      },
      {
        "hostname": "brnestrm.com",
        "service": "http://caddy:80"
      },
      {
        "service": "http_status:404"
      }
    ]
  }
}
EOM

curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels/$TUNNEL_ID/configurations"      -H "X-Auth-Email: $EMAIL"      -H "X-Auth-Key: $KEY"      -H "Content-Type: application/json"      -d "$BODY" > config_update.log
