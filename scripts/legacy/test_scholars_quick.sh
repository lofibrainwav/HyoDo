#!/bin/bash
# Scholar MCP 도구 테스트 스크립트

cd /Users/brnestrm/AFO_Kingdom

echo "=========================================="
echo "🧪 Scholar MCP Tools Test"
echo "=========================================="

# 테스트 1: Initialize
echo ""
echo "📋 [TEST 1] Initialize"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python -u packages/trinity-os/trinity_os/servers/afo_scholars_mcp.py 2>/dev/null | tail -1 | python -c "import sys, json; r=json.load(sys.stdin); print('✅ PASS' if r.get('result',{}).get('serverInfo',{}).get('name') == 'afo-scholars-mcp' else '❌ FAIL')"

# 테스트 2: Tools List
echo ""
echo "📋 [TEST 2] Tools List"
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_scholars_mcp.py 2>/dev/null | tail -1 | python -c "import sys, json; r=json.load(sys.stdin); tools = r.get('result',{}).get('tools',[]); print(f'✅ PASS (Found {len(tools)} tools)' if len(tools) >= 8 else '❌ FAIL')"

# 테스트 3: Scholar 도구 이름 검증
echo ""
echo "📋 [TEST 3] Tool Names Validation"
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_scholars_mcp.py 2>/dev/null | tail -1 | python -c "
import sys, json
r = json.load(sys.stdin)
tools = r.get('result', {}).get('tools', [])
tool_names = [t['name'] for t in tools]
expected = [
    'scholar_bangtong_implement',
    'scholar_bangtong_review',
    'scholar_jaryong_verify',
    'scholar_jaryong_refactor',
    'scholar_yukson_strategy',
    'scholar_yeongdeok_document',
    'scholar_yeongdeok_security_scan',
    'scholar_yeongdeok_summarize',
]
missing = [n for n in expected if n not in tool_names]
if missing:
    print(f'❌ FAIL (Missing: {missing})')
else:
    print('✅ PASS (All 8 tools present)')
for name in tool_names:
    print(f'  - {name}')
"

# 테스트 4: JSON-RPC 구조 검증
echo ""
echo "📋 [TEST 4] JSON-RPC Structure Validation"
echo '{"jsonrpc":"2.0","id":99,"method":"invalid_method"}' | python -u packages/trinity-os/trinity_os/servers/afo_scholars_mcp.py 2>/dev/null | tail -1 | python -c "
import sys, json
try:
    r = json.load(sys.stdin)
    has_error = 'error' in r
    print('✅ PASS (Error response valid)' if has_error else '❌ FAIL (Missing error)')
    print(f'  Error code: {r.get(\"error\", {}).get(\"code\")}')
except Exception as e:
    print(f'❌ FAIL (JSON parse error: {e})')
"

echo ""
echo "=========================================="
echo "📊 Test Suite Complete"
echo "=========================================="
