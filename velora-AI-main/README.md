# 🎬 Velora AI — Agentic Video Production Pipeline

> **From script to storyboard to video — fully autonomous, zero manual steps.**

Velora is an end-to-end agentic AI video production pipeline that takes a raw text script and autonomously generates a coherent storyboard, styled captions, and a downloadable MP4 video. Built on LangChain, Groq, Streamlit, and FFmpeg.

---

## 📋 Table of Contents

- [What is Velora?](#what-is-velora)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Using Velora](#using-velora)
- [Agent Pipeline Deep Dive](#agent-pipeline-deep-dive)
- [Observability with LangSmith](#observability-with-langsmith)
- [Video Generation](#video-generation)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## What is Velora?

Velora is not a template tool or a simple API wrapper. It is a **fully autonomous agentic pipeline** — powered by LangChain — that reasons about your script, plans a production sequence, calls specialised tools in the right order, evaluates its own output, and self-corrects before delivering results.

The core innovation is **Narrative Coherence Intelligence** — a dedicated agent tool that reviews the entire storyboard as a film critic would, scores it from 0 to 100, identifies the weakest scene, and triggers automatic regeneration if quality falls below threshold. No existing consumer video tool does this.

---

## Key Features

- **Script to Storyboard** — paste any script, get vivid scene-by-scene breakdowns instantly
- **Coherence Checking** — agent scores narrative arc and auto-fixes weak scenes
- **Caption Styling** — captions rewritten to match your chosen style (cinematic, documentary, fun, minimal, dramatic)
- **MP4 Export** — mood-colored video frames stitched into a downloadable video
- **User Controls** — choose style, number of scenes, tone
- **Full Observability** — every agent decision traced on LangSmith in real time
- **JSON Export** — structured storyboard data for downstream integrations

---

## How It Works

```
User pastes script + selects style
            ↓
    LangChain Agent starts
            ↓
┌─────────────────────────────────┐
│  STEP 1: generate_storyboard    │  → Breaks script into N scenes
│  STEP 2: coherence_checker      │  → Scores narrative arc 0–100
│  STEP 3: scene_regenerator      │  → Fixes weak scene if score < 70
│  STEP 4: caption_styler         │  → Rewrites captions to match style
└─────────────────────────────────┘
            ↓
   Storyboard displayed in UI
            ↓
   User clicks Export MP4
            ↓
   FFmpeg renders downloadable video
```

The agent decides the order and logic of tool calls autonomously — no hardcoded sequence.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq — LLaMA 3.3 70B Versatile |
| Agent Framework | LangChain 0.3.7 |
| UI | Streamlit |
| Video Rendering | FFmpeg + Pillow |
| Observability | LangSmith |
| Environment | Python 3.11+ |

---

## Project Structure

```
velora-AI/
├── agent.py              ← LangChain agent + all 4 tools + run_pipeline()
├── app.py                ← Streamlit UI
├── video_generator.py    ← FFmpeg video rendering pipeline
├── .env                  ← API keys (never commit this)
├── .gitignore            ← Ensures .env is never committed
├── requirements.txt      ← Python dependencies
├── temp_frames/          ← Auto-created during video generation
└── velora_output.mp4     ← Auto-created video output
```

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.11+** installed — check with `python --version`
- **FFmpeg** installed on your system
- **Git** installed
- API keys for **Groq** and **LangSmith** (both free)

### Installing FFmpeg (Windows)

1. Go to `https://github.com/BtbN/FFmpeg-Builds/releases`
2. Download `ffmpeg-master-latest-win64-gpl-shared.zip`
3. Extract it — you'll find a `bin` folder inside
4. Copy the full path to that `bin` folder (e.g. `C:\ffmpeg-master-latest-win64-gpl-shared\bin`)
5. Open Windows search → "Environment Variables" → Edit System Variables → Path → New → paste the path → OK
6. Verify: open a new terminal and run `ffmpeg -version`

### Installing FFmpeg (Mac)

```bash
brew install ffmpeg
```

### Installing FFmpeg (Linux)

```bash
sudo apt install ffmpeg
```

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/velora-AI.git
cd velora-AI
```

### Step 2 — Create a virtual environment

```bash
python -m venv velora-env
```

Activate it:

```bash
# Windows
velora-env\Scripts\activate

# Mac / Linux
source velora-env/bin/activate
```

You'll see `(velora-env)` appear at the start of your terminal line. Always make sure this is active before running anything.

### Step 3 — Install dependencies

```bash
pip install langchain==0.3.7 langchain-openai==0.2.9 langchain-groq==0.2.1 langsmith==0.1.147 streamlit python-dotenv Pillow
```

---

## Configuration

### Step 1 — Get your API keys

**Groq API Key (free):**
1. Go to `console.groq.com`
2. Sign up with Google
3. Click API Keys → Create API Key
4. Copy the key

**LangSmith API Key (free):**
1. Go to `smith.langchain.com`
2. Sign in with Google
3. Click Projects → New Project → name it `velora`
4. Click Settings → API Keys → Create API Key
5. Copy the key

### Step 2 — Create your `.env` file

Create a file called `.env` in the root of your project and paste this:

```
# Groq
GROQ_API_KEY=paste-your-groq-key-here

# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=paste-your-langsmith-key-here
LANGSMITH_PROJECT=velora
```

> ⚠️ **Never commit your `.env` file to GitHub.** Make sure `.env` is listed in your `.gitignore`.

### Step 3 — Update FFmpeg path in `video_generator.py`

Open `video_generator.py` and update this line at the top with your actual FFmpeg path:

```python
FFMPEG_PATH = r"C:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
```

To find your exact path, run `where ffmpeg` in terminal (Windows) or `which ffmpeg` (Mac/Linux).

---

## Running the App

Make sure your virtual environment is active, then:

```bash
streamlit run app.py
```

Your browser will automatically open `http://localhost:8501`. That's your Velora interface.

---

## Using Velora

### Step 1 — Set your controls
In the left sidebar, choose:
- **Visual Style** — cinematic, documentary, fun, minimal, or dramatic
- **Number of Scenes** — anywhere from 3 to 8

### Step 2 — Paste your script
Paste any text script into the main text area. It can be a short-form video script, a speech, a product description, a news article — anything narrative works.

**Example script to try:**
```
Artificial intelligence is no longer a distant dream — it's here, reshaping 
every industry, every profession, every human interaction. From doctors 
diagnosing cancer in seconds to farmers predicting harvests before seeds 
are sown, AI is quietly revolutionizing the world around us. But with great 
power comes great responsibility. Who controls the algorithm? Who bears the 
consequences? As we stand at the crossroads of the greatest technological 
shift in human history, one question echoes louder than all others — 
are we building AI for everyone, or just for the few?
```

### Step 3 — Generate Storyboard
Click **Generate Storyboard**. Watch your terminal — you'll see the agent calling tools in real time.

Generation takes 20-60 seconds depending on script length.

### Step 4 — Review output
Once done you'll see:
- **Coherence Score banner** — narrative quality rating with arc assessment
- **Scene cards** — shot description, caption, mood, and duration for each scene
- **Issues expander** — any weak scenes the agent detected and fixed

### Step 5 — Export
- Click **Download JSON** to get structured storyboard data
- Click **Export as MP4** to generate and download your video

---

## Agent Pipeline Deep Dive

Velora uses a LangChain `create_tool_calling_agent` with four specialised tools:

### Tool 1 — `generate_storyboard`
Takes the raw script and splits it into N scenes. Each scene has a `shot_description` (what the camera sees), `caption` (subtitle text), `duration_seconds`, and `mood`.

### Tool 2 — `coherence_checker`
Reviews the complete storyboard as a film critic. Returns:
- `coherence_score` (0–100)
- `arc_quality` (excellent / good / weak / broken)
- `issues` (list of specific problems)
- `weakest_scene` (scene number)
- `suggestion` (concrete fix recommendation)

### Tool 3 — `scene_regenerator`
Called automatically if `coherence_score` is below 70. Takes the weak scene number, the issue description, and the full storyboard, then rewrites the weak scene to fix the narrative problem and reconnect it with surrounding scenes.

### Tool 4 — `caption_styler`
Rewrites all captions to match the user's chosen style:
- **Cinematic** — bold, poetic, punchy. Think movie trailer.
- **Documentary** — calm, factual, informative. Think BBC narrator.
- **Fun** — energetic, casual. Think viral TikTok.
- **Minimal** — one or two words max. Clean, silent-film style.
- **Dramatic** — intense, emotional, urgent.

### Why this is truly agentic
The agent decides the sequence of tool calls itself based on the results it observes. If coherence is high, it skips scene regeneration. If a tool errors, it retries. This is not a hardcoded pipeline — it is autonomous reasoning.

---

## Observability with LangSmith

Every Velora run is automatically traced on LangSmith. To view traces:

1. Go to `smith.langchain.com`
2. Click Projects → velora
3. Click any run to see the full trace

You'll see every tool call with its exact input, output, latency, and token usage. This is production-grade AI observability built in from day one.

---

## Video Generation

Velora's video generator (`video_generator.py`) works as follows:

1. For each scene, a 1280×720 PNG frame is created using Pillow
2. Each frame has a unique mood-based background color
3. The shot description is rendered center-aligned in the middle
4. The caption is rendered large and bold at the bottom
5. Scene number and mood tag appear in the corners
6. FFmpeg concatenates all frames using the concat demuxer
7. Output is a standard H.264 MP4 at 24fps

Each scene's duration in the video matches the `duration_seconds` the agent assigned — so pacing is AI-driven, not fixed.

---

## Troubleshooting

**`ModuleNotFoundError`**
```bash
pip install <missing module name>
```

**`cannot import name 'create_tool_calling_agent'`**
Your LangChain version is wrong. Run:
```bash
pip install langchain==0.3.7
```

**`temperature` error from LLM**
Some models don't support custom temperature. Set it explicitly to `1` in the LLM config or remove it entirely.

**`Too many requests` / rate limit error**
You're hitting the free tier limit. Wait 60 seconds and try again. If persistent, switch to a different model in `agent.py`.

**`[WinError 2] system cannot find the file specified`** during video export
FFmpeg is not found. Run `where ffmpeg` in terminal and hardcode that exact path in `video_generator.py`:
```python
FFMPEG_PATH = r"C:\your\exact\path\to\ffmpeg.exe"
```

**Agent output is empty / scenes not showing**
The LLM occasionally returns inconsistent field names. Hit Generate again — it resolves on retry.

**`.env` accidentally committed to GitHub**
```bash
git rm --cached .env
git commit -m "remove .env from tracking"
git push
```
Then immediately rotate all your API keys — delete old ones and create new ones on Groq and LangSmith.

---

## Roadmap

**Phase 1 — Enhanced Assets**
- AI image generation per scene using Stable Diffusion or DALL-E
- Scene thumbnail previews in the Streamlit UI

**Phase 2 — Audio**
- Voiceover synthesis using ElevenLabs or Azure TTS
- Background music selection based on mood

**Phase 3 — Full Video**
- Animated transitions between scenes
- Text animation effects on captions
- Real footage integration via stock video APIs

**Phase 4 — Platform**
- User accounts and project history
- Collaboration features
- API access for third-party integrations
- Mobile-responsive interface

---

---

*"We didn't build a video tool. We built an agent that thinks like a director."*
