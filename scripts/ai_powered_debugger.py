#!/usr/bin/env python3
"""
AFO 왕국 AI 기반 자동 디버깅 시스템 연구
머신러닝을 활용한 스마트한 오류 수정
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional


class AIPoweredDebugger:
    """AI 기반 자동 디버깅 시스템"""

    def __init__(self) -> None:
        self.error_patterns = self._load_error_patterns()
        self.success_patterns = self._load_success_patterns()
        self.ml_model = self._initialize_ml_model()

    def _load_error_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """학습된 오류 패턴 로드"""
        return {
            "undefined_variable": [
                {
                    "pattern": r"request\.",
                    "context": "async function",
                    "solution": "add_request_parameter",
                    "confidence": 0.95,
                },
                {
                    "pattern": r"(\w+)\.(\w+)",
                    "context": "undefined",
                    "solution": "check_import",
                    "confidence": 0.85,
                },
            ],
            "type_mismatch": [
                {
                    "pattern": r"AsyncGenerator.*dict",
                    "context": "return type",
                    "solution": "fix_async_generator_type",
                    "confidence": 0.90,
                }
            ],
            "import_error": [
                {
                    "pattern": r"could not be resolved",
                    "context": "import",
                    "solution": "suggest_import",
                    "confidence": 0.80,
                }
            ],
        }

    def _load_success_patterns(self) -> Dict[str, List[str]]:
        """성공한 수정 패턴 로드"""
        return {
            "request_parameter": [
                "async def function(request: Request):",
                "from fastapi import Request",
            ],
            "async_generator_type": [
                "-> AsyncGenerator[dict[str, Any], None]",
                "from typing import AsyncGenerator, Any",
            ],
        }

    def _initialize_ml_model(self) -> Dict[str, Any]:
        """간단한 ML 모델 초기화 (룰 기반)"""
        return {
            "patterns": defaultdict(int),
            "success_rate": defaultdict(float),
            "context_weights": {
                "async": 1.2,
                "import": 1.1,
                "type": 1.0,
                "function": 0.9,
            },
        }

    def analyze_error_with_ai(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """AI를 활용한 오류 분석"""
        error_type = error.get("type", "")
        message = error.get("message", "")
        file_path = error.get("file", "")

        # 컨텍스트 분석
        context = self._analyze_context(file_path, error.get("line", 0))

        # 패턴 매칭
        matches = self._find_pattern_matches(error_type, message, context)

        # ML 기반 신뢰도 계산
        best_match = self._select_best_solution(matches, context)

        return {
            "error": error,
            "context": context,
            "matches": matches,
            "best_solution": best_match,
            "confidence": best_match.get("confidence", 0) if best_match else 0,
            "ai_reasoning": self._generate_reasoning(best_match, context),
        }

    def _analyze_context(self, file_path: str, line_no: int) -> Dict[str, Any]:
        """오류 주변 컨텍스트 분석"""
        context = {
            "file_type": "unknown",
            "function_type": "unknown",
            "imports": [],
            "nearby_code": [],
        }

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # 파일 타입 분석
            if any("fastapi" in line for line in lines[:20]):
                context["file_type"] = "fastapi_router"
            elif any("async def" in line for line in lines):
                context["file_type"] = "async_module"

            # 함수 타입 분석
            for i in range(max(0, line_no - 5), min(len(lines), line_no + 5)):
                line = lines[i].strip()
                if "async def" in line:
                    context["function_type"] = "async_function"
                    break
                elif "def " in line:
                    context["function_type"] = "sync_function"
                    break

            # import 분석
            context["imports"] = [
                line.strip() for line in lines[:30] if line.strip().startswith(("import", "from"))
            ]

            # 주변 코드
            context["nearby_code"] = [
                lines[i].strip() for i in range(max(0, line_no - 3), min(len(lines), line_no + 3))
            ]

        except Exception as e:
            context["error"] = str(e)

        return context

    def _find_pattern_matches(
        self, error_type: str, message: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """패턴 매칭 수행"""
        matches = []

        patterns = self.error_patterns.get(error_type, [])

        for pattern in patterns:
            if re.search(pattern["pattern"], message):
                # 컨텍스트 가중치 적용
                confidence = pattern["confidence"]
                context_multiplier = 1.0

                if pattern["context"] in context.get("function_type", ""):
                    context_multiplier = 1.3
                elif pattern["context"] in context.get("file_type", ""):
                    context_multiplier = 1.2

                matches.append(
                    {
                        **pattern,
                        "adjusted_confidence": confidence * context_multiplier,
                        "context_match": pattern["context"] in str(context),
                    }
                )

        return sorted(matches, key=lambda x: x.get("adjusted_confidence", 0), reverse=True)

    def _select_best_solution(
        self, matches: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """최적 솔루션 선택"""
        if not matches:
            return None

        # 가장 높은 신뢰도의 솔루션 선택
        best_match = max(matches, key=lambda x: x.get("adjusted_confidence", 0))

        # ML 모델 기반 추가 검증
        if self._ml_validation(best_match, context):
            return best_match

        return None

    def _ml_validation(self, solution: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """ML 기반 솔루션 검증"""
        solution_type = solution.get("solution", "")

        # 성공 패턴 확인
        _success_patterns = self.success_patterns.get(solution_type, [])

        # 컨텍스트 일치도 확인
        context_score = 0
        for key, weight in self.ml_model["context_weights"].items():
            if key in str(context).lower():
                context_score += weight

        # 성공률 기반 최종 결정
        success_rate = self.ml_model["success_rate"].get(solution_type, 0.5)

        return (context_score > 1.5) and (success_rate > 0.7)

    def _generate_reasoning(
        self, solution: Optional[Dict[str, Any]], context: Dict[str, Any]
    ) -> str:
        """AI 추론 결과 생성"""
        if not solution:
            return "적합한 솔루션을 찾을 수 없습니다."

        reasoning = f"패턴 '{solution.get('pattern', '')}'이 오류 메시지와 일치합니다. "
        reasoning += f"컨텍스트 '{solution.get('context', '')}'가 "
        reasoning += f"{context.get('function_type', 'unknown')}과 일치합니다. "
        reasoning += ".2f"

        return reasoning

    def apply_ai_solution(self, analysis: Dict[str, Any]) -> bool:
        """AI 솔루션 적용"""
        solution = analysis.get("best_solution")
        error = analysis.get("error")

        if not solution or analysis.get("confidence", 0) < 0.8:
            return False

        solution_type = solution.get("solution")

        # 솔루션 타입별 적용
        if solution_type == "add_request_parameter":
            return self._apply_add_request_parameter(error)
        elif solution_type == "fix_async_generator_type":
            return self._apply_fix_async_generator_type(error)
        elif solution_type == "suggest_import":
            return self._apply_suggest_import(error)

        return False

    def _apply_add_request_parameter(self, error: Dict[str, Any]) -> bool:
        """request 파라미터 추가 적용 (기존 로직 재사용)"""
        file_path = error.get("file", "")
        line_no = error.get("line", 0)

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # 함수 정의 찾기 및 수정
            for i in range(max(0, line_no - 10), min(len(lines), line_no + 10)):
                line = lines[i]
                if "async def" in line and "(" in line and ")" in line:
                    if "request" not in line:
                        # request 파라미터 추가
                        paren_idx = line.find("(")
                        next_paren_idx = line.find(")", paren_idx)
                        if next_paren_idx > paren_idx:
                            params = line[paren_idx + 1 : next_paren_idx]
                            if params.strip():
                                new_params = f"request: Request, {params}"
                            else:
                                new_params = "request: Request"
                            lines[i] = line[: paren_idx + 1] + new_params + line[next_paren_idx:]

                            # FastAPI Request import 확인 및 추가
                            self._ensure_import(lines, "from fastapi import Request")

                            with open(file_path, "w") as f:
                                f.writelines(lines)
                            return True
        except Exception:
            pass
        return False

    def _apply_fix_async_generator_type(self, error: Dict[str, Any]) -> bool:
        """AsyncGenerator 타입 수정 적용"""
        file_path = error.get("file", "")
        line_no = error.get("line", 0)

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # 리턴 타입 수정
            for i in range(max(0, line_no - 5), min(len(lines), line_no + 5)):
                line = lines[i]
                if "-> dict" in line and "async def" in line:
                    lines[i] = line.replace("-> dict", "-> AsyncGenerator[dict[str, Any], None]")

                    # AsyncGenerator import 확인 및 추가
                    self._ensure_import(lines, "from typing import AsyncGenerator, Any")

                    with open(file_path, "w") as f:
                        f.writelines(lines)
                    return True
        except Exception:
            pass
        return False

    def _apply_suggest_import(self, error: Dict[str, Any]) -> bool:
        """import 제안 및 적용"""
        message = error.get("message", "")

        # 오류 메시지에서 모듈 이름 추출
        if "sse_starlette" in message:
            return self._add_import(
                error.get("file", ""),
                "from sse_starlette.sse import EventSourceResponse",
            )
        elif "redis" in message:
            return self._add_import(error.get("file", ""), "import redis.asyncio as redis")

        return False

    def _ensure_import(self, lines: List[str], import_statement: str) -> None:
        """import 문이 없으면 추가"""
        for line in lines:
            if import_statement in line:
                return  # 이미 존재함

        # 적절한 위치에 추가
        for i, line in enumerate(lines):
            if line.strip().startswith(("import", "from")):
                continue
            elif line.strip() and not line.strip().startswith("#"):
                lines.insert(i, import_statement + "\n")
                break

    def _add_import(self, file_path: str, import_statement: str) -> bool:
        """파일에 import 문 추가"""
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            self._ensure_import(lines, import_statement)

            with open(file_path, "w") as f:
                f.writelines(lines)
            return True
        except Exception:
            return False

    def learn_from_feedback(self, analysis: Dict[str, Any], success: bool) -> None:
        """피드백으로부터 학습"""
        solution = analysis.get("best_solution", {})
        solution_type = solution.get("solution", "")

        # 성공률 업데이트
        current_rate = self.ml_model["success_rate"].get(solution_type, 0.5)
        self.ml_model["success_rate"][solution_type] = (
            current_rate + (1.0 if success else 0.0)
        ) / 2


def main() -> None:
    """메인 실행 함수"""
    debugger = AIPoweredDebugger()

    print("🤖 AFO 왕국 AI 기반 자동 디버깅 시스템 연구\n")

    # 샘플 오류들로 테스트
    sample_errors = [
        {
            "type": "undefined_variable",
            "message": '"request" is not defined',
            "file": "packages/afo-core/api/routers/debugging.py",
            "line": 42,
        },
        {
            "type": "type_mismatch",
            "message": "AsyncGenerator type mismatch",
            "file": "packages/afo-core/api/routers/debugging.py",
            "line": 14,
        },
    ]

    print("🧠 AI 기반 오류 분석 실행\n")

    successful_fixes = 0

    for i, error in enumerate(sample_errors, 1):
        print(f"{i}. 오류 분석: {error.get('message', '')}")

        # AI 분석
        analysis = debugger.analyze_error_with_ai(error)

        print(f"   AI 추론: {analysis.get('ai_reasoning', '')}")
        print(f"   신뢰도: {analysis.get('confidence', 0):.2f}")  # 솔루션 적용
        if analysis.get("confidence", 0) > 0.8:
            success = debugger.apply_ai_solution(analysis)
            if success:
                successful_fixes += 1
                print("   ✅ 자동 수정 적용 성공")
            else:
                print("   ❌ 자동 수정 적용 실패")
        else:
            print("   ⚠️ 신뢰도가 낮아 수동 검토 필요")

        print()

        # 학습
        debugger.learn_from_feedback(analysis, success if "success" in locals() else False)

    print("📊 AI 디버깅 연구 결과:")
    print(f"   분석된 오류: {len(sample_errors)}개")
    print(f"   자동 수정 성공: {successful_fixes}개")
    print(
        f"   AI 모델 정확도: 평균 {(sum(debugger.ml_model['success_rate'].values()) / len(debugger.ml_model['success_rate']) * 100):.1f}%"
    )

    print("\n🔮 향후 발전 방향:")
    print("1. 더 큰 데이터셋으로 패턴 학습")
    print("2. 딥러닝 모델 적용으로 정확도 향상")
    print("3. 자연어 처리로 오류 메시지 이해 향상")
    print("4. 컨텍스트 인식으로 더 정확한 수정")
    print("5. 사용자 피드백 기반 지속 학습")

    print("\n✅ AI 기반 자동 디버깅 시스템 연구 완료")


if __name__ == "__main__":
    main()
