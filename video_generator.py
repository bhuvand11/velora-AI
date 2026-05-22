import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

FFMPEG_PATH = r"C:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

SCENE_COLORS = {
    1: ("#0d1b2a", "#00b4d8"),
    2: ("#1a0a0a", "#e63946"),
    3: ("#0a1a0a", "#52b788"),
    4: ("#1a1a0a", "#f4a261"),
    5: ("#0a0a1a", "#9b5de5"),
    6: ("#1a0a1a", "#f15bb5"),
    7: ("#0a1a1a", "#00f5d4"),
    8: ("#1a1209", "#ffd166"),
}

MOOD_COLORS = {
    "tense"          : ("#1a1a2e", "#e94560"),
    "uplifting"      : ("#0f3460", "#f5a623"),
    "melancholic"    : ("#2c3e50", "#8e9eab"),
    "energetic"      : ("#3d0000", "#ff4500"),
    "calm"           : ("#1a3a4a", "#48cae4"),
    "dramatic"       : ("#0d0d0d", "#ff0000"),
    "hopeful"        : ("#1b4332", "#95d5b2"),
    "reflective"     : ("#2d3561", "#a8dadc"),
    "inspiring"      : ("#1a0533", "#c77dff"),
    "intense"        : ("#1a0000", "#ff6b6b"),
    "serious"        : ("#0a0a0a", "#aaaaaa"),
    "somber"         : ("#0d1117", "#6e7681"),
    "neutral"        : ("#1a1a1a", "#ffffff"),
    "cinematic"      : ("#0d1b2a", "#00b4d8"),
    "determined"     : ("#0a0a2a", "#4361ee"),
    "focused"        : ("#0a1628", "#4895ef"),
}

WIDTH, HEIGHT = 1280, 720


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def clean_text(text: str) -> str:
    return str(text).replace("**", "").replace("*", "").replace("__", "").replace("`", "").strip()


def wrap_text(text, max_chars=50):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current + word) < max_chars:
            current += word + " "
        else:
            lines.append(current.strip())
            current = word + " "
    if current:
        lines.append(current.strip())
    return lines


def create_scene_image(scene: dict, output_path: str):
    scene_num = int(scene.get("scene_number") or 1)
    mood = str(scene.get("mood") or "").lower()

    if scene_num in SCENE_COLORS:
        bg_hex, accent_hex = SCENE_COLORS[scene_num]
    elif mood in MOOD_COLORS:
        bg_hex, accent_hex = MOOD_COLORS[mood]
    else:
        bg_hex, accent_hex = ("#0d1b2a", "#00b4d8")

    bg_rgb     = hex_to_rgb(bg_hex)
    accent_rgb = hex_to_rgb(accent_hex)
    white      = (255, 255, 255)
    gray       = (200, 200, 200)

    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    for y in range(HEIGHT):
        alpha = y / HEIGHT
        r = max(0, int(bg_rgb[0] * (1 - alpha * 0.4)))
        g = max(0, int(bg_rgb[1] * (1 - alpha * 0.4)))
        b = max(0, int(bg_rgb[2] * (1 - alpha * 0.4)))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    draw.rectangle([(0, 0), (WIDTH, 6)], fill=accent_rgb)
    draw.rectangle([(0, HEIGHT - 6), (WIDTH, HEIGHT)], fill=accent_rgb)

    try:
        font_small   = ImageFont.truetype("arial.ttf", 22)
        font_medium  = ImageFont.truetype("arial.ttf", 28)
        font_caption = ImageFont.truetype("arialbd.ttf", 54)
    except Exception:
        font_small   = ImageFont.load_default()
        font_medium  = ImageFont.load_default()
        font_caption = ImageFont.load_default()

    # Scene number top left
    draw.text((50, 28), f"SCENE {scene_num}", font=font_small, fill=accent_rgb)

    # Mood top right
    mood_text = f"[ {mood.upper()} ]"
    bbox = draw.textbbox((0, 0), mood_text, font=font_small)
    mood_w = bbox[2] - bbox[0]
    draw.text((WIDTH - mood_w - 50, 28), mood_text, font=font_small, fill=accent_rgb)

    # Shot description — center aligned middle of screen
    shot = clean_text(
        scene.get("shot_description") or
        scene.get("description") or
        scene.get("shot") or ""
    )
    lines = wrap_text(shot, max_chars=50)
    total_h = len(lines[:4]) * 38
    y_start = (HEIGHT // 2) - (total_h // 2) - 30

    for line in lines[:4]:
        bbox = draw.textbbox((0, 0), line, font=font_medium)
        line_w = bbox[2] - bbox[0]
        x = (WIDTH - line_w) // 2
        draw.text((x, y_start), line, font=font_medium, fill=gray)
        y_start += 38

    # Caption bottom center
    caption = clean_text(
        scene.get("caption") or
        scene.get("text") or
        scene.get("subtitle") or ""
    ).upper()

    if caption:
        bbox = draw.textbbox((0, 0), caption, font=font_caption)
        cap_w = bbox[2] - bbox[0]
        x = (WIDTH - cap_w) // 2
        draw.text((x, HEIGHT - 110), caption, font=font_caption, fill=white)

    img.save(output_path)


def generate_video(scenes: list, output_path: str = "velora_output.mp4") -> str:
    os.makedirs("temp_frames", exist_ok=True)
    frame_list_path = "temp_frames/frames.txt"

    with open(frame_list_path, "w") as f:
        for scene in scenes:
            scene_num = scene.get("scene_number") or scene.get("scene", 0)
            img_path = os.path.abspath(f"temp_frames/scene_{scene_num}.png")
            create_scene_image(scene, img_path)
            duration = min(int(scene.get("duration_seconds") or scene.get("duration") or 4), 6)
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {duration}\n")

        last = scenes[-1]
        last_num = last.get("scene_number") or last.get("scene", 0)
        last_path = os.path.abspath(f"temp_frames/scene_{last_num}.png")
        f.write(f"file '{last_path}'\n")

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