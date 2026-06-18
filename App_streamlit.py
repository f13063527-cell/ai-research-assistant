import streamlit as st
import requests
import fitz
import re
from typing import Optional

st.set_page_config(
    page_title="Executive Research Paper Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Enterprise Glassmorphism UI Theme Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body {
        font-family: 'Inter', sans-serif;
    }
    
    /* 1. APPLY BACKGROUND IMAGE TO MAIN DASHBOARD ONLY */
    [data-testid="stMain"] {
        background: linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,.45)),
                    url("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXHIiSJDlGl80GsWGNNbwNdQVYrjZOHgy2_rMwtz6j6g&s=10") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }

    /* Keep outer container base neutral/transparent so main image functions correctly */
    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }

    /* 2. SOLID SIDEBAR BACKGROUND (NO IMAGE LEAK) */
    [data-testid="stSidebar"] {
        background-color: #07111F !important;
        border-right: 1px solid rgba(255,255,255,.08) !important;
    }

    /* Keep inner main container blocks transparent */
    [data-testid="stAppViewBlockContainer"],
    .block-container {
        background: transparent !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, label { 
        font-family: 'Inter', sans-serif !important; 
    }
    
    /* Title Fix */
    [data-testid="stMain"] h1 {
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 20px !important;
        color: var(--text-color) !important;
    }

    h1 span.gradient-title {
        background: linear-gradient(135deg, var(--text-color) 0%, #94A3B8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        display: inline-block !important;
    }

    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: var(--text-color) !important;
    }
    
    /* Glassmorphism Cards */
    .report-card {
        background: color-mix(in srgb, var(--background-color) 75%, transparent) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 30px;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: var(--text-color) !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.15);
        line-height: 1.8;
    }
    
    .report-card h1, .report-card h2, .report-card h3 {
        color: #38BDF8 !important;
        -webkit-text-fill-color: initial !important;
        background: none !important;
        font-weight: 600 !important;
        margin-top: 24px !important;
        margin-bottom: 12px !important;
    }
    
    .report-card h1 { font-size: 26px !important; }
    .report-card h2 { font-size: 22px !important; }
    .report-card h3 { font-size: 19px !important; }
    
    .flow-step-container {
        background: color-mix(in srgb, var(--secondary-background-color) 80%, transparent) !important;
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin: 0 auto;
        max-width: 900px;
        overflow: hidden;
    }
    
    .flow-step-container:hover {
        border-color: rgba(56, 189, 248, 0.5);
        transform: translateY(-2px);
    }
    
    .flow-step-header {
        background: rgba(56, 189, 248, 0.1);
        color: #38BDF8;
        padding: 16px 24px;
        font-size: 20px;
        font-weight: 600;
        border-bottom: 1px solid rgba(56, 189, 248, 0.15);
        text-align: center;
    }
    
    .flow-step-body {
        color: var(--text-color);
        opacity: 0.85;
        padding: 24px;
        font-size: 16px;
    }
    
    div[data-baseweb="select"] > div {
        background-color: var(--secondary-background-color) !important;
        border-color: rgba(148, 163, 184, 0.2) !important;
        color: var(--text-color) !important;
    }
    
    .stTextArea textarea {
        background-color: var(--background-color) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        color: var(--text-color) !important;
        border-radius: 10px !important;
    }
    
    /* 3. FILE UPLOAD DROPZONE CUSTOMIZATION */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(0, 0, 0, 0.45) !important;
        backdrop-filter: blur(8px);
        border: 1px dashed rgba(56, 189, 248, 0.6) !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* Force the upload box content area into a row alignment */
    [data-testid="stFileUploaderDropzone"] section {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. BULLETPROOF FILE UPLOADER OVERRIDE FOR STREAMLIT CLOUD */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(0, 0, 0, 0.45) !important;
        backdrop-filter: blur(8px);
        border: 1px dashed rgba(56, 189, 248, 0.6) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Step A: Make ALL default text strings (including the 200MB limit notice) completely invisible */
    [data-testid="stFileUploaderDropzone"] * {
        color: transparent !important;
        font-size: 0 !important;
    }

    /* Step B: Explicitly protect and restore the "Browse files" button text size and visibility */
    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploaderDropzone"] button * {
        color: #ffffff !important;
        font-size: 14px !important;
    }

    /* Step C: Securely inject your exact custom instruction string directly beneath the button */
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drag and drop PDF file here" !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        color: #38BDF8 !important;
        font-weight: 500 !important;
        margin-top: 14px !important;
        display: block !important;
        visibility: visible !important;
    }
    </style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

# Sync global tracking states
for key, default in [
    ("summary", None), ("pdf_content", None), ("flowchart_bytes", None),
    ("messages", []), ("current_view", "📝 Research Analyzer"), ("filename", ""),
    ("uploaded_pdf_text", ""), ("selected_section_text", ""), ("selected_section_name", ""),
    ("analyzer_steps", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ======================================================
# HELPERS
# ======================================================
def extract_pdf_text(file_bytes):
    text = ""
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    for page in pdf_document:
        text += page.get_text("text")
    return text

def clean_pdf_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'(.{25,80}?)\1+', r'\1', text)
    text = re.sub(r'Ushus - Journal of Business Management|Artificial Intelligence in Self Driving Cars', '', text, flags=re.IGNORECASE)
    text = re.sub(r'ISSN\s*\d+\-\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
    return text.strip()

def extract_section(text, section_name):
    text = clean_pdf_text(text)
    section_patterns = {
        "Abstract": r"abstract[\s:.-]*(.*?)(keywords|introduction)",
        "Introduction": r"introduction[\s:.-]*(.*?)(1\.1|methodology|methods|results)",
        "Methodology": r"(methodology|methods)[\s:.-]*(.*?)(results|discussion)",
        "Results": r"results[\s:.-]*(.*?)(discussion|conclusion)",
        "Discussion": r"discussion[\s:.-]*(.*?)(conclusion|references)",
        "Conclusion": r"conclusion[\s:.-]*(.*?)(references)",
        "References": r"references[\s:.-]*(.*)"
    }
    pattern = section_patterns.get(section_name)
    if not pattern: return "Section pattern not found"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else "Section not found"

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.title("🛰️ FEATURES")
    page = st.radio("Select Page", ["📝 Research Analyzer", "🤖 AI Chat Agent", "📑 PDF Section Extractor", "📊 Research Flow Diagram"])
    st.session_state.current_view = page
    st.divider()

    if page == "📑 PDF Section Extractor":
        st.subheader("📑 Extract PDF Section")
        section_option = st.selectbox("Select Section", ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion", "References"])
        
        if st.button("Extract Section", use_container_width=True):
            if st.session_state.uploaded_pdf_text:
                extracted_text = extract_section(st.session_state.uploaded_pdf_text, section_option)
                if extracted_text and "not found" not in extracted_text.lower():
                    st.session_state.selected_section_text = extracted_text
                    st.session_state.selected_section_name = section_option
                else:
                    st.warning("Section not found in PDF")
            else:
                st.warning("Please upload and analyze a PDF first")

    st.divider()
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ======================================================
# BACKEND API CONNECTOR
# ======================================================
def process_content(file_name: Optional[str] = None, file_bytes: Optional[bytes] = None, raw_text: Optional[str] = None):
    try:
        if raw_text:
            response = requests.post(f"{BACKEND_URL}/analyze-paper", data={"text": raw_text}, timeout=600)
        else:
            files = {"pdf_file": (file_name, file_bytes, "application/pdf")}
            response = requests.post(f"{BACKEND_URL}/analyze-paper", files=files, timeout=600)
        
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            return None, None, None, data["error"]
            
        summary = data.get("summary")
        flowchart_url = data.get("flowchart_url")
        
        pdf_bytes = None
        flowchart_bytes = None
        
        if flowchart_url:
            img_res = requests.get(f"{BACKEND_URL}{flowchart_url}")
            if img_res.status_code == 200:
                flowchart_bytes = img_res.content

        download_url = data.get("download_url")
        if download_url:
            report_res = requests.get(f"{BACKEND_URL}{download_url}")
            if report_res.status_code == 200:
                pdf_bytes = report_res.content

        return summary, flowchart_bytes, pdf_bytes, ""
    except Exception as e:
        return None, None, None, f"Network Connectivity Fault: {str(e)}"

# ======================================================
# VIEWS
# ======================================================
if st.session_state.current_view == "📝 Research Analyzer":
    st.title("📝 Research Paper Analyzer")
    st.markdown("Transform long operational papers into production workflows instantly.")

    tab1, tab2 = st.tabs(["📄 Document Processing Engine", "✍️ Raw Text Core Field"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload Target Research Document (PDF)", 
            type=["pdf"],
            help="Strict Operational Boundary: Please ensure your PDF document is between 1 to 40 pages maximum."
        )
        
        if uploaded_file:
            pdf_bytes = uploaded_file.getvalue()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(pdf_document)

            if not (1 <= page_count <= 40):
                st.error(f"❌ PDF has {page_count} pages. Only documents between 1 and 25 pages are allowed.")
                st.stop()
            st.success(f"✅ PDF accepted ({page_count} pages)")
        
        st.caption("📋 **Document Rule:** Limit 1 to 40 pages per file • PDF")
        if uploaded_file:
            pdf_bytes = uploaded_file.getvalue()
            raw_extracted_text = extract_pdf_text(pdf_bytes)
            
            if st.button("Analyze PDF Structure", type="primary", use_container_width=True):
                with st.spinner("Analyzing structures, compiling operational vectors and generating canvas matrices..."):
                    st.session_state.uploaded_pdf_text = raw_extracted_text
                    st.session_state.analyzer_steps = []  
                    summary, flow_bytes, report_bytes, err = process_content(file_name=uploaded_file.name, file_bytes=pdf_bytes)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.summary = summary
                        st.session_state.flowchart_bytes = flow_bytes
                        st.session_state.pdf_content = report_bytes
                        st.session_state.filename = uploaded_file.name
                        st.rerun()

    with tab2:
        user_text = st.text_area("Input system text data sequences directly:", height=250)
        if user_text and st.button("Compile Text Matrix", type="primary"):
            with st.spinner("Processing framework steps..."):
                st.session_state.analyzer_steps = []  
                summary, flow_bytes, report_bytes, err = process_content(raw_text=user_text)
                if err: 
                    st.error(err)
                else:
                    st.session_state.summary = summary
                    st.session_state.flowchart_bytes = flow_bytes
                    st.session_state.pdf_content = report_bytes
                    st.session_state.filename = "Text_Payload.pdf"
                    st.rerun()

    if st.session_state.summary:
        st.divider()
        st.write("") 
        
        # 1. Summarization View Block
        st.markdown("### 📝 Executive Analysis Summary")
        st.markdown(f'<div class="report-card">\n\n{st.session_state.summary}\n\n</div>', unsafe_allow_html=True)
        
        st.write("")
        st.write("")
            
        # 2. HEADLINES ONLY FOR RESEARCH ANALYZER VIEW
        st.markdown("### 🗺️ Derived Research Process Workflow")
        st.caption("This responsive diagram outlines the core headlines and sequential milestones extracted from the PDF context.")
        
        if not st.session_state.analyzer_steps:
            st.session_state.analyzer_steps = [
                {"title": "1. Study Conceptualization", "desc": "The foundational problem statement and primary research targets are isolated directly from the document introduction headers."},
                {"title": "2. Literature Review", "desc": "The specific datasets, baseline criteria, and raw structural inputs compiled for the practical experiment stages."},
                {"title": "3. Data Collection", "desc": "The step-by-step algorithms, mathematical proofs, or implementation procedures deployed by the research authors."},
                {"title": "4. Data Analysis & Validation", "desc": "The performance checking stage where findings are verified against control metrics and standard industry baselines."},
                {"title": "5. Conclusion & Future Work", "desc": "The ultimate takeaway and operational real-world impacts derived from the document findings."}
            ]

        # Render step badges (Headlines Only)
        for i, step in enumerate(st.session_state.analyzer_steps):
            c1, card_col, c3 = st.columns([0.5, 5, 0.5])
            with card_col:
                st.markdown(f"""
                    <div style="
                        background: rgba(56, 189, 248, 0.08); 
                        border: 1px solid #38BDF8; 
                        border-radius: 12px; 
                        overflow: hidden; 
                        margin: 0 auto;
                        max-width: 900px;
                        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.1);
                    ">
                        <div style="
                            color: #38BDF8; 
                            padding: 20px; 
                            text-align: center; 
                            font-family: 'Inter', sans-serif;
                            font-size: 22px; 
                            font-weight: 600;
                            letter-spacing: -0.01em;
                        ">
                            {step['title']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            if i < len(st.session_state.analyzer_steps) - 1:
                a1, arrow_col, a3 = st.columns([0.5, 5, 0.5])
                with arrow_col:
                    st.markdown("""
                        <div style="text-align: center; margin: 10px 0;">
                            <span style="color: #38BDF8; font-size: 32px; font-weight: bold; opacity: 0.8;">↓</span>
                        </div>
                    """, unsafe_allow_html=True)
            
        st.write("")
        st.divider()
        
        # 3. PDF Download Button
        if st.session_state.pdf_content:
            st.download_button(
                label="📥 Download Complete Executive PDF Report",
                data=st.session_state.pdf_content,
                file_name=f"Executive_Report_{st.session_state.filename}",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


elif st.session_state.current_view == "🤖 AI Chat Agent":
    st.title("🤖 AI Research Assistant")

    if not st.session_state.summary:
        st.warning("Please analyze a document first")
    else:
        st.caption("Context: Active Paper")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "scroll_to_bottom" not in st.session_state:
            st.session_state.scroll_to_bottom = False

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.scroll_to_bottom:
            st.components.v1.html(
                """
                <script>
                setTimeout(() => {
                    const mainSection = window.parent.document.querySelector("section.stMain");
                    if (mainSection) {
                        const start = mainSection.scrollTop;
                        const end = mainSection.scrollHeight;
                        const duration = 1500;
                        let startTime = null;
                        function animateScroll(timestamp) {
                            if (!startTime) startTime = timestamp;
                            const progress = Math.min((timestamp - startTime) / duration, 1);
                            mainSection.scrollTop = start + (end - start) * progress;
                            if (progress < 1) requestAnimationFrame(animateScroll);
                        }
                        requestAnimationFrame(animateScroll);
                    }
                }, 500);
                </script>
                """,
                height=0
            )
            st.session_state.scroll_to_bottom = False

        prompt = st.chat_input("Ask a follow-up question...")

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat-with-paper",
                    data={"question": prompt},
                    timeout=300
                )
                raw_data = response.json()
                if isinstance(raw_data, dict):
                    if "answer" in raw_data:
                        answer = raw_data["answer"]
                    elif "error" in raw_data:
                        answer = f"⚠️ {raw_data['error']}"
                    else:
                        answer = "Unexpected response received from server."
                else:
                    answer = "Invalid response received from server."
            except Exception as e:
                answer = f"Connection error: {str(e)}"

            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.scroll_to_bottom = True
            st.rerun()


elif st.session_state.current_view == "📑 PDF Section Extractor":
    st.title("📑 PDF Section Extractor ")
    st.markdown("Extract, break down, and view isolated core sections from your uploaded research document context.")
    
    if not st.session_state.uploaded_pdf_text:
        st.warning("⚠️ Please upload and analyze a PDF document first in the **Document Processing Engine** to allow section parsing.")
    else:
        if st.session_state.selected_section_text:
            st.write("")
            st.markdown(f"### 📄 Extracted Section: {st.session_state.selected_section_name}")
            
            col_raw, col_exp = st.columns(2)
            
            with col_raw:
                st.subheader("📝 Raw Academic Text")
                st.markdown(f'<div class="report-card" style="white-space: pre-wrap; height: 400px; overflow-y: auto; font-size: 14px;">{st.session_state.selected_section_text}</div>', unsafe_allow_html=True)
            
            with col_exp:
                st.subheader("💡 Student Study Guide")
                st.info(f"To get a simplified explanation of this {st.session_state.selected_section_name} section, copy any text block from the left and paste it into the **🤖 AI Chat Agent** with the phrase: *'Explain this section simply:'*")
                st.markdown("""
                **Recommended Reading Focus for this Section:**
                * Identify the primary methodologies or metrics introduced here.
                * Take note of any foundational limitations highlighted by the authors.
                """)
        else:
            st.info("ℹ️ Select a target section from the sidebar dropdown options and click **Extract Section** to display its text payload here.")


elif st.session_state.current_view == "📊 Research Flow Diagram":
    st.title("📊 Research Flow Diagram")
    st.markdown("Generate an integrated structural workflow diagram with embedded step-by-step breakdowns.")
    
    if "diagram_generated" not in st.session_state:
        st.session_state.diagram_generated = False

    col1, col2, col3 = st.columns([1.5, 1, 1.5]) 
    with col2:
        if st.button("Generate Diagram", type="primary", use_container_width=True):
            if not st.session_state.summary:
                st.warning("⚠️ Please analyze a PDF document first on the primary engine page.")
            else:
                with st.spinner("Extracting unique research process milestones from your document..."):
                    try:
                        response = requests.post(f"{BACKEND_URL}/generate-flowchart")
                        raw_data = response.json()
                        if "error" in raw_data:
                            st.error(raw_data["error"])
                        else:
                            st.session_state.analyzer_steps = raw_data.get("steps", [])
                            st.session_state.diagram_generated = True
                    except Exception as e:
                        st.error(f"Network error syncing steps: {e}")
    
    if st.session_state.diagram_generated:
        st.write("")
        st.write("")
        
        if st.session_state.flowchart_bytes:
            c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
            with c_img2:
                st.markdown("<h4 style='text-align: center; color: #38BDF8;'>Visual Process Flowchart</h4>", unsafe_allow_html=True)
                st.image(st.session_state.flowchart_bytes, use_container_width=True)
                st.write("")

        if st.session_state.analyzer_steps:
            st.markdown("<h4 style='text-align: center; color: #38BDF8; margin-bottom: 20px;'>Core Milestone Breakdown</h4>", unsafe_allow_html=True)
            for i, step in enumerate(st.session_state.analyzer_steps):
                c1, card_col, c3 = st.columns([0.5, 5, 0.5])
                with card_col:
                    st.markdown(f"""
                        <div class="flow-step-container">
                            <div class="flow-step-header">
                                {step['title']}
                            </div>
                            <div class="flow-step-body">
                                {step['desc']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                if i < len(st.session_state.analyzer_steps) - 1:
                    a1, arrow_col, a3 = st.columns([0.5, 5, 0.5])
                    with arrow_col:
                        st.markdown("""
                            <div style="text-align: center; margin: 12px 0;">
                                <span style="color: #38BDF8; font-size: 36px; font-weight: bold; opacity: 0.8;">↓</span>
                            </div>
                        """, unsafe_allow_html=True)
