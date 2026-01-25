"""
Diff Generator - 문서 변경사항 생성

眞 (장영실 - Jang Yeong-sil): 아키텍처 설계
- Diff 생성 알고리즘
- 텍스트 diff 생성
- 구조화된 diff 출력
"""

from __future__ import annotations

import difflib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TextDiff:
    """텍스트 Diff 클래스"""

    @staticmethod
    def unified_diff(
        old_text: str,
        new_text: str,
        fromfile: str = "old",
        tofile: str = "new",
        context_lines: int = 3,
    ) -> list[str]:
        """
        Unified Diff 생성

        Args:
            old_text: 원본 텍스트
            new_text: 새 텍스트
            fromfile: 원본 파일명
            tofile: 새 파일명
            context_lines: 컨텍스트 라인 수

        Returns:
            Unified Diff 라인 리스트
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=fromfile,
            tofile=tofile,
            n=context_lines,
        )

        return list(diff)

    @staticmethod
    def diff_to_dict(diff_lines: list[str]) -> dict[str, Any]:
        """
        Diff를 딕셔너리로 변환

        Args:
            diff_lines: Unified Diff 라인 리스트

        Returns:
            구조화된 Diff 딕셔너리
        """

        diff_dict: dict[str, Any] = {
            "hunks": [],
            "total_additions": 0,
            "total_deletions": 0,
            "total_changes": 0,
            "summary": "",
        }

        current_hunk: dict[str, Any] | None = None
        hunk_index = -1

        for line in diff_lines:
            # Hunk 시작
            if line.startswith("@@"):
                if current_hunk is not None:
                    diff_dict["hunks"].append(current_hunk)

                hunk_index += 1
                current_hunk = {
                    "index": hunk_index,
                    "header": line.strip(),
                    "lines": [],
                    "additions": 0,
                    "deletions": 0,
                }
            # Hunk 내용
            elif current_hunk is not None:
                current_hunk["lines"].append(line)

                # 통계
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk["additions"] += 1
                    diff_dict["total_additions"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk["deletions"] += 1
                    diff_dict["total_deletions"] += 1

        # 마지막 Hunk 추가
        if current_hunk is not None:
            diff_dict["hunks"].append(current_hunk)

        # 총 변경 수 계산
        diff_dict["total_changes"] = diff_dict["total_additions"] + diff_dict["total_deletions"]

        # 요약 생성
        diff_dict["summary"] = (
            f"{diff_dict['total_additions']} additions, "
            f"{diff_dict['total_deletions']} deletions, "
            f"{diff_dict['total_changes']} total changes"
        )

        logger.debug(f"Diff 생성: {diff_dict['summary']}, {len(diff_dict['hunks'])} hunks")

        return diff_dict

    @staticmethod
    def diff_to_json(diff_lines: list[str], indent: int = 2) -> str:
        """
        Diff를 JSON으로 변환

        Args:
            diff_lines: Unified Diff 라인 리스트
            indent: 들여쓰기

        Returns:
            JSON 문자열
        """
        diff_dict = TextDiff.diff_to_dict(diff_lines)
        return json.dumps(diff_dict, indent=indent, ensure_ascii=False)

    @staticmethod
    def save_diff_to_file(diff_lines: list[str], output_path: Path | str) -> None:
        """
        Diff를 파일에 저장

        Args:
            diff_lines: Unified Diff 라인 리스트
            output_path: 출력 파일 경로
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(diff_lines)

        logger.info(f"Diff 저장 완료: {output_path}")


class FileDiff:
    """파일 Diff 클래스"""

    @staticmethod
    def diff_files(
        old_file: str | Path,
        new_file: str | Path,
        output_file: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        두 파일의 Diff 생성

        Args:
            old_file: 원본 파일 경로
            new_file: 새 파일 경로
            output_file: 출력 파일 경로 (옵션)

        Returns:
            Diff 딕셔너리
        """
        old_path = Path(old_file)
        new_path = Path(new_file)

        if not old_path.exists():
            raise FileNotFoundError(f"원본 파일이 존재하지 않음: {old_path}")

        if not new_path.exists():
            raise FileNotFoundError(f"새 파일이 존재하지 않음: {new_path}")

        old_text = old_path.read_text(encoding="utf-8")
        new_text = new_path.read_text(encoding="utf-8")

        diff_lines = TextDiff.unified_diff(
            old_text,
            new_text,
            fromfile=str(old_path),
            tofile=str(new_path),
        )

        diff_dict = TextDiff.diff_to_dict(diff_lines)

        if output_file is not None:
            TextDiff.save_diff_to_file(diff_lines, output_file)

        return diff_dict


# Convenience Functions
def generate_diff(
    old_text: str,
    new_text: str,
    fromfile: str = "old",
    tofile: str = "new",
    context_lines: int = 3,
) -> list[str]:
    """Diff 생성 (편의 함수)"""
    return TextDiff.unified_diff(old_text, new_text, fromfile, tofile, context_lines)


def diff_to_dict(diff_lines: list[str]) -> dict[str, Any]:
    """Diff를 딕셔너리로 변환 (편의 함수)"""
    return TextDiff.diff_to_dict(diff_lines)


def diff_to_json(diff_lines: list[str], indent: int = 2) -> str:
    """Diff를 JSON으로 변환 (편의 함수)"""
    return TextDiff.diff_to_json(diff_lines, indent)


__all__ = [
    "TextDiff",
    "FileDiff",
    "generate_diff",
    "diff_to_dict",
    "diff_to_json",
]
