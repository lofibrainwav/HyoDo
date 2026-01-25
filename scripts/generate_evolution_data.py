import csv
import pathlib
import random

OUTPUT_FILE = "data/afo_thoughts_500.csv"

# 5 Pillars Definitions for Synthetic Data
PILLARS: dict[str, list[str]] = {
    "眞": [
        "type checking",
        "mypy strict",
        "validation",
        "logic verification",
        "integrity check",
        "schema validation",
        "truth enforcement",
        "syntax analysis",
        "backend logic",
        "pydantic model",
    ],
    "善": [
        "security scan",
        "vulnerability check",
        "grype",
        "syft",
        "sbom generation",
        "risk assessment",
        "firewall",
        "guardrails",
        "ethical check",
        "safe execution",
    ],
    "美": [
        "glassmorphism",
        "tailwind css",
        "ui design",
        "aesthetic upgrade",
        "visual polish",
        "gradient background",
        "animation",
        "lucide icons",
        "responsive layout",
        "beautiful interface",
    ],
    "孝": [
        "reducing friction",
        "user experience",
        "serenity",
        "zero config",
        "easy deployment",
        "thought stream",
        "sse feedback",
        "comfort",
        "peace of mind",
        "automatic handling",
    ],
    "永": [
        "logging to history",
        "evolution log",
        "database commit",
        "persistent storage",
        "archiving",
        "memory update",
        "ssot synchronization",
        "record keeping",
        "backup",
        "timeline event",
    ],
}


def generate_data() -> None:
    """Generate synthetic evolution data for AFO Kingdom training."""
    data: list[list[str]] = []

    # Generate 100 samples per pillar for perfect balance
    for pillar, phrases in PILLARS.items():
        for _ in range(100):
            phrase = random.choice(phrases)
            context = random.choice(
                [
                    f"Executing {phrase} for system stability.",
                    f"Applying {phrase} to the codebase.",
                    f"System is optimizing {phrase} now.",
                    f"Checking {phrase} status...",
                    f"Refining {phrase} based on feedback.",
                    f"Integration of {phrase} complete.",
                    f"Analyzing {phrase} metrics.",
                ]
            )
            data.append([context, pillar])

    # Shuffle
    random.shuffle(data)

    # Write to CSV
    with pathlib.Path(OUTPUT_FILE).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(data)

    print(f"✅ Generated {len(data)} synthetic thoughts in {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_data()
