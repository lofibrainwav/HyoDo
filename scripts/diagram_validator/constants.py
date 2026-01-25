"""
Diagram Validator Constants - Configuration values and patterns

Contains:
- AFO Pillar definitions
- Valid Excalidraw element types
- Valid stroke/fill styles
- Naming convention patterns
"""

import re

# AFO Pillar definitions (based on diagram_generator.py)
PILLAR_NAMES = {
    "truth": ["truth", "jin", "uc9c4"],  # Korean: jin/uc9c4
    "goodness": ["goodness", "seon", "uc120"],  # Korean: seon/uc120
    "beauty": ["beauty", "mi", "ubbf8"],  # Korean: mi/ubbf8
    "serenity": ["serenity", "hyo", "ud6a8"],  # Korean: hyo/ud6a8
    "eternity": ["eternity", "yeong", "uc601"],  # Korean: yeong/uc601
}

# Valid Excalidraw element types (from diagram_generator.py ElementType)
VALID_ELEMENT_TYPES = {
    "rectangle",
    "ellipse",
    "diamond",
    "text",
    "arrow",
    "line",
    "freedraw",
    "image",
    "frame",
}

# Valid stroke/fill styles
VALID_STROKE_STYLES = {"solid", "dashed", "dotted"}
VALID_FILL_STYLES = {"solid", "hachure", "cross-hatch"}

# AFO Naming Convention Patterns
FILE_NAMING_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.excalidraw$")
NODE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
