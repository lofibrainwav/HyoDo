from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    p = Path.cwd()
    if (p / ".git").exists():
        return p
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(out)
    except Exception:
        return Path.cwd()


@dataclass(frozen=True)
class MLXMusicGenConfig:
    venv_dir: Path
    musicgen_dir: Path
    model_name: str
    steps_per_second: int
    default_max_steps: int
    timeout_sec: int


class MLXMusicGenRunner:
    def __init__(self, cfg: MLXMusicGenConfig) -> None:
        self.cfg = cfg

    @staticmethod
    def from_env() -> MLXMusicGenRunner:
        root = _repo_root()

        venv_dir = Path(os.environ.get("AFO_MLX_MUSICGEN_VENV", "venv_musicgen"))
        if not venv_dir.is_absolute():
            venv_dir = (root / venv_dir).resolve()

        musicgen_dir = os.environ.get("AFO_MLX_MUSICGEN_DIR", "")
        if musicgen_dir:
            mg = Path(musicgen_dir)
            if not mg.is_absolute():
                mg = (root / mg).resolve()
            musicgen_dir_path = mg
        else:
            candidates = [
                root / "mlx-examples" / "musicgen",
                root / "tools" / "mlx-examples" / "musicgen",
                root / "third_party" / "mlx-examples" / "musicgen",
            ]
            musicgen_dir_path = next(
                (c.resolve() for c in candidates if (c / "generate.py").exists()), root
            )

        model_name = os.environ.get("AFO_MLX_MUSICGEN_MODEL", "facebook/musicgen-small")
        steps_per_second = int(os.environ.get("AFO_MLX_MUSICGEN_STEPS_PER_SEC", "50"))
        default_max_steps = int(os.environ.get("AFO_MLX_MUSICGEN_DEFAULT_MAX_STEPS", "500"))
        timeout_sec = int(os.environ.get("AFO_MLX_MUSICGEN_TIMEOUT_SEC", "600"))

        cfg = MLXMusicGenConfig(
            venv_dir=venv_dir,
            musicgen_dir=musicgen_dir_path,
            model_name=model_name,
            steps_per_second=steps_per_second,
            default_max_steps=default_max_steps,
            timeout_sec=timeout_sec,
        )
        return MLXMusicGenRunner(cfg)

    def is_available(self) -> bool:
        py = self._venv_python()
        gen = self._generate_py()
        return py.exists() and gen.exists()

    def generate(
        self,
        text: str,
        duration_sec: int | None = None,
        output_dir: Path | None = None,
        model_name: str | None = None,
        max_steps: int | None = None,
    ) -> Path:
        if not self.is_available():
            raise RuntimeError(
                f"MLX MusicGen not available. venv_python={self._venv_python()} generate_py={self._generate_py()} "
                "Set AFO_MLX_MUSICGEN_VENV and AFO_MLX_MUSICGEN_DIR if needed."
            )

        root = _repo_root()
        out_dir = (output_dir or (root / "artifacts" / "musicgen")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        mname = model_name or self.cfg.model_name

        if max_steps is None:
            if duration_sec is None:
                max_steps = self.cfg.default_max_steps
            else:
                max_steps = max(1, int(duration_sec) * self.cfg.steps_per_second)

        key = hashlib.sha256(f"{mname}|{max_steps}|{text}".encode()).hexdigest()[:16]
        out_path = out_dir / f"mlx_musicgen_{key}.wav"

        cmd = [
            str(self._venv_python()),
            str(self._generate_py()),
            "--model",
            mname,
            "--text",
            text,
            "--output-path",
            str(out_path),
            "--max-steps",
            str(max_steps),
        ]

        proc = subprocess.run(
            cmd,
            cwd=str(self.cfg.musicgen_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=self.cfg.timeout_sec,
        )

        if proc.returncode != 0 or not out_path.exists():
            snippet = (proc.stdout or "")[-4000:]
            raise RuntimeError(
                "MLX MusicGen generation failed.\n"
                f"cmd={shlex.join(cmd)}\n"
                f"cwd={self.cfg.musicgen_dir}\n"
                f"returncode={proc.returncode}\n"
                f"tail_log=\n{snippet}"
            )

        return out_path

    def _venv_python(self) -> Path:
        # venv 경로를 절대 경로로 강제 변환
        venv_dir = self.cfg.venv_dir
        if isinstance(venv_dir, str):
            venv_dir = Path(venv_dir)
        if not venv_dir.is_absolute():
            venv_dir = (_repo_root() / venv_dir).resolve()

        # symlink를 따라가지 않고 직접 경로 사용 (Reality Gate 로그 추가)
        python_path = venv_dir / "bin" / "python3"
        print(f"MLX Reality Gate: venv_python raw path: {python_path}")
        print(f"MLX Reality Gate: venv_python exists: {python_path.exists()}")
        print(f"MLX Reality Gate: venv_python resolved: {python_path.resolve()}")

        # venv가 존재하지 않으면 시스템 python 사용 (fallback)
        if not python_path.exists():
            print(f"MLX Reality Gate: venv python not found, using system: {sys.executable}")
            return Path(sys.executable)

        print(f"MLX Reality Gate: using venv python: {python_path}")
        return python_path

    def _generate_py(self) -> Path:
        return (self.cfg.musicgen_dir / "generate.py").resolve()
