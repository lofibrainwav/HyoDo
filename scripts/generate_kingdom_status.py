import json
from pathlib import Path


def generate():
    score_path = Path("scripts/trinity_score.json")
    if not score_path.exists():
        print("Score data missing!")
        return

    data = json.load(score_path.open())
    score = data["total_score"]

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; background: #1a1a1a; color: white; text-align: center; }}
            .trinity-number {{ font-size: 8rem; color: #FFD700; text-shadow: 0 0 20px rgba(255,215,0,0.5); }}
            .pill-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; padding: 20px; }}
            .pill {{ border: 1px solid #444; padding: 10px; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <h1>🏰 AFO Kingdom Status</h1>
        <div class="trinity-number">{score:.1f}</div>
        <div class="pill-grid">
    """
    for pillar, p_score in data["pillar_scores"].items():
        html += f'<div class="pill"><h3>{pillar.upper()}</h3><p>{p_score:.1f}</p></div>'

    html += "</div></body></html>"
    Path("scripts/kingdom_status.html").write_text(html)
    print(f"Generated status with score {score:.1f}")


if __name__ == "__main__":
    generate()
