import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception

load_dotenv()

# ─────────────────────────────────────────────
# LLM — Groq
# ─────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    max_retries=0,
)


def _is_rate_limit(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate_limit_exceeded" in msg or "rate limit" in msg


@retry(
    retry=retry_if_exception(_is_rate_limit),
    wait=wait_fixed(20),
    stop=stop_after_attempt(6),
    reraise=True,
)
def _invoke(prompt: str) -> str:
    """Call the LLM and return the text content, auto-retrying on rate-limit errors."""
    return llm.invoke(prompt).content


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _extract_json_array(text: str) -> list:
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return []


def _extract_json_object(text: str) -> dict:
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _normalize_scenes(raw_scenes: list) -> list:
    scenes = []
    for i, scene in enumerate(raw_scenes):
        raw_dur = scene.get("duration_seconds") or scene.get("duration") or 4
        try:
            duration = min(int(float(str(raw_dur))), 6)
        except (ValueError, TypeError):
            duration = 4

        scenes.append({
            "scene_number": scene.get("scene_number") or scene.get("scene") or i + 1,
            "shot_description": (
                scene.get("shot_description") or
                scene.get("description") or
                scene.get("shot") or
                scene.get("visual") or ""
            ).replace("**", "").replace("*", "").strip(),
            "caption": str(
                scene.get("caption") or
                scene.get("text") or
                scene.get("subtitle") or
                scene.get("title") or ""
            ).replace("**", "").replace("*", "").strip(),
            "duration_seconds": duration,
            "mood": str(scene.get("mood") or "cinematic").lower().strip(),
        })
    return scenes


# ─────────────────────────────────────────────
# STEP 1 — Script → Storyboard
# ─────────────────────────────────────────────
def generate_storyboard(script: str, num_scenes: int = 5) -> str:
    return _invoke(f"""
You are a professional Hollywood video director creating a richly detailed storyboard.

Split this script into exactly {num_scenes} scenes. Return a JSON array where each object has EXACTLY these fields:

{{
  "scene_number": 1,
  "shot_description": "A slow aerial drone descends over a frost-covered mountain valley at pre-dawn, jagged peaks cutting through violet clouds as faint firelight spills from stone-house windows below. A lone shepherd steps outside, her breath visible in the freezing air, gazing upward as pale dawn light bleeds across the horizon.",
  "caption": "Where Mountains Breathe",
  "duration_seconds": 5,
  "mood": "epic"
}}

RULES FOR shot_description (MOST IMPORTANT):
- Write 2-3 sentences, approximately 35-50 words.
- Cover: camera angle/movement, environment/setting, lighting, subjects/action, mood.
- NEVER write a single short sentence or just a shot type name. No asterisks or markdown.

OTHER RULES:
- caption: 2-6 plain words, no asterisks or markdown.
- duration_seconds: integer between 3 and 6.
- mood: exactly one lowercase word.
- scene_number: 1 through {num_scenes}.
- Return ONLY the JSON array. No markdown, no code fences. Start with [ and end with ]

Script:
{script}
""")


# ─────────────────────────────────────────────
# STEP 2 — Coherence Check
# ─────────────────────────────────────────────
def check_coherence(storyboard_json: str) -> dict:
    raw = _invoke(f"""
You are a film critic. Review this storyboard.

Check: clear beginning/middle/end, natural scene flow, consistent emotional arc, any jarring scenes.

Return ONLY this JSON object, nothing else:
{{
  "coherence_score": 85,
  "arc_quality": "good",
  "issues": ["example issue"],
  "strongest_scene": 1,
  "weakest_scene": 3,
  "suggestion": "one concrete sentence on how to improve"
}}

Storyboard:
{storyboard_json}
""")
    result = _extract_json_object(raw)
    result.setdefault("coherence_score", 75)
    result.setdefault("arc_quality", "good")
    result.setdefault("issues", [])
    result.setdefault("suggestion", "")
    result.setdefault("weakest_scene", 1)
    return result


# ─────────────────────────────────────────────
# STEP 3 — Scene Regenerator (only if score < 70)
# ─────────────────────────────────────────────
def fix_weak_scene(weak_scene_number: int, issue: str, storyboard_json: str) -> str:
    return _invoke(f"""
You are a video director fixing a weak scene in a storyboard.

Storyboard:
{storyboard_json}

Problem with scene {weak_scene_number}: {issue}

Rewrite ONLY scene {weak_scene_number} to fix this issue and connect smoothly with surrounding scenes.
The shot_description must be 2-3 sentences (35-50 words) covering camera angle, environment, lighting, and mood.

Return the COMPLETE storyboard array with the fixed scene replacing the old one.
Return ONLY valid JSON. No markdown. Start with [ end with ]
""")


# ─────────────────────────────────────────────
# STEP 4 — Caption Styler
# ─────────────────────────────────────────────
def style_captions(storyboard_json: str, style: str) -> str:
    style_guides = {
        "cinematic"  : "Bold, poetic, epic. Short punchy phrases. Think movie trailer.",
        "documentary": "Calm, factual, informative. Like a BBC narrator.",
        "fun"        : "Energetic, casual, emoji-friendly. Like a viral TikTok.",
        "minimal"    : "One or two words max. Clean. Silent-film style.",
        "dramatic"   : "Intense, emotional, urgent. Think breaking news meets poetry.",
    }
    guide = style_guides.get(style, "Clear and engaging.")

    return _invoke(f"""
Rewrite ONLY the caption field in each scene to match this style:
Style: {style}
Guide: {guide}

RULES:
- Keep scene_number, shot_description, duration_seconds, mood exactly the same.
- Only change the caption text.
- caption must be 2-6 plain words. No asterisks, no markdown, no empty captions.
- Return ONLY a valid JSON array. No markdown. Start with [ end with ]

Storyboard:
{storyboard_json}
""")


# ─────────────────────────────────────────────
# run_pipeline — called by app.py
# ─────────────────────────────────────────────
def run_pipeline(script: str, style: str, num_scenes: int) -> tuple:
    # Step 1: Generate storyboard
    raw1 = generate_storyboard(script, num_scenes)
    scenes1 = _normalize_scenes(_extract_json_array(raw1))

    # Step 2: Coherence check
    coherence = check_coherence(json.dumps(scenes1))

    # Step 3: Fix weakest scene if score is low
    if coherence.get("coherence_score", 100) < 70:
        weak_num = coherence.get("weakest_scene", 1)
        suggestion = coherence.get("suggestion", "Improve narrative flow.")
        raw1 = fix_weak_scene(weak_num, suggestion, json.dumps(scenes1))
        scenes1 = _normalize_scenes(_extract_json_array(raw1))

    # Step 4: Style captions
    raw4 = style_captions(json.dumps(scenes1), style)
    scenes_final = _normalize_scenes(_extract_json_array(raw4))

    # Fall back to pre-styling scenes if styling broke the JSON
    if not scenes_final:
        scenes_final = scenes1

    # Final coherence check for UI display
    try:
        coherence = check_coherence(json.dumps(scenes_final))
    except Exception:
        pass  # keep the coherence result from step 2

    return scenes_final, coherence
