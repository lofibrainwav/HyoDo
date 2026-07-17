"""Focused regression checks for async critical-path offloading."""

import ast
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services.log_analysis import LogAnalysisService
from services.pdf_parsing_service import PDFParsingService


@pytest.mark.asyncio
async def test_log_pipeline_offloads_full_file_read(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"
    log_file.write_text("one\ntwo\n", encoding="utf-8")
    service = LogAnalysisService(output_dir=str(tmp_path / "output"))

    with patch(
        "services.log_analysis.anyio.to_thread.run_sync", new_callable=AsyncMock
    ) as run_sync:
        run_sync.return_value = (8, 2)
        result = await service.run_pipeline(str(log_file))

    assert result["status"] == "success"
    assert result["file_size"] == 8
    assert result["lines_processed"] == 2
    assert run_sync.await_count == 1


@pytest.mark.asyncio
async def test_pdf_extraction_offloads_blocking_parser(tmp_path: Path) -> None:
    pdf_file = tmp_path / "document.pdf"
    pdf_file.write_bytes(b"%PDF-test")
    service = PDFParsingService()

    with (
        patch("services.pdf_parsing_service.PYPDF_AVAILABLE", True),
        patch(
            "services.pdf_parsing_service.anyio.to_thread.run_sync", new_callable=AsyncMock
        ) as run_sync,
    ):
        run_sync.return_value = {
            "success": True,
            "text": "receipt",
            "meta": {"pages": 1, "info": None},
            "is_scanned": False,
            "error": None,
        }
        result = await service.extract_text(str(pdf_file))

    assert result["text"] == "receipt"
    run_sync.assert_awaited_once()


@pytest.mark.parametrize(
    ("relative_path", "function_name", "required_call"),
    [
        (
            "api/routes/system_health.py",
            "_sse_log_generator",
            "anyio.to_thread.run_sync",
        ),
        (
            "api/chancellor_v2/graph/nodes/truth_node.py",
            "_run_verification_command",
            "asyncio.create_subprocess_exec",
        ),
        (
            "api/routes/integrity_check.py",
            "_run_verification_command",
            "asyncio.create_subprocess_exec",
        ),
    ],
)
def test_async_critical_paths_keep_blocking_work_off_the_event_loop(
    relative_path: str, function_name: str, required_call: str
) -> None:
    source_path = Path(__file__).resolve().parents[1] / relative_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
    )
    calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}

    assert required_call in calls
    assert "subprocess.run" not in calls
