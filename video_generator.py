import os
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont
FFMPEG_PATH = r"C:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

# Color palette per mood
MOOD_COLORS = {
    "tense"       : ("#1a1a2e", "#e94560"),
    "uplifting"   : ("#0f3460", "#f5a623"),
    "melancholic" : ("#2c3e50", "#8e9eab"),
    "energetic"   : ("#ff4500", "#ffd700"),
    "calm"        : ("#1a3a4a", "#48cae4"),
    "dramatic"    : ("#0d0d0d", "#ff0000"),
    "hopeful"     : ("#1b4332", "#95d5b2"),
    "reflective"  : ("#2d3561", "#a8dadc"),
}
DEFAULT_COLORS = ("#1a1a2e", "#ffffff")

WIDTH, HEIGHT = 1280, 720


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_scene_image(scene: dict, output_path: str):
    mood = scene.get("mood", "").lower()
    bg_hex, text_hex = MOOD_COLORS.get(mood, DEFAULT_COLORS)

    bg_rgb = hex_to_rgb(bg_hex)
    text_rgb = hex_to_rgb(text_hex)
    white = (255, 255, 255)
    gray = (180, 180, 180)

    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # Gradient overlay (simple horizontal bands)
    for y in range(HEIGHT):
        alpha = y / HEIGHT
        r = int(bg_rgb[0] * (1 - alpha * 0.3))
        g = int(bg_rgb[1] * (1 - alpha * 0.3))
        b = int(bg_rgb[2] * (1 - alpha * 0.3))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Try to load a font, fall back to default
    try:
        font_large  = ImageFont.truetype("arial.ttf", 52)
        font_medium = ImageFont.truetype("arial.ttf", 32)
        font_small  = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_large  = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small  = ImageFont.load_default()

    # Scene number top left
    draw.text((60, 50), f"SCENE {scene.get('scene_number', 1)}", 
              font=font_small, fill=text_rgb)

    # Mood top right
    draw.text((WIDTH - 200, 50), f"[ {mood.upper()} ]", 
              font=font_small, fill=text_rgb)

    # Shot description (wrapped)
    shot = scene.get("shot_description", "")
    words = shot.split()
    lines = []
    current = ""
    for word in words:
        if len(current + word) < 55:
            current += word + " "
        else:
            lines.append(current.strip())
            current = word + " "
    if current:
        lines.append(current.strip())

    y_start = HEIGHT // 2 - 80
    for line in lines[:3]:
        draw.text((60, y_start), line, font=font_medium, fill=gray)
        y_start += 45

    # Caption — big and bold at bottom
    caption = scene.get("caption", "").upper()
    bbox = draw.textbbox((0, 0), caption, font=font_large)
    text_width = bbox[2] - bbox[0]
    x_center = (WIDTH - text_width) // 2
    draw.text((x_center, HEIGHT - 140), caption, font=font_large, fill=white)

    # Bottom accent line
    draw.rectangle([(60, HEIGHT - 60), (WIDTH - 60, HEIGHT - 55)], 
                   fill=text_rgb)

    img.save(output_path)


def generate_video(scenes: list, output_path: str = "velora_output.mp4") -> str:
    """
    Takes storyboard scenes, creates images for each,
    and stitches them into an MP4 using FFmpeg.
    """
    os.makedirs("temp_frames", exist_ok=True)
    frame_list_path = "temp_frames/frames.txt"

    # Generate one image per scene
    with open(frame_list_path, "w") as f:
        for scene in scenes:
            img_path = f"temp_frames/scene_{scene.get('scene_number', 0)}.png"
            create_scene_image(scene, img_path)
            duration = scene.get("duration_seconds", 4)
            # FFmpeg concat format
            f.write(f"file '{os.path.abspath(img_path)}'\n")
            f.write(f"duration {duration}\n")

        # FFmpeg needs last file repeated
        last = scenes[-1]
        last_path = f"temp_frames/scene_{last.get('scene_number', 0)}.png"
        f.write(f"file '{os.path.abspath(last_path)}'\n")

    # Run FFmpeg
    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", frame_list_path,
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-r", "24",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")

    return output_path