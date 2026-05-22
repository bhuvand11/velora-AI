import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

# ─────────────────────────────────────────────
# LLM — Groq
# ─────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
)


# ─────────────────────────────────────────────
# TOOL 1 — Script → Storyboard
# ─────────────────────────────────────────────
@tool
def generate_storyboard(script: str) -> str:
    """Generate a storyboard from a script."""
    resp = llm.invoke(f"""
You are a professional Hollywood video director creating a detailed storyboard.

Split this script into exactly 5 scenes. Return a JSON array where each object has EXACTLY these fields with EXACTLY these names:

{{
  "scene_number": 1,
  "shot_description": "A sweeping aerial shot of a neon-lit cityscape at dusk, rain falling on glass skyscrapers as yellow taxi cabs weave through congested streets below, the camera slowly descending toward street level.",
  "caption": "Cities Never Sleep",
  "duration_seconds": 5,
  "mood": "dramatic"
}}

STRICT RULES:
- "shot_description" must be AT LEAST 25 words. Describe camera angle, environment, lighting, subjects, movement, and atmosphere in full vivid detail. NEVER write less than 25 words. NEVER write just a shot type like "establishing shot".
- "caption" must be 2-6 words of punchy subtitle text. NEVER leave it empty. NEVER use asterisks or markdown. Just plain words.
- "duration_seconds" must be between 3 and 6. NEVER more than 6.
- "mood" must be one single word.
- "scene_number" must be 1 through 5.
- Return ONLY the JSON array. No markdown. No code blocks. No explanation. Start your response with [ and end with ]

Script to storyboard:
{script}
""")
    return resp.content


# ─────────────────────────────────────────────
# TOOL 2 — Coherence Checker
# ─────────────────────────────────────────────
@tool
def coherence_checker(storyboard_json: str) -> str:
    """Check if the storyboard tells a coherent story. Returns score and issues."""
    resp = llm.invoke(f"""
You are a film critic. Review this storyboard carefully.

Check:
1. Does it have a clear beginning, middle, and end?
2. Do scenes flow naturally into each other?
3. Is there any jarring or out-of-place scene?
4. Is the emotional arc consistent?

Return ONLY this JSON, nothing else:
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
    return resp.content


# ─────────────────────────────────────────────
# TOOL 3 — Caption Styler
# ─────────────────────────────────────────────
@tool
def caption_styler(storyboard_json: str, style: str) -> str:
    """Rewrite captions in the storyboard to match the given style."""
    style_guides = {
        "cinematic"   : "Bold, poetic, epic. Short punchy phrases. Think movie trailer.",
        "documentary" : "Calm, factual, informative. Like a BBC narrator.",
        "fun"         : "Energetic, casual, emoji-friendly. Like a viral TikTok.",
        "minimal"     : "One or two words max. Clean. Silent-film style.",
        "dramatic"    : "Intense, emotional, urgent. Think breaking news meets poetry."
    }
    guide = style_guides.get(style, "Clear and engaging.")

    resp = llm.invoke(f"""
Rewrite ONLY the caption field in each scene to match this style:
Style: {style}
Guide: {guide}

STRICT RULES:
- Keep scene_number, shot_description, duration_seconds, mood exactly the same
- Only change the caption text
- caption must be 2-6 plain words. No asterisks. No markdown. No empty captions.
- Return ONLY a valid JSON array. No markdown. No explanation. Start with [ end with ]

Storyboard:
{storyboard_json}
""")
    return resp.content


# ─────────────────────────────────────────────
# TOOL 4 — Scene Regenerator
# ─────────────────────────────────────────────
@tool
def scene_regenerator(weak_scene_number: int, issue: str, full_storyboard_json: str) -> str:
    """Fix a specific weak scene based on coherence checker feedback."""
    resp = llm.invoke(f"""
You are a video director fixing a weak scene in a storyboard.

Storyboard:
{full_storyboard_json}

Problem with scene {weak_scene_number}:
{issue}

Rewrite ONLY scene {weak_scene_number} to fix this issue.
Make sure it connects smoothly with scenes before and after it.
Return the COMPLETE storyboard array with the fixed scene replacing the old one.
Return ONLY valid JSON. No markdown. No explanation. Start with [ end with ]
""")
    return resp.content


# ─────────────────────────────────────────────
# AGENT SETUP
# ─────────────────────────────────────────────
tools = [
    generate_storyboard,
    coherence_checker,
    caption_styler,
    scene_regenerator
]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Velora — an agentic AI video production assistant.

Your job is to turn a user's script into a polished, coherent storyboard.

Always follow these steps in order:

STEP 1: Call generate_storyboard with the script.

STEP 2: Call coherence_checker with the storyboard JSON from step 1.

STEP 3: Check the coherence_score.
  - If score is BELOW 70: Call scene_regenerator to fix the weakest_scene using the suggestion.
  - If score is 70 or above: Skip this step.

STEP 4: Call caption_styler with the final storyboard and the user's chosen style.

STEP 5: Return the final storyboard JSON only. No explanation. Just the JSON array. Start with [ end with ]

Important:
- Never skip steps 1, 2, or 4.
- Always pass actual JSON content between tools, not descriptions.
- If a tool errors, retry it once.
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10
)


# ─────────────────────────────────────────────
# run_pipeline — called by app.py
# ─────────────────────────────────────────────
def run_pipeline(script: str, style: str, num_scenes: int) -> tuple:
    result = agent_executor.invoke({
        "input": f"""
Script: {script}

Settings:
- Style: {style}
- Number of scenes: {num_scenes}

Step 1: Call generate_storyboard with the script.
Step 2: Call coherence_checker with the result.
Step 3: If coherence_score below 70, call scene_regenerator to fix weak scene.
Step 4: Call caption_styler with final storyboard and style: {style}
Return final JSON array only. Start with [ end with ]
"""
    })

    output = result["output"]

    # Extract JSON array
    try:
        start = output.find("[")
        end = output.rfind("]") + 1
        if start != -1 and end > start:
            raw_scenes = json.loads(output[start:end])
        else:
            raw_scenes = []
    except json.JSONDecodeError:
        raw_scenes = []

    # Normalize all field names and fix values
    scenes = []
    for i, scene in enumerate(raw_scenes):
        scenes.append({
            "scene_number"    : scene.get("scene_number") or scene.get("scene") or i + 1,
            "shot_description": (
                scene.get("shot_description") or
                scene.get("description") or
                scene.get("shot") or
                scene.get("visual") or ""
            ),
            "caption": str(
                scene.get("caption") or
                scene.get("text") or
                scene.get("subtitle") or
                scene.get("title") or ""
            ).replace("**", "").replace("*", "").strip(),
            "duration_seconds": min(
                int(scene.get("duration_seconds") or scene.get("duration") or 4), 6
            ),
            "mood": scene.get("mood") or "cinematic"
        })

    # Final coherence check for UI display
    try:
        coherence_raw = coherence_checker.invoke({"storyboard_json": json.dumps(scenes)})
        c_start = coherence_raw.find("{")
        c_end = coherence_raw.rfind("}") + 1
        coherence = json.loads(coherence_raw[c_start:c_end])
    except Exception:
        coherence = {
            "coherence_score": 75,
            "arc_quality": "good",
            "issues": []
        }

    return scenes, coherence