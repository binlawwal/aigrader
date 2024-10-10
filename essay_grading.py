import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key='') #INSERT KEY INSODE HE QUOTES IN THE BRACKET
import os
from docx import Document

# Function to extract text from a .docx file
def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

# Function to parse the feedback into rubric components
def parse_feedback(feedback):
    # You can customize this based on how GPT provides the feedback
    # Here, I assume feedback includes specific scoring lines like 'Content Relevance: X/25'
    scores = {
        'Content Relevance': None,
        'Clarity and Organisation': None,
        'Originality and Creativity': None,
        'Research and Evidence': None,
        'Writing Style and Language': None,
        'Conclusion': None,
        'Overall Impression': None,
        'Total Score': None
    }
    
    lines = feedback.split('\n')
    for line in lines:
        for key in scores.keys():
            if key in line:
                score = line.split(':')[-1].strip()
                scores[key] = score

    # Assume that the last numerical value mentioned is the total score
    total_score = sum([int(score) for score in scores.values() if score])
    scores['Total Score'] = total_score
    return scores

# Function to grade the essay using GPT-4
def grade_essay(essay, guided_data, rubric):
    # Sample prompt for grading using GPT-4
    prompt = f"""
    You are an AI that grades essays based on a provided rubric, ensuring an unbiased evaluation while considering clarity, originality, organization, and depth of analysis.

    The topic of the essay is: "The Role of Technology in Bridging Nigeria’s Doctor-to-Patient Ratio."

    Consider the following attributes in your evaluation:

    Content Relevance: Ensure that the essay addresses the topic thoroughly and engages with the main issues effectively.
    Clarity and Organization: Look for logical flow and structure in the essay, ensuring that ideas are presented clearly and cohesively.
    Originality and Creativity: Assess the uniqueness of the perspective and insights presented, encouraging innovative thinking.
    Research and Evidence: Evaluate the depth of research, the use of credible sources, and the integration of data and examples to support claims.
    Writing Style and Language: Consider the appropriateness of language, grammar, and style, aiming for clear and engaging writing.
    Conclusion: Check if the conclusion effectively summarizes the main points and provides a strong final impression.
    Overall Impression: Formulate an overall assessment of the essay's impact, quality, and coherence.
    
    Here is the rubric for grading:
    {rubric}
    
    Here are examples of previously graded essays and their scores: {guided_data}
    
    Please grade the following essay and provide feedback:
    {essay}
    """

    # Call OpenAI's GPT-4 for grading
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "user", "content": prompt}
    ])
    return response.choices[0].message.content

# Function to export results to CSV
def export_to_csv(data):
    df = pd.DataFrame(data)
    df.to_csv('essay_grades.csv', index=False)

# Main function for the Streamlit app
def main():
    st.title("olukoAI Essay Grader by Effico")

    # Predefined rubric for grading
    rubric = """
    INSTRUCTIONS FOR GRADING
    1. Content and Relevance: 25
    2. Clarity and Organisation: 20
    3. Originality and Creativity: 15
    4. Research and Evidence: 20
    5. Writing Style and Language: 15
    6. Conclusion: 5
    7. Overall Impression: 10
    
    Total: 110
    """

    # State to store results
    if 'results' not in st.session_state:
        st.session_state.results = []

    # File uploader for example graded essays (DOCX)
    example_files = st.file_uploader("Upload 10 example graded essays (DOCX)", type=["docx"], accept_multiple_files=True)

    # File uploader for corresponding scores (DOCX)
    scores_file = st.file_uploader("Upload the DOCX file containing corresponding scores", type=["docx"])

    # File uploader for new essays to be graded (DOCX)
    new_files = st.file_uploader("Upload DOCX files with essays to be graded", type=["docx"], accept_multiple_files=True)

    # Grading button
    if st.button("Grade Essays"):
        if example_files and scores_file and new_files:
            # Extract scores from the scores file
            scores_text = extract_text_from_docx(scores_file)
            scores_lines = scores_text.splitlines()

            # Create a dictionary to match scores to participant names
            scores_dict = {}
            for line in scores_lines:
                if ':' in line:  # Assuming the format is "Participant Name: Score"
                    name, score = line.split(':', 1)
                    scores_dict[name.strip()] = score.strip()

            # Prepare guided data from example graded essays
            guided_data = {}
            for example_file in example_files:
                essay_text = extract_text_from_docx(example_file)
                participant_name = os.path.splitext(example_file.name)[0]  # Assuming name is file name
                if participant_name in scores_dict:
                    guided_data[participant_name] = {
                        'essay': essay_text,
                        'score': scores_dict[participant_name]
                    }

            # Combine guided essays with their scores
            guided_data_combined = "\n".join([f"{name}: {data['essay']} (Score: {data['score']})" for name, data in guided_data.items()])

            # Process each new essay
            for new_file in new_files:
                new_essay = extract_text_from_docx(new_file)
                new_participant_name = os.path.splitext(new_file.name)[0]  # Assuming name is file name
                st.write(f"Grading essay for: {new_participant_name}")

                # Grading the new essay using the provided rubric and example graded essays
                result = grade_essay(new_essay, guided_data_combined, rubric)

                # Parse feedback into rubric components
                parsed_scores = parse_feedback(result)

                # Store results in session state
                st.session_state.results.append({
                    'Participant Name': new_participant_name,
                    'Essay File': new_file.name,
                    **parsed_scores,
                    'Feedback': result,
                })

                # Display the grading feedback
                st.write("Feedback:")
                st.write(result)

            st.success("Grading completed for all uploaded essays.")
        else:
            st.error("Please upload all required files.")

    # Export results button always visible
    with st.sidebar:
        if st.button("Export All Results to CSV"):
            if st.session_state.results:
                export_to_csv(st.session_state.results)
                st.success("All results exported to essay_grades.csv")
            else:
                st.warning("No results to export.")

if __name__ == "__main__":
    main()