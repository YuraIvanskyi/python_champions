from pathlib import Path

root = Path(__file__).resolve().parents[1] / "implementation" / "issues"
count = 0
for p in root.glob("ISS-*.md"):
    text = p.read_text(encoding="utf-8")
    if "status: open" in text:
        text = text.replace("status: open", "status: fixed")
        p.write_text(text, encoding="utf-8")
        count += 1
print(f"Marked {count} tickets fixed")
