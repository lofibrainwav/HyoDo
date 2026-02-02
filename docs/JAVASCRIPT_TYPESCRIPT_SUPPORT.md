# JavaScript/TypeScript Support Design

> **"眞善美孝永을 JavaScript 세계로"** - 언어 중립적 품질 철학

---

## 🎯 목표

HyoDo를 Python 프로젝트에서 JavaScript/TypeScript 프로젝트로 확장

---

## 🔍 JS/TS 생태계 도구 매핑

### 4-Gate CI 매핑

| Gate | Python | JavaScript/TypeScript | 역할 |
|------|--------|----------------------|------|
| 眞 Truth | Pyright | TypeScript Compiler (tsc) | 타입 검사 |
| 美 Beauty | Ruff | ESLint + Prettier | 린트/포맷 |
| 善 Goodness | pytest | Jest / Vitest | 테스트 |
| 永 Eternity | SBOM | npm audit / Snyk | 보안 |

### 도구별 상세 비교

#### 타입 검사 (眞 Truth)

| 특성 | Pyright | TypeScript Compiler |
|------|---------|-------------------|
| 엄격도 | Strict | strict/nullChecks |
| 성능 | 빠름 | 빠름 |
| 설정 | pyproject.toml | tsconfig.json |
| 출력 | JSON | JSON |

**통합 방식**:
```bash
# HyoDo가 tsc 실행
tsc --noEmit --project tsconfig.json --pretty false
```

#### 린트/포맷 (美 Beauty)

| 특성 | Ruff | ESLint + Prettier |
|------|------|------------------|
| 속도 | 매우 빠름 | 빠름 |
| 규칙 | 500+ | 200+ (ESLint) |
| 자동 수정 | ✅ | ✅ |
| 설정 | pyproject.toml | .eslintrc, .prettierrc |

**통합 방식**:
```bash
# ESLint 실행
eslint . --format json --ext .js,.ts,.jsx,.tsx

# Prettier 실행
prettier --check "**/*.{js,ts,jsx,tsx,json,css,md}"
```

#### 테스트 (善 Goodness)

| 특성 | pytest | Jest | Vitest |
|------|--------|------|--------|
| 속도 | 빠름 | 빠름 | 매우 빠름 |
| 병렬 실행 | ✅ | ✅ | ✅ (기본) |
| 커버리지 | pytest-cov | 내장 | 내장 |
| 스냅샷 | pytest-snapshot | 내장 | 내장 |
| 모킹 | pytest-mock | jest.mock | vi.mock |

**통합 방식**:
```bash
# Jest 실행
jest --coverage --json --outputFile=jest-results.json

# Vitest 실행
vitest run --coverage --reporter=json
```

#### 보안 (永 Eternity)

| 특성 | SBOM | npm audit | Snyk |
|------|------|-----------|------|
| 취약점 DB | OSV | npm | Snyk |
| 라이선스 | ✅ | ❌ | ✅ |
| CI 통합 | ✅ | ✅ | ✅ |

**통합 방식**:
```bash
# npm audit
npm audit --json

# Snyk
snyk test --json
```

---

## 🏗️ 아키텍처 설계

### 플러그인 아키텍처

```python
# hyodo/languages/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class LanguagePlugin(ABC):
    """언어 플러그인 기본 클래스"""
    
    name: str
    extensions: List[str]
    
    @abstractmethod
    def check_truth(self, files: List[str]) -> Dict[str, Any]:
        """眞 (Truth) - 타입 검사"""
        pass
    
    @abstractmethod
    def check_beauty(self, files: List[str]) -> Dict[str, Any]:
        """美 (Beauty) - 린트/포맷"""
        pass
    
    @abstractmethod
    def check_goodness(self, files: List[str]) -> Dict[str, Any]:
        """善 (Goodness) - 테스트"""
        pass
    
    @abstractmethod
    def check_eternity(self, files: List[str]) -> Dict[str, Any]:
        """永 (Eternity) - 보안"""
        pass
```

### Python 플러그인 (기존)

```python
# hyodo/languages/python.py
from .base import LanguagePlugin

class PythonPlugin(LanguagePlugin):
    name = "python"
    extensions = [".py"]
    
    def check_truth(self, files):
        # Pyright 실행
        return run_pyright(files)
    
    def check_beauty(self, files):
        # Ruff 실행
        return run_ruff(files)
    
    def check_goodness(self, files):
        # pytest 실행
        return run_pytest(files)
    
    def check_eternity(self, files):
        # SBOM 생성
        return generate_sbom()
```

### JavaScript/TypeScript 플러그인 (신규)

```python
# hyodo/languages/javascript.py
from .base import LanguagePlugin
import subprocess
import json

class JavaScriptPlugin(LanguagePlugin):
    name = "javascript"
    extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
    
    def __init__(self, config=None):
        self.config = config or {}
        self.use_typescript = self._detect_typescript()
        self.test_runner = self._detect_test_runner()
    
    def _detect_typescript(self) -> bool:
        """TypeScript 사용 여부 감지"""
        return (
            Path("tsconfig.json").exists() or
            any(f.suffix in ['.ts', '.tsx'] for f in self._get_project_files())
        )
    
    def _detect_test_runner(self) -> str:
        """테스트 러너 감지"""
        if Path("vitest.config.ts").exists() or Path("vitest.config.js").exists():
            return "vitest"
        elif Path("jest.config.js").exists() or Path("jest.config.ts").exists():
            return "jest"
        return "jest"  # 기본값
    
    def check_truth(self, files):
        """眞 - TypeScript 컴파일러 실행"""
        if not self.use_typescript:
            return {"status": "skipped", "reason": "TypeScript not detected"}
        
        cmd = ["tsc", "--noEmit", "--pretty", "false"]
        if Path("tsconfig.json").exists():
            cmd.extend(["--project", "tsconfig.json"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # tsc 출력 파싱
        errors = self._parse_tsc_output(result.stdout)
        
        return {
            "tool": "tsc",
            "status": "pass" if result.returncode == 0 else "fail",
            "errors": errors,
            "score": max(0, 1 - len(errors) * 0.01)  # 오류 1개당 1% 감점
        }
    
    def check_beauty(self, files):
        """美 - ESLint + Prettier 실행"""
        results = {}
        
        # ESLint
        if self._has_eslint():
            eslint_result = self._run_eslint(files)
            results["eslint"] = eslint_result
        
        # Prettier
        if self._has_prettier():
            prettier_result = self._run_prettier(files)
            results["prettier"] = prettier_result
        
        # 종합 점수
        scores = [r["score"] for r in results.values()]
        avg_score = sum(scores) / len(scores) if scores else 1.0
        
        return {
            "tools": results,
            "status": "pass" if avg_score >= 0.9 else "fail",
            "score": avg_score
        }
    
    def check_goodness(self, files):
        """善 - Jest/Vitest 실행"""
        runner = self.test_runner
        
        if runner == "vitest":
            return self._run_vitest()
        else:
            return self._run_jest()
    
    def check_eternity(self, files):
        """永 - npm audit 실행"""
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True,
            text=True
        )
        
        audit_data = json.loads(result.stdout) if result.stdout else {}
        vulnerabilities = audit_data.get("metadata", {}).get("vulnerabilities", {})
        
        total_vulns = sum(vulnerabilities.values())
        
        return {
            "tool": "npm-audit",
            "status": "pass" if total_vulns == 0 else "warn",
            "vulnerabilities": vulnerabilities,
            "score": max(0, 1 - total_vulns * 0.05)  # 취약점 1개당 5% 감점
        }
    
    def _run_eslint(self, files):
        """ESLint 실행"""
        cmd = [
            "eslint",
            "--format", "json",
            "--ext", ".js,.jsx,.ts,.tsx"
        ]
        cmd.extend(files)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            eslint_output = json.loads(result.stdout)
            error_count = sum(len(f["messages"]) for f in eslint_output)
        except json.JSONDecodeError:
            error_count = 0
        
        return {
            "tool": "eslint",
            "errors": error_count,
            "score": max(0, 1 - error_count * 0.005)
        }
    
    def _run_prettier(self, files):
        """Prettier 실행"""
        cmd = ["prettier", "--check"] + files
        result = subprocess.run(cmd, capture_output=True)
        
        return {
            "tool": "prettier",
            "status": "pass" if result.returncode == 0 else "fail",
            "score": 1.0 if result.returncode == 0 else 0.8
        }
    
    def _run_jest(self):
        """Jest 실행"""
        cmd = [
            "jest",
            "--coverage",
            "--json",
            "--outputFile=/tmp/jest-results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        try:
            with open("/tmp/jest-results.json") as f:
                jest_data = json.load(f)
            
            coverage = jest_data.get("coverageMap", {})
            total_tests = jest_data.get("numTotalTests", 0)
            passed_tests = jest_data.get("numPassedTests", 0)
            
            return {
                "tool": "jest",
                "status": "pass" if result.returncode == 0 else "fail",
                "tests": {"total": total_tests, "passed": passed_tests},
                "score": passed_tests / total_tests if total_tests > 0 else 1.0
            }
        except (FileNotFoundError, json.JSONDecodeError):
            return {"tool": "jest", "status": "error", "score": 0.0}
    
    def _run_vitest(self):
        """Vitest 실행"""
        cmd = [
            "vitest",
            "run",
            "--reporter=json",
            "--outputFile=/tmp/vitest-results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        # Vitest 결과 파싱
        return {
            "tool": "vitest",
            "status": "pass" if result.returncode == 0 else "fail",
            "score": 1.0 if result.returncode == 0 else 0.5
        }
```

---

## 📊 Trinity Score 매핑

### JavaScript/TypeScript용 점수 계산

```python
def calculate_js_trinity_score(results: Dict) -> float:
    """
    JS/TS 프로젝트용 Trinity Score 계산
    """
    # 眞 (35%) - 타입 검사
    truth_score = results["truth"]["score"]
    
    # 善 (35%) - 테스트
    goodness_score = results["goodness"]["score"]
    
    # 美 (20%) - 린트/포맷
    beauty_score = results["beauty"]["score"]
    
    # 孝 (8%) - 패키지 최신성
    serenity_score = check_package_freshness()
    
    # 永 (2%) - 보안
    eternity_score = results["eternity"]["score"]
    
    return (
        truth_score * 0.35 +
        goodness_score * 0.35 +
        beauty_score * 0.20 +
        serenity_score * 0.08 +
        eternity_score * 0.02
    ) * 100


def check_package_freshness() -> float:
    """
    孝 (Serenity) - 패키지 최신성 확인
    
    outdated 패키지 비율로 점수 계산
    """
    result = subprocess.run(
        ["npm", "outdated", "--json"],
        capture_output=True,
        text=True
    )
    
    try:
        outdated = json.loads(result.stdout)
        total_deps = len(outdated)
        
        if total_deps == 0:
            return 1.0
        
        # Major 업데이트 필요한 패키지 카운트
        major_updates = sum(
            1 for dep in outdated.values()
            if dep.get("current", "").split(".")[0] != 
               dep.get("latest", "").split(".")[0]
        )
        
        # Major 업데이트 1개당 10% 감점
        return max(0, 1 - major_updates / total_deps * 0.1)
    except json.JSONDecodeError:
        return 1.0
```

---

## 🔧 설정 파일

### `.hyodorc.json` (JS/TS 설정)

```json
{
  "language": "javascript",
  "typescript": {
    "configFile": "tsconfig.json",
    "strict": true
  },
  "eslint": {
    "configFile": ".eslintrc.json",
    "extensions": [".js", ".jsx", ".ts", ".tsx"]
  },
  "prettier": {
    "configFile": ".prettierrc"
  },
  "test": {
    "runner": "vitest",
    "coverage": true
  },
  "trinity": {
    "thresholds": {
      "autoRun": 90,
      "askCommander": 70
    }
  }
}
```

---

## 🚀 사용 예시

### CLI 사용

```bash
# JS/TS 프로젝트에서 HyoDo 실행
hyodo check --language javascript

# TypeScript 강제
hyodo check --language typescript --strict

# 특정 파일만
hyodo check src/components/*.tsx
```

### CI/CD 통합

```yaml
# .github/workflows/hyodo-js.yml
name: HyoDo JS Quality Check

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install HyoDo
        run: pip install hyodo
      
      - name: Run HyoDo
        run: hyodo check --language javascript --ci
```

---

## 📈 마일스톤

### Phase 1: 기본 지원 (v3.2.0)
- [ ] JavaScriptPlugin 클래스 구현
- [ ] tsc 통합
- [ ] ESLint 통합
- [ ] 기본 테스트 지원

### Phase 2: 고급 기능 (v3.3.0)
- [ ] Prettier 통합
- [ ] Jest/Vitest 완전 지원
- [ ] npm audit 통합
- [ ] 커버리지 리포트

### Phase 3: 최적화 (v3.4.0)
- [ ] 병렬 실행
- [ ] 캐싱
- [ ] IDE 확장
- [ ] 커스텀 규칙

---

## 🎓 결론

JavaScript/TypeScript 지원은 HyoDo의 眞善美孝永 철학을  
JS 생태계에 확장하는 것입니다.

**핵심 원칙**:
- 언어에 종속되지 않는 품질 철학
- 표준 도구 활용 (tsc, ESLint, Jest)
- 기존 워크플로우 존중
- 점진적 도입

---

*설계 문서: v1.0*  
*목표 버전: v3.2.0+
