"""
T-RAG Audio Analyzer - 오디오 시간적 특성 분석
Temporal RAG: 오디오 신호를 시간 윈도우(Window)로 분석하여 벡터화
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np

try:
    import librosa

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("librosa not installed. Using fallback audio processing")

logger = logging.getLogger(__name__)


class AudioTemporalFeatures:
    """
    오디오 시간적 특성 데이터클래스

    Attributes:
        - rhythm: 리듬 (BPM, 비트 강도)
        - tempo: 템포 (음악 속도)
        - harmony: 하모니 (조화/부조화)
        - texture: 텍스처 (밀도, 악기 편성)
        - timbre: 팀버 (색채, 질감)
        - dynamics: 다이내믹 (음량 변화)
        - temporal_sequence: 시간 시퀀스 (특징 시계열)
    """

    def __init__(
        self,
        audio_path: str,
        sr: int = 22050,
        hop_length: int = 512,
        n_fft: int = 2048,
    ) -> None:
        self.audio_path = audio_path
        self.sr = sr
        self.hop_length = hop_length
        self.n_fft = n_fft

        # 분석 로드
        self.y, self.sr = self._load_audio()

        # 시간적 특성 추출
        self.features = {}
        self._extract_temporal_features()

    def _load_audio(self) -> tuple[np.ndarray, int]:
        """오디오 로드 (librosa 또는 폴백)"""
        if LIBROSA_AVAILABLE:
            y, sr = librosa.load(self.audio_path, sr=self.sr)
            return y, sr
        else:
            from scipy.io import wavfile

            sample_rate, data = wavfile.read(self.audio_path)

            # 스테레오 → 모노
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            return data, sample_rate

    def _extract_temporal_features(self) -> None:
        """시간적 특성 추출"""

        # 1. 템포 및 BPM
        self.features["tempo"] = self._extract_tempo()
        self.features["rhythm"] = {
            "bpm": self.features["tempo"]["bpm"],
            "beat_strength": self._extract_beat_strength(),
        }

        # 2. 템포 (Spectral Centroid 변화)
        self.features["dynamics"] = self._extract_dynamics()

        # 3. 텍스처 (톤로그램)
        self.features["timbre"] = self._extract_timbre()

        # 4. 하모니 (Chroma 및 Tonnetz)
        self.features["harmony"] = self._extract_harmony()

        # 5. 시간 시퀀스 (Sliding Window)
        self.features["temporal_sequence"] = self._extract_temporal_sequence()

    def _extract_tempo(self) -> dict[str, Any]:
        """템포 추출 (librosa 또는 폴백)"""
        if LIBROSA_AVAILABLE:
            tempo, beats = librosa.beat.beat_track(y=self.y, sr=self.sr)
            return {
                "bpm": float(tempo),
                "beat_frames": beats.tolist(),
            }
        else:
            # 폴백: 에너지 기반 템포 추출
            onset_envelope = np.abs(self.y)
            threshold = np.mean(onset_envelope) + np.std(onset_envelope) * 2
            beats = (onset_envelope > threshold).astype(int)

            # BPM 추정
            if len(beats) > 1:
                intervals = np.diff(np.where(beats)[0])
                avg_interval = np.mean(intervals[intervals > 0])
                bpm = 60.0 / avg_interval if avg_interval > 0 else 120.0
            else:
                bpm = 120.0

            return {
                "bpm": float(bpm),
                "beat_frames": np.where(beats)[0].tolist(),
            }

    def _extract_beat_strength(self) -> float:
        """비트 강도 추출"""
        onset_env = np.abs(self.y)

        # 슬라이딩 윈도우
        window_size = int(self.sr * 0.05)  # 50ms window
        hop = int(self.sr * 0.01)  # 10ms hop

        # 롤링 에너지 추출
        energy = []
        for i in range(0, len(onset_env) - window_size, hop):
            window = onset_env[i : i + window_size]
            energy.append(np.mean(window))

        energy = np.array(energy)

        # 비트 변화량
        energy_diff = np.diff(energy)
        beat_strength = np.mean(np.abs(energy_diff[energy_diff > 0]))

        return float(beat_strength)

    def _extract_dynamics(self) -> dict[str, Any]:
        """다이내믹 (음량 변화) 추출"""
        # RMS 에너지 추출
        if LIBROSA_AVAILABLE:
            rms_energy = librosa.feature.rms(y=self.y, frame_length=2048, hop_length=512)
        else:
            rms_energy = self._fallback_rms()

        dynamics = {
            "rms_mean": float(np.mean(rms_energy)),
            "rms_std": float(np.std(rms_energy)),
            "dynamic_range": float(np.max(rms_energy) - np.min(rms_energy)),
            "rms_values": rms_energy.tolist(),
        }

        return dynamics

    def _extract_timbre(self) -> dict[str, Any]:
        """팀버 (색채, 질감) 추출"""
        if LIBROSA_AVAILABLE:
            # MFCC (팀버 특성)
            mfcc = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13)

            # Spectral Centroid (색채)
            spectral_centroids = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)

            # Spectral Rolloff (밝음/어두음 비율)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=self.y, sr=self.sr)

            # Zero Crossing Rate (질감)
            zcr = librosa.feature.zero_crossing_rate(self.y, sr=self.sr)

            return {
                "mfcc": mfcc.T.tolist(),  # 13 MFCC 계수
                "spectral_centroid": spectral_centroids.tolist(),
                "spectral_rolloff": spectral_rolloff.tolist(),
                "zero_crossing_rate": zcr.tolist(),
            }
        else:
            # 폴백: 기본 스펙트럼 특성
            spectral_centroids = []
            spectral_rolloff = []

            window_size = int(self.sr * 0.05)
            hop = int(self.sr * 0.01)

            for i in range(0, len(self.y) - window_size, hop):
                window = self.y[i : i + window_size]

                # FFT
                fft = np.fft.rfft(window)
                mag = np.abs(fft)
                freqs = np.fft.rfftfreq(len(window), d=1.0 / self.sr)

                # Spectral Centroid
                if np.sum(mag) > 0:
                    centroid = np.sum(freqs * mag) / np.sum(mag)
                    spectral_centroids.append(centroid)

            return {
                "mfcc": [],
                "spectral_centroid": spectral_centroids,
                "spectral_rolloff": [],
                "zero_crossing_rate": [],
            }

    def _extract_harmony(self) -> dict[str, Any]:
        """하모니 (Chroma 및 Tonnetz) 추출"""
        if LIBROSA_AVAILABLE:
            # Chroma (음색 계열)
            chromagram = librosa.feature.chroma_stft(y=self.y, sr=self.sr)

            # Tonnetz (톤넷라)
            tonnetz = librosa.feature.tonnetz(y=self.y, sr=self.sr)

            return {
                "chromagram": chromagram.tolist(),  # 12 pitch classes
                "tonnetz": tonnetz.tolist(),  # 6 tonal dimensions
            }
        else:
            # 폴백: 빈 하모니
            return {
                "chromagram": [],
                "tonnetz": [],
            }

    def _extract_temporal_sequence(self) -> dict[str, Any]:
        """시간 시퀀스 (Sliding Window) 추출"""
        # 각 시간 윈도우에서의 특징 추출

        window_duration = 1.0  # 1초
        hop_duration = 0.5  # 0.5초 슬라이드
        window_samples = int(window_duration * self.sr)
        hop_samples = int(hop_duration * self.sr)

        sequence = []
        num_windows = 0

        for i in range(0, len(self.y) - window_samples, hop_samples):
            window = self.y[i : i + window_samples]

            # 윈도우 내 기본 통계
            window_features = {
                "mean": float(np.mean(window)),
                "std": float(np.std(window)),
                "max": float(np.max(window)),
                "min": float(np.min(window)),
                "energy": float(np.mean(np.abs(window))),
                "zero_crossing_rate": float(np.sum(np.diff(np.sign(window))) / len(window)),
            }
            sequence.append(window_features)
            num_windows += 1

        return {
            "sequence": sequence,
            "num_windows": num_windows,
            "window_duration": window_duration,
            "hop_duration": hop_duration,
        }

    def _fallback_rms(self) -> np.ndarray:
        """폴백 RMS 에너지 계산"""
        frame_length = 2048
        hop_length = 512

        1 + (len(self.y) - frame_length) // hop_length
        rms = []

        for i in range(0, len(self.y) - frame_length, hop_length):
            frame = self.y[i : i + frame_length]
            rms.append(np.sqrt(np.mean(frame**2)))

        return np.array(rms)

    def to_dict(self) -> dict[str, Any]:
        """특징을 딕셔너리로 변환"""
        return {
            "audio_path": self.audio_path,
            "sample_rate": self.sr,
            "duration": len(self.y) / self.sr,
            "features": self.features,
        }

    def get_embedding_vector(self) -> list[float]:
        """임베딩 벡터 생성 (모든 특징 평탈화)"""
        vector = []

        # 템포 및 리듬
        vector.append(self.features["rhythm"]["bpm"] / 200.0)  # BPM 정규화
        vector.append(self.features["rhythm"]["beat_strength"])

        # 다이내믹
        dynamics = self.features["dynamics"]
        vector.append(dynamics["rms_mean"])
        vector.append(dynamics["rms_std"])
        vector.append(dynamics["dynamic_range"])

        # 팀버 (평균)
        if "mfcc" in self.features["timbre"]:
            mfccs = self.features["timbre"]["mfcc"]
            mfcc_mean = np.mean([np.mean(mfcc) for mfcc in mfccs]) if mfccs else 0.0
            vector.append(mfcc_mean)

        # 하모니 (평균 Chroma)
        if "chromagram" in self.features["harmony"]:
            chroma = self.features["harmony"]["chromagram"]
            if chroma:
                chroma_mean = np.mean([np.mean(c) for c in chroma]) if chroma else 0.0
                vector.append(chroma_mean)

        # 시간 시퀀스 통계
        temp_seq = self.features.get("temporal_sequence", {})
        if "sequence" in temp_seq:
            seq_stats = [
                np.mean([w["mean"] for w in temp_seq["sequence"]]),
                np.std([w["std"] for w in temp_seq["sequence"]]),
            ]
            vector.extend(seq_stats)

        # 결측치 처리
        vector = [v if not np.isnan(v) else 0.0 for v in vector]

        return vector


def analyze_audio_file(audio_path: str) -> dict[str, Any]:
    """
    오디오 파일 분석 (便捷 함수)

    Args:
        audio_path: 오디오 파일 경로

    Returns:
        시간적 특성이 포함된 딕셔너리
    """
    if not Path(audio_path).exists():
        return {
            "error": f"Audio file not found: {audio_path}",
            "success": False,
        }

    analyzer = AudioTemporalFeatures(audio_path)
    return analyzer.to_dict()


def batch_analyze_audio_files(audio_paths: list[str]) -> list[dict[str, Any]]:
    """
    여러 오디오 파일 배치 분석

    Args:
        audio_paths: 오디오 파일 경로 리스트

    Returns:
        분석 결과 리스트
    """
    results = []

    for audio_path in audio_paths:
        try:
            result = analyze_audio_file(audio_path)
            results.append(result)
            logger.info(f"Analyzed: {audio_path}")
        except Exception as e:
            logger.error(f"Failed to analyze {audio_path}: {e}")
            results.append(
                {
                    "audio_path": audio_path,
                    "error": str(e),
                    "success": False,
                }
            )

    return results


if __name__ == "__main__":
    # 테스트
    test_audio = "artifacts/mlx_music_output.wav"

    if Path(test_audio).exists():
        print("=" * 60)
        print("T-RAG Audio Analyzer 테스트")
        print("=" * 60)

        result = analyze_audio_file(test_audio)

        if result.get("success", True):
            print(f"오디오: {result['audio_path']}")
            print(f"길이: {result['duration']:.2f}초")
            print(f"샘플 레이트: {result['sample_rate']}Hz")
            print("\n특징:")
            print(f"  - BPM: {result['features']['rhythm']['bpm']:.2f}")
            print(f"  - 다이내믹 범위: {result['features']['dynamics']['dynamic_range']:.4f}")
            print(f"  - 시퀀스 윈도우 수: {result['features']['temporal_sequence']['num_windows']}")
            print(f"\n임베딩 벡터 길이: {len(result.get('embedding_vector', []))}")
        else:
            print(f"분석 실패: {result.get('error', 'Unknown error')}")

        print("=" * 60)
    else:
        print(f"테스트 오디오 파일 없음: {test_audio}")
        print("MLX MusicGen으로 오디오를 생성해주세요.")
