#!/bin/bash
exec > purge.log 2>&1
CF_TOKEN="Xexa9ndS83B6REWJ0fOt2-ebNsyS8otV3VcPHzM3"

echo "Starting Purge..."
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=brnestrm.com" -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ "$ZONE_ID" == "null" ] || [ -z "$ZONE_ID" ]; then
    echo "ERROR: Failed to get Zone ID"
    exit 1
fi
echo "Zone ID: $ZONE_ID"

echo "Fetching records..."
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?per_page=100" -H "Authorization: Bearer $CF_TOKEN" > records.json

RECORD_COUNT=$(jq '.result | length' records.json)
echo "Total Records: $RECORD_COUNT"

echo "Identifying Zombies..."
ZOMBIE_IDS=$(jq -r '.result[] | select(.content == "91.99.189.125" or .content == "46.224.141.113" or .content == "91.98.227.86" or .content == "46.224.49.91") | .id' records.json)

COUNT=0
for id in $ZOMBIE_IDS; do
    name=$(jq -r ".result[] | select(.id == \"$id\") | .name" records.json)
    ip=$(jq -r ".result[] | select(.id == \"$id\") | .content" records.json)
    echo "💀 Deleting $name -> $ip ($id)..."
    
    curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$id"          -H "Authorization: Bearer $CF_TOKEN"          -H "Content-Type: application/json" | jq -r '.success'
    COUNT=$((COUNT+1))
done

echo "Purge Complete. Deleted $COUNT records."
