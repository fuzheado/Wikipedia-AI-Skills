#!/usr/bin/env bash
# LiftWing LLM chat completions via the Toolforge bastion (higher rate-limit tier).
#
# Why: public access to the LiftWing LLM endpoint is capped at a shared
# 100 requests/hour PER CLIENT IP (HTTP 429 when exceeded). Requests sent
# from Toolforge egress IPs are automatically on the higher
# ("effectively unlimited") tier — no API key, no request needed, same
# endpoint. This script builds the payload locally and runs curl on the
# Toolforge bastion over SSH, so prompts with arbitrary quoting work.
#
# Usage:
#   ./llm-toolforge.sh <prompt> [model] [max_tokens] [count]
#
#   prompt       The user message
#   model        llm-qwen3-14b (default) | llm-qwen36-27b
#   max_tokens   Completion cap (default 256)
#   count        Burst: run the request this many times back-to-back
#                (default 1) and report an ok/429/other summary.
#
# Environment:
#   TOOLFORGE_SSH      SSH target (default: $USER@dev.toolforge.org;
#                      prod bastion: $USER@login.toolforge.org)
#   WIKIMEDIA_USER_AGENT  User-Agent for requests (descriptive UA required)
#
# Examples:
#   ./llm-toolforge.sh "Explain vLLM in one sentence."
#   ./llm-toolforge.sh "Translate to Spanish: The quick brown fox" llm-qwen36-27b
#   ./llm-toolforge.sh "Reply with exactly: OK" llm-qwen3-14b 8 50   # 50-request burst
#
# Verified 2026-09-09: 100-request burst from dev.toolforge.org → 0x429 in ~14s.

set -euo pipefail

PROMPT="${1:?Usage: $0 <prompt> [model] [max_tokens] [count]}"
MODEL="${2:-llm-qwen3-14b}"
MAX_TOKENS="${3:-256}"
COUNT="${4:-1}"
SSH_TARGET="${TOOLFORGE_SSH:-${USER}@dev.toolforge.org}"
UA="${WIKIMEDIA_USER_AGENT:-LiftWingLLMCLI/1.0 (user@example.com) LiftWingLLMTest}"
URL="https://api.wikimedia.org/service/lw/inference/v1/models/${MODEL}/openai/v1/chat/completions"

# Build the JSON payload locally, base64-encode it → immune to shell-quoting
# issues across the SSH hop. Decoding happens on the (Linux) remote side.
PAYLOAD_B64=$(python3 - "$MODEL" "$MAX_TOKENS" "$PROMPT" <<'PY'
import base64, json, sys
model, max_tokens, prompt = sys.argv[1], int(sys.argv[2]), sys.argv[3]
payload = {"model": model, "max_tokens": max_tokens,
           "messages": [{"role": "user", "content": prompt}]}
sys.stdout.write(base64.b64encode(json.dumps(payload).encode()).decode())
PY
)

# ssh joins argv with spaces on the remote side, so quote each argument
# explicitly for the remote shell. b64 and the URL are safe chars; the UA
# may contain spaces/parens, so escape single quotes (' -> '\'' ).
ua_q=${UA//\'/\'\\\'\'}
REMOTE_CMD="bash -s -- '$PAYLOAD_B64' '$ua_q' '$URL'"

if [ "$COUNT" -eq 1 ]; then
    ssh "$SSH_TARGET" "$REMOTE_CMD" <<'REMOTE'
b64="$1"; UA="$2"; URL="$3"
payload=$(echo "$b64" | base64 -d)
curl -sS -w '\n[HTTP %{http_code}]\n' -A "$UA" \
  -H 'Content-Type: application/json' -d "$payload" "$URL"
REMOTE
    exit $?
fi

echo "→ Burst: $COUNT × $MODEL via $SSH_TARGET" >&2
REMOTE_CMD="$REMOTE_CMD '$COUNT'"
ssh "$SSH_TARGET" "$REMOTE_CMD" <<'REMOTE'
b64="$1"; UA="$2"; URL="$3"; COUNT="$4"
payload=$(echo "$b64" | base64 -d)
ok=0; r429=0; other=0
for i in $(seq 1 "$COUNT"); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -A "$UA" \
        -H 'Content-Type: application/json' -d "$payload" "$URL")
    case "$code" in
        200) ok=$((ok+1));;
        429) r429=$((r429+1));;
        *)   other=$((other+1)); echo "  request $i -> HTTP $code" >&2;;
    esac
done
echo "BURST via Toolforge: ok=$ok 429=$r429 other=$other (model=$URL)"
REMOTE
