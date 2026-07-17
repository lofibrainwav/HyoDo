"""Platform boundary tests for the legacy AFO QLoRA entry point."""

from unittest.mock import patch

import pytest

# qlora_trainer_service imports torch (ml extra); without it collection must skip, not error.
pytest.importorskip("torch")

from AFO.qlora_trainer_service import QLoRATrainerService


def test_qlora_rejects_missing_cuda_before_model_load() -> None:
    """QLoRA must not attempt a model download when CUDA is unavailable."""
    service = QLoRATrainerService()

    with (
        patch("AFO.qlora_trainer_service.torch.cuda.is_available", return_value=False),
        patch(
            "AFO.qlora_trainer_service.AutoModelForCausalLM.from_pretrained",
            side_effect=AssertionError("model loader must not run"),
        ),
        pytest.raises(RuntimeError, match="NVIDIA CUDA"),
    ):
        service.load_model_and_tokenizer()


def test_qlora_rejects_non_linux_host_before_model_load() -> None:
    """QLoRA must not attempt a model download from a non-Linux host."""
    service = QLoRATrainerService()

    with (
        patch("AFO.qlora_trainer_service.sys.platform", "darwin"),
        patch("AFO.qlora_trainer_service.torch.cuda.is_available", return_value=True),
        patch(
            "AFO.qlora_trainer_service.AutoModelForCausalLM.from_pretrained",
            side_effect=AssertionError("model loader must not run"),
        ),
        pytest.raises(RuntimeError, match="Linux hosts with NVIDIA CUDA"),
    ):
        service.load_model_and_tokenizer()
