import markdown
import os
from pathlib import Path

def generate():
    docs_dir = Path(__file__).resolve().parent.parent / "assets" / "docs"
    template = """
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Camera Manual</title>
    <link rel="stylesheet" href="manual_style.css">
</head>
<body>
    {content}
</body>
</html>
    """
    
    langs = ["zh_CN", "zh_TW", "en_US"]
    
    for lang in langs:
        md_file = docs_dir / f"manual_{lang}.md"
        html_file = docs_dir / f"manual_{lang}.html"
        
        if not md_file.exists():
            print(f"Skipping {lang}, MD not found")
            continue
            
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
            html_content = markdown.markdown(text, extensions=['extra'])
            
        full_html = template.format(lang=lang.split('_')[0], content=html_content)
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"Generated {html_file}")

if __name__ == "__main__":
    generate()
