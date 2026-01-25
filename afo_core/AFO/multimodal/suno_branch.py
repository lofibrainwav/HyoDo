from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from moviepy import AudioFileClip, VideoFileClip


@dataclass(frozen=True)
class SunoConfig:
    base_url: str
    api_key: str
    callback_url: str
    model: str
    timeout_sec: int
    poll_interval_sec: float
    max_retries: int

    @staticmethod
    def from_env() -> SunoConfig:
        return SunoConfig(
            base_url=os.environ.get("SUNO_API_BASE_URL", "https://api.sunoapi.org"),
            api_key=os.environ.get("SUNO_API_KEY", "").strip(),
            callback_url=os.environ.get("SUNO_CALLBACK_URL", "").strip(),
            model=os.environ.get("SUNO_MODEL", "V4_5ALL"),
            timeout_sec=int(os.environ.get("SUNO_TIMEOUT_SEC", "240")),
            poll_interval_sec=float(os.environ.get("SUNO_POLL_INTERVAL_SEC", "3.0")),
            max_retries=int(os.environ.get("SUNO_MAX_RETRIES", "3")),
        )


class SunoClient:
    def __init__(self, cfg: SunoConfig) -> None:
        self.cfg = cfg

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request_json(
        self, method: str, url: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url=url, data=data, method=method, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_sec) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTPError {e.code}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"URLError: {e}") from e

    def generate(self, req_payload: dict[str, Any]) -> str:
        url = urllib.parse.urljoin(self.cfg.base_url, "/api/v1/generate")
        last_err: Exception | None = None
        for i in range(self.cfg.max_retries):
            try:
                res = self._request_json("POST", url, req_payload)
                task_id = (res.get("data") or {}).get("taskId")
                if not task_id:
                    raise RuntimeError(f"Missing taskId: {res}")
                return str(task_id)
            except Exception as e:
                last_err = e
                time.sleep(min(2**i, 8))
        raise RuntimeError(f"Generate failed after retries: {last_err}")

    def record_info(self, task_id: str) -> dict[str, Any]:
        q = urllib.parse.urlencode({"taskId": task_id})
        url = urllib.parse.urljoin(self.cfg.base_url, f"/api/v1/generate/record-info?{q}")
        return self._request_json("GET", url)

    def wait_for_success(self, task_id: str, timeout_sec: int | None = None) -> dict[str, Any]:
        timeout = timeout_sec if timeout_sec is not None else self.cfg.timeout_sec
        t0 = time.time()
        while True:
            res = self.record_info(task_id)
            data = res.get("data") or {}
            status = str(data.get("status") or "").upper()
            if status in {"SUCCESS", "FAILED"}:
                return res
            if (time.time() - t0) > timeout:
                raise TimeoutError(f"Suno polling timeout after {timeout}s (taskId={task_id})")
            time.sleep(self.cfg.poll_interval_sec)


def _which(cmd: str) -> str | None:
    try:
        out = subprocess.check_output(["bash", "-lc", f"command -v {cmd}"], text=True).strip()
        return out or None
    except Exception:
        return None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def download_url(url: str, out_path: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    Path(out_path).write_bytes(data)
    return out_path


def ffprobe_summary(media_path: str) -> dict[str, Any]:
    if not _which("ffprobe"):
        return {"ok": False, "reason": "ffprobe_not_found"}
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        media_path,
    ]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        return {"ok": False, "stderr": p.stderr}
    try:
        j = json.loads(p.stdout)
    except Exception:
        return {"ok": False, "raw": p.stdout}
    fmt = j.get("format") or {}
    streams = j.get("streams") or []
    dur = fmt.get("duration")
    return {
        "ok": True,
        "duration": float(dur) if dur else None,
        "streams": streams,
        "format": fmt,
    }


def make_silence_audio(out_path: str, duration_sec: float, sample_rate: int = 44100) -> str:
    if not _which("ffmpeg"):
        raise RuntimeError("ffmpeg not found (needed for silence fallback)")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl=stereo",
        "-t",
        str(duration_sec),
        "-c:a",
        "aac",
        out_path,
    ]
    _run(cmd)
    return out_path


def trim_or_loop_audio_to_duration(
    in_audio: str, out_audio: str, target_duration_sec: float
) -> str:
    if not _which("ffmpeg"):
        raise RuntimeError("ffmpeg not found (needed for duration alignment)")
    Path(out_audio).parent.mkdir(parents=True, exist_ok=True)

    info = ffprobe_summary(in_audio)
    dur = info.get("duration") if info.get("ok") else None

    if dur is None:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            in_audio,
            "-t",
            str(target_duration_sec),
            "-c:a",
            "aac",
            out_audio,
        ]
        _run(cmd)
        return out_audio

    if dur >= target_duration_sec:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            in_audio,
            "-t",
            str(target_duration_sec),
            "-c:a",
            "aac",
            out_audio,
        ]
        _run(cmd)
        return out_audio

    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        in_audio,
        "-t",
        str(target_duration_sec),
        "-c:a",
        "aac",
        out_audio,
    ]
    _run(cmd)
    return out_audio


def fuse_av(video_path: str, audio_path: str, out_path: str, prefer_moviepy: bool = True) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    if prefer_moviepy:
        try:
            v = VideoFileClip(video_path)
            a = AudioFileClip(audio_path)
            out = v.with_audio(a)
            out.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                fps=getattr(v, "fps", None) or 30,
            )
            v.close()
            a.close()
            return out_path
        except Exception:
            pass

    if not _which("ffmpeg"):
        raise RuntimeError("ffmpeg not found (needed for AV fusion fallback)")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        out_path,
    ]
    _run(cmd)
    return out_path


def _build_suno_prompt(timeline_state: dict[str, Any], music: dict[str, Any]) -> str:
    sections = timeline_state.get("sections") or []
    parts: list[str] = []
    for s in sections:
        st = s.get("start")
        en = s.get("end")
        txt = s.get("text") or ""
        fx = s.get("effects") or []
        parts.append(f"[{st}-{en}] {txt} effects={','.join(map(str, fx))}")
    return (music.get("prompt") or "\n".join(parts) or "Upbeat track").strip()


def _add_custom_params(music: dict[str, Any], payload: dict[str, Any]) -> None:
    for k_in, k_out in [
        ("personaId", "personaId"),
        ("vocalGender", "vocalGender"),
        ("styleWeight", "styleWeight"),
        ("weirdnessConstraint", "weirdnessConstraint"),
        ("audioWeight", "audioWeight"),
    ]:
        v = music.get(k_in)
        if v is not None:
            payload[k_out] = v


def timeline_to_suno_request(timeline_state: dict[str, Any], cfg: SunoConfig) -> dict[str, Any]:
    music = timeline_state.get("music") or {}
    template = timeline_state.get("template") or music.get("template") or "default"

    custom_mode = bool(music.get("custom_mode", music.get("customMode", True)))
    instrumental = bool(music.get("instrumental", music.get("is_instrumental", True)))

    prompt = _build_suno_prompt(timeline_state, music)

    payload: dict[str, Any] = {
        "customMode": custom_mode,
        "instrumental": instrumental,
        "model": str(music.get("model") or cfg.model),
        "callBackUrl": str(music.get("callBackUrl") or cfg.callback_url),
        "prompt": prompt,
    }

    if custom_mode:
        style = str(music.get("style") or template).strip()[:1000]
        title = str(music.get("title") or (timeline_state.get("title") or "AFO Track")).strip()[
            :100
        ]
        negative_tags = str(music.get("negative_tags", music.get("negativeTags", ""))).strip()

        payload["style"] = style
        payload["title"] = title
        if negative_tags:
            payload["negativeTags"] = negative_tags

        _add_custom_params(music, payload)

    return payload


def trinity_quality_score(audio_path: str, expected_min_sec: float | None = None) -> dict[str, Any]:
    info = ffprobe_summary(audio_path)
    if not info.get("ok"):
        return {"score": 0.0, "reason": "ffprobe_failed", "detail": info}

    dur = info.get("duration") or 0.0
    streams = info.get("streams") or []
    has_audio = any((s.get("codec_type") == "audio") for s in streams)

    score = 100.0
    if not has_audio:
        score -= 80.0
    if expected_min_sec is not None and dur < expected_min_sec:
        score -= min(50.0, (expected_min_sec - dur) * 10.0)

    size = Path(audio_path).stat().st_size if Path(audio_path).exists() else 0
    if size < 1024:
        score -= 40.0

    return {
        "score": max(0.0, min(100.0, score)),
        "duration": dur,
        "has_audio_stream": has_audio,
        "bytes": size,
        "ffprobe": info,
    }


def run_suno_pipeline(
    timeline_state: dict[str, Any],
    *,
    out_dir: str = "artifacts",
    dry_run: bool = True,
    target_av_duration_sec: float | None = None,
    video_path_for_fusion: str | None = None,
) -> dict[str, Any]:
    cfg = SunoConfig.from_env()
    req_payload = timeline_to_suno_request(timeline_state, cfg)

    plan = {
        "dry_run": dry_run,
        "suno": {
            "base_url": cfg.base_url,
            "model": req_payload.get("model"),
            "customMode": req_payload.get("customMode"),
            "instrumental": req_payload.get("instrumental"),
        },
        "request_payload": {k: v for k, v in req_payload.items() if k != "Authorization"},
        "outputs": {},
    }

    if dry_run:
        return plan

    if not cfg.api_key:
        raise ValueError("SUNO_API_KEY is required for WET mode")
    if not cfg.callback_url:
        raise ValueError("SUNO_CALLBACK_URL is required by docs for WET mode (set a valid URL)")

    client = SunoClient(cfg)
    task_id = client.generate(req_payload)
    plan["suno"]["taskId"] = task_id

    res = client.wait_for_success(task_id, timeout_sec=cfg.timeout_sec)
    data = res.get("data") or {}
    status = str(data.get("status") or "").upper()
    plan["suno"]["status"] = status

    if status != "SUCCESS":
        raise RuntimeError(f"Suno generation failed: {res}")

    tracks = ((data.get("response") or {}).get("data")) or []
    if not tracks:
        raise RuntimeError(f"No tracks in response: {res}")

    track0 = tracks[0] or {}
    audio_url = track0.get("audio_url")
    if not audio_url:
        raise RuntimeError(f"Missing audio_url: {track0}")

    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    raw_audio_path = str(out_dir_p / "suno_raw.mp3")
    download_url(str(audio_url), raw_audio_path)
    plan["outputs"]["audio_raw"] = raw_audio_path

    final_audio_path = raw_audio_path
    if target_av_duration_sec is not None:
        aligned = str(out_dir_p / "suno_aligned.m4a")
        trim_or_loop_audio_to_duration(raw_audio_path, aligned, float(target_av_duration_sec))
        final_audio_path = aligned
        plan["outputs"]["audio_aligned"] = final_audio_path

    plan["quality"] = trinity_quality_score(final_audio_path, expected_min_sec=1.0)

    if video_path_for_fusion:
        fused = str(out_dir_p / "suno_fused.mp4")
        fuse_av(video_path_for_fusion, final_audio_path, fused, prefer_moviepy=True)
        plan["outputs"]["av_fused"] = fused
        plan["outputs"]["av_fused_ffprobe"] = ffprobe_summary(fused)

    return plan


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--wet", action="store_true")
    ap.add_argument("--out-dir", default="artifacts")
    ap.add_argument("--video", default="")
    ap.add_argument("--target-sec", default="")
    args = ap.parse_args()

    timeline = _load_json(args.timeline)
    target = float(args.target_sec) if args.target_sec else None
    video = args.video.strip() or None

    try:
        out = run_suno_pipeline(
            timeline,
            out_dir=args.out_dir,
            dry_run=(not args.wet),
            target_av_duration_sec=target,
            video_path_for_fusion=video,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except Exception as e:
        if args.wet and video and target is not None:
            silence = str(Path(args.out_dir) / "fallback_silence.m4a")
            make_silence_audio(silence, float(target))
            fused = str(Path(args.out_dir) / "fallback_silence_fused.mp4")
            fuse_av(video, silence, fused, prefer_moviepy=True)
            out = {
                "wet": True,
                "fallback": "silence_audio",
                "outputs": {
                    "audio": silence,
                    "av_fused": fused,
                    "av_fused_ffprobe": ffprobe_summary(fused),
                },
                "error": f"{type(e).__name__}: {e}",
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return
        raise


if __name__ == "__main__":
    main()
