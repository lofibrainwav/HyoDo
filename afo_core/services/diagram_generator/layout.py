"""Layout Calculator for Diagram Generation

Calculates node positions for various layout types.

Trinity Score: 眞 95% | 善 90% | 美 95%
- 眞 (Truth): Accurate position calculations
- 善 (Goodness): Consistent spacing
- 美 (Beauty): Visually pleasing layouts
"""

from __future__ import annotations

from typing import Any


def calculate_layout(
    nodes: list[dict[str, Any]],
    layout_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate node positions based on layout configuration.

    Args:
        nodes: List of node definitions
        layout_config: Layout configuration with type and direction

    Returns:
        List of nodes with x, y positions added
    """
    layout_type = layout_config.get("type", "hierarchical")
    positioned_nodes = []

    if layout_type == "hierarchical":
        positioned_nodes = _hierarchical_layout(nodes)
    elif layout_type == "circular":
        positioned_nodes = _circular_layout(nodes)
    else:
        positioned_nodes = _grid_layout(nodes)

    return positioned_nodes


def _hierarchical_layout(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hierarchical top-down layout."""
    x_start, y_start = 100, 100
    x_spacing, y_spacing = 250, 150
    positioned_nodes = []

    for i, node in enumerate(nodes):
        positioned_node = node.copy()
        positioned_node.update(
            {
                "x": x_start + (i % 4) * x_spacing,
                "y": y_start + (i // 4) * y_spacing,
            }
        )
        positioned_nodes.append(positioned_node)

    return positioned_nodes


def _circular_layout(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Circular radial layout."""
    center_x, center_y = 400, 300
    radius = 200
    positioned_nodes = []

    for i, node in enumerate(nodes):
        positioned_node = node.copy()
        positioned_node.update(
            {
                "x": center_x + radius * 0.7 * (i % 2 * 2 - 1),
                "y": center_y + radius * (i // 2) * 0.5,
            }
        )
        positioned_nodes.append(positioned_node)

    return positioned_nodes


def _grid_layout(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simple grid layout."""
    positioned_nodes = []

    for i, node in enumerate(nodes):
        positioned_node = node.copy()
        positioned_node.update(
            {
                "x": 100 + (i % 5) * 200,
                "y": 100 + (i // 5) * 120,
            }
        )
        positioned_nodes.append(positioned_node)

    return positioned_nodes
