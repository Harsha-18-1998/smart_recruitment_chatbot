import os
import re
import pandas as pd
from docx import Document
from pdfminer.high_level import extract_text as extract_pdf_text

# ✅ Load skills directly from job_dataset.csv
job_data = pd.read_csv('data/job_dataset.csv')  # Adjust path if needed

# Get all skills into a flat list
skills_list = job_data['Skills'].dropna().apply(lambda x: [s.strip() for s in x.split(',')])
all_skills = sorted(set([skill for sublist in skills_list for skill in sublist]))

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_pdf_text(file_path)
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""

def extract_skills(text):
    extracted_skills = set()
    text = text.lower()
    for skill in all_skills:
        pattern = re.escape(skill.lower())
        if re.search(r'\b' + pattern + r'\b', text):
            extracted_skills.add(skill)
    return list(extracted_skills)
