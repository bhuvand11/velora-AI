import streamlit as st
import json
from agent import run_pipeline

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Velora AI",
    page_icon="🎬",
    layout="wide"
)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("# 🎬 Velora AI")
st.markdown("##### Script → Storyboard → Captions. Powered by an agentic AI pipeline.")
st.divider()

# ─────────────────────────────────────────────
# Sidebar — user controls
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    st.markdown("Customise your video output below.")

    style = st.selectbox(
        "Visual Style",
        ["cinematic", "documentary", "fun", "minimal", "dramatic"],
        help="Controls the tone and language of your captions"
    )

    num_scenes = st.slider(
        "Number of Scenes",
        min_value=3,
        max_value=8,
        value=5,
        help="How many scenes to split your script into"
    )

    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. Agent splits script into scenes")
    st.markdown("2. Agent checks narrative coherence")
    st.markdown("3. Agent fixes weak scenes automatically")
    st.markdown("4. Agent styles your captions")
    st.markdown("")
    st.caption("Traces visible on smith.langchain.com")

# ─────────────────────────────────────────────
# Main — script input
# ─────────────────────────────────────────────
script = st.text_area(
    "📝 Paste your script here",
    height=220,
    placeholder="""Example: Climate change is reshaping our world at an alarming pace. 
Glaciers are melting, sea levels are rising, and extreme weather events are 
becoming more frequent. But scientists, activists, and communities around 
the world are fighting back with innovation, policy, and sheer determination. 
The question is no longer whether we can act — it's whether we will."""
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate = st.button("🎬 Generate Storyboard", type="primary", use_container_width=True)
with col2:
    clear = st.button("🗑️ Clear", use_container_width=True)

if clear:
    st.session_state.clear()
    st.rerun()

# ─────────────────────────────────────────────
# Pipeline execution
# ─────────────────────────────────────────────
if generate:
    if not script.strip():
        st.warning("Please paste a script first.")
    else:
        with st.spinner("🤖 Velora agent is working... check your terminal to watch it think!"):
            try:
                scenes, coherence = run_pipeline(script, style, num_scenes)
                st.session_state['scenes'] = scenes
                st.session_state['coherence'] = coherence
                st.session_state['style'] = style
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
                st.stop()

# ─────────────────────────────────────────────
# Show results if scenes exist in session
# ─────────────────────────────────────────────
if 'scenes' in st.session_state and st.session_state['scenes']:
    scenes = st.session_state['scenes']
    coherence = st.session_state.get('coherence', {})
    current_style = st.session_state.get('style', style)

    # Coherence report banner
    score = coherence.get("coherence_score", 0)
    arc = coherence.get("arc_quality", "unknown")

    if score >= 80:
        st.success(f"✅ Coherence Score: **{score}/100** — Arc quality: **{arc}**")
    elif score >= 60:
        st.warning(f"⚠️ Coherence Score: **{score}/100** — Arc quality: **{arc}**")
    else:
        st.error(f"❌ Coherence Score: **{score}/100** — Arc quality: **{arc}**")

    if coherence.get("issues"):
        with st.expander("🔍 Coherence issues the agent detected and fixed"):
            for issue in coherence["issues"]:
                st.markdown(f"- {issue}")
            if coherence.get("suggestion"):
                st.info(f"💡 Agent's fix: {coherence['suggestion']}")

    st.divider()

    # Storyboard cards
    st.markdown(f"### 🎞️ Your Storyboard — *{current_style.title()}* style")
    st.caption(f"{len(scenes)} scenes generated")
    st.markdown("")

    cols = st.columns(min(len(scenes), 3))
    for i, scene in enumerate(scenes):
        with cols[i % 3]:
            mood = scene.get("mood", "")
            mood_emoji = {
                "tense": "😰", "uplifting": "🌟", "melancholic": "😔",
                "energetic": "⚡", "calm": "🌊", "dramatic": "🎭",
                "hopeful": "🌅", "intense": "🔥", "reflective": "🪞",
                "inspiring": "💫", "empowering": "💪", "innovative": "🚀",
                "thought-provoking": "🤔"
            }.get(mood, "🎬")

            # Handle both field name versions
            scene_num = scene.get("scene_number") or scene.get("scene", i+1)
            shot_desc = scene.get("shot_description") or scene.get("shot", "")
            caption = scene.get("caption", "").replace("**", "")
            duration = scene.get("duration_seconds") or scene.get("duration", 4)

            st.markdown(f"**Scene {scene_num}** {mood_emoji} *{mood}*")
            st.info(shot_desc if shot_desc else "No description available")
            st.markdown(f"**Caption:** *\"{caption}\"*")
            st.markdown(f"🕐 `{duration}s`")
            st.markdown("")

    # JSON export
    st.divider()
    with st.expander("📦 Export raw storyboard JSON"):
        st.json(scenes)
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(scenes, indent=2),
            file_name="velora_storyboard.json",
            mime="application/json"
        )

    # ─────────────────────────────────────────────
    # Video generation section
    # ─────────────────────────────────────────────
    st.divider()
    st.markdown("### 🎥 Generate Video")
    st.caption("Converts your storyboard into a downloadable MP4 slideshow")

    if st.button("🎬 Export as MP4", type="secondary"):
        from video_generator import create_scene_image, generate_video
        import os

        progress_bar = st.progress(0, text="Starting image generation…")
        status_area = st.empty()
        provider_log = []

        try:
            os.makedirs("temp_frames", exist_ok=True)
            frame_list_path = "temp_frames/frames.txt"
            total = len(scenes)

            with open(frame_list_path, "w") as frame_file:
                for idx, scene in enumerate(scenes):
                    num = scene.get("scene_number") or scene.get("scene", idx + 1)
                    pct = int((idx / total) * 80)
                    progress_bar.progress(pct, text=f"Generating scene {num} of {total}…")
                    status_area.info(f"🎨 Scene {num}: generating AI image…")

                    img_path = f"temp_frames/scene_{num}.png"
                    provider = create_scene_image(scene, img_path)
                    provider_log.append(f"Scene {num} → {provider}")

                    duration = scene.get("duration_seconds") or scene.get("duration", 4)
                    frame_file.write(f"file '{os.path.abspath(img_path)}'\n")
                    frame_file.write(f"duration {duration}\n")

                last = scenes[-1]
                last_num = last.get("scene_number") or last.get("scene", total)
                frame_file.write(f"file '{os.path.abspath(f'temp_frames/scene_{last_num}.png')}'\n")

            progress_bar.progress(85, text="Stitching frames with FFmpeg…")
            status_area.info("🎬 Encoding MP4…")

            import subprocess
            from video_generator import FFMPEG_PATH
            cmd = [
                FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
                "-i", frame_list_path,
                "-vf", "scale=1280:720,format=yuv420p",
                "-c:v", "libx264", "-r", "24", "velora_output.mp4",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")

            progress_bar.progress(100, text="Done!")
            status_area.empty()

            provider_summary = " · ".join(provider_log)
            st.success(f"✅ Video ready!  |  {provider_summary}")

            with open("velora_output.mp4", "rb") as f:
                st.download_button(
                    "⬇️ Download MP4",
                    data=f,
                    file_name="velora_storyboard.mp4",
                    mime="video/mp4"
                )
        except Exception as e:
            progress_bar.empty()
            status_area.empty()
            st.error(f"Video generation failed: {str(e)}")