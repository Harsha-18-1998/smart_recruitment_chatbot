import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import TreebankWordTokenizer

nltk.download('stopwords')

tokenizer = TreebankWordTokenizer()

# Load skill dataset
skills_df = pd.read_csv("data/job_skills.csv")
all_skills = skills_df.iloc[:, 0].dropna().astype(str).str.lower().tolist()

def extract_skills(resume_text):
    stop_words = set(stopwords.words('english'))
    tokens = tokenizer.tokenize(resume_text.lower())
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]

    extracted_skills = [token for token in tokens if token in all_skills]

    return list(set(extracted_skills))
