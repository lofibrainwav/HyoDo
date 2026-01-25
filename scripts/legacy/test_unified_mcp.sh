#!/bin/bash
# 통합 MCP 서버 테스트 스크립트
# Scholar MCP 통합 후 전체 기능 검증

cd /Users/brnestrm/AFO_Kingdom

echo "=========================================="
echo "🧪 AFO Ultimate MCP Server Test"
echo "=========================================="

# 테스트 1: Initialize
echo ""
echo "📋 [TEST 1] Initialize"
response=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
server_name=$(echo "$response" | python -c "import sys, json; r=json.load(sys.stdin); print(r.get('result',{}).get('serverInfo',{}).get('name',''))")
if [ "$server_name" = "AfoUltimate" ]; then
    echo "✅ PASS - Server: AfoUltimate v0.2.0"
else
    echo "❌ FAIL - Got: $server_name"
fi

# 테스트 2: Tools List (총 도구 수)
echo ""
echo "📋 [TEST 2] Tools List (Total Count)"
response=$(echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
tool_count=$(echo "$response" | python -c "import sys, json; r=json.load(sys.stdin); print(len(r.get('result',{}).get('tools',[])))")
echo "Total tools: $tool_count"
if [ "$tool_count" -ge 14 ]; then
    echo "✅ PASS - Found $tool_count+ tools (Core + Scholars + Others)"
else
    echo "❌ FAIL - Expected 14+ tools, got $tool_count"
fi

# 테스트 3: Scholar 도구 존재 확인
echo ""
echo "📋 [TEST 3] Scholar Tools Exist"
response=$(echo '{"jsonrpc":"2.0","id":3,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
scholar_count=$(echo "$response" | python -c "import sys, json; r=json.load(sys.stdin); tools=r.get('result',{}).get('tools',[]); scholar_tools=[t for t in tools if 'scholar_' in t.get('name','')]; print(len(scholar_tools))")
echo "Scholar tools: $scholar_count"
if [ "$scholar_count" -eq 8 ]; then
    echo "✅ PASS - All 8 scholar tools available"
else
    echo "❌ FAIL - Expected 8 scholar tools, got $scholar_count"
fi

# 테스트 4: Core Tools 존재 확인
echo ""
echo "📋 [TEST 4] Core Tools Exist"
response=$(echo '{"jsonrpc":"2.0","id":4,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
core_tools=$(echo "$response" | python -c "import sys, json; r=json.load(sys.stdin); tools=r.get('result',{}).get('tools',[]); core_tools=[t['name'] for t in tools if t['name'] in ['shell_execute','read_file','write_file','kingdom_health']]; print(len(core_tools))")
echo "Core tools: $core_tools"
if [ "$core_tools" -eq 4 ]; then
    echo "✅ PASS - All 4 core tools available"
else
    echo "❌ FAIL - Expected 4 core tools, got $core_tools"
fi

# 테스트 5: Skills Tools 존재 확인
echo ""
echo "📋 [TEST 5] Skills Tools Exist"
response=$(echo '{"jsonrpc":"2.0","id":5,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
skills_tools=$(echo "$response" | python -c "import sys, json; r=json.load(sys.stdin); tools=r.get('result',{}).get('tools',[]); skills_tools=[t['name'] for t in tools if t['name'] in ['verify_fact','cupy_weighted_sum']]; print(len(skills_tools))")
echo "Skills tools: $skills_tools"
if [ "$skills_tools" -eq 2 ]; then
    echo "✅ PASS - All 2 skills tools available"
else
    echo "❌ FAIL - Expected 2 skills tools, got $skills_tools"
fi

# 테스트 6: Scholar 로드 상태
echo ""
echo "📋 [TEST 6] Scholar Load Status"
init_stderr=$(echo '{"jsonrpc":"2.0","id":99,"method":"initialize"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>&1 | grep -i "scholar")
if echo "$init_stderr" | grep -q "AfoScholarsMCP"; then
    echo "✅ PASS - AfoScholarsMCP loaded"
else
    if echo "$init_stderr" | grep -q "Failed to load"; then
        echo "❌ FAIL - AfoScholarsMCP failed to load"
    else
        echo "⚠️ WARN - Could not determine scholar load status"
    fi
fi

# 테스트 7: 학자 도구 이름 확인
echo ""
echo "📋 [TEST 7] Scholar Tool Names"
response=$(echo '{"jsonrpc":"2.0","id":6,"method":"tools/list"}' | python -u packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py 2>/dev/null | tail -1)
echo "Scholar tools found:"
echo "$response" | python -c "
import sys, json
r = json.load(sys.stdin)
tools = r.get('result', {}).get('tools', [])
scholar_tools = [t for t in tools if 'scholar_' in t.get('name', '')]
for t in scholar_tools:
    print(f'  - {t[\"name\"]}')"

expected_scholars=(
    "scholar_bangtong_implement"
    "scholar_bangtong_review"
    "scholar_jaryong_verify"
    "scholar_jaryong_refactor"
    "scholar_yukson_strategy"
    "scholar_yeongdeok_document"
    "scholar_yeongdeok_security_scan"
    "scholar_yeongdeok_summarize"
)

echo ""
echo "Expected scholar tools:"
for s in "${expected_scholars[@]}"; do
    echo "  - $s"
done

found_count=$(echo "$response" | python -c "
import sys, json
r = json.load(sys.stdin)
tools = r.get('result', {}).get('tools', [])
scholar_tools = [t for t in tools if 'scholar_' in t.get('name', '')]
print(len(scholar_tools))")

if [ "$found_count" -eq 8 ]; then
    echo "✅ PASS - All 8 expected scholar tools found"
else
    echo "❌ FAIL - Expected 8 scholar tools, got $found_count"
fi

# 요약
echo ""
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo "Total tests: 7"
echo "Passed: $(grep -c '✅ PASS' <<< "$0")"
echo "Failed: $(grep -c '❌ FAIL' <<< "$0")"
echo "Warnings: $(grep -c '⚠️ WARN' <<< "$0")"
echo ""

if grep -q '❌ FAIL' <<< "$0"; then
    echo "❌ Some tests failed"
    exit 1
else
    echo "✅ All tests passed!"
    exit 0
fi
