"""
Streamlit frontend for the AI Blog Generator.

Run:  streamlit run app.py
"""

import os
import hashlib
import base64
import mimetypes
import re
import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from backend.service import generate_blog_stream  # noqa: E402 (after set_page_config)
from backend.config import (  # noqa: E402
    BLOG_LENGTH_OPTIONS,
    BLOG_TONE_OPTIONS,
    BLOG_FORMAT_OPTIONS,
    TARGET_AUDIENCE_OPTIONS,
)
from backend.utils import clear_cached  # noqa: E402


def render_markdown_with_local_images(markdown: str) -> str:
    """
    Replace local markdown image paths with inline data URIs for Streamlit display.

    This keeps downloaded markdown readable while making inline blog images render
    inside the app.
    """
    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def repl(match: re.Match[str]) -> str:
        alt = match.group(1)
        raw_path = match.group(2).strip()
        if raw_path.startswith(("http://", "https://", "data:")):
            return match.group(0)

        candidate_path = raw_path
        if not os.path.isabs(candidate_path):
            candidate_path = os.path.join(os.getcwd(), candidate_path)

        if not os.path.exists(candidate_path):
            return match.group(0)

        mime_type, _ = mimetypes.guess_type(candidate_path)
        if not mime_type:
            mime_type = "image/png"

        with open(candidate_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")

        safe_alt = alt.replace('"', "&quot;")
        return (
            f'<figure class="inline-blog-image">'
            f'<img src="data:{mime_type};base64,{encoded}" alt="{safe_alt}" />'
            f"</figure>"
        )

    return image_pattern.sub(repl, markdown)

# ---------------------------------------------------------------------------
# Streamlit-level caching for blog generation
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def cached_generate_blog(
    topic: str,
    enable_images: bool,
    blog_length: str,
    blog_format: str,
    tone: str,
    target_audience: str,
    llm_provider: str,
):
    """
    Cached wrapper around generate_blog_stream.
    Cache key = combination of all parameters.
    TTL = 1 hour.
    """
    # No callback in cached version to keep it simple
    return generate_blog_stream(
        topic=topic,
        enable_images=enable_images,
        callback=None,
        blog_length=blog_length,
        blog_format=blog_format,
        tone=tone,
        target_audience=target_audience,
        llm_provider=llm_provider,
    )

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=DM+Sans:wght@400;500;600&display=swap');

    /* Global overrides */
    .stApp { background: #0e1117; }

    .main .block-container {
        max-width: 960px;
        padding-top: 2rem;
    }

    /* Hero header */
    .hero {
        text-align: center;
        padding: 2rem 0 1.5rem;
    }
    .hero h1 {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero p {
        font-family: 'DM Sans', sans-serif;
        color: #94a3b8;
        font-size: 1.05rem;
    }

    /* Stat pills */
    .stat-row { display: flex; gap: 0.75rem; flex-wrap: wrap; justify-content: center; margin: 1rem 0; }
    .stat-pill {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.82rem;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        border: 1px solid #334155;
        color: #cbd5e1;
        background: #1e293b;
    }
    .stat-pill strong { color: #60a5fa; }

    /* Blog output area */
    .blog-output {
        font-family: 'Source Serif 4', Georgia, serif;
        line-height: 1.75;
        color: #e2e8f0;
        font-size: 1.05rem;
    }
    .blog-output h1 { font-size: 2rem; color: #f1f5f9; margin-top: 1.5rem; }
    .blog-output h2 { font-size: 1.45rem; color: #e2e8f0; border-bottom: 1px solid #334155; padding-bottom: 0.4rem; margin-top: 2rem; }
    .blog-output h3 { font-size: 1.2rem; color: #cbd5e1; }
    .blog-output p { margin-bottom: 1rem; }
    .blog-output ul, .blog-output ol { margin-left: 1.5rem; margin-bottom: 1rem; }
    .blog-output .inline-blog-image { margin: 1.25rem 0 1.75rem; }
    .blog-output .inline-blog-image img {
        width: 100%;
        border-radius: 14px;
        display: block;
        border: 1px solid #334155;
    }

    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>✍️ AI Blog Generator</h1>
    <p>Multi-stage LangGraph pipeline · Ollama LLM (local) · Tavily search · Pollinations images</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
for key in ("result", "generating", "progress_updates"):
    if key == "progress_updates":
        if key not in st.session_state:
            st.session_state[key] = []
    else:
        if key not in st.session_state:
            st.session_state[key] = None if key == "result" else False

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    topic = st.text_area(
        "Blog Topic",
        placeholder="e.g. How quantum computing will reshape cybersecurity",
        height=100,
    )
    
    # ── Blog Customization Controls ────────────────────────────────────
    st.subheader("📝 Customization")
    
    col1, col2 = st.columns(2)
    with col1:
        blog_length = st.selectbox(
            "Blog Length",
            list(BLOG_LENGTH_OPTIONS.keys()),
            index=1,  # default: medium
            help="Controls target word count"
        )
    with col2:
        blog_format = st.selectbox(
            "Format",
            BLOG_FORMAT_OPTIONS,
            index=0,  # default: standard
            help="Blog structure and style"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        tone = st.selectbox(
            "Tone",
            BLOG_TONE_OPTIONS,
            index=0,  # default: educational
            help="Writing style and voice"
        )
    with col4:
        target_audience = st.selectbox(
            "Audience",
            TARGET_AUDIENCE_OPTIONS,
            index=3,  # default: general
            help="Expertise level of readers"
        )
    
    # ── LLM Provider Selection ─────────────────────────────────────────
    llm_provider = st.selectbox(
        "🤖 LLM Provider",
        ["auto", "ollama", "openai"],
        index=0,
        help="'auto' tries Ollama first, falls back to OpenAI. Set OPENAI_API_KEY for OpenAI fallback."
    )
    
    # ── Image & Generation Options ─────────────────────────────────────
    enable_images = st.toggle("🎨 Generate Images", value=False,
                               help="Uses Pollinations AI to create illustrations")
    
    enable_streaming = st.toggle("⚡ Real-time Streaming", value=True,
                                 help="Stream progress in real-time (better UX)")

    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🚀 Generate", use_container_width=True, type="primary")
    with col2:
        regen_btn = st.button("🔄 Regenerate", use_container_width=True)

    st.divider()
    st.caption("**Pipeline stages:** Router → Research → Planner → Writers → Editor → Images")

# ---------------------------------------------------------------------------
# Generation logic
# ---------------------------------------------------------------------------
should_run = (generate_btn or regen_btn) and topic and not st.session_state.generating

if should_run:
    st.session_state.generating = True
    st.session_state.result = None
    st.session_state.progress_updates = []

    with st.status("Generating your blog …", expanded=True) as status:
        # Create placeholders for streaming updates
        progress_container = st.container()
        plan_placeholder = st.empty()
        sections_placeholder = st.empty()
        
        # Callback function for streaming progress
        def progress_callback(stage: str, data: dict):
            """Called at each pipeline stage to update UI in real-time."""
            st.session_state.progress_updates.append({"stage": stage, "data": data})
            
            # Update status message
            stage_names = {
                "routing": "🔍 **Routing** — analysing topic complexity",
                "research": "📚 **Research** — gathering information",
                "planning": "📋 **Planning** — structuring blog",
                "writing": "✍️ **Writing** — generating sections",
                "editing": "✏️ **Editing** — polishing content",
                "images": "🎨 **Images** — creating visuals",
                "complete": "✅ **Complete** — blog ready",
                "error": "❌ **Error** — generation failed",
            }
            
            if stage in stage_names:
                status.update(label=stage_names[stage], state="running" if stage != "complete" else "complete")
            
            # Show plan when available
            if stage == "planning" and "plan" in data:
                with plan_placeholder.container():
                    st.write("📋 **Blog Plan:**")
                    plan = data.get("plan", {})
                    if plan:
                        st.write(f"*{plan.get('title', 'Untitled')}*")
                        st.caption(f"Target: ~{plan.get('estimated_word_count', 'N/A')} words")
            
            # Show sections as they're written
            if stage == "writing" and "sections" in data:
                sections = data.get("sections", [])
                if sections:
                    with sections_placeholder.container():
                        st.caption(f"🔄 Writing section {len(sections)}...")
        
        # Generate with callback (live streaming - bypasses cache)
        if enable_streaming:
            result = generate_blog_stream(
                topic=topic.strip(),
                enable_images=enable_images,
                callback=progress_callback,
                blog_length=blog_length,
                blog_format=blog_format,
                tone=tone,
                target_audience=target_audience,
                llm_provider=llm_provider,
            )
        else:
            # Use Streamlit-level cache for non-streaming generation
            result = cached_generate_blog(
                topic=topic.strip(),
                enable_images=enable_images,
                blog_length=blog_length,
                blog_format=blog_format,
                tone=tone,
                target_audience=target_audience,
                llm_provider=llm_provider,
            )
        
        if "error" in result:
            status.update(label="Generation failed", state="error")
            st.error(f"❌ {result['error']}")
            st.session_state.generating = False
            st.stop()

        elapsed = result.get('elapsed_seconds', '?')
        cached = result.get('cached', False)
        cache_badge = " ⚡ (cached)" if cached else ""
        status.update(label=f"✅ Done in {elapsed}s{cache_badge}", state="complete")

    st.session_state.result = result
    st.session_state.generating = False
    progress_container.empty()
    plan_placeholder.empty()
    sections_placeholder.empty()

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
result = st.session_state.result

if result and "error" not in (result or {}):
    # ── Metadata pills ──────────────────────────────────────────────────
    mode_emoji = {"closed_book": "📕", "hybrid": "📗", "open_book": "📖"}.get(result["mode"], "📄")
    format_emoji = {"standard": "📄", "seo-optimized": "🔍", "listicle": "📋", "how-to": "🎯", "opinion": "💭"}.get(result.get("blog_format"), "📄")
    length_emoji = {"short": "📱", "medium": "📖", "long": "📚"}.get(result.get("blog_length"), "📄")
    
    pills_html = f"""
    <div class="stat-row">
        <span class="stat-pill">{mode_emoji} Mode: <strong>{result['mode']}</strong></span>
        <span class="stat-pill">📂 Category: <strong>{result.get('category','—')}</strong></span>
        <span class="stat-pill">🎯 Audience: <strong>{result.get('target_audience','—')}</strong></span>
        <span class="stat-pill">🎵 Tone: <strong>{result.get('tone','—')}</strong></span>
        <span class="stat-pill">{format_emoji} Format: <strong>{result.get('blog_format','—')}</strong></span>
        <span class="stat-pill">{length_emoji} Length: <strong>{result.get('blog_length','—')}</strong></span>
        <span class="stat-pill">⏱️ <strong>{result.get('elapsed_seconds','?')}s</strong></span>
    </div>
    """
    st.markdown(pills_html, unsafe_allow_html=True)

    # ── Expandable plan ─────────────────────────────────────────────────
    plan = result.get("plan", {})
    if plan:
        with st.expander("📋 Blog Plan", expanded=False):
            st.subheader(plan.get("title", ""))
            st.write(f"**Word target:** ~{plan.get('estimated_word_count', '—')} words")
            for i, sec in enumerate(plan.get("sections", []), 1):
                st.markdown(f"**{i}. {sec.get('heading', '')}** — {sec.get('goal', '')}")
                for bp in sec.get("bullet_points", []):
                    st.markdown(f"  - {bp}")

    # ── Final blog ──────────────────────────────────────────────────────
    st.divider()
    final_md = result.get("final_markdown", "")
    rendered_md = render_markdown_with_local_images(final_md)

    st.markdown(f'<div class="blog-output">', unsafe_allow_html=True)
    st.markdown(rendered_md, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Images ──────────────────────────────────────────────────────────
    images = result.get("images", [])
    if images:
        st.divider()
        st.subheader("🖼️ Generated Images")
        cols = st.columns(min(len(images), 3))
        for i, img in enumerate(images):
            path = img.get("path", "")
            if os.path.exists(path):
                cols[i % len(cols)].image(path, caption=img.get("alt", ""), use_container_width=True)

    # ── Errors (if any) ─────────────────────────────────────────────────
    errors = result.get("errors", [])
    if errors:
        with st.expander("⚠️ Warnings / Errors", expanded=False):
            for e in errors:
                st.warning(e)

    # ── Download ────────────────────────────────────────────────────────
    st.divider()
    st.download_button(
        label="⬇️ Download Blog (.md)",
        data=final_md,
        file_name="blog_post.md",
        mime="text/markdown",
    )
    if st.button("🗑️ Clear Output"):
        st.session_state.result = None
        st.session_state.progress_updates = []
        st.rerun()

    if st.button("♻️ Clear Cache"):
        st.cache_data.clear()
        clear_cached()

    if st.button("🚨 Reset All"):
        st.session_state.clear()
        st.cache_data.clear()
        clear_cached()
        st.rerun()

elif not result:
    # Empty state
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; color: #64748b;">
        <p style="font-size: 3rem; margin-bottom: 0.5rem;">✍️</p>
        <p style="font-family: 'DM Sans', sans-serif; font-size: 1.1rem;">
            Enter a topic in the sidebar and hit <strong>Generate</strong> to create your blog.
        </p>
    </div>
    """, unsafe_allow_html=True)
