import os
import re
import fitz
import uuid
import tempfile
import faiss
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # ✨ Added CORS Support
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from graphviz import Digraph

# ReportLab Layout Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# =========================================================
# FASTAPI APP WITH CORS ENABLED
# =========================================================
app = FastAPI()

# Allow your Streamlit app frontend to communicate freely with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# LLM CONFIG
# =========================================================
OPENROUTER_API_KEY = os.environ.get("GROQ_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# =========================================================
# EMBEDDING MODEL & STORE GLOBALS
# =========================================================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

global_index = None
global_chunks = []
global_summary = ""
global_flowchart_path = ""  # ✨ FIX: Initialized tracking global variable

# =========================================================
# HELPERS
# =========================================================
def extract_text_from_pdf(pdf_path):
    text = ""
    pdf_document = fitz.open(pdf_path)
    for page in pdf_document:
        text += page.get_text("text")
    return text

def create_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    return splitter.split_text(text)

def build_vector_store(chunks):
    global global_index, global_chunks
    global_chunks = chunks
    embeddings = embedding_model.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    global_index = index

def search_chunks(query, top_k=2):
    query_embedding = embedding_model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")
    distances, indices = global_index.search(query_embedding, top_k)
    return [global_chunks[idx] for idx in indices[0]]

# =========================================================
# GENERATE RESPONSES
# =========================================================
def generate_llm_response(prompt, temperature=0.3, max_tokens=1200):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# =========================================================
# CREATE PDF REPORT
# =========================================================
def create_pdf_report(summary, flowchart_img_path=None):
    report_path = "research_report.pdf"
    
    doc = SimpleDocTemplate(
        report_path, 
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E293B'),
        alignment=0,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    story = []
    
    story.append(Paragraph("Executive Research Analysis Report", title_style))
    story.append(Spacer(1, 10))
    
    formatted_summary = summary.replace("\n", "<br/>")
    story.append(Paragraph(formatted_summary, body_style))
    story.append(Spacer(1, 15))
    
    if flowchart_img_path and os.path.exists(flowchart_img_path):
        img = ImageReader(flowchart_img_path)
        orig_w, orig_h = img.getSize()
        
        MAX_WIDTH = 450
        MAX_HEIGHT = 550
        
        scale = min(MAX_WIDTH / float(orig_w), MAX_HEIGHT / float(orig_h))
        final_w = orig_w * scale
        final_h = orig_h * scale

        diagram_elements = [
            Spacer(1, 15),
            Paragraph("System Workflow & Logic Structural Diagram", heading_style),
            Spacer(1, 15),
            RLImage(flowchart_img_path, width=final_w, height=final_h)
        ]
        story.append(KeepTogether(diagram_elements))
        
    doc.build(story)
    return report_path

# =========================================================
# ENDPOINTS
# =========================================================
@app.post("/analyze-paper")
async def analyze_paper(pdf_file: UploadFile = File(None), text: str = Form(None)):
    global global_summary, global_flowchart_path
    text_data = ""
    try:
        if pdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(await pdf_file.read())
                temp_path = temp_pdf.name
            text_data = extract_text_from_pdf(temp_path)
        elif text:
            text_data = text
        else:
            return {"error": "No PDF or text data detected"}

        chunks = create_chunks(text_data)
        build_vector_store(chunks)

        summary_prompt = f"Analyze this research paper and provide structured synthesis using bold markdown headers:\n\n1. MAIN RESEARCH OBJECTIVE\n2. KEY METHODOLOGY & FINDINGS\n3. BUSINESS & REAL-WORLD IMPLICATIONS\n\nResearch Paper Context:\n{text_data[:8000]}"
        summary = generate_llm_response(summary_prompt, temperature=0.3, max_tokens=1500)
        global_summary = summary

        flow_text = " ".join(chunks[:8])
        flow_prompt = f"Extract exactly 4-5 core logical milestones from this research process sequence flow.\nRules:\n- One absolute short step name per line\n- No sequence numbers or explanation text\n- Max 4 words per line\n\nPaper Text:\n{flow_text}"
        steps_text = generate_llm_response(flow_prompt, temperature=0.2, max_tokens=500)
        steps = [line.strip() for line in steps_text.split("\n") if line.strip() and len(line.strip()) < 40][:5]

        if len(steps) < 2:
            steps = ["Document Ingestion", "Feature Extraction", "Neural Aggregation", "Validation Verification", "Output Compilation"]

        # 3. Create clean Executive Corporate Stylized Flowchart (COMPACT VERSION)
        dot = Digraph()
        
        # Reduced ranksep to 0.25 to bring vertical steps much closer together
        dot.attr(rankdir="TB", dpi="200", ranksep="0.25")
        
        # Reduced fontsize to 13 and margin to "0.2,0.1" to make boxes significantly shorter
        dot.attr('node', fontname='Helvetica', fontsize='13', shape='box', style='filled, rounded', 
                 color='#3B82F6', fillcolor='#F0F9FF', fontcolor='#1E3A8A', penwidth='1.2', margin="0.2,0.1")
        dot.attr('edge', fontname='Helvetica', fontsize='9', color='#64748B', penwidth='1.2', arrowsize='0.7')

        for i, step in enumerate(steps):
            dot.node(str(i), f" {step} ")
        for i in range(len(steps) - 1):
            dot.edge(str(i), str(i + 1))

        filename = f"flowchart_{uuid.uuid4().hex}"
        output_img = dot.render(filename, format="png", cleanup=True)
        global_flowchart_path = output_img

        create_pdf_report(summary, output_img)

        return {
            "summary": summary, 
            "flowchart_url": f"/flowchart/{os.path.basename(output_img)}",
            "download_url": "/download-report"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat-with-paper")
async def chat_with_paper(question: str = Form(...)):
    try:
        if global_index is None:
            return {"error": "Please analyze a paper first"}
        relevant_chunks = search_chunks(question)
        context = "\n\n".join(relevant_chunks)
        prompt = f"Answer the question using the context below.\n\nContext:\n{context}\n\nQuestion:\n{question}"
        return {"question": question, "answer": generate_llm_response(prompt, temperature=0.5, max_tokens=800)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download-report")
async def download_report():
    return FileResponse("research_report.pdf", media_type="application/pdf", filename="research_report.pdf")

@app.post("/generate-flowchart")
async def generate_flowchart():
    try:
        global global_chunks
        if not global_chunks:
            return {"error": "Analyze PDF first in the primary engine tab."}

        text_data = " ".join(global_chunks[:10])
        
        prompt = (
            "You are an expert academic analysis system. Extract the core sequential research process milestones from this paper.\n"
            "Provide exactly 5 steps in historical chronological order. For each step, provide a short Title (max 5 words) and a 1-sentence Description of what the authors did.\n"
            "Format your response exactly like this template with a pipe (|) character separating title and description:\n"
            "Title of Step | Description of what happened in this step.\n"
            f"Research Paper Context:\n{text_data}"
        )
        
        steps_text = generate_llm_response(prompt, temperature=0.2, max_tokens=1000)
        lines = [line.strip() for line in steps_text.split("\n") if "|" in line]
        
        extracted_steps = []
        for idx, line in enumerate(lines[:5]):
            parts = line.split("|")
            title = parts[0].strip()
            
            # ✨ FIX: Clean any leading digits (e.g., '1. ', '2. ') injected by the LLM
            title = re.sub(r'^\d+[\.\s\-–]+', '', title)
            
            desc = parts[1].strip()
            extracted_steps.append({
                "title": f"{idx+1}. {title}",
                "desc": desc
            })
        
        if len(extracted_steps) < 3:
            extracted_steps = [
                {"title": "1. Core Objective Alignment", "desc": "The primary problem statement and initial experimental hypotheses are established from document constraints."},
                {"title": "2. Data Assembly & Preprocessing", "desc": "Raw source matrices, baseline metrics, or study populations are clean-filtered for processing."},
                {"title": "3. Experimental Framework Execution", "desc": "The main technical methodology, core algorithms, or operational tests are systematically deployed."},
                {"title": "4. Performance Metrics Validation", "desc": "Outputs are analyzed against rigorous control benchmarks to verify scientific validation accuracy."},
                {"title": "5. Insight Synthesis & Conclusions", "desc": "Final qualitative and quantitative findings are compiled alongside real-world implementation scopes."}
            ]
            
        return {"steps": extracted_steps}
    except Exception as e:
        return {"error": str(e)}
        
@app.get("/flowchart/{filename}")
async def get_flowchart(filename: str):
    return FileResponse(filename, media_type="image/png")

@app.get("/")
async def root():
    return {"message": "Research Paper RAG API Active"}