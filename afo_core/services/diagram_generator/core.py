# Trinity Score: 94.0 (Phase 32 Diagram Generator Refactoring)
"""Core Diagram Generation Logic and Node/Connection Management"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .schemas import (
    ArrowElement,
    DiagramGeneratorResult,
    ElementType,
    ExcalidrawElement,
    TextElement,
)
from .styles import NEO_BRUTALISM, NeoBrutalismStyle

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """AI-Driven Diagram Generator (PH-SE-05.01).

    텍스트 설명을 Excalidraw JSON으로 변환하는 파이프라인.
    """

    def __init__(
        self,
        style: NeoBrutalismStyle | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the diagram generator.

        Args:
            style: Neo-Brutalism style configuration
            output_dir: Output directory for generated diagrams
        """
        self.style = style or NEO_BRUTALISM
        self.output_dir = output_dir or Path("docs/diagrams")

    def create_node(
        self,
        label: str,
        x: float,
        y: float,
        width: float = 200,
        height: float = 100,
        node_type: ElementType = ElementType.RECTANGLE,
        pillar: str | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> tuple[ExcalidrawElement, TextElement]:
        """Create a labeled node (shape + text).

        Args:
            label: Node label text
            x: X position
            y: Y position
            width: Node width
            height: Node height
            node_type: Shape type
            pillar: Trinity pillar (眞善美孝永) for color
            custom_data: Custom data to attach

        Returns:
            Tuple of (shape_element, text_element)
        """
        node_id = str(id(self)) + "_node_" + str(hash(label))[:8]
        text_id = str(id(self)) + "_text_" + str(hash(label))[:8]

        # Determine background color
        bg_color = self.style.background_color
        if pillar:
            bg_color = self.style.get_pillar_color(pillar)

        # Create shape
        shape = ExcalidrawElement(
            id=node_id,
            type=node_type,
            x=x,
            y=y,
            width=width,
            height=height,
            backgroundColor=bg_color,
            strokeColor=self.style.stroke_color,
            strokeWidth=self.style.stroke_width,
            boundElements=[{"id": text_id, "type": "text"}],
            customData=custom_data or {},
        )

        # Create text
        text = TextElement(
            id=text_id,
            x=x + width / 2,
            y=y + height / 2,
            width=width - 20,
            height=height - 20,
            text=label,
            originalText=label,
            containerId=node_id,
            fontSize=self.style.font_size,
        )

        return shape, text

    def create_arrow(
        self,
        from_element: ExcalidrawElement,
        to_element: ExcalidrawElement,
        label: str | None = None,
    ) -> ArrowElement:
        """Create an arrow connecting two elements.

        Args:
            from_element: Source element
            to_element: Target element
            label: Optional arrow label

        Returns:
            Arrow element
        """
        # Calculate connection points
        from_x = from_element.x + from_element.width
        from_y = from_element.y + from_element.height / 2
        to_x = to_element.x
        to_y = to_element.y + to_element.height / 2

        return ArrowElement(
            x=from_x,
            y=from_y,
            width=to_x - from_x,
            height=to_y - from_y,
            points=[[0, 0], [to_x - from_x, to_y - from_y]],
            startBinding={
                "elementId": from_element.id,
                "focus": 0,
                "gap": 1,
            },
            endBinding={
                "elementId": to_element.id,
                "focus": 0,
                "gap": 1,
            },
            strokeColor=self.style.stroke_color,
            strokeWidth=self.style.stroke_width,
        )

    def inject_graph_state(
        self,
        elements: list[ExcalidrawElement],
        graph_state: dict[str, Any],
    ) -> list[ExcalidrawElement]:
        """Inject GraphState data into diagram elements.

        Args:
            elements: List of diagram elements
            graph_state: GraphState data to inject

        Returns:
            Updated elements with injected data
        """
        # Extract key fields from GraphState
        state_info = {
            "trace_id": graph_state.get("trace_id", ""),
            "request_id": graph_state.get("request_id", ""),
            "step": graph_state.get("step", ""),
            "errors": graph_state.get("errors", []),
            "outputs": graph_state.get("outputs", {}),
        }

        for element in elements:
            if hasattr(element, "customData"):
                element.customData["graph_state"] = state_info

        return elements

    def generate_trinity_diagram(
        self,
        title: str = "Trinity Architecture",
        graph_state: dict[str, Any] | None = None,
    ) -> DiagramGeneratorResult:
        """Generate a Trinity (眞善美孝永) diagram.

        Args:
            title: Diagram title
            graph_state: Optional GraphState to inject

        Returns:
            DiagramGeneratorResult with generated diagram
        """
        elements: list[ExcalidrawElement | TextElement | ArrowElement] = []

        # Create title
        title_text = TextElement(
            x=300,
            y=20,
            width=400,
            height=40,
            text=title,
            fontSize=32,
            strokeColor=self.style.stroke_color,
        )
        elements.append(title_text)

        # Create Trinity nodes
        pillars = [
            ("眞 Truth", 100, 100, "眞"),
            ("善 Goodness", 350, 100, "善"),
            ("美 Beauty", 600, 100, "美"),
            ("孝 Serenity", 225, 250, "孝"),
            ("永 Eternity", 475, 250, "永"),
        ]

        nodes: list[ExcalidrawElement] = []
        for label, x, y, pillar in pillars:
            shape, text = self.create_node(
                label=label,
                x=x,
                y=y,
                width=180,
                height=80,
                pillar=pillar,
                custom_data={"pillar": pillar},
            )
            elements.extend([shape, text])
            nodes.append(shape)

        # Create connections (眞→善, 善→美, 眞→孝, 美→孝, 孝→永)
        connections = [
            (0, 1),  # 眞 → 善
            (1, 2),  # 善 → 美
            (0, 3),  # 眞 → 孝
            (2, 3),  # 美 → 孝
            (3, 4),  # 孝 → 永
        ]

        for from_idx, to_idx in connections:
            arrow = self.create_arrow(nodes[from_idx], nodes[to_idx])
            elements.append(arrow)

        # Inject GraphState if provided
        if graph_state:
            elements = self.inject_graph_state(elements, graph_state)  # type: ignore[assignment]

        # Build Excalidraw JSON
        excalidraw_json = self._build_excalidraw_json(elements)

        return DiagramGeneratorResult(
            success=True,
            elements=[e.to_dict() for e in elements],
            excalidraw_json=excalidraw_json,
        )

    def generate_flow_diagram(
        self,
        nodes: list[dict[str, Any]],
        connections: list[tuple[int, int]],
        title: str = "Flow Diagram",
        graph_state: dict[str, Any] | None = None,
    ) -> DiagramGeneratorResult:
        """Generate a flow diagram from node definitions.

        Args:
            nodes: List of node definitions with keys: label, x, y, pillar (optional)
            connections: List of (from_index, to_index) tuples
            title: Diagram title
            graph_state: Optional GraphState to inject

        Returns:
            DiagramGeneratorResult with generated diagram
        """
        elements: list[ExcalidrawElement | TextElement | ArrowElement] = []
        node_elements: list[ExcalidrawElement] = []

        # Create title
        title_text = TextElement(
            x=300,
            y=20,
            width=400,
            height=40,
            text=title,
            fontSize=32,
            strokeColor=self.style.stroke_color,
        )
        elements.append(title_text)

        # Create nodes
        for node_def in nodes:
            shape, text = self.create_node(
                label=node_def.get("label", "Node"),
                x=node_def.get("x", 0),
                y=node_def.get("y", 0),
                width=node_def.get("width", 180),
                height=node_def.get("height", 80),
                pillar=node_def.get("pillar"),
                custom_data=node_def.get("custom_data"),
            )
            elements.extend([shape, text])
            node_elements.append(shape)

        # Create connections
        for from_idx, to_idx in connections:
            if 0 <= from_idx < len(node_elements) and 0 <= to_idx < len(node_elements):
                arrow = self.create_arrow(node_elements[from_idx], node_elements[to_idx])
                elements.append(arrow)

        # Inject GraphState if provided
        if graph_state:
            elements = self.inject_graph_state(elements, graph_state)  # type: ignore[assignment]

        # Build Excalidraw JSON
        excalidraw_json = self._build_excalidraw_json(elements)

        return DiagramGeneratorResult(
            success=True,
            elements=[e.to_dict() for e in elements],
            excalidraw_json=excalidraw_json,
        )

    def save_diagram(
        self,
        result: DiagramGeneratorResult,
        filename: str,
    ) -> DiagramGeneratorResult:
        """Save diagram to file.

        Args:
            result: Diagram generation result
            filename: Output filename (without extension)

        Returns:
            Updated result with file path
        """
        if not result.success:
            return result

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save .excalidraw file
        excalidraw_path = self.output_dir / f"{filename}.excalidraw"
        excalidraw_path.write_text(
            json.dumps(result.excalidraw_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"Saved diagram to {excalidraw_path}")

        return DiagramGeneratorResult(
            success=True,
            elements=result.elements,
            excalidraw_json=result.excalidraw_json,
            file_path=str(excalidraw_path),
        )

    def _build_excalidraw_json(
        self,
        elements: list[ExcalidrawElement | TextElement | ArrowElement],
    ) -> dict[str, Any]:
        """Build complete Excalidraw JSON structure.

        Args:
            elements: List of diagram elements

        Returns:
            Complete Excalidraw JSON dict
        """
        return {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": [e.to_dict() for e in elements],
            "appState": {
                "gridSize": None,
                "viewBackgroundColor": "#ffffff",
            },
            "files": {},
        }

    def validate_excalidraw_json(self, json_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate Excalidraw JSON structure.

        Args:
            json_data: JSON data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Check required top-level fields
        required_fields = ["type", "version", "elements"]
        for req_field in required_fields:
            if req_field not in json_data:
                errors.append(f"Missing required field: {req_field}")

        # Check type
        if json_data.get("type") != "excalidraw":
            errors.append(f"Invalid type: {json_data.get('type')}, expected 'excalidraw'")

        # Check elements
        elements = json_data.get("elements", [])
        if not isinstance(elements, list):
            errors.append("'elements' must be a list")
        else:
            for i, elem in enumerate(elements):
                if not isinstance(elem, dict):
                    errors.append(f"Element {i} is not a dict")
                    continue
                if "id" not in elem:
                    errors.append(f"Element {i} missing 'id'")
                if "type" not in elem:
                    errors.append(f"Element {i} missing 'type'")

        return len(errors) == 0, errors


# ============================================================================
# Module-level Convenience Functions (Backward Compatibility)
# ============================================================================


def generate_trinity_diagram(
    title: str = "Trinity Architecture",
    trinity_scores: dict[str, float] | None = None,  # Reserved for future use
    graph_state: dict[str, Any] | None = None,
    output_dir: Path | None = None,
) -> DiagramGeneratorResult:
    """Generate a Trinity diagram.

    Convenience function that creates a DiagramGenerator and generates a diagram.

    Args:
        title: Diagram title
        trinity_scores: Optional trinity scores dict (reserved for future use)
        graph_state: Optional graph state for injection
        output_dir: Output directory for saved files

    Returns:
        DiagramGeneratorResult with generated diagram
    """
    # Note: trinity_scores is accepted for API compatibility but not yet used
    # by the underlying DiagramGenerator.generate_trinity_diagram method
    _ = trinity_scores  # Suppress unused variable warning
    generator = DiagramGenerator(output_dir=output_dir)
    return generator.generate_trinity_diagram(
        title=title,
        graph_state=graph_state,
    )


def parse_and_generate_diagram(
    description: str,
    graph_state: dict[str, Any] | None = None,
    output_dir: Path | None = None,
) -> DiagramGeneratorResult:
    """Parse text description and generate diagram.

    Convenience function that creates a DiagramGenerator and parses a description.

    Args:
        description: Text description of the diagram (e.g., "A -> B -> C")
        graph_state: Optional graph state for injection
        output_dir: Output directory for saved files

    Returns:
        DiagramGeneratorResult with generated diagram
    """
    generator = DiagramGenerator(output_dir=output_dir)

    # Parse simple arrow notation (e.g., "A -> B -> C")
    # into nodes and connections for generate_flow_diagram
    parts = [p.strip() for p in description.split("->")]
    nodes = [{"label": p, "x": i * 200, "y": 100} for i, p in enumerate(parts)]
    connections = [(i, i + 1) for i in range(len(parts) - 1)]

    return generator.generate_flow_diagram(
        nodes=nodes,
        connections=connections,
        title="Parsed Diagram",
        graph_state=graph_state,
    )
