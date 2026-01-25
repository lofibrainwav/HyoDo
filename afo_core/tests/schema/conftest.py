"""Shared fixtures for diagram schema tests.

Fixtures used across test_diagram_*.py split files.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def valid_excalidraw_json() -> dict:
    """Minimal valid Excalidraw JSON structure."""
    return {
        "type": "excalidraw",
        "version": 2,
        "elements": [
            {
                "id": "elem_001",
                "type": "rectangle",
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 150,
            }
        ],
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }


@pytest.fixture
def trinity_diagram_json() -> dict:
    """Excalidraw JSON with all 5 pillar nodes."""
    return {
        "type": "excalidraw",
        "version": 2,
        "elements": [
            {
                "id": "truth_node",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "truth"},
            },
            {
                "id": "truth_text",
                "type": "text",
                "x": 130,
                "y": 130,
                "text": "Truth",
                "originalText": "Truth",
            },
            {
                "id": "goodness_node",
                "type": "rectangle",
                "x": 350,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "goodness"},
            },
            {
                "id": "goodness_text",
                "type": "text",
                "x": 380,
                "y": 130,
                "text": "Goodness",
            },
            {
                "id": "beauty_node",
                "type": "rectangle",
                "x": 600,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "beauty"},
            },
            {
                "id": "beauty_text",
                "type": "text",
                "x": 630,
                "y": 130,
                "text": "Beauty",
            },
            {
                "id": "serenity_node",
                "type": "rectangle",
                "x": 225,
                "y": 250,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "serenity"},
            },
            {
                "id": "serenity_text",
                "type": "text",
                "x": 255,
                "y": 280,
                "text": "Serenity",
            },
            {
                "id": "eternity_node",
                "type": "rectangle",
                "x": 475,
                "y": 250,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "eternity"},
            },
            {
                "id": "eternity_text",
                "type": "text",
                "x": 505,
                "y": 280,
                "text": "Eternity",
            },
            {
                "id": "arrow_01",
                "type": "arrow",
                "x": 280,
                "y": 140,
                "width": 70,
                "height": 0,
                "points": [[0, 0], [70, 0]],
            },
        ],
        "appState": {},
        "files": {},
    }


@pytest.fixture
def tmp_diagram_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with diagram files."""
    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()
    return diagrams_dir
