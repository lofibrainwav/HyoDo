from __future__ import annotations

from miditok import REMI, TokenizerConfig
from mido import MidiFile

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""🎵 AFO Kingdom - MIDI REMI+ 토크나이저

프로페셔널 뮤지션을 위한 MIDI 토큰화 도구:
- REMI+ (멀티트랙 + 박자 변화)
- V5 Suno 통합
- 형님의 라이브러리 연결 준비

眞善美孝: Truth 95%, Goodness 90%, Beauty 95%, Serenity 100%
"""


# MIDI 라이브러리
try:
    MIDI_AVAILABLE = True
except ImportError:
    MIDI_AVAILABLE = False
    print("⚠️ MIDI 라이브러리 없음: pip install miditok mido")


class AFOMidiTokenizer:
    """🎵 AFO Kingdom MIDI 토크나이저

    형님의 프로페셔널 뮤직 프로덕션을 위한 REMI+ 구현
    """

    def __init__(self, use_remi_plus: bool = True) -> None:
        """Args:
        use_remi_plus: True면 멀티트랙/박자변화 지원

        """
        if not MIDI_AVAILABLE:
            raise ImportError("MIDI 라이브러리 필요: pip install miditok mido")

        self.use_remi_plus = use_remi_plus

        # REMI+ 설정
        config = TokenizerConfig(
            pitch_range=range(21, 109),  # A0 ~ G9
            beat_res={(0, 4): 8, (4, 12): 4},
            num_velocities=32,
            additional_tokens={
                "Chord": True,
                "Rest": True,
                "Tempo": True,
                "Program": use_remi_plus,  # 멀티트랙
                "TimeSignature": use_remi_plus,  # 박자 변화
                "num_tempos": 32,
                "tempo_range": (40, 250),
                "rest_range": (2, 8),
            },
            special_tokens=["PAD", "BOS", "EOS", "MASK"],
        )

        self.tokenizer = REMI(config)
        print("🎵 AFO MIDI Tokenizer 초기화!")
        print(f"   REMI+: {use_remi_plus}")
        print(f"   Vocab Size: {len(self.tokenizer)}")

    def tokenize(self, midi_path: str) -> dict:
        """MIDI → REMI+ 토큰 변환

        Args:
            midi_path: MIDI 파일 경로

        Returns:
            Dict with tokens and metadata

        """
        print(f"🎹 토큰화 중: {midi_path}")

        midi = MidiFile(midi_path)
        tokens = self.tokenizer(midi)

        # 메타데이터
        result = {
            "file": midi_path,
            "tracks": len(tokens.ids) if hasattr(tokens, "ids") else 1,
            "tokens": tokens.ids if hasattr(tokens, "ids") else tokens,
            "vocab_size": len(self.tokenizer),
        }

        print("   ✅ 토큰화 완료!")
        print(f"   트랙 수: {result['tracks']}")

        return result

    def detokenize(self, tokens: list, output_path: str) -> str:
        """REMI+ 토큰 → MIDI 변환

        Args:
            tokens: 토큰 리스트
            output_path: 출력 MIDI 경로

        Returns:
            저장된 파일 경로

        """
        print("🎵 디토큰화 중...")

        midi = self.tokenizer.decode(tokens)
        midi.dump_midi(output_path)

        print(f"   ✅ MIDI 저장: {output_path}")
        return output_path

    def analyze(self, midi_path: str) -> dict:
        """MIDI 파일 분석 (형님의 라이브러리 연결용)

        Args:
            midi_path: MIDI 파일 경로

        Returns:
            분석 결과 (BPM, 키, 트랙 등)

        """
        print(f"🔍 MIDI 분석 중: {midi_path}")

        midi = MidiFile(midi_path)

        # 기본 분석
        analysis = {
            "file": midi_path,
            "tracks": len(midi.tracks),
            "ticks_per_beat": midi.ticks_per_beat,
            "length_seconds": midi.length,
            "track_names": [],
            "instruments": [],
        }

        for i, track in enumerate(midi.tracks):
            {"index": i, "name": track.name, "messages": len(track)}
            analysis["track_names"].append(track.name or f"Track {i}")

            # 프로그램 체인지 (악기) 찾기
            for msg in track:
                if msg.type == "program_change":
                    analysis["instruments"].append({"track": i, "program": msg.program})

        print("   ✅ 분석 완료!")
        print(f"   트랙: {analysis['tracks']}")
        print(f"   길이: {analysis['length_seconds']:.1f}초")
        print(f"   악기: {len(analysis['instruments'])}개")

        return analysis


# ============================================================
# CLI 테스트
# ============================================================
if __name__ == "__main__":
    print("🏰 AFO Kingdom - MIDI Tokenizer")
    print("=" * 60)

    tokenizer = AFOMidiTokenizer(use_remi_plus=True)

    print("\n✅ 토크나이저 준비 완료!")
    print("   형님의 MIDI 파일을 분석/토큰화할 준비가 되었습니다.")
    print("\n사용법:")
    print("   tokenizer.analyze('your_midi.mid')  # 분석")
    print("   tokenizer.tokenize('your_midi.mid') # 토큰화")
