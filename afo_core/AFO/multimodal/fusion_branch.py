"""
FusionBranch - DaVinci Resolve Fusion 컴포지팅 통합
TimelineState를 Fusion 페이지 노드 그래프로 변환하여 VFX 합성 자동화

외부 자료 기반: Blackmagic Fusion Scripting Guide 2026, DaVinci Resolve API
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FusionBranch:
    """
    DaVinci Resolve Fusion 컴포지팅 브랜치
    TimelineState를 Fusion 노드 그래프로 변환
    """

    def __init__(self) -> None:
        self.resolve: Any | None = None
        self.fusion: Any | None = None
        self._connected = False

    def connect_resolve(self) -> bool:
        """
        DaVinci Resolve Fusion API 연결

        Returns:
            bool: 연결 성공 여부
        """
        try:
            # DaVinci Resolve API 임포트 (외부 의존성)
            import DaVinciResolveScript as dvr

            self.resolve = dvr.scriptapp("Resolve")
            if self.resolve:
                self.fusion = self.resolve.Fusion()
                self._connected = True
                logger.info("DaVinci Resolve Fusion API 연결 성공")
                return True
            else:
                logger.warning("DaVinci Resolve가 실행되지 않음")
                return False

        except ImportError:
            logger.warning("DaVinciResolveScript 모듈을 찾을 수 없음")
            return False
        except Exception as e:
            logger.error(f"Fusion API 연결 실패: {e}")
            return False

    def create_composition_from_timeline(
        self,
        timeline_sections: list[dict[str, Any]],
        input_clips: list[str],
        output_path: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        TimelineState를 Fusion 컴포지션으로 변환

        Args:
            timeline_sections: TimelineState sections
            input_clips: 입력 클립 경로 리스트
            output_path: 출력 파일 경로
            dry_run: 실제 렌더링 없이 계획만 생성

        Returns:
            컴포지션 결과 정보
        """
        if not self._connected:
            return {
                "success": True,
                "mode": "dry_run_fallback",
                "error": "Fusion API 연결되지 않음 - dry run 모드로 진행",
                "dry_run_plan": self._generate_dry_run_plan(
                    timeline_sections, input_clips, output_path
                ),
            }

        try:
            # 새 컴포지션 생성
            comp = self.fusion.NewComp()

            # 클립 로더 노드 생성 및 타임라인 빌드
            prev_node = None
            vfx_nodes = []

            for i, section in enumerate(timeline_sections):
                if i >= len(input_clips):
                    break

                # 클립 로더 생성
                loader = comp.Loader({"Clip": input_clips[i]})

                # 첫 번째 클립은 백그라운드
                if prev_node is None:
                    prev_node = loader
                else:
                    # Merge 노드로 클립 합성
                    merge = comp.Merge({"Background": prev_node, "Foreground": loader})
                    prev_node = merge

                # VFX 효과 적용
                effect_nodes = self._apply_vfx_effects(comp, section, merge)
                vfx_nodes.extend(effect_nodes)

            # Saver 노드로 출력 설정
            saver = comp.Saver({"Clip": output_path})
            if prev_node:
                saver.ConnectInput("Input", prev_node)

            # Dry run 모드
            if dry_run:
                result = {
                    "success": True,
                    "mode": "dry_run",
                    "composition_created": True,
                    "nodes_created": (
                        len(comp.GetToolList()) if hasattr(comp, "GetToolList") else "unknown"
                    ),
                    "vfx_nodes_applied": len(vfx_nodes),
                    "output_path": output_path,
                    "render_ready": True,
                }
                logger.info(f"Dry run 완료: {len(vfx_nodes)}개 VFX 노드 적용")
                return result

            # 실제 렌더링 (WET 모드)
            logger.info("Fusion 렌더링 시작...")
            comp.SetActiveTool(saver)
            render_result = comp.Render()

            return {
                "success": True,
                "mode": "wet_run",
                "render_result": render_result,
                "output_path": output_path,
                "composition_saved": True,
            }

        except Exception as e:
            logger.error(f"Fusion 컴포지션 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "dry_run_plan": self._generate_dry_run_plan(
                    timeline_sections, input_clips, output_path
                ),
            }

    def _apply_vfx_effects(self, comp: Any, section: dict[str, Any], input_node: Any) -> list[Any]:
        """
        섹션별 VFX 효과 적용

        Args:
            comp: Fusion 컴포지션 객체
            section: TimelineState 섹션
            input_node: 입력 노드

        Returns:
            생성된 VFX 노드 리스트
        """
        vfx_nodes = []
        video_effect = section.get("video", "")

        try:
            if video_effect == "keying":
                # Ultra Key 노드 (그린스크린 키잉)
                keyer = comp.AddTool("UltraKeyer")
                keyer.ConnectInput("Input", input_node)
                vfx_nodes.append(keyer)

            elif video_effect == "roto":
                # BSpline 노드 (로토스코핑)
                roto = comp.AddTool("BSpline")
                roto.ConnectInput("Input", input_node)
                vfx_nodes.append(roto)

            elif video_effect == "particle":
                # pEmitter 노드 (파티클 효과)
                particles = comp.AddTool("pEmitter")
                particles.ConnectInput("Input", input_node)
                vfx_nodes.append(particles)

            elif video_effect == "blur":
                # Blur 노드
                blur = comp.AddTool("Blur")
                blur.ConnectInput("Input", input_node)
                blur.SetAttrs({"BlurType": "Gaussian", "XBlurSize": 5.0})
                vfx_nodes.append(blur)

            elif video_effect == "glow":
                # Glow 노드
                glow = comp.AddTool("Glow")
                glow.ConnectInput("Input", input_node)
                vfx_nodes.append(glow)

            # 추가 VFX 효과는 여기에 확장 가능

        except Exception as e:
            logger.warning(f"VFX 효과 적용 실패 ({video_effect}): {e}")

        return vfx_nodes

    def _generate_dry_run_plan(
        self,
        timeline_sections: list[dict[str, Any]],
        input_clips: list[str],
        output_path: str,
    ) -> dict[str, Any]:
        """
        Dry run용 계획 생성

        Args:
            timeline_sections: TimelineState sections
            input_clips: 입력 클립 리스트
            output_path: 출력 경로

        Returns:
            Dry run 계획
        """
        plan = {
            "timeline_sections": len(timeline_sections),
            "input_clips": len(input_clips),
            "output_path": output_path,
            "planned_nodes": [],
        }

        for i, section in enumerate(timeline_sections):
            video_effect = section.get("video", "none")
            plan["planned_nodes"].append(
                {
                    "section": i,
                    "effect": video_effect,
                    "clip": input_clips[i] if i < len(input_clips) else None,
                }
            )

        return plan

    def get_available_tools(self) -> list[str]:
        """
        사용 가능한 Fusion 도구 리스트 반환

        Returns:
            도구 이름 리스트
        """
        if not self._connected or not self.fusion:
            return []

        try:
            # Fusion에서 사용 가능한 도구 조회
            tools = self.fusion.GetArgs()
            return list(tools.keys()) if tools else []
        except Exception as e:
            logger.error(f"Fusion 도구 목록 조회 실패: {e}")
            return []


# 글로벌 FusionBranch 인스턴스
_fusion_branch = None


def get_fusion_branch() -> FusionBranch:
    """
    FusionBranch 싱글톤 인스턴스 반환

    Returns:
        FusionBranch 인스턴스
    """
    global _fusion_branch
    if _fusion_branch is None:
        _fusion_branch = FusionBranch()
    return _fusion_branch


def fusion_composite(
    timeline: list[dict[str, Any]],
    input_clips: list[str],
    output_path: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Fusion 컴포지팅 편의 함수

    Args:
        timeline: TimelineState sections
        input_clips: 입력 클립 경로 리스트
        output_path: 출력 파일 경로
        dry_run: 실제 렌더링 없이 계획만 생성

    Returns:
        컴포지션 결과
    """
    fusion = get_fusion_branch()

    # 연결 시도
    if not fusion.connect_resolve():
        logger.warning("Fusion 연결 실패, dry run 모드로 진행")
        dry_run = True

    return fusion.create_composition_from_timeline(timeline, input_clips, output_path, dry_run)


if __name__ == "__main__":
    # 테스트용 TimelineState
    test_timeline = [
        {"time": "0:00-0:15", "intent": "intro", "video": "keying"},
        {"time": "0:15-0:30", "intent": "hook", "video": "particle"},
        {"time": "0:30-0:45", "intent": "content", "video": "blur"},
        {"time": "0:45-1:00", "intent": "climax", "video": "glow"},
        {"time": "1:00-1:15", "intent": "outro", "video": "roto"},
    ]

    test_clips = [
        "/path/to/clip1.mp4",
        "/path/to/clip2.mp4",
        "/path/to/clip3.mp4",
        "/path/to/clip4.mp4",
        "/path/to/clip5.mp4",
    ]

    # Dry run 테스트
    result = fusion_composite(
        test_timeline, test_clips, "/output/fusion_composite.mp4", dry_run=True
    )
    print("Fusion 컴포지팅 테스트 결과:")
    print(f"성공: {result.get('success', False)}")
    print(f"모드: {result.get('mode', 'unknown')}")
    print(f"VFX 노드 수: {result.get('vfx_nodes_applied', 0)}")
