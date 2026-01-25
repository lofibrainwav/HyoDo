import asyncio
import os
import pathlib
import sys

# Add package root to path
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.start.serenity.genui_orchestrator import GenUIOrchestrator


async def main():
    print("🎨 [GenUI] Initializing Royal Architect...")
    orchestrator = GenUIOrchestrator()

    prompt = """
    Create a 'RoyalAnalyticsWidget' using 'recharts' and 'framer-motion'.
    It should display a LineChart of the Kingdom's Trinity Scores (Truth, Goodness, Beauty) over 7 days.

    Data:
    - Truth: [80, 82, 85, 88, 87, 89, 92]
    - Goodness: [75, 78, 80, 85, 90, 88, 91]
    - Beauty: [60, 65, 70, 75, 80, 85, 95]

    Design:
    - Container: Glassmorphism Card (bg-white/10, backdrop-blur-md, border-white/20).
    - Title: "Royal Trinity Analysis" with a crown icon (Lucide).
    - Colors: Truth=Cyan, Goodness=Emerald, Beauty=Purple.
    - Animation: Entry fade-in.
    """

    print(f"🧠 [Prompt] {prompt.strip()[:100]}...")
    result = await orchestrator.generate_component(prompt)

    if result["success"]:
        print("✅ Creation Successful!")
        print(f"   Path: {result['path']}")
        print(f"   Trinity Score: {result['trinity_score']}")
    else:
        print(f"❌ Creation Failed: {result.get('reason')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
