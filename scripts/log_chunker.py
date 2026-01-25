#!/usr/bin/env python3
"""
AFO 왕국 로그 청킹 시스템 (Log Chunker)
대용량 로그를 효율적으로 분석하기 위해 청크로 분할

Context7 기반 분류:
- SYNTAX: Python 구문 오류
- IMPORT: 모듈/함수 import 누락
- COMPATIBILITY: Python 버전 호환성 문제
- TYPE: 타입 힌팅 오류
- UNKNOWN: 기타 오류
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class LogChunk:
    """로그 청크 데이터 클래스"""

    chunk_id: str
    lines: List[str]
    start_line: int
    end_line: int
    error_count: int
    primary_category: str
    file_path: str = ""


@dataclass
class ErrorPattern:
    """에러 패턴 정의"""

    category: str
    patterns: List[str]
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str


class Context7Classifier:
    """Context7 기반 에러 분류기"""

    ERROR_PATTERNS = [
        ErrorPattern(
            category="SYNTAX",
            patterns=[
                r"Expected.*indented.*block",
                r"invalid-syntax",
                r"Simple statements must be separated",
                r"Expected.*newline",
                r"Expected.*semicolon",
            ],
            priority="CRITICAL",
            description="Python 구문 및 들여쓰기 오류",
        ),
        ErrorPattern(
            category="IMPORT",
            patterns=[
                r".*is not defined",
                r"ImportError",
                r"Module level import not at top",
                r"reportMissingImports",
                r"reportUndefinedVariable",
            ],
            priority="HIGH",
            description="모듈/함수 import 누락 또는 정의되지 않음",
        ),
        ErrorPattern(
            category="COMPATIBILITY",
            patterns=[
                r"Union.*not defined",
                r"Optional.*not defined",
                r"TypeVar.*not defined",
                r"reportInvalidTypeForm",
            ],
            priority="CRITICAL",
            description="Python 버전 호환성 및 타입 힌팅 문제",
        ),
        ErrorPattern(
            category="TYPE",
            patterns=[
                r"reportAttributeAccessIssue",
                r"reportGeneralTypeIssues",
                r"Variable not allowed in type expression",
            ],
            priority="MEDIUM",
            description="타입 시스템 관련 오류",
        ),
        ErrorPattern(
            category="UNKNOWN",
            patterns=[r".*"],
            priority="LOW",
            description="분류되지 않은 기타 오류",
        ),
    ]

    @classmethod
    def classify_error(cls, error_line: str) -> str:
        """에러 라인을 Context7 카테고리로 분류"""
        for pattern in cls.ERROR_PATTERNS:
            for regex_pattern in pattern.patterns:
                if re.search(regex_pattern, error_line, re.IGNORECASE):
                    return pattern.category
        return "UNKNOWN"


class LogChunker:
    """로그 청킹 시스템"""

    def __init__(self, log_path: str, chunk_size: int = 100) -> None:
        self.log_path = Path(log_path)
        self.chunk_size = chunk_size
        self.chunks: List[LogChunk] = []

    def load_log(self) -> List[str]:
        """로그 파일 로드"""
        if not self.log_path.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_path}")

        with open(self.log_path, "r", encoding="utf-8") as f:
            return f.readlines()

    def split_by_error_type(self, lines: List[str]) -> List[LogChunk]:
        """에러 타입별로 청크 분할"""
        chunks = []
        current_chunk_lines = []
        current_category = None
        start_line = 0

        for i, line in enumerate(lines):
            category = Context7Classifier.classify_error(line)

            # 새로운 카테고리가 나오거나 청크 크기 초과 시 새로운 청크 시작
            if (category != current_category and current_category is not None) or len(
                current_chunk_lines
            ) >= self.chunk_size:
                if current_chunk_lines:
                    chunk = LogChunk(
                        chunk_id=f"chunk_{len(chunks):03d}",
                        lines=current_chunk_lines.copy(),
                        start_line=start_line,
                        end_line=i - 1,
                        error_count=len(current_chunk_lines),
                        primary_category=current_category,
                    )
                    chunks.append(chunk)

                current_chunk_lines = []
                start_line = i
                current_category = category

            if line.strip():  # 빈 라인 제외
                current_chunk_lines.append(line.rstrip())
                if current_category is None:
                    current_category = category

        # 마지막 청크 추가
        if current_chunk_lines:
            chunk = LogChunk(
                chunk_id=f"chunk_{len(chunks):03d}",
                lines=current_chunk_lines,
                start_line=start_line,
                end_line=len(lines) - 1,
                error_count=len(current_chunk_lines),
                primary_category=current_category or "UNKNOWN",
            )
            chunks.append(chunk)

        return chunks

    def split_by_file(self, lines: List[str]) -> List[LogChunk]:
        """파일별로 청크 분할"""
        file_chunks = {}
        current_file = None

        for i, line in enumerate(lines):
            # 파일 경로 패턴 찾기
            file_match = re.search(r"/Users/brnestrm/AFO_Kingdom/([^:]+):", line)
            if file_match:
                current_file = file_match.group(1)

                if current_file not in file_chunks:
                    file_chunks[current_file] = []

                file_chunks[current_file].append((i, line.rstrip()))

        # 파일별 청크 생성
        chunks = []
        for file_path, file_lines in file_chunks.items():
            if len(file_lines) > self.chunk_size:
                # 큰 파일은 여러 청크로 분할
                for i in range(0, len(file_lines), self.chunk_size):
                    chunk_lines = file_lines[i : i + self.chunk_size]
                    chunk = LogChunk(
                        chunk_id=f"file_{file_path.replace('/', '_')}_{i // self.chunk_size:02d}",
                        lines=[line for _, line in chunk_lines],
                        start_line=chunk_lines[0][0],
                        end_line=chunk_lines[-1][0],
                        error_count=len(chunk_lines),
                        primary_category=Context7Classifier.classify_error(chunk_lines[0][1]),
                        file_path=file_path,
                    )
                    chunks.append(chunk)
            else:
                # 작은 파일은 하나의 청크
                chunk = LogChunk(
                    chunk_id=f"file_{file_path.replace('/', '_')}",
                    lines=[line for _, line in file_lines],
                    start_line=file_lines[0][0],
                    end_line=file_lines[-1][0],
                    error_count=len(file_lines),
                    primary_category=Context7Classifier.classify_error(file_lines[0][1]),
                    file_path=file_path,
                )
                chunks.append(chunk)

        return chunks

    def process_log(self, method: str = "error_type") -> List[LogChunk]:
        """로그 처리 메인 함수"""
        lines = self.load_log()

        if method == "error_type":
            self.chunks = self.split_by_error_type(lines)
        elif method == "file":
            self.chunks = self.split_by_file(lines)
        else:
            raise ValueError(f"Unknown method: {method}")

        return self.chunks

    def save_chunks(self, output_dir: str = "log_chunks") -> str:
        """청크들을 파일로 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 청크별로 저장
        for chunk in self.chunks:
            chunk_file = output_path / f"{chunk.chunk_id}.json"
            with open(chunk_file, "w", encoding="utf-8") as f:
                json.dump(asdict(chunk), f, ensure_ascii=False, indent=2)

        # 통계 파일 생성
        stats = self.generate_statistics()
        stats_file = output_path / "statistics.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        return str(output_path)

    def generate_statistics(self) -> Dict:
        """청크 통계 생성"""
        total_errors = sum(chunk.error_count for chunk in self.chunks)
        category_stats = {}

        for chunk in self.chunks:
            cat = chunk.primary_category
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "chunks": 0, "total_errors": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["chunks"] += 1
            category_stats[cat]["total_errors"] += chunk.error_count

        return {
            "total_chunks": len(self.chunks),
            "total_errors": total_errors,
            "avg_errors_per_chunk": (total_errors / len(self.chunks) if self.chunks else 0),
            "category_breakdown": category_stats,
            "chunks_by_category": {
                cat: [chunk.chunk_id for chunk in self.chunks if chunk.primary_category == cat]
                for cat in set(chunk.primary_category for chunk in self.chunks)
            },
        }


def main() -> None:
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 로그 청킹 시스템")
    parser.add_argument("log_path", help="분석할 로그 파일 경로")
    parser.add_argument(
        "--method",
        choices=["error_type", "file"],
        default="error_type",
        help="청킹 방법",
    )
    parser.add_argument("--chunk-size", type=int, default=100, help="청크 크기 (라인 수)")
    parser.add_argument("--output-dir", default="log_chunks", help="출력 디렉토리")

    args = parser.parse_args()

    # 로그 청커 초기화
    chunker = LogChunker(args.log_path, args.chunk_size)

    print(f"🔍 로그 파일 분석 중: {args.log_path}")
    print(f"📊 청킹 방법: {args.method}")
    print(f"📏 청크 크기: {args.chunk_size} 라인")

    # 로그 처리
    chunks = chunker.process_log(args.method)

    print(f"✅ 생성된 청크 수: {len(chunks)}")

    # 청크 저장
    output_dir = chunker.save_chunks(args.output_dir)
    print(f"💾 청크 저장 완료: {output_dir}")

    # 통계 출력
    stats = chunker.generate_statistics()
    print("\n📈 분석 통계:")
    print(f"   총 에러 수: {stats['total_errors']}")
    print(f"   평균 에러/청크: {stats['avg_errors_per_chunk']:.1f}")
    print("\n🏷️  카테고리별 분포:")
    for cat, data in stats["category_breakdown"].items():
        print(f"   {cat}: {data['chunks']} 청크, {data['total_errors']} 에러")


if __name__ == "__main__":
    main()
