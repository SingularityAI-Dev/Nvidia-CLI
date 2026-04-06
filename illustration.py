import os
from PIL import Image, ImageDraw, ImageFont

def generate_repo_gif(output_path="docs/preview.gif"):
    # Settings
    width, height = 800, 450
    bg_color = (13, 17, 23)  # GitHub Dark Theme
    text_color = (57, 255, 20) # Matrix Green
    font_size = 18
    
    # The structure we want to "type out"
    lines = [
        "> Initializing Nvidia-CLI v7.0...",
        "> Scanning Agentic Framework...",
        "├── nv_cli/          # Agent Orchestration",
        "├── nv_pkg/          # Skills & Memory",
        "├── nv.py            # CLI Entry Point",
        "├── nv_v6.py         # Legacy Core",
        "└── pyproject.toml   # Dependencies",
        "",
        "> Status: Soul/Identity System Active."
    ]

    frames = []
    # Create "typing" effect by adding one line at a time
    for i in range(len(lines) + 1):
        img = Image.new('RGB', (width, height), color=bg_color)
        d = ImageDraw.Draw(img)
        
        # You may need to point this to a valid .ttf on your Mac
        # Defaulting to a basic font if not found
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New.ttf", font_size)
        except:
            font = ImageFont.load_default()

        for j, line in enumerate(lines[:i]):
            d.text((40, 40 + (j * 30)), line, fill=text_color, font=font)
        
        # Add a "cursor" to the last line
        if i < len(lines):
            cursor_x = 40 + d.textlength(lines[i-1], font=font) if i > 0 else 40
            d.rectangle([cursor_x, 40 + ((i-1) * 30), cursor_x + 10, 60 + ((i-1) * 30)], fill=text_color)

        # Duplicate frames to slow down the "reading" of the final state
        repeat = 20 if i == len(lines) else 5
        for _ in range(repeat):
            frames.append(img)

    frames[0].save(output_path, save_all=True, append_images=frames[1:], optimize=False, duration=100, loop=0)
    print(f"GIF saved to {output_path}")

if __name__ == "__main__":
    generate_repo_gif()