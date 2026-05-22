import streamlit as st
import json
from agent import run_pipeline

st.set_page_config(
    page_title="Velora AI",
    page_icon="🎬",
    layout="wide"
)

st.markdown("# 🎬 Velora AI")
st.markdown("##### Script → Storyboard → Captions → Video. Powered by an agentic AI pipeline.")
st.divider()

with st.sidebar:
    st.markdown("## ⚙️ Controls")
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
    st.caption("Traces visible on smith.langchain.com")

script = st.text_area(
    "📝 Paste your script here",
    height=220,
    placeholder="""Example: Climate change is reshaping our world at an alarming pace.
Glaciers are melting, sea levels are rising, and extreme weather events are
becoming more frequent. But scientists, activists, and communities around
the world are fighting back with innovation, policy, and sheer determination."""
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate = st.button("🎬 Generate Storyboard", type="primary", use_container_width=True)
with col2:
    clear = st.button("🗑️ Clear", use_container_width=True)

if clear:
    st.session_state.clear()
    st.rerun()

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

if 'scenes' in st.session_state and st.session_state['scenes']:
    scenes = st.session_state['scenes']
    coherence = st.session_state.get('coherence', {})
    current_style = st.session_state.get('style', style)

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
                "thought-provoking": "🤔", "cinematic": "🎬",
                "neutral": "😐", "somber": "😞", "monotone": "😑",
                "serious": "😤", "determined": "💪", "focused": "🎯"
            }.get(mood, "🎬")

            scene_num = scene.get("scene_number", i + 1)
            shot_desc = scene.get("shot_description", "")
            caption = scene.get("caption", "")
            duration = scene.get("duration_seconds", 4)

            st.markdown(f"**Scene {scene_num}** {mood_emoji} *{mood}*")
            st.info(shot_desc if shot_desc else "No description available")
            st.markdown(f"**Caption:** *\"{caption}\"*")
            st.markdown(f"🕐 `{duration}s`")
            st.markdown("")

    st.divider()
    with st.expander("📦 Export raw storyboard JSON"):
        st.json(scenes)
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(scenes, indent=2),
            file_name="velora_storyboard.json",
            mime="application/json"
        )

    st.divider()
    st.markdown("### 🎥 Generate Video")
    st.caption("Converts your storyboard into a downloadable MP4 slideshow")

    if st.button("🎬 Export as MP4", type="secondary"):
        with st.spinner("Generating video with FFmpeg... this takes ~10 seconds"):
            try:
                from video_generator import generate_video
                video_path = generate_video(scenes)
                st.success("✅ Video generated!")
                with open(video_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download MP4",
                        data=f,
                        file_name="velora_storyboard.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"Video generation failed: {str(e)}")