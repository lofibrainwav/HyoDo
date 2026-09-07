"""Audience profile resolution and per-profile presentation vocabulary.

A profile is a presentation lens, never a decision input: the decision word,
exit code, ``rule_id``, evidence references, and ``--json`` payload content
stay byte-identical across profiles. This module only resolves *which*
vocabulary table a caller should read from and stores that vocabulary data
(config I/O, the six-virtue label sets). See ``docs/AUDIENCE.md``.

Config lives at ``.hyodo/config.toml`` (schema ``hyodo.config/v1``)::

    schema = "hyodo.config/v1"

    [audience]
    profile = "vibe"       # "vibe" | "engineer" | "professional"
    domain = "law"         # optional, professional only: "law" | "accounting" | "general"

Resolution order for the profile: ``--audience`` flag -> ``HYODO_AUDIENCE``
env var -> config file -> default ``engineer``. A missing or unreadable
config file is never an error -- it silently resolves to the default. An
explicit ``--audience``/``HYODO_AUDIENCE`` value outside the known set is an
error the caller must surface (``InvalidAudienceError``); an invalid value
sitting in the config file is treated the same as a missing config file
(silently falls through to the next source), keeping "never an error"
scoped to the file a human is less likely to be looking at when it fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]

CONFIG_SCHEMA_ID = "hyodo.config/v1"
CONFIG_RELATIVE_PATH = Path(".hyodo") / "config.toml"

VALID_PROFILES: tuple[str, ...] = ("engineer", "vibe", "professional")
VALID_DOMAINS: tuple[str, ...] = ("law", "accounting", "general")
DEFAULT_PROFILE = "engineer"


class InvalidAudienceError(ValueError):
    """Raised when an explicit ``--audience``/``HYODO_AUDIENCE`` value is unknown.

    Callers surface this as exit 2 ``UNOBSERVED`` with reason
    ``invalid_audience:<value>`` -- never as a silent fallback, because the
    caller asked for something explicit and got it wrong.
    """

    def __init__(self, value: str) -> None:
        super().__init__(f"invalid_audience:{value}")
        self.value = value


@dataclass(frozen=True)
class AudienceProfile:
    """A resolved presentation lens. ``domain`` is only ever set for professional."""

    profile: str
    domain: str | None = None


def load_config(root: Path) -> dict[str, Any] | None:
    """Load ``.hyodo/config.toml`` under *root*.

    Returns ``None`` on any problem (missing file, unreadable, invalid TOML,
    non-table root) -- callers treat that identically to "no config file".
    """
    path = Path(root) / CONFIG_RELATIVE_PATH
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        raw = tomllib.loads(raw_text)
    except Exception:  # tomllib.TOMLDecodeError, but be defensive like other loaders here
        return None
    if not isinstance(raw, dict):
        return None
    return raw


def resolve_audience(
    root: Path, flag: str | None = None, env: str | None = None
) -> AudienceProfile:
    """Resolve the audience profile: ``flag`` -> ``env`` -> config file -> default.

    Raises :class:`InvalidAudienceError` only when *flag* or *env* was given
    and is not one of :data:`VALID_PROFILES`. An invalid or absent config
    file value never raises.
    """
    if flag is not None:
        if flag not in VALID_PROFILES:
            raise InvalidAudienceError(flag)
        chosen = flag
    elif env is not None:
        if env not in VALID_PROFILES:
            raise InvalidAudienceError(env)
        chosen = env
    else:
        chosen = None

    config = load_config(root)
    config_domain: str | None = None
    if isinstance(config, dict):
        audience_table = config.get("audience")
        if isinstance(audience_table, dict):
            if chosen is None:
                candidate = audience_table.get("profile")
                if isinstance(candidate, str) and candidate in VALID_PROFILES:
                    chosen = candidate
            domain_candidate = audience_table.get("domain")
            if isinstance(domain_candidate, str) and domain_candidate in VALID_DOMAINS:
                config_domain = domain_candidate

    if chosen is None:
        chosen = DEFAULT_PROFILE

    domain = config_domain if chosen == "professional" else None
    return AudienceProfile(profile=chosen, domain=domain)


def write_config(root: Path, profile: str, domain: str | None = None) -> Path:
    """Write ``.hyodo/config.toml`` with an explicit audience selection.

    Raises ``ValueError`` for an unknown *profile*; a *domain* is only ever
    written alongside ``profile == "professional"`` and only when it is one
    of :data:`VALID_DOMAINS` -- silently dropped otherwise, never guessed.
    """
    if profile not in VALID_PROFILES:
        raise ValueError(f"invalid_audience:{profile}")
    path = Path(root) / CONFIG_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'schema = "{CONFIG_SCHEMA_ID}"', "", "[audience]", f'profile = "{profile}"']
    if profile == "professional" and isinstance(domain, str) and domain in VALID_DOMAINS:
        lines.append(f'domain = "{domain}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Six-virtue labels per profile
# --------------------------------------------------------------------------- #
# Keyed identically to hyodo.dashboard.PILLAR_SPECS's first column (jin, seon,
# mi, in, hyo, yeong) so a caller can zip the two without changing
# PILLAR_SPECS itself. Exposed as data for `--explain` headers and a future
# dashboard column-header source; this PR does not wire it into either
# surface yet.
VIRTUE_LABELS: dict[str, dict[str, str]] = {
    "engineer": {
        "jin": "Truth",
        "seon": "Goodness",
        "mi": "Beauty",
        "in": "Benevolence",
        "hyo": "Filial Piety",
        "yeong": "Eternity",
    },
    "vibe": {
        "jin": "Is it true?",
        "seon": "Is it safe?",
        "mi": "Is it clear?",
        "in": "Is it kind to the next person?",
        "hyo": "Does it follow the project?",
        "yeong": "Will it last?",
    },
    "professional": {
        "jin": "Accuracy",
        "seon": "Safety & security",
        "mi": "Clarity",
        "in": "Usability",
        "hyo": "Alignment",
        "yeong": "Sustainability",
    },
}


# --------------------------------------------------------------------------- #
# Professional domain noun substitution
# --------------------------------------------------------------------------- #
# Applied only in professional mode, only to these three nouns. "accounting"
# and "general" keep the defaults already baked into EXPLANATIONS_PROFESSIONAL
# (workpaper/sign-off/engagement are already the accounting-native terms).
DOMAIN_NOUNS: dict[str, dict[str, str]] = {
    "law": {
        "engagement": "matter",
        "workpaper": "exhibit",
        "sign-off": "counsel review",
    },
}


def apply_domain_nouns(text: str, domain: str | None) -> str:
    """Swap the professional-mode domain nouns in *text* for *domain*, if any."""
    substitutions = DOMAIN_NOUNS.get(domain or "")
    if not substitutions:
        return text
    for noun, replacement in substitutions.items():
        text = text.replace(noun, replacement)
    return text
