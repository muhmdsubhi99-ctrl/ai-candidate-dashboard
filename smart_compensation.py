import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io

st.set_page_config(page_title="Smart Compensation System", layout="centered")

st.title("💰 Smart Compensation System")

job_title = st.text_input("Job Title")
experience = st.slider("Years of Experience", 0, 20, 3)
country = st.text_input("Country")
skills = st.text_area("Key Skills (comma separated)")

def calculate_salary(job, exp, country, skills):
    base = 30000
    base += exp * 2500
    
    if "AI" in skills or "Machine Learning" in skills:
        base += 10000
    if "Python" in skills:
        base += 5000
    if country.lower() in ["usa", "uk", "germany"]:
        base *= 1.5
        
    return int(base)

if st.button("Calculate Compensation"):
    salary = calculate_salary(job_title, experience, country, skills)
    
    st.success(f"💵 Recommended Annual Salary: ${salary:,}")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Smart Compensation Report", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Job Title: {job_title}", styles["Normal"]))
    elements.append(Paragraph(f"Experience: {experience} years", styles["Normal"]))
    elements.append(Paragraph(f"Country: {country}", styles["Normal"]))
    elements.append(Paragraph(f"Skills: {skills}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Recommended Salary: ${salary:,}", styles["Heading2"]))
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf,
        file_name="compensation_report.pdf",
        mime="application/pdf"
    )
