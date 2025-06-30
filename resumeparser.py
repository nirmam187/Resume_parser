# open terminal
# ollama serve
# ollama pull llama3.2




import ollama
import json
import streamlit as st
from pypdf import PdfReader
import regex 

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text

def ats_extractor(resume_data, job_description):
    prompt = f"""
    You are an expert AI system designed to perform resume parsing and job relevance evaluation. Also give the time 
    served by the person in each company in the Employment Details field.

    Task 1: Parse the following resume text and extract the following strictly in valid JSON format:
    {{
    "Full Name": "",
    "Email ID": "",
    "GitHub Portfolio": "",
    "LinkedIn ID": "",
    "Employment Details": "",
    "Technical Skills": [],
    "Soft Skills": []
    }}

    Task 2: Compare the resume's "Technical Skills", "Soft Skills", and "Employment Details" with the provided Job Description.
    Evaluate how well the resume matches the Job Description on these factors:
    - Technical Skills Match
    - Soft Skills Match
    - Relevant Companies/Employers Match (from Employment Details)

    Return a JSON object with this additional field:
    "Match Percentage": "xx%"   // Give an approximate percentage (0 to 100) of how well this resume matches the job description.
    below "Match Percentage" also give "Missing Skills" as a list of skills that are mentioned in the job description but not present in the resume.

    VERY IMPORTANT:
    - Return only a **single JSON object**.
    - DO NOT add explanations, descriptions, or extra text.
    - The JSON must include all fields from Task 1 and "Match Percentage" from Task 2 inside the **same JSON object**.

    Job Description:
    {job_description}

    Resume Text:
    {resume_data}
    """


    response = ollama.chat(
        model='llama3.2:latest',  # or 'llama3.2'
        messages=[{"role": "user", "content": prompt}]
    )

    output = response['message']['content']
    print("LLM Raw Output:\n", output)  # Debugging output

    # Extract JSON part using regex
    json_matches = regex.findall(r'\{(?:[^{}]|(?R))*\}', output, regex.DOTALL)
    if not json_matches:
        raise ValueError("No JSON content found in response.")

    for json_str in json_matches:
        try:
            extracted_data = json.loads(json_str)
            # Ensure required keys are present before accepting this JSON
            if all(k in extracted_data for k in ["Full Name", "Email ID", "Match Percentage"]):
                break
        except json.JSONDecodeError:
            continue

    return extracted_data

# -------- Main --------
pdf_path = 'viraj_resume.pdf'  # Replace with your PDF path
resume_text = extract_text_from_pdf(pdf_path)

# Example job description (can be dynamically input or read from a file)
job_description = '''
We are looking for a Software Engineer skilled in Python, Machine Learning, and Data Analysis.
The candidate should have problem-solving abilities, teamwork skills, and experience at top tech companies.
'''

parsed_data = ats_extractor(resume_text, job_description)
print("\nExtracted Resume Data with Match Percentage:\n", json.dumps(parsed_data, indent=4))



# ---------- Streamlit App ----------
st.set_page_config(page_title="Resume Matcher", layout="wide")

st.title("📄 Resume Matcher using AI (ATS)")
st.markdown("Upload a PDF resume and enter the job description. This tool will extract key info and compute a match score.")

# Input fields
uploaded_pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste Job Description Here", height=250)

#Run when inputs are available
if uploaded_pdf and job_description.strip():
    with st.spinner("Analyzing resume..."):
        try:
            resume_text = extract_text_from_pdf(uploaded_pdf)
            result = ats_extractor(resume_text, job_description)

            st.success("✅ Resume processed successfully!")
            st.subheader("🎯 Match Percentage:")
            st.markdown(f"**{result['Match Percentage']}**")

            st.subheader("📌 Missing Skills:")
            st.write(result.get("Missing Skills", []))

            st.subheader("📄 Extracted Resume Details:")
            st.json(result)

        except Exception as e:
            st.error(f"❌ Error: {e}")
else:
    st.info("📥 Please upload a PDF resume and enter a job description to begin.")