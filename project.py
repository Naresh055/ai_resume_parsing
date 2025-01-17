import streamlit as st
import google.generativeai as genai
import re
import os
from PyPDF2 import PdfReader
import docx
import json
import pandas as pd

# Configure the Gemini API
genai.configure(api_key="AIzaSyDXZPliVK0af7yXTp-TdetcPiESOS4JX3U")

# Function to extract text from resumes
def extract_text(file):
    if file.type == "application/pdf":
        pdf_reader = PdfReader(file)
        return " ".join([page.extract_text() for page in pdf_reader.pages])
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        doc = docx.Document(file)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        st.error("Unsupported file format. Please upload a PDF or Word document.")
        return None

# Function to parse resume using Gemini AI
def parse_resume(text, job_title, required_skills):
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"""
            Parse the following resume for the job title `{job_title}` and match the required skills: {', '.join(required_skills)}.
    Return the following details:

    - Full Name
    - Email Address
    - Phone Number
    - Skills Match Percentage

    Resume Text: {text}

    Please ensure the response includes the following fields: "Full name", "Email address", "Phone number", and "Skills match percentage". If any field is missing or not found, use "N/A" as the value.
    """
        )
        print(response.text)
        # Try parsing the response text into JSON
        try:
            # Regular Expression to extract JSON from the response
            pattern = r'```json\s*(\{.*\})\s*```'
            # Find the match
            match = re.search(pattern, response.text, re.DOTALL)
            json_string = match.group(1)
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError:
            st.error("The response from Gemini AI could not be parsed into JSON. Please check the response format.")
            return None
    except Exception as e:
        st.error(f"Error with Gemini API: {e}")
        return None

# Streamlit App UI
def main():
    st.title("AI-Powered Resume Parser")
    st.write("Upload multiple resumes, specify job details, and extract actionable insights.")

    # Job Details Input
    job_title = st.text_input("Job Title", help="Enter the job title for matching (e.g., Data Scientist).")

    # Required Skills Input (comma-separated values)
    required_skills_input = st.text_area("Required Skills", help="Enter the required skills, separated by commas (e.g., Python, Machine Learning, SQL).")
    required_skills = [skill.strip() for skill in required_skills_input.split(",")]  # Convert to list

    # File Upload (multiple files allowed)
    uploaded_files = st.file_uploader("Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True)

    if st.button("Parse Resumes"):
        if uploaded_files and job_title and required_skills_input:
            all_results = []  # To store the results for each resume

            for uploaded_file in uploaded_files:
                resume_text = extract_text(uploaded_file)  # Assuming `extract_text` function extracts text from resume
                
                if resume_text:
                    st.info(f"Processing {uploaded_file.name}... This may take a moment.")
                    result = parse_resume(resume_text, job_title, required_skills)  # Assuming `parse_resume` parses the resume
                    
                    if result:
                        # Extract necessary details for the table
                        name = result["Full name"]
                        email = result["Email address"]
                        phone = result["Phone number"]
                        skills_match = result["Skills match percentage"]

                        # Append the data for this resume to the results list
                        all_results.append({
                            "Name": name,
                            "Email": email,
                            "Phone Number": phone,
                            "Skills Match Percentage": f"{skills_match}%"
                        })

            if all_results:
                # Convert the results list to DataFrame for table display
                df = pd.DataFrame(all_results)

                # Display the table
                st.success("Resumes parsed successfully!")
                st.table(df)  # Display the parsed data in a table format
        else:
            st.error("Please upload resumes and fill in the job details.")

# Run the Streamlit app
if __name__ == "__main__":
    main()