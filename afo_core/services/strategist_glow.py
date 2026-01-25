"""Strategist Glow - Trinity Layer Visualization (PH-SE-05.03)

眞善美孝永 5기둥의 점수를 시각적 오버레이(Glow, Badge)로 표현하는 레이어.

Trinity Score: 眞 100% | 善 95% | 美 95%
- 眞 (Truth): 정확한 색상/강도 매핑
- 善 (Goodness): 테마 호환성 (다크/라이트)
- 美 (Beauty): 시각적 일관성과 미적 표현
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)


# ============================================================================
# Glow Schema Definitions (眞 - Truth)
# ============================================================================


class Pillar(str, Enum):
    """5기둥 (眞善美孝永) 열거형."""

    TRUTH = "truth"  # 眞
    GOODNESS = "goodness"  # 善
    BEAUTY = "beauty"  # 美
    SERENITY = "serenity"  # 孝
    ETERNITY = "eternity"  # 永


class ThemeMode(str, Enum):
    """테마 모드."""

    DARK = "dark"
    LIGHT = "light"


@dataclass(frozen=True)
class PillarColor:
    """기둥별 색상 정의 (SSOT).

    dark/light 테마 각각의 색상을 정의.
    """

    pillar: Pillar
    symbol: str  # 한자 심볼
    dark_primary: str  # 다크 모드 주 색상
    dark_glow: str  # 다크 모드 Glow 색상 (더 밝은 톤)
    light_primary: str  # 라이트 모드 주 색상
    light_glow: str  # 라이트 모드 Glow 색상 (더 어두운 톤)


# 🎨 5기둥 색상 팔레트 SSOT (Dark/Light 테마 지원)
PILLAR_COLORS: dict[Pillar, PillarColor] = {
    Pillar.TRUTH: PillarColor(
        pillar=Pillar.TRUTH,
        symbol="眞",
        dark_primary="#3b82f6",  # Blue 500
        dark_glow="#60a5fa",  # Blue 400 (밝은 톤)
        light_primary="#2563eb",  # Blue 600
        light_glow="#1d4ed8",  # Blue 700 (어두운 톤)
    ),
    Pillar.GOODNESS: PillarColor(
        pillar=Pillar.GOODNESS,
        symbol="善",
        dark_primary="#22c55e",  # Green 500
        dark_glow="#4ade80",  # Green 400
        light_primary="#16a34a",  # Green 600
        light_glow="#15803d",  # Green 700
    ),
    Pillar.BEAUTY: PillarColor(
        pillar=Pillar.BEAUTY,
        symbol="美",
        dark_primary="#a855f7",  # Purple 500
        dark_glow="#c084fc",  # Purple 400
        light_primary="#9333ea",  # Purple 600
        light_glow="#7e22ce",  # Purple 700
    ),
    Pillar.SERENITY: PillarColor(
        pillar=Pillar.SERENITY,
        symbol="孝",
        dark_primary="#f59e0b",  # Amber 500
        dark_glow="#fbbf24",  # Amber 400
        light_primary="#d97706",  # Amber 600
        light_glow="#b45309",  # Amber 700
    ),
    Pillar.ETERNITY: PillarColor(
        pillar=Pillar.ETERNITY,
        symbol="永",
        dark_primary="#ef4444",  # Red 500
        dark_glow="#f87171",  # Red 400
        light_primary="#dc2626",  # Red 600
        light_glow="#b91c1c",  # Red 700
    ),
}


@dataclass
class GlowIntensity:
    """Glow 강도 계산 결과.

    Trinity Score를 시각적 효과로 변환.
    """

    score: float  # 원본 점수 (0.0-1.0 또는 0-100)
    normalized: float  # 정규화 점수 (0.0-1.0)
    blur_radius: float  # SVG feGaussianBlur stdDeviation (px)
    opacity: float  # Glow opacity (0.0-1.0)
    spread: float  # Glow 확산 반경 (px)
    level: Literal["none", "low", "medium", "high", "critical"]

    @classmethod
    def from_score(cls, score: float, scale: Literal["unit", "percent"] = "unit") -> GlowIntensity:
        """점수로부터 Glow 강도 계산.

        Args:
            score: Trinity 점수 (0-1 또는 0-100)
            scale: 점수 스케일 ("unit" = 0-1, "percent" = 0-100)

        Returns:
            GlowIntensity 객체
        """
        # 정규화 (0.0-1.0)
        normalized = score if scale == "unit" else score / 100.0
        normalized = max(0.0, min(1.0, normalized))

        # 레벨 결정
        if normalized < 0.2:
            level: Literal["none", "low", "medium", "high", "critical"] = "none"
        elif normalized < 0.5:
            level = "low"
        elif normalized < 0.75:
            level = "medium"
        elif normalized < 0.9:
            level = "high"
        else:
            level = "critical"

        # 시각적 파라미터 계산 (비선형 스케일링)
        # Blur: 0-20px (점수에 비례)
        blur_radius = normalized * 20.0

        # Opacity: 0.3-0.9 (기본 가시성 보장)
        opacity = 0.3 + (normalized * 0.6)

        # Spread: 2-15px (점수에 비례)
        spread = 2.0 + (normalized * 13.0)

        return cls(
            score=score,
            normalized=normalized,
            blur_radius=round(blur_radius, 2),
            opacity=round(opacity, 3),
            spread=round(spread, 2),
            level=level,
        )


@dataclass
class PillarGlow:
    """개별 기둥의 Glow 설정.

    노드 customData에 저장되어 시각적 효과로 렌더링됨.
    """

    pillar: Pillar
    score: float  # 원본 점수 (0.0-1.0)
    intensity: GlowIntensity
    color: PillarColor

    @classmethod
    def from_trinity_score(
        cls,
        pillar: Pillar | str,
        score: float,
        scale: Literal["unit", "percent"] = "unit",
    ) -> PillarGlow:
        """Trinity 점수로부터 PillarGlow 생성.

        Args:
            pillar: 기둥 이름 또는 Pillar enum
            score: 점수
            scale: 점수 스케일

        Returns:
            PillarGlow 객체
        """
        # Pillar enum 변환
        if isinstance(pillar, str):
            pillar_map = {
                "truth": Pillar.TRUTH,
                "眞": Pillar.TRUTH,
                "goodness": Pillar.GOODNESS,
                "善": Pillar.GOODNESS,
                "beauty": Pillar.BEAUTY,
                "美": Pillar.BEAUTY,
                "serenity": Pillar.SERENITY,
                "孝": Pillar.SERENITY,
                "eternity": Pillar.ETERNITY,
                "永": Pillar.ETERNITY,
            }
            pillar = pillar_map.get(pillar.lower(), Pillar.TRUTH)

        intensity = GlowIntensity.from_score(score, scale)
        color = PILLAR_COLORS[pillar]

        return cls(
            pillar=pillar,
            score=score if scale == "unit" else score / 100.0,
            intensity=intensity,
            color=color,
        )

    def to_custom_data(self) -> dict[str, Any]:
        """customData 형식으로 변환 (Excalidraw 호환)."""
        return {
            "glow": {
                "pillar": self.pillar.value,
                "symbol": self.color.symbol,
                "score": round(self.score, 4),
                "level": self.intensity.level,
                "blur_radius": self.intensity.blur_radius,
                "opacity": self.intensity.opacity,
                "spread": self.intensity.spread,
            }
        }


@dataclass
class GlowConfig:
    """전체 Glow 설정.

    다이어그램 전체에 적용되는 Glow 테마 설정.
    """

    theme: ThemeMode = ThemeMode.DARK
    animation_enabled: bool = False
    animation_duration_ms: int = 2000
    badge_enabled: bool = True
    badge_size: int = 24  # Badge 크기 (px)
    glow_enabled: bool = True

    def get_pillar_colors(self, pillar: Pillar) -> tuple[str, str]:
        """테마에 따른 기둥 색상 반환.

        Returns:
            (primary_color, glow_color) 튜플
        """
        color = PILLAR_COLORS[pillar]
        if self.theme == ThemeMode.DARK:
            return color.dark_primary, color.dark_glow
        return color.light_primary, color.light_glow


# ============================================================================
# SVG Filter Generation (美 - Beauty)
# ============================================================================


class SVGFilterGenerator:
    """SVG Glow Filter 생성기.

    Trinity 점수에 따른 SVG feGaussianBlur/feDropShadow 필터 생성.
    """

    def __init__(self, config: GlowConfig | None = None) -> None:
        """초기화.

        Args:
            config: Glow 설정 (기본값 사용 시 None)
        """
        self.config = config or GlowConfig()

    def generate_filter_id(self, pillar: Pillar, level: str) -> str:
        """필터 ID 생성.

        Args:
            pillar: 기둥
            level: 강도 레벨

        Returns:
            고유 필터 ID (예: "glow-truth-high")
        """
        return f"glow-{pillar.value}-{level}"

    def generate_glow_filter(self, pillar_glow: PillarGlow) -> str:
        """개별 기둥의 SVG Glow 필터 생성.

        Args:
            pillar_glow: PillarGlow 객체

        Returns:
            SVG <filter> 요소 문자열
        """
        pillar = pillar_glow.pillar
        intensity = pillar_glow.intensity
        primary_color, glow_color = self.config.get_pillar_colors(pillar)

        filter_id = self.generate_filter_id(pillar, intensity.level)

        # 강도에 따른 필터 복잡도 조절
        if intensity.level == "none":
            return ""  # Glow 없음

        # SVG feGaussianBlur + feComposite 기반 Glow
        svg_filter = f"""<filter id="{filter_id}" x="-50%" y="-50%" width="200%" height="200%">
  <!-- Glow Layer 1: Outer Blur -->
  <feGaussianBlur in="SourceAlpha" stdDeviation="{intensity.blur_radius}" result="blur1"/>
  <feFlood flood-color="{glow_color}" flood-opacity="{intensity.opacity}" result="glowColor"/>
  <feComposite in="glowColor" in2="blur1" operator="in" result="glow1"/>

  <!-- Glow Layer 2: Inner Glow (더 선명) -->
  <feGaussianBlur in="SourceAlpha" stdDeviation="{intensity.blur_radius / 2:.2f}" result="blur2"/>
  <feFlood flood-color="{primary_color}" flood-opacity="{intensity.opacity * 0.8:.3f}" result="innerColor"/>
  <feComposite in="innerColor" in2="blur2" operator="in" result="glow2"/>

  <!-- Merge: Outer Glow + Inner Glow + Source -->
  <feMerge>
    <feMergeNode in="glow1"/>
    <feMergeNode in="glow2"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>"""

        return svg_filter

    def generate_all_filters(self, pillar_glows: list[PillarGlow]) -> str:
        """모든 기둥의 SVG 필터를 <defs>로 래핑하여 생성.

        Args:
            pillar_glows: PillarGlow 리스트

        Returns:
            SVG <defs> 요소 문자열
        """
        filters = [
            self.generate_glow_filter(pg) for pg in pillar_glows if pg.intensity.level != "none"
        ]

        if not filters:
            return ""

        return f"""<defs>
{chr(10).join(filters)}
</defs>"""

    def generate_css_glow(self, pillar_glow: PillarGlow) -> str:
        """CSS box-shadow 기반 Glow 스타일 생성 (Web 호환).

        Args:
            pillar_glow: PillarGlow 객체

        Returns:
            CSS box-shadow 값
        """
        intensity = pillar_glow.intensity
        primary_color, glow_color = self.config.get_pillar_colors(pillar_glow.pillar)

        if intensity.level == "none":
            return "none"

        # 다중 레이어 box-shadow (외부 + 내부)
        outer_shadow = f"0 0 {intensity.spread}px {intensity.blur_radius}px {glow_color}"
        inner_shadow = (
            f"0 0 {intensity.spread / 2:.1f}px {intensity.blur_radius / 2:.1f}px {primary_color}"
        )

        return f"{outer_shadow}, {inner_shadow}"

    def generate_animation_keyframes(self, pillar: Pillar) -> str:
        """Glow 애니메이션 keyframes 생성 (선택적).

        Args:
            pillar: 기둥

        Returns:
            CSS @keyframes 문자열
        """
        if not self.config.animation_enabled:
            return ""

        _, glow_color = self.config.get_pillar_colors(pillar)
        duration = self.config.animation_duration_ms

        return f"""@keyframes glow-pulse-{pillar.value} {{
  0%, 100% {{
    filter: drop-shadow(0 0 5px {glow_color});
    opacity: 0.8;
  }}
  50% {{
    filter: drop-shadow(0 0 20px {glow_color});
    opacity: 1;
  }}
}}

.glow-{pillar.value}-animated {{
  animation: glow-pulse-{pillar.value} {duration}ms ease-in-out infinite;
}}"""


# ============================================================================
# Badge Generation (善 - Goodness)
# ============================================================================


@dataclass
class PillarBadge:
    """기둥 Badge 정의.

    노드 옆에 표시되는 작은 기둥 심볼 + 점수 Badge.
    """

    pillar: Pillar
    score: float
    symbol: str
    color: str
    size: int = 24

    @classmethod
    def from_pillar_glow(cls, pillar_glow: PillarGlow, config: GlowConfig) -> PillarBadge:
        """PillarGlow로부터 Badge 생성."""
        primary_color, _ = config.get_pillar_colors(pillar_glow.pillar)
        return cls(
            pillar=pillar_glow.pillar,
            score=pillar_glow.score,
            symbol=pillar_glow.color.symbol,
            color=primary_color,
            size=config.badge_size,
        )

    def to_svg(self, x: float, y: float) -> str:
        """Badge SVG 요소 생성.

        Args:
            x: X 위치
            y: Y 위치

        Returns:
            SVG 요소 문자열
        """
        score_text = f"{self.score * 100:.0f}" if self.score <= 1.0 else f"{self.score:.0f}"

        return f"""<g class="pillar-badge" transform="translate({x}, {y})">
  <circle cx="{self.size / 2}" cy="{self.size / 2}" r="{self.size / 2}"
          fill="{self.color}" opacity="0.9"/>
  <text x="{self.size / 2}" y="{self.size / 2 + 4}"
        text-anchor="middle" font-size="12" fill="white" font-weight="bold">
    {self.symbol}
  </text>
  <text x="{self.size / 2}" y="{self.size + 12}"
        text-anchor="middle" font-size="10" fill="{self.color}">
    {score_text}
  </text>
</g>"""


# ============================================================================
# Trinity Glow Manager (孝永 - Integration)
# ============================================================================


@dataclass
class TrinityGlowResult:
    """Trinity Glow 적용 결과."""

    pillar_glows: list[PillarGlow]
    svg_filters: str
    css_styles: str
    badges: list[PillarBadge]
    custom_data: dict[str, Any]


class TrinityGlowManager:
    """Trinity Score를 시각적 Glow로 변환하는 매니저.

    DiagramGenerator와 통합하여 노드에 Glow 효과를 적용.
    """

    def __init__(self, config: GlowConfig | None = None) -> None:
        """초기화.

        Args:
            config: Glow 설정
        """
        self.config = config or GlowConfig()
        self.filter_generator = SVGFilterGenerator(self.config)

    @shield(default_return=None, pillar="美")
    def create_from_trinity_scores(
        self,
        scores: dict[str, float],
        scale: Literal["unit", "percent"] = "unit",
    ) -> TrinityGlowResult:
        """Trinity 점수 딕셔너리로부터 Glow 결과 생성.

        Args:
            scores: {"truth": 0.95, "goodness": 0.90, ...} 형태의 점수
            scale: 점수 스케일

        Returns:
            TrinityGlowResult 객체
        """
        pillar_glows: list[PillarGlow] = []

        # 각 기둥별 PillarGlow 생성
        pillar_map = {
            "truth": Pillar.TRUTH,
            "goodness": Pillar.GOODNESS,
            "beauty": Pillar.BEAUTY,
            "serenity": Pillar.SERENITY,
            "eternity": Pillar.ETERNITY,
        }

        for key, pillar in pillar_map.items():
            score = scores.get(key, 0.0)
            pillar_glow = PillarGlow.from_trinity_score(pillar, score, scale)
            pillar_glows.append(pillar_glow)

        # SVG 필터 생성
        svg_filters = self.filter_generator.generate_all_filters(pillar_glows)

        # CSS 스타일 생성
        css_parts = []
        for pg in pillar_glows:
            css_shadow = self.filter_generator.generate_css_glow(pg)
            css_parts.append(f".glow-{pg.pillar.value} {{ box-shadow: {css_shadow}; }}")
            if self.config.animation_enabled:
                css_parts.append(self.filter_generator.generate_animation_keyframes(pg.pillar))

        css_styles = "\n".join(css_parts)

        # Badge 생성
        badges = []
        if self.config.badge_enabled:
            badges = [PillarBadge.from_pillar_glow(pg, self.config) for pg in pillar_glows]

        # customData 통합
        custom_data = {
            "trinity_glow": {
                "theme": self.config.theme.value,
                "pillars": {pg.pillar.value: pg.to_custom_data()["glow"] for pg in pillar_glows},
            }
        }

        return TrinityGlowResult(
            pillar_glows=pillar_glows,
            svg_filters=svg_filters,
            css_styles=css_styles,
            badges=badges,
            custom_data=custom_data,
        )

    def inject_glow_into_element(
        self,
        element_data: dict[str, Any],
        pillar: Pillar | str,
        score: float,
        scale: Literal["unit", "percent"] = "unit",
    ) -> dict[str, Any]:
        """단일 엘리먼트에 Glow customData 주입.

        Args:
            element_data: Excalidraw 엘리먼트 딕셔너리
            pillar: 기둥
            score: 점수
            scale: 점수 스케일

        Returns:
            Glow customData가 주입된 엘리먼트
        """
        pillar_glow = PillarGlow.from_trinity_score(pillar, score, scale)

        # customData 병합
        if "customData" not in element_data:
            element_data["customData"] = {}

        element_data["customData"].update(pillar_glow.to_custom_data())

        # SVG filter reference 추가
        filter_id = self.filter_generator.generate_filter_id(
            pillar_glow.pillar, pillar_glow.intensity.level
        )
        element_data["customData"]["svgFilter"] = f"url(#{filter_id})"

        return element_data

    def apply_theme(self, theme: ThemeMode) -> None:
        """테마 변경.

        Args:
            theme: 새 테마 모드
        """
        self.config.theme = theme
        self.filter_generator.config = self.config
        logger.info(f"[TrinityGlow] Theme changed to: {theme.value}")


# ============================================================================
# Convenience Functions
# ============================================================================


def create_glow_from_scores(
    scores: dict[str, float],
    theme: ThemeMode = ThemeMode.DARK,
    scale: Literal["unit", "percent"] = "unit",
) -> TrinityGlowResult:
    """Trinity 점수로부터 Glow 결과 생성 (편의 함수).

    Args:
        scores: 5기둥 점수 딕셔너리
        theme: 테마 모드
        scale: 점수 스케일

    Returns:
        TrinityGlowResult 객체

    Example:
        >>> scores = {"truth": 0.95, "goodness": 0.90, "beauty": 0.85, "serenity": 0.92, "eternity": 1.0}
        >>> result = create_glow_from_scores(scores, theme=ThemeMode.DARK)
        >>> print(result.svg_filters)
    """
    config = GlowConfig(theme=theme)
    manager = TrinityGlowManager(config)
    return manager.create_from_trinity_scores(scores, scale)


def get_pillar_css_class(pillar: Pillar | str, score: float) -> str:
    """기둥과 점수에 따른 CSS 클래스 이름 반환.

    Args:
        pillar: 기둥
        score: 점수 (0-1)

    Returns:
        CSS 클래스 이름 (예: "glow-truth glow-level-high")
    """
    pillar_name = pillar.lower() if isinstance(pillar, str) else pillar.value

    intensity = GlowIntensity.from_score(score)
    return f"glow-{pillar_name} glow-level-{intensity.level}"
