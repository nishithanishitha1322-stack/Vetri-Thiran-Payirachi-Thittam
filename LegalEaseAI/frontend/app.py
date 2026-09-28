import streamlit as st
import requests
from fpdf import FPDF
import json

# Page Config
st.set_page_config(
    page_title="LegalEase - AI Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .risk-high { color: #dc3545; font-weight: bold; }
    .risk-medium { color: #ffc107; font-weight: bold; }
    .risk-low { color: #28a745; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ LegalEase - AI Legal Document Simplifier")
st.markdown("Upload your legal PDF and get simple English summary, risks, and clause-by-clause insights powered by Gemini AI.")
st.divider()

BACKEND_URL = "http://localhost:8000"

# Tabs
tab1, tab2 = st.tabs(["📄 Upload PDF", "📝 Paste Text"])

# Store analysis in session
if 'analysis' not in st.session_state:
    st.session_state['analysis'] = None

with tab1:
    st.subheader("Upload Legal Document (PDF)")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")
    if uploaded_file:
        st.info(f"File selected: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        if st.button("Analyze PDF", type="primary", use_container_width=True):
            with st.spinner("Analyzing document with Gemini AI... Please wait"):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    res = requests.post(f"{BACKEND_URL}/analyze-pdf", files=files, timeout=180)
                    res.raise_for_status()
                    st.session_state['analysis'] = res.json()
                    st.success("Analysis Complete!")
                except requests.exceptions.ConnectionError:
                    st.error("Backend not running! Start backend with: uvicorn main:app --reload --port 8000")
                except Exception as e:
                    st.error(f"Error: {e} - {res.text if 'res' in locals() else ''}")

with tab2:
    st.subheader("Paste Legal Text")
    text_input = st.text_area("Paste your legal text here", height=300, placeholder="Paste your Terms & Conditions, NDA, Lease Agreement...")
    if st.button("Analyze Text", type="primary", use_container_width=True, key="analyze_text"):
        if not text_input.strip():
            st.warning("Please paste some text first")
        else:
            with st.spinner("Analyzing..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/analyze-text", json={"text": text_input}, timeout=180)
                    res.raise_for_status()
                    st.session_state['analysis'] = res.json()
                    st.success("Analysis Complete!")
                except requests.exceptions.ConnectionError:
                    st.error("Backend not running!")
                except Exception as e:
                    st.error(f"Error: {e}")

# Display Results
if st.session_state['analysis']:
    data = st.session_state['analysis']
    st.divider()
    st.header("📊 Analysis Report")

    # Summary
    st.subheader("📌 Executive Summary")
    st.write(data.get('summary', 'N/A'))

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("✅ Simplified Document (Plain English)")
        st.text_area("", value=data.get('simplified_document', ''), height=400)

    with col2:
        st.subheader("⚠️ Risk Factors")
        for risk in data.get('risks', []):
            st.warning(f"• {risk}")

        st.subheader("💡 Recommendations")
        for rec in data.get('recommendations', []):
            st.info(f"• {rec}")

    # Key Clauses
    st.subheader("📑 Clause-by-Clause Breakdown")
    for i, clause in enumerate(data.get('key_clauses', []), 1):
        risk_color = "🔴" if clause.get('risk_level') == "High" else "🟡" if clause.get('risk_level') == "Medium" else "🟢"
        with st.expander(f"{risk_color} Clause {i} - {clause.get('risk_level', 'N/A')} Risk: {clause.get('original_clause', '')[:70]}..."):
            st.markdown(f"**Original Clause:**\n> {clause.get('original_clause', '')}")
            st.markdown(f"**Simplified:**\n{clause.get('simplified', '')}")
            st.markdown(f"**Why it matters:** {clause.get('explanation', '')}")

    # Export Feature
    st.divider()
    st.subheader("📤 Export Report")
    col_a, col_b = st.columns(2)
    
    with col_a:
        # JSON Export
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="Download JSON Report",
            data=json_str,
            file_name="LegalEase_Report.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col_b:
        # PDF Export
        if st.button("Generate PDF Report", use_container_width=True):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "LegalEase - Legal Analysis Report", ln=True, align='C')
                pdf.ln(10)
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Summary:", ln=True)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, data.get('summary', ''))
                pdf.ln(5)
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Simplified Document:", ln=True)
                pdf.set_font("Arial", '', 10)
                # Encode to handle special chars
                safe_text = data.get('simplified_document', '').encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, safe_text)
                
                pdf.output("LegalEase_Report.pdf")
                with open("LegalEase_Report.pdf", "rb") as f:
                    st.download_button("⬇️ Click to Download PDF", f, file_name="LegalEase_Report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    if st.button("Clear Report"):
        st.session_state['analysis'] = None
        st.rerun()