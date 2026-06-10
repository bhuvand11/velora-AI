import os
import subprocess
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

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
    "tense"      : ("#1a1a2e", "#e94560"),
    "uplifting"  : ("#0f3460", "#f5a623"),
    "melancholic": ("#2c3e50", "#8e9eab"),
    "energetic"  : ("#3d0000", "#ff4500"),
    "calm"       : ("#1a3a4a", "#48cae4"),
    "dramatic"   : ("#0d0d0d", "#ff0000"),
    "hopeful"    : ("#1b4332", "#95d5b2"),
    "reflective" : ("#2d3561", "#a8dadc"),
    "inspiring"  : ("#1a0533", "#c77dff"),
    "intense"    : ("#1a0000", "#ff6b6b"),
    "serious"    : ("#0a0a0a", "#aaaaaa"),
    "somber"     : ("#0d1117", "#6e7681"),
    "neutral"    : ("#1a1a1a", "#ffffff"),
    "cinematic"  : ("#0d1b2a", "#00b4d8"),
    "determined" : ("#0a0a2a", "#4361ee"),
    "focused"    : ("#0a1628", "#4895ef"),
    "epic"       : ("#0a0f1e", "#e8c84a"),
    "mysterious" : ("#0f0a1a", "#a56cc1"),
    "romantic"   : ("#1a0a12", "#ff6b9d"),
    "suspenseful": ("#0d0d0d", "#ff8800"),
    "serene"     : ("#0a1a2a", "#90e0ef"),
    "peaceful"   : ("#0a1a10", "#74c69d"),
}

WIDTH, HEIGHT = 1280, 720
FPS = 24


def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def clean_text(text: str) -> str:
    return str(text).replace("**", "").replace("*", "").replace("__", "").replace("`", "").strip()


def wrap_text(text: str, max_chars: int = 68) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _load_fonts():
    sizes = {"label": 22, "desc": 21, "caption": 52}
    fonts = {}
    for name, size in sizes.items():
        try:
            face = "arialbd.ttf" if name == "caption" else "arial.ttf"
            fonts[name] = ImageFont.truetype(face, size)
        except Exception:
            fonts[name] = ImageFont.load_default()
    return fonts


def create_scene_image(scene: dict) -> np.ndarray:
    scene_num = int(scene.get("scene_number") or 1)
    mood      = str(scene.get("mood") or "").lower().strip()

    if scene_num in SCENE_COLORS:
        bg_hex, accent_hex = SCENE_COLORS[scene_num]
    elif mood in MOOD_COLORS:
        bg_hex, accent_hex = MOOD_COLORS[mood]
    else:
        bg_hex, accent_hex = ("#0d1b2a", "#00b4d8")

    bg_rgb     = hex_to_rgb(bg_hex)
    accent_rgb = hex_to_rgb(accent_hex)

    img  = Image.new("RGB", (WIDTH, HEIGHT), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = max(0, int(bg_rgb[0] * (1 - t * 0.45)))
        g = max(0, int(bg_rgb[1] * (1 - t * 0.45)))
        b = max(0, int(bg_rgb[2] * (1 - t * 0.45)))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Accent borders
    draw.rectangle([(0, 0),          (WIDTH, 5)],      fill=accent_rgb)
    draw.rectangle([(0, HEIGHT - 5), (WIDTH, HEIGHT)], fill=accent_rgb)
    draw.rectangle([(0, 0),          (4, HEIGHT)],     fill=accent_rgb)

    fonts = _load_fonts()

    # Header
    draw.text((40, 20), f"SCENE  {scene_num:02d}", font=fonts["label"], fill=accent_rgb)
    mood_text = f"[ {mood.upper()} ]"
    mw = draw.textbbox((0, 0), mood_text, font=fonts["label"])[2]
    draw.text((WIDTH - mw - 40, 20), mood_text, font=fonts["label"], fill=accent_rgb)
    draw.line([(40, 56), (WIDTH - 40, 56)], fill=(*accent_rgb,), width=1)

    # Shot description (medium length — up to 7 lines)
    DESC_TOP    = 68
    CAPTION_TOP = 590
    LINE_H      = 30

    shot  = clean_text(scene.get("shot_description") or "")
    lines = wrap_text(shot, max_chars=72)
    MAX_LINES    = min(7, (CAPTION_TOP - DESC_TOP) // LINE_H)
    visible      = lines[:MAX_LINES]
    total_h      = len(visible) * LINE_H
    y0           = DESC_TOP + max(0, (CAPTION_TOP - DESC_TOP - total_h) // 2)

    for j, line in enumerate(visible):
        color = (160, 160, 160) if (j == len(visible) - 1 and len(lines) > MAX_LINES) else (210, 210, 210)
        lw = draw.textbbox((0, 0), line, font=fonts["desc"])[2]
        draw.text(((WIDTH - lw) // 2, y0 + j * LINE_H), line, font=fonts["desc"], fill=color)

    # Caption
    caption = clean_text(scene.get("caption") or "").upper()
    if caption:
        draw.rectangle([(0, CAPTION_TOP - 6), (WIDTH, HEIGHT - 6)], fill=(*bg_rgb,))
        cw, ch = draw.textbbox((0, 0), caption, font=fonts["caption"])[2:4]
        cx = (WIDTH - cw) // 2
        cy = CAPTION_TOP + ((HEIGHT - 6 - CAPTION_TOP - ch) // 2)
        draw.text((cx + 2, cy + 2), caption, font=fonts["caption"], fill=(0, 0, 0))
        draw.text((cx, cy),         caption, font=fonts["caption"], fill=(255, 255, 255))

    return np.array(img)


def generate_video(scenes: list, output_path: str = "velora_output.mp4") -> str:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    _write_with_ffmpeg(scenes, output_path, ffmpeg_exe)
    return output_path


def _write_with_ffmpeg(scenes: list, output_path: str, ffmpeg_exe: str):
    os.makedirs("temp_frames", exist_ok=True)
    frame_list = os.path.abspath("temp_frames/frames.txt")

    with open(frame_list, "w") as f:
        for scene in scenes:
            num = scene.get("scene_number", 1)
            img_path = os.path.abspath(f"temp_frames/scene_{num}.png")
            Image.fromarray(create_scene_image(scene)).save(img_path)
            raw_dur = scene.get("duration_seconds") or 4
            try:
                dur = min(int(float(str(raw_dur))), 6)
            except (ValueError, TypeError):
                dur = 4
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {dur}\n")
        # last file without duration (FFmpeg concat requirement)
        last = scenes[-1]
        last_path = os.path.abspath(f"temp_frames/scene_{last.get('scene_number', 1)}.png")
        f.write(f"file '{last_path}'\n")

    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0", "-i", frame_list,
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-r", str(FPS),
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-2000:]}")


