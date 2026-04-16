"""
Streamlit frontend for the AI Blog Generator.

Run:  streamlit run app.py
"""

import os
import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from backend.service import generate_blog  # noqa: E402 (after set_page_config)

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
    <p>Multi-stage LangGraph pipeline · Ollama LLM (local) · DuckDuckGo search · Pollinations images</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
for key in ("result", "generating"):
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
    enable_images = st.toggle("🎨 Generate Images", value=False,
                               help="Uses Google Gemini Imagen to create illustrations")

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

    with st.status("Generating your blog …", expanded=True) as status:
        st.write("🔍 **Routing** — analysing topic complexity …")
        result = generate_blog(topic.strip(), enable_images=enable_images)
        if "error" in result:
            status.update(label="Generation failed", state="error")
            st.error(result["error"])
            st.session_state.generating = False
            st.stop()

        status.update(label=f"✅ Done in {result.get('elapsed_seconds', '?')}s", state="complete")

    st.session_state.result = result
    st.session_state.generating = False

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
result = st.session_state.result

if result and "error" not in (result or {}):
    # ── Metadata pills ──────────────────────────────────────────────────
    mode_emoji = {"closed_book": "📕", "hybrid": "📗", "open_book": "📖"}.get(result["mode"], "📄")
    pills_html = f"""
    <div class="stat-row">
        <span class="stat-pill">{mode_emoji} Mode: <strong>{result['mode']}</strong></span>
        <span class="stat-pill">📂 Category: <strong>{result.get('category','—')}</strong></span>
        <span class="stat-pill">🎯 Audience: <strong>{result.get('target_audience','—')}</strong></span>
        <span class="stat-pill">🎵 Tone: <strong>{result.get('tone','—')}</strong></span>
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

    st.markdown(f'<div class="blog-output">', unsafe_allow_html=True)
    st.markdown(final_md)
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
