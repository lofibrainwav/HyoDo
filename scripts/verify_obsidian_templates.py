#!/usr/bin/env python3
"""
옵시디언 템플릿 시스템 검증 스크립트

이 스크립트는 AFO Kingdom 옵시디언 템플릿 시스템의 완전성을 검증합니다.
- 템플릿 파일 존재 확인
- YAML Frontmatter 유효성 검증
- Mermaid 다이어그램 문법 검증
- Dataview 쿼리 문법 검증
- 옵시디언 설정 검증
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TemplateValidationResult:
    """템플릿 검증 결과"""

    template_name: str
    is_valid: bool
    errors: list[str]
    warnings: list[str]


@dataclass
class SystemValidationResult:
    """시스템 검증 결과"""

    component: str
    status: str
    details: dict


class ObsidianTemplateValidator:
    """옵시디언 템플릿 검증기"""

    def __init__(self, vault_path: str = "docs") -> None:
        self.vault_path = Path(vault_path)
        self.templates_path = self.vault_path / "_templates"
        self.obsidian_path = self.vault_path / ".obsidian"

    def validate_all(self) -> dict:
        """전체 시스템 검증"""
        results = {}

        # 템플릿 검증
        results["templates"] = self.validate_templates()

        # 옵시디언 설정 검증
        results["obsidian_config"] = self.validate_obsidian_config()

        # 파일 구조 검증
        results["file_structure"] = self.validate_file_structure()

        # 종합 결과
        results["summary"] = self.generate_summary(results)

        return results

    def validate_templates(self) -> list[TemplateValidationResult]:
        """템플릿 파일들 검증"""
        results = []

        if not self.templates_path.exists():
            return [
                TemplateValidationResult(
                    template_name="templates_directory",
                    is_valid=False,
                    errors=["템플릿 디렉토리가 존재하지 않습니다"],
                    warnings=[],
                )
            ]

        template_files = [
            "project_doc.md",
            "system_component.md",
            "api_endpoint.md",
            "dataview_queries.md",
            "collaboration_guide.md",
            "ai_integration_guide.md",
            "publish_template.html",
            "README.md",
        ]

        for template_file in template_files:
            template_path = self.templates_path / template_file
            result = self.validate_single_template(template_file, template_path)
            results.append(result)

        return results

    def validate_single_template(
        self, template_name: str, template_path: Path
    ) -> TemplateValidationResult:
        """단일 템플릿 파일 검증"""
        errors = []
        warnings = []

        # 파일 존재 확인
        if not template_path.exists():
            return TemplateValidationResult(
                template_name=template_name,
                is_valid=False,
                errors=[f"템플릿 파일이 존재하지 않습니다: {template_path}"],
                warnings=[],
            )

        try:
            content = template_path.read_text(encoding="utf-8")

            # YAML Frontmatter 검증
            if template_name.endswith(".md"):
                frontmatter_errors, frontmatter_warnings = self.validate_frontmatter(content)
                errors.extend(frontmatter_errors)
                warnings.extend(frontmatter_warnings)

            # Mermaid 다이어그램 검증
            mermaid_errors = self.validate_mermaid_syntax(content)
            errors.extend(mermaid_errors)

            # Dataview 쿼리 검증
            if template_name == "dataview_queries.md":
                dataview_errors, dataview_warnings = self.validate_dataview_queries(content)
                errors.extend(dataview_errors)
                warnings.extend(dataview_warnings)

            # HTML 템플릿 검증
            if template_name.endswith(".html"):
                html_errors = self.validate_html_template(content)
                errors.extend(html_errors)

        except Exception as e:
            errors.append(f"파일 읽기 오류: {e!s}")

        return TemplateValidationResult(
            template_name=template_name,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_frontmatter(self, content: str) -> tuple[list[str], list[str]]:
        """YAML Frontmatter 검증"""
        errors = []
        warnings = []

        # Frontmatter 추출
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return [], ["YAML Frontmatter가 없습니다"]

        frontmatter_text = frontmatter_match.group(1)

        try:
            # 옵시디언 템플릿 변수들 전처리 (임시 값으로 치환)
            processed_text = self.preprocess_obsidian_variables(frontmatter_text)
            frontmatter = yaml.safe_load(processed_text)

            # 필수 필드 검증
            required_fields = ["tags"]
            errors.extend(
                f"필수 필드가 누락됨: {field}"
                for field in required_fields
                if field not in frontmatter
            )

            # 태그 형식 검증
            if "tags" in frontmatter and not isinstance(frontmatter["tags"], list):
                errors.append("tags 필드는 리스트 형식이어야 합니다")

        except yaml.YAMLError as e:
            errors.append(f"YAML 파싱 오류: {e!s}")

        return errors, warnings

    def preprocess_obsidian_variables(self, text: str) -> str:
        """옵시디언 템플릿 변수들을 임시 값으로 치환"""
        # 옵시디언 변수 패턴들
        replacements = {
            r"\{\{date:YYYY-MM-DD\}\}": "2025-01-27",
            r"\{\{date:format\}\}": "2025-01-27",
            r"\{\{time\}\}": "12:00:00",
            r"\{\{title\}\}": "Sample Title",
            r"\{\{author\}\}": "Sample Author",
            r"\{\{assignee\}\}": "Sample Assignee",
            r"\{\{status\}\}": "draft",
            r"\{\{priority\}\}": "medium",
            r"\{\{version\}\}": "1.0.0",
            r"\{\{category\}\}": "sample",
            # 기타 일반적인 변수들
            r"\{\{\w+\}\}": "sample_value",
        }

        processed_text = text
        for pattern, replacement in replacements.items():
            processed_text = re.sub(pattern, replacement, processed_text)

        return processed_text

    def validate_mermaid_syntax(self, content: str) -> list[str]:
        """Mermaid 다이어그램 문법 검증"""
        errors = []

        # Mermaid 코드 블록 찾기
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)\n```", content, re.DOTALL)

        for i, block in enumerate(mermaid_blocks):
            # 지원되는 다이어그램 타입들 (확장된 목록)
            valid_patterns = [
                r"\bgraph\b",
                r"\bflowchart\b",  # 그래프 다이어그램
                r"\bsequenceDiagram\b",  # 시퀀스 다이어그램
                r"\bstateDiagram\b",
                r"\bstateDiagram-v2\b",  # 상태 다이어그램
                r"\bpie\b",  # 파이 차트
                r"\bgantt\b",  # 간트 차트
            ]

            # 다이어그램 타입 검증
            is_valid_type = any(re.search(pattern, block) for pattern in valid_patterns)
            if not is_valid_type:
                errors.append(f"Mermaid 블록 {i + 1}: 유효하지 않은 다이어그램 타입")

            # 따옴표 불일치 검증
            if block.count('"') % 2 != 0:
                errors.append(f"Mermaid 블록 {i + 1}: 따옴표가 닫히지 않았습니다")

        return errors

    def validate_dataview_queries(self, content: str) -> tuple[list[str], list[str]]:
        """Dataview 쿼리 검증"""
        errors = []
        warnings = []

        # Dataview 코드 블록 찾기
        dataview_blocks = re.findall(r"```dataview\n(.*?)\n```", content, re.DOTALL)

        for i, block in enumerate(dataview_blocks):
            # 기본 FROM 절 검증
            if not re.search(r"\bFROM\b", block, re.IGNORECASE):
                errors.append(f"Dataview 쿼리 {i + 1}: FROM 절이 없습니다")

            # 기본 SELECT 절 검증 (TABLE, LIST, TASK)
            has_select = re.search(r"\b(TABLE|LIST|TASK)\b", block, re.IGNORECASE)
            if not has_select:
                warnings.append(f"Dataview 쿼리 {i + 1}: SELECT 절이 명시되지 않았습니다")

        return errors, warnings

    def validate_html_template(self, content: str) -> list[str]:
        """HTML 템플릿 검증"""
        errors = []

        # 기본 HTML 구조 검증
        if not re.search(r"<!DOCTYPE html>", content, re.IGNORECASE):
            errors.append("HTML DOCTYPE 선언이 없습니다")

        if not re.search(r"<html[^>]*>", content, re.IGNORECASE):
            errors.append("HTML 루트 태그가 없습니다")

        if not re.search(r"<head[^>]*>.*?</head>", content, re.IGNORECASE | re.DOTALL):
            errors.append("HEAD 태그가 없습니다")

        if not re.search(r"<body[^>]*>.*?</body>", content, re.IGNORECASE | re.DOTALL):
            errors.append("BODY 태그가 없습니다")

        # 변수 치환 검증
        variables = re.findall(r"\{\{(\w+)\}\}", content)
        if not variables:
            errors.append("템플릿 변수가 없습니다")

        return errors

    def validate_obsidian_config(self) -> list[SystemValidationResult]:
        """옵시디언 설정 검증"""
        results = []

        # app.json 검증
        app_config_path = self.obsidian_path / "app.json"
        if app_config_path.exists():
            try:
                with Path(app_config_path).open(encoding="utf-8") as f:
                    config = json.load(f)

                # 템플릿 폴더 설정 확인
                template_folder = config.get("templateFolderPath", "")
                if template_folder != "_templates":
                    results.append(
                        SystemValidationResult(
                            component="template_folder",
                            status="warning",
                            details={
                                "expected": "_templates",
                                "actual": template_folder,
                            },
                        )
                    )
                else:
                    results.append(
                        SystemValidationResult(
                            component="template_folder",
                            status="success",
                            details={"configured": template_folder},
                        )
                    )

            except Exception as e:
                results.append(
                    SystemValidationResult(
                        component="app_config",
                        status="error",
                        details={"error": str(e)},
                    )
                )
        else:
            results.append(
                SystemValidationResult(
                    component="app_config",
                    status="error",
                    details={"error": "app.json 파일이 없습니다"},
                )
            )

        # community-plugins.json 검증
        plugins_path = self.obsidian_path / "community-plugins.json"
        if plugins_path.exists():
            try:
                with Path(plugins_path).open(encoding="utf-8") as f:
                    plugins = json.load(f)

                required_plugins = ["dataview", "kanban", "calendar", "advanced-tables"]
                missing_plugins = [p for p in required_plugins if p not in plugins]

                if missing_plugins:
                    results.append(
                        SystemValidationResult(
                            component="required_plugins",
                            status="warning",
                            details={"missing": missing_plugins},
                        )
                    )
                else:
                    results.append(
                        SystemValidationResult(
                            component="required_plugins",
                            status="success",
                            details={"installed": required_plugins},
                        )
                    )

            except Exception as e:
                results.append(
                    SystemValidationResult(
                        component="plugins_config",
                        status="error",
                        details={"error": str(e)},
                    )
                )

        return results

    def validate_file_structure(self) -> dict:
        """파일 구조 검증"""
        structure = {}

        # 템플릿 파일 수 확인
        if self.templates_path.exists():
            template_files = list(self.templates_path.glob("*.md")) + list(
                self.templates_path.glob("*.html")
            )
            structure["templates_count"] = len(template_files)
        else:
            structure["templates_count"] = 0

        # 옵시디언 설정 파일 확인
        obsidian_files = ["app.json", "community-plugins.json", "appearance.json"]
        structure["obsidian_config_files"] = {}

        for config_file in obsidian_files:
            config_path = self.obsidian_path / config_file
            structure["obsidian_config_files"][config_file] = config_path.exists()

        return structure

    def generate_summary(self, results: dict) -> dict:
        """종합 결과 생성"""
        summary = {
            "total_templates": len(results.get("templates", [])),
            "valid_templates": sum(1 for t in results.get("templates", []) if t.is_valid),
            "total_errors": sum(len(t.errors) for t in results.get("templates", [])),
            "total_warnings": sum(len(t.warnings) for t in results.get("templates", [])),
            "system_status": "unknown",
        }

        # 시스템 상태 결정
        template_success_rate = (
            summary["valid_templates"] / summary["total_templates"]
            if summary["total_templates"] > 0
            else 0
        )

        if template_success_rate >= 0.9 and summary["total_errors"] == 0:
            summary["system_status"] = "excellent"
        elif template_success_rate >= 0.8 and summary["total_errors"] <= 2:
            summary["system_status"] = "good"
        elif template_success_rate >= 0.7:
            summary["system_status"] = "acceptable"
        else:
            summary["system_status"] = "needs_attention"

        return summary


def main() -> None:
    """메인 실행 함수"""
    print("🔍 옵시디언 템플릿 시스템 검증 시작")
    print("=" * 50)

    validator = ObsidianTemplateValidator()

    try:
        results = validator.validate_all()

        # 템플릿 검증 결과 출력
        print("\n📋 템플릿 검증 결과:")
        for template_result in results["templates"]:
            status = "✅" if template_result.is_valid else "❌"
            print(f"  {status} {template_result.template_name}")

            if template_result.errors:
                for error in template_result.errors:
                    print(f"    🔴 {error}")

            if template_result.warnings:
                for warning in template_result.warnings:
                    print(f"    🟡 {warning}")

        # 옵시디언 설정 검증 결과 출력
        print("\n⚙️ 옵시디언 설정 검증 결과:")
        for config_result in results["obsidian_config"]:
            if config_result.status == "success":
                print(f"  ✅ {config_result.component}")
            elif config_result.status == "warning":
                print(f"  🟡 {config_result.component}: {config_result.details}")
            else:
                print(f"  🔴 {config_result.component}: {config_result.details}")

        # 파일 구조 정보 출력
        structure = results["file_structure"]
        print("\n📊 파일 구조 정보:")
        print(f"  📁 템플릿 파일 수: {structure['templates_count']}")
        print(
            f"  ⚙️ 옵시디언 설정 파일: {sum(structure['obsidian_config_files'].values())}/{len(structure['obsidian_config_files'])}"
        )

        # 종합 결과 출력
        summary = results["summary"]
        print("\n🎯 종합 결과:")
        print(
            f"  📊 템플릿 검증율: {summary['valid_templates']}/{summary['total_templates']} ({summary['valid_templates'] / summary['total_templates'] * 100:.1f}%)"
        )
        print(f"  🔴 총 오류 수: {summary['total_errors']}")
        print(f"  🟡 총 경고 수: {summary['total_warnings']}")

        status_emoji = {
            "excellent": "🌟",
            "good": "✅",
            "acceptable": "⚠️",
            "needs_attention": "🔴",
        }

        print(
            f"  {status_emoji.get(summary['system_status'], '❓')} 시스템 상태: {summary['system_status'].upper()}"
        )

        # 검증 성공/실패 결정
        if summary["system_status"] in {"excellent", "good"}:
            print("\n🎉 옵시디언 템플릿 시스템 검증 완료!")
            return 0
        print("\n⚠️ 옵시디언 템플릿 시스템 검증 실패 - 개선 필요")
        return 1

    except Exception as e:
        print(f"\n🔴 검증 중 오류 발생: {e!s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
