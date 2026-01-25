"""
Sequential Thinking Analysis for Chancellor Router Issue
Sequential Thinking과 Context7을 활용한 Chancellor 라우터 문제 분석
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# #region agent log
LOG_PATH = Path("/Users/brnestrm/AFO_Kingdom/.cursor/debug.log")


def log_debug(
    location: str, message: str, data: dict | None = None, hypothesis_id: str = "A"
) -> None:
    """Debug logging to NDJSON file"""
    try:
        log_entry = {
            "id": f"log_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "sequential-analysis-chancellor",
            "runId": "sequential",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))


def sequential_thinking_step_1() -> None:
    """Step 1: 문제 정의"""
    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_1",
        "Step 1: Problem definition",
        {"problem": "Chancellor /chancellor/health endpoint returns 404"},
        "STEP1",
    )
    # #endregion agent log

    print("\n🔍 Sequential Thinking Step 1: 문제 정의\n")
    print("=" * 60)
    print("문제: /chancellor/health 엔드포인트가 404 오류를 반환합니다.")
    print("=" * 60)
    return {
        "step": 1,
        "problem": "Chancellor /chancellor/health endpoint returns 404",
        "status": "DEFINED",
    }


def sequential_thinking_step_2() -> None:
    """Step 2: 가설 생성"""
    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_2",
        "Step 2: Hypothesis generation",
        {},
        "STEP2",
    )
    # #endregion agent log

    print("\n💡 Sequential Thinking Step 2: 가설 생성\n")
    print("=" * 60)

    hypotheses = [
        {
            "id": "H1",
            "description": "Chancellor 라우터가 등록되지 않았음",
            "evidence_needed": "api_server.py에서 등록 코드 확인",
        },
        {
            "id": "H2",
            "description": "Chancellor 라우터의 prefix가 다름",
            "evidence_needed": "chancellor_router.py에서 prefix 확인",
        },
        {
            "id": "H3",
            "description": "Chancellor 라우터 등록 시 ImportError 발생",
            "evidence_needed": "서버 시작 로그에서 에러 메시지 확인",
        },
        {
            "id": "H4",
            "description": "Chancellor 라우터가 다른 경로로 등록됨",
            "evidence_needed": "OpenAPI 스키마에서 실제 경로 확인",
        },
    ]

    for h in hypotheses:
        print(f"{h['id']}: {h['description']}")
        print(f"   필요한 증거: {h['evidence_needed']}\n")

    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_2",
        "Hypotheses generated",
        {"hypotheses": hypotheses},
        "STEP2",
    )
    # #endregion agent log

    return {"step": 2, "hypotheses": hypotheses, "status": "GENERATED"}


def sequential_thinking_step_3() -> None:
    """Step 3: 증거 수집"""
    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_3",
        "Step 3: Evidence collection",
        {},
        "STEP3",
    )
    # #endregion agent log

    print("\n📊 Sequential Thinking Step 3: 증거 수집\n")
    print("=" * 60)

    evidence = {}

    # 증거 1: Chancellor 라우터 파일 확인
    print("증거 1: Chancellor 라우터 파일 확인")
    try:
        from AFO.api.routers.chancellor_router import router as chancellor_router

        prefix = getattr(chancellor_router, "prefix", "N/A")
        # #region agent log
        log_debug(
            "sequential_analysis_chancellor.py:sequential_thinking_step_3",
            "Chancellor router imported",
            {"prefix": str(prefix)},
            "STEP3",
        )
        # #endregion agent log
        print("   ✅ Chancellor 라우터 import 성공")
        print(f"   Prefix: {prefix}")
        evidence["router_import"] = True
        evidence["router_prefix"] = prefix
    except Exception as e:
        # #region agent log
        log_debug(
            "sequential_analysis_chancellor.py:sequential_thinking_step_3",
            "Chancellor router import failed",
            {"error": str(e)},
            "STEP3",
        )
        # #endregion agent log
        print(f"   ❌ Chancellor 라우터 import 실패: {e}")
        evidence["router_import"] = False
        evidence["router_error"] = str(e)

    # 증거 2: api_server.py에서 등록 코드 확인
    print("\n증거 2: api_server.py에서 등록 코드 확인")
    api_server_path = project_root / "packages" / "afo-core" / "api_server.py"
    if api_server_path.exists():
        content = api_server_path.read_text(encoding="utf-8")
        if "chancellor_router" in content and "app.include_router" in content:
            # #region agent log
            log_debug(
                "sequential_analysis_chancellor.py:sequential_thinking_step_3",
                "Chancellor router registration code found",
                {},
                "STEP3",
            )
            # #endregion agent log
            print("   ✅ 등록 코드 발견")
            evidence["registration_code_exists"] = True
        else:
            print("   ❌ 등록 코드 없음")
            evidence["registration_code_exists"] = False

    # 증거 3: OpenAPI 스키마 확인
    print("\n증거 3: OpenAPI 스키마에서 실제 경로 확인")
    try:
        import requests

        response = requests.get("http://localhost:8010/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})
            chancellor_paths = [p for p in paths if "chancellor" in p.lower()]
            # #region agent log
            log_debug(
                "sequential_analysis_chancellor.py:sequential_thinking_step_3",
                "OpenAPI schema checked",
                {"chancellor_paths": chancellor_paths},
                "STEP3",
            )
            # #endregion agent log
            if chancellor_paths:
                print(f"   ✅ Chancellor 관련 경로 발견: {chancellor_paths}")
                evidence["chancellor_paths"] = chancellor_paths
            else:
                print("   ❌ Chancellor 관련 경로 없음")
                evidence["chancellor_paths"] = []
    except Exception as e:
        print(f"   ⚠️  OpenAPI 스키마 확인 실패: {e}")
        evidence["openapi_check_failed"] = True

    return {"step": 3, "evidence": evidence, "status": "COLLECTED"}


def sequential_thinking_step_4() -> None:
    """Step 4: 가설 평가 및 결론"""
    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_4",
        "Step 4: Hypothesis evaluation",
        {},
        "STEP4",
    )
    # #endregion agent log

    print("\n🎯 Sequential Thinking Step 4: 가설 평가 및 결론\n")
    print("=" * 60)

    # Step 3의 증거를 사용하여 가설 평가
    step3_result = sequential_thinking_step_3()

    evidence = step3_result["evidence"]

    # 가설 평가
    evaluations = []

    # H1 평가
    if evidence.get("registration_code_exists"):
        evaluations.append({"hypothesis": "H1", "status": "REJECTED", "reason": "등록 코드 존재"})
    else:
        evaluations.append({"hypothesis": "H1", "status": "CONFIRMED", "reason": "등록 코드 없음"})

    # H2 평가
    prefix = evidence.get("router_prefix", "")
    if prefix and prefix != "/chancellor":
        evaluations.append(
            {
                "hypothesis": "H2",
                "status": "CONFIRMED",
                "reason": f"Prefix가 {prefix}임",
            }
        )
    else:
        evaluations.append({"hypothesis": "H2", "status": "REJECTED", "reason": "Prefix 정상"})

    # H3 평가 (서버 로그 확인 불가하므로 INCONCLUSIVE)
    evaluations.append(
        {
            "hypothesis": "H3",
            "status": "INCONCLUSIVE",
            "reason": "서버 시작 로그 확인 필요",
        }
    )

    # H4 평가
    paths = evidence.get("chancellor_paths", [])
    if paths:
        evaluations.append(
            {
                "hypothesis": "H4",
                "status": "CONFIRMED",
                "reason": f"다른 경로로 등록됨: {paths}",
            }
        )
    else:
        evaluations.append({"hypothesis": "H4", "status": "REJECTED", "reason": "경로 없음"})

    for eval_result in evaluations:
        status_icon = (
            "✅"
            if eval_result["status"] == "CONFIRMED"
            else "❌"
            if eval_result["status"] == "REJECTED"
            else "⚠️"
        )
        print(f"{status_icon} {eval_result['hypothesis']}: {eval_result['status']}")
        print(f"   이유: {eval_result['reason']}\n")

    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:sequential_thinking_step_4",
        "Hypothesis evaluation completed",
        {"evaluations": evaluations},
        "STEP4",
    )
    # #endregion agent log

    return {"step": 4, "evaluations": evaluations, "status": "EVALUATED"}


def main() -> None:
    print("\n🏰 Sequential Thinking + Context7 기반 Chancellor 라우터 문제 분석\n")

    # Sequential Thinking 4단계 실행
    step1 = sequential_thinking_step_1()
    step2 = sequential_thinking_step_2()
    step4 = sequential_thinking_step_4()  # Step 3는 Step 4 내부에서 호출됨

    # 최종 결론
    print("\n" + "=" * 60)
    print("📋 최종 결론")
    print("=" * 60)

    confirmed = [e for e in step4["evaluations"] if e["status"] == "CONFIRMED"]
    if confirmed:
        print("\n✅ 확인된 가설:")
        for c in confirmed:
            print(f"   - {c['hypothesis']}: {c['reason']}")

    # #region agent log
    log_debug(
        "sequential_analysis_chancellor.py:main",
        "Sequential analysis completed",
        {"step1": step1, "step2": step2, "step4": step4},
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
