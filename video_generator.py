import os
import shutil
import subprocess
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
HF_TOKEN          = os.getenv("HF_TOKEN", "")

WIDTH, HEIGHT = 1280, 720

MOOD_ACCENTS = {
    "tense"       : "#e94560",
    "uplifting"   : "#f5a623",
    "melancholic" : "#8e9eab",
    "energetic"   : "#ffd700",
    "calm"        : "#48cae4",
    "dramatic"    : "#ff0000",
    "hopeful"     : "#95d5b2",
    "reflective"  : "#a8dadc",
}
DEFAULT_ACCENT = "#ffffff"

MOOD_FALLBACK_BG = {
    "tense"       : ("#1a1a2e", "#e94560"),
    "uplifting"   : ("#0f3460", "#f5a623"),
    "melancholic" : ("#2c3e50", "#8e9eab"),
    "energetic"   : ("#ff4500", "#ffd700"),
    "calm"        : ("#1a3a4a", "#48cae4"),
    "dramatic"    : ("#0d0d0d", "#ff0000"),
    "hopeful"     : ("#1b4332", "#95d5b2"),
    "reflective"  : ("#2d3561", "#a8dadc"),
}


def _find_ffmpeg():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return r"C:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"


FFMPEG_PATH = _find_ffmpeg()


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _build_prompt(shot_description: str, mood: str) -> str:
    return (
        f"{shot_description}. "
        f"Cinematic film still, {mood} mood, dramatic lighting, "
        "professional cinematography, photorealistic, high detail, 16:9"
    )


def _stability_generate(prompt: str):
    """
    Stability AI stable-image/generate/core.
    Returns (Image | None, error_str).
    """
    if not STABILITY_API_KEY:
        return None, "no key"
    try:
        resp = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"authorization": f"Bearer {STABILITY_API_KEY}", "accept": "image/*"},
            files={"none": b""},
            data={"prompt": prompt, "output_format": "png", "aspect_ratio": "16:9"},
            timeout=60,
        )
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGB"), ""
        return None, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        return None, str(exc)


def _huggingface_generate(prompt: str):
    """
    Hugging Face Inference API — SDXL (free with a free HF account token).
    Returns (Image | None, error_str).
    """
    if not HF_TOKEN:
        return None, "no key"
    try:
        resp = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt},
            timeout=120,
        )
        if resp.status_code == 200 and len(resp.content) > 5000:
            return Image.open(BytesIO(resp.content)).convert("RGB"), ""
        return None, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        return None, str(exc)


def _generate_ai_image(shot_description: str, mood: str, scene_number: int = 0):
    """
    Try Stability AI first, then Together AI (free FLUX).
    Returns (PIL Image | None, provider_name).
    """
    prompt = _build_prompt(shot_description, mood)

    img, err = _stability_generate(prompt)
    if img is not None:
        return img, "Stability AI"
    if err != "no key":
        print(f"[Stability AI] scene {scene_number}: {err}")

    img, err = _huggingface_generate(prompt)
    if img is not None:
        return img, "HuggingFace SDXL"
    if err != "no key":
        print(f"[HuggingFace] scene {scene_number}: {err}")

    return None, "fallback"


def _fallback_image(mood: str) -> Image.Image:
    bg_hex, _ = MOOD_FALLBACK_BG.get(mood, ("#1a1a2e", "#ffffff"))
    bg_rgb = hex_to_rgb(bg_hex)
    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg_rgb)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        factor = 1 - (y / HEIGHT) * 0.35
        draw.line(
            [(0, y), (WIDTH, y)],
            fill=(int(bg_rgb[0] * factor), int(bg_rgb[1] * factor), int(bg_rgb[2] * factor)),
        )
    return img


def _load_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 52),
            ImageFont.truetype("arial.ttf", 32),
            ImageFont.truetype("arial.ttf", 22),
        )
    except Exception:
        d = ImageFont.load_default()
        return d, d, d


def create_scene_image(scene: dict, output_path: str) -> str:
    """
    Renders a 1280×720 PNG for one scene.
    Returns the provider name used ('Stability AI', 'Together AI (FLUX)', 'fallback').
    """
    mood      = scene.get("mood", "").lower()
    shot_desc = scene.get("shot_description") or scene.get("shot", "")
    scene_num = scene.get("scene_number") or scene.get("scene", 0)

    base_img, provider = _generate_ai_image(shot_desc, mood, scene_num)
    if base_img is None:
        base_img = _fallback_image(mood)
        provider = "fallback"

    img = base_img.resize((WIDTH, HEIGHT), Image.LANCZOS)

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    ov.rectangle([(0, 0), (WIDTH, 75)], fill=(0, 0, 0, 140))
    ov.rectangle([(0, HEIGHT - 190), (WIDTH, HEIGHT)], fill=(0, 0, 0, 175))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_large, font_medium, font_small = _load_fonts()
    accent_rgb = hex_to_rgb(MOOD_ACCENTS.get(mood, DEFAULT_ACCENT))
    white      = (255, 255, 255)
    light_gray = (210, 210, 210)

    draw.text((55, 22), f"SCENE {scene_num}", font=font_small, fill=accent_rgb)
    draw.text((WIDTH - 220, 22), f"[ {mood.upper()} ]", font=font_small, fill=accent_rgb)

    caption = (scene.get("caption") or "").upper()
    bbox = draw.textbbox((0, 0), caption, font=font_large)
    caption_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - caption_w) // 2, HEIGHT - 145), caption, font=font_large, fill=white)

    duration = scene.get("duration_seconds") or scene.get("duration", 4)
    draw.text((WIDTH - 95, HEIGHT - 48), f"{duration}s", font=font_small, fill=light_gray)
    draw.rectangle([(55, HEIGHT - 52), (WIDTH - 55, HEIGHT - 47)], fill=accent_rgb)

    img.save(output_path)
    return provider


def generate_video(scenes: list, output_path: str = "velora_output.mp4") -> str:
    """Generate one AI image per scene and stitch into an MP4 with FFmpeg."""
    os.makedirs("temp_frames", exist_ok=True)
    frame_list_path = "temp_frames/frames.txt"
    providers = []

    with open(frame_list_path, "w") as f:
        for scene in scenes:
            num      = scene.get("scene_number") or scene.get("scene", 0)
            img_path = f"temp_frames/scene_{num}.png"
            provider = create_scene_image(scene, img_path)
            providers.append(f"Scene {num}: {provider}")
            duration = scene.get("duration_seconds") or scene.get("duration", 4)
            f.write(f"file '{os.path.abspath(img_path)}'\n")
            f.write(f"duration {duration}\n")

        last     = scenes[-1]
        last_num = last.get("scene_number") or last.get("scene", 0)
        f.write(f"file '{os.path.abspath(f'temp_frames/scene_{last_num}.png')}'\n")

    print("[video_generator] Provider summary:\n  " + "\n  ".join(providers))

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", frame_list_path,
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264", "-r", "24",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")

    return output_path
