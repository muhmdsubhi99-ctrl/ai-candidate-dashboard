import streamlit as st
import pandas as pd
import PyPDF2
from docx import Document
from transformers import pipeline

st.set_page_config(
    page_title="AI Candidate Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🤖 AI Candidate Evaluation Dashboard")

# =========================
# Load Lightweight Model
# =========================
@st.cache_resource
def load_model():
    return pipeline(
        "zero-shot-classification",
        model="valhalla/distilbart-mnli-12-3"
    )

extractor = load_model()

# =========================
# Extract Text
# =========================
def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        return file.read().decode("utf-8")

# =========================
# Analyze CV
# =========================
def analyze_cv(cv_text):
    labels = [
        "Leadership",
        "Decision Making",
        "Analytics Skills",
        "Governance & Risk",
        "Financial Impact",
        "C-Level Exposure",
        "Sustainability",
        "Communication",
        "Innovation",
        "Training Potential"
    ]

    result = extractor(cv_text[:1500], labels)

    scores = {}
    for label, score in zip(result["labels"], result["scores"]):
        scores[label] = round(score * 10, 1)

    total_score = sum(scores.values()) / len(scores) * 10
    return scores, total_score

# =========================
# Generate PDF (ReportLab)
# =========================
def generate_pdf(name, scores, total_score, salary, recommendation):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"<b>Candidate Scorecard: {name}</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [["Skill", "Score (/10)"]]
    for skill, score in scores.items():
        data.append([skill, str(score)])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"<b>Total Score:</b> {total_score:.2f}/100", styles["Normal"]))
    elements.append(Paragraph(f"<b>Recommended Salary:</b> {salary:,.0f} SAR", styles["Normal"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"<b>AI Recommendation:</b> {recommendation}", styles["Normal"]))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# =========================
# Upload Section
# =========================
uploaded_files = st.file_uploader(
    "Upload CVs (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    results = []

    for file in uploaded_files:
        with st.spinner(f"Analyzing {file.name}..."):
            text = extract_text(file)
            scores, total_score = analyze_cv(text)

            base_salary = 20000
            final_salary = base_salary + (total_score * 300)

            if total_score >= 85:
                recommendation = "Hire / Promotion Potential"
            elif total_score >= 70:
                recommendation = "Training Recommended"
            else:
                recommendation = "Not Recommended"

            candidate = {
                "Candidate": file.name,
                "Total Score": round(total_score, 2),
                "Salary SAR": round(final_salary, 0),
                "Recommendation": recommendation
            }

            candidate.update(scores)
            results.append(candidate)

            pdf_bytes = generate_pdf(
                file.name,
                scores,
                total_score,
                final_salary,
                recommendation
            )

            st.download_button(
                label=f"Download Scorecard - {file.name}",
                data=pdf_bytes,
                file_name=f"{file.name}_scorecard.pdf",
                mime="application/pdf"
            )

    df = pd.DataFrame(results)

    st.divider()
    st.subheader("Candidates Comparison")

    min_score = st.slider("Minimum Score", 0, 100, 0)
    filtered = df[df["Total Score"] >= min_score]

    st.dataframe(filtered, use_container_width=True)

    st.subheader("Skills Visualization")

    for candidate in filtered.to_dict(orient="records"):
        st.markdown(f"### {candidate['Candidate']}")
        skills = {
            k: candidate[k]
            for k in candidate
            if k not in ["Candidate", "Total Score", "Salary SAR", "Recommendation"]
        }
        skills_df = pd.DataFrame.from_dict(
            skills,
            orient="index",
            columns=["Score"]
        )
        st.bar_chart(skills_df)
