#!/usr/bin/env bash
#
# Setup Genie provider in Omni for Namastex
#
# Prerequisites:
#   - Omni running (API on port 8882)
#   - MCP server running (docker compose up)
#   - OMNI_KEY set (Omni API key)
#
# Usage:
#   OMNI_KEY=omni_sk_... ./scripts/setup-genie.sh
#

set -euo pipefail

API="http://localhost:8882/api/v2"
OMNI_KEY="${OMNI_KEY:?Set OMNI_KEY to your Omni API key}"

echo "=== Namastex Genie Setup ==="
echo ""

# --- 1. Create Genie provider ---
echo "[1/4] Creating Genie provider..."
PROVIDER_ID=$(curl -sf -X POST "$API/providers" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d '{
    "name": "nex-genie",
    "schema": "genie",
    "baseUrl": "file://'"$HOME"'/.claude/teams",
    "schemaConfig": {
      "agentName": "omni",
      "targetAgent": "nex",
      "teamName": "namastex-{chat_id}",
      "agentRole": "team-lead",
      "autoSpawn": true,
      "autoSpawnDir": "'"$(pwd)"'"
    }
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

echo "  Provider: $PROVIDER_ID"

# --- 2. Create agent linked to provider ---
echo "[2/4] Creating agent..."
AGENT_ID=$(curl -sf -X POST "$API/agents" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d '{
    "name": "nex",
    "provider": "genie",
    "model": "claude-sonnet-4-20250514",
    "systemPrompt": "You are Nex, Namastex business intelligence assistant. Use MCP tools for data queries."
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

echo "  Agent: $AGENT_ID"

# Link agent to provider
curl -sf -X PATCH "$API/agents/$AGENT_ID" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d "{\"agentProviderId\": \"$PROVIDER_ID\"}" > /dev/null

echo "  Linked agent → provider"

# --- 3. Create WhatsApp instance ---
echo "[3/4] Creating WhatsApp instance..."
INSTANCE_ID=$(curl -sf -X POST "$API/instances" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d '{"name": "report-bot", "channel": "whatsapp-baileys"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

echo "  Instance: $INSTANCE_ID"

# Link instance to agent
curl -sf -X PATCH "$API/instances/$INSTANCE_ID" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d "{\"agentId\": \"$AGENT_ID\", \"agentReplyFilter\": {\"mode\": \"all\"}}" > /dev/null

echo "  Linked instance → agent"

# --- 4. Done ---
echo ""
echo "[4/4] Done!"
echo ""
echo "  Provider: $PROVIDER_ID (genie → nex)"
echo "  Agent:    $AGENT_ID"
echo "  Instance: $INSTANCE_ID (report-bot)"
echo ""
echo "Next steps:"
echo "  1. Connect WhatsApp:"
echo "     curl -X POST $API/instances/$INSTANCE_ID/connect -H 'x-api-key: $OMNI_KEY'"
echo "     curl -X POST $API/instances/$INSTANCE_ID/pair -H 'Content-Type: application/json' -H 'x-api-key: $OMNI_KEY' -d '{\"phoneNumber\": \"+5511999999999\"}'"
echo ""
echo "  2. Link device in WhatsApp: Settings → Linked Devices → Link with phone number"
echo ""
echo "  3. Send a message on WhatsApp and check:"
echo "     ls ~/.claude/teams/namastex-*"
