
from pathlib import Path
import json
import markdown

from pypdf import PdfReader
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# INITIAL SETUP
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

client = OpenAI()


# ==================================================
# COMMON FUNCTION: QUESTION COUNT
# ==================================================

def get_question_count():

    try:
        num_questions = int(
            request.form.get("num_questions", "5")
        )

        if num_questions < 1 or num_questions > 30:
            raise ValueError()

        return num_questions

    except (ValueError, TypeError):
        raise ValueError(
            "Please enter a number between 1 and 30."
        )


# ==================================================
# COMMON FUNCTION: VALIDATE MCQ QUESTIONS
# ==================================================

def validate_mcq_questions(quiz_data, num_questions):

    questions = quiz_data["questions"]

    if not isinstance(questions, list):
        raise ValueError("Questions must be a list.")

    if len(questions) != num_questions:
        raise ValueError("Incorrect question count.")

    for question in questions:

        if not isinstance(question, dict):
            raise ValueError("Invalid question.")

        if not question.get("question"):
            raise ValueError("Question is missing.")

        options = question.get("options")

        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("Each MCQ needs four options.")

        if question.get("answer") not in options:
            raise ValueError("Correct answer must match an option.")

        if not question.get("explanation"):
            raise ValueError("Explanation is missing.")

        question["type"] = "MCQ"

    return questions


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():

    return render_template("index.html")


# ==================================================
# AI QUIZ GENERATOR
# ==================================================

@app.route("/generate", methods=["POST"])
def generate():

    topic = request.form.get("topic", "").strip()

    difficulty = request.form.get(
        "difficulty", "Easy"
    )

    question_type = request.form.get(
        "question_type", "Multiple Choice"
    )

    if not topic:
        return "Please enter a topic."

    if question_type not in [
        "Multiple Choice",
        "Short Answer",
        "Long Answer"
    ]:
        return "Invalid question type."

    try:
        num_questions = get_question_count()

    except ValueError as error:
        return str(error)

    if question_type == "Multiple Choice":

        format_instructions = """
        Generate MCQ questions.
        Each question must contain exactly four options.
        The answer must exactly match one option.
        """

    elif question_type == "Short Answer":

        format_instructions = """
        Generate short-answer questions.
        Do not generate options.
        Give a correct model answer.
        """

    else:

        format_instructions = """
        Generate long-answer descriptive questions.
        Do not generate options.
        Give a detailed model answer.
        """

    prompt = f"""
    You are an expert educational question generator.

    Topic: {topic}
    Difficulty: {difficulty}
    Number of Questions: {num_questions}
    Question Type: {question_type}

    Generate exactly {num_questions} questions.

    {format_instructions}

    Every question must contain:
    - question
    - type
    - answer
    - explanation

    For MCQ questions, also include four options.

    Return ONLY valid JSON:

    {{
      "questions": [
        {{
          "question": "Question text",
          "type": "{question_type}",
          "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
          ],
          "answer": "Correct answer",
          "explanation": "Explanation"
        }}
      ]
    }}

    Omit options for written questions.
    Return valid JSON only.
    """

    try:

        response = client.responses.create(
            model="gpt-6-luna",
            input=prompt
        )

        quiz_data = json.loads(response.output_text)
        questions = quiz_data["questions"]

        if not isinstance(questions, list):
            raise ValueError("Invalid question list.")

        if len(questions) != num_questions:
            raise ValueError("Incorrect question count.")

        for question in questions:

            if not isinstance(question, dict):
                raise ValueError("Invalid question.")

            if not question.get("question"):
                raise ValueError("Question is missing.")

            if not question.get("answer"):
                raise ValueError("Answer is missing.")

            if not question.get("explanation"):
                raise ValueError("Explanation is missing.")

            question["type"] = (
                "MCQ" if question_type == "Multiple Choice"
                else question_type
            )

            if question_type == "Multiple Choice":

                options = question.get("options")

                if not isinstance(options, list) or len(options) != 4:
                    raise ValueError("Invalid MCQ options.")

                if question["answer"] not in options:
                    raise ValueError("Answer does not match options.")

            else:
                question.pop("options", None)

        return render_template(
            "quiz.html",
            questions=questions
        )

    except Exception as error:

        print("Quiz generation error:", error)

        return "Unable to generate quiz. Please try again."


# ==================================================
# AI QUESTION PAPER GENERATOR
# ==================================================

@app.route("/generate-paper", methods=["POST"])
def generate_paper():

    subject = request.form.get(
        "subject", ""
    ).strip()

    marks = request.form.get("marks", "50")

    difficulty = request.form.get(
        "difficulty", "Medium"
    )

    paper_type = request.form.get(
        "paper_type", "Model Exam"
    )

    question_format = request.form.get(
        "question_format", "Mixed"
    )

    if not subject:
        return "Please enter a subject."

    if marks not in ["25", "50", "75", "100"]:
        return "Invalid marks selection."

    if question_format == "MCQ":

        format_instructions = """
        Create only Multiple Choice Questions.
        Each question must have four options.
        Include a correct answer key.
        """

    elif question_format == "Short Answer":

        format_instructions = """
        Create only short-answer questions.
        Include a separate answer key.
        """

    elif question_format == "Long Answer":

        format_instructions = """
        Create only long-answer questions.
        Include detailed model answers separately.
        """

    else:

        format_instructions = """
        Create three sections:
        Section A: MCQ
        Section B: Short Answer
        Section C: Long Answer
        Include a separate answer key.
        """

    prompt = f"""
    Create a professional university examination question paper.

    Subject: {subject}
    Total Marks: {marks}
    Difficulty: {difficulty}
    Examination Type: {paper_type}
    Question Format: {question_format}

    Requirements:

    1. Start with UNIVERSITY EXAMINATION.
    2. Include subject name and maximum marks.
    3. Include examination duration.
    4. Include clear examination instructions.
    5. Organize questions into sections.
    6. Number all questions sequentially.
    7. Show marks for every question.
    8. Ensure total marks equal exactly {marks}.
    9. Keep MCQ options on separate lines.
    10. Avoid duplicate questions.
    11. Put the answer key in a separate final section.
    12. Use standard Markdown formatting.
    13. Do not use HTML tags or code blocks.

    {format_instructions}

    Return only the question paper.
    """

    try:

        response = client.responses.create(
            model="gpt-6-luna",
            input=prompt
        )

        paper = response.output_text

        # Fix escaped Markdown symbols
        paper = paper.replace(r"\*\*", "**")
        paper = paper.replace(r"\#", "#")

        # Convert Markdown into HTML
        paper_html = markdown.markdown(
            paper,
            extensions=["tables", "fenced_code"]
        )

        return render_template(
            "paper.html",
            paper_html=paper_html
        )

    except Exception as error:

        print("Question paper error:", error)

        return "Unable to generate question paper."


# ==================================================
# PDF QUIZ GENERATOR
# ==================================================

@app.route("/generate-from-pdf", methods=["POST"])
def generate_from_pdf():

    pdf_file = request.files.get("pdf_file")

    difficulty = request.form.get(
        "difficulty", "Easy"
    )

    try:
        num_questions = get_question_count()

    except ValueError as error:
        return str(error)

    if not pdf_file or not pdf_file.filename.lower().endswith(".pdf"):
        return "Please upload a valid PDF."

    try:

        reader = PdfReader(pdf_file.stream)

        if reader.is_encrypted:
            return "Please upload an unlocked PDF."

        pdf_text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        if not pdf_text.strip():
            return "No readable text found in the PDF."

        pdf_text = pdf_text[:20000]

        prompt = f"""
        Create exactly {num_questions} MCQ questions
        using ONLY the following study material.

        Difficulty: {difficulty}

        STUDY MATERIAL:
        {pdf_text}

        Return ONLY valid JSON:

        {{
          "questions": [
            {{
              "question": "Question text",
              "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
              ],
              "answer": "Exact correct option",
              "explanation": "Short explanation"
            }}
          ]
        }}

        Rules:
        - Use only the study material.
        - Every question needs four options.
        - Answer must match one option.
        - Return valid JSON only.
        """

        response = client.responses.create(
            model="gpt-6-luna",
            input=prompt
        )

        quiz_data = json.loads(response.output_text)

        questions = validate_mcq_questions(
            quiz_data,
            num_questions
        )

        return render_template(
            "quiz.html",
            questions=questions
        )

    except Exception as error:

        print("PDF generation error:", error)

        return "Unable to generate PDF quiz."


# ==================================================
# TEXT QUIZ GENERATOR
# ==================================================

@app.route("/generate-from-text", methods=["POST"])
def generate_from_text():

    study_text = request.form.get(
        "study_text", ""
    ).strip()

    difficulty = request.form.get(
        "difficulty", "Easy"
    )

    try:
        num_questions = get_question_count()

    except ValueError as error:
        return str(error)

    if not study_text:
        return "Please paste your study material."

    study_text = study_text[:20000]

    prompt = f"""
    You are an AI quiz generator.

    Create exactly {num_questions} MCQ questions
    using ONLY the supplied study material.

    Difficulty: {difficulty}

    STUDY MATERIAL:
    {study_text}

    Return ONLY valid JSON:

    {{
      "questions": [
        {{
          "question": "Question text",
          "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
          ],
          "answer": "Exact correct option",
          "explanation": "Short explanation"
        }}
      ]
    }}

    Rules:
    - Generate exactly {num_questions} questions.
    - Each question must have four options.
    - Answer must exactly match one option.
    - Use only supplied study material.
    - Return valid JSON only.
    """

    try:

        response = client.responses.create(
            model="gpt-6-luna",
            input=prompt
        )

        quiz_data = json.loads(response.output_text)

        questions = validate_mcq_questions(
            quiz_data,
            num_questions
        )

        return render_template(
            "quiz.html",
            questions=questions
        )

    except Exception as error:

        print("Text quiz error:", error)

        return "Unable to generate text quiz."


# ==================================================
# AI WRITTEN ANSWER EVALUATION
# ==================================================

@app.route("/evaluate-answers", methods=["POST"])
def evaluate_answers():

    data = request.get_json(silent=True) or {}

    answers = data.get("answers", [])

    if not isinstance(answers, list) or not answers:
        return jsonify({
            "error": "No answers submitted."
        }), 400

    if len(answers) > 30:
        return jsonify({
            "error": "Maximum 30 answers allowed."
        }), 400

    for item in answers:

        if not isinstance(item, dict):
            return jsonify({
                "error": "Invalid answer data."
            }), 400

        for key in [
            "question",
            "model_answer",
            "student_answer"
        ]:

            if (
                not isinstance(item.get(key), str)
                or not item[key].strip()
            ):
                return jsonify({
                    "error": f"Missing or invalid {key}."
                }), 400

            if len(item[key]) > 10000:
                return jsonify({
                    "error": "Answer content is too long."
                }), 400

    prompt = f"""
    You are an educational answer evaluator.

    Evaluate each student's answer using the model answer.

    Give marks out of 10 for each answer.

    Evaluate:
    1. Conceptual understanding
    2. Correctness
    3. Relevant points
    4. Clarity

    Accept different wording if the meaning is correct.
    Do not award marks for irrelevant information.

    QUESTIONS AND ANSWERS:

    {json.dumps(answers, ensure_ascii=False)}

    Return ONLY valid JSON:

    {{
      "evaluations": [
        {{
          "question": "Question text",
          "score": 8,
          "max_score": 10,
          "feedback": "Good explanation.",
          "suggestion": "Include more important points."
        }}
      ]
    }}

    Return one evaluation for every answer.
    Return valid JSON only.
    """

    try:

        response = client.responses.create(
            model="gpt-6-luna",
            input=prompt
        )

        result = json.loads(response.output_text)

        evaluations = result["evaluations"]

        if not isinstance(evaluations, list):
            raise ValueError("Invalid evaluation format.")

        if len(evaluations) != len(answers):
            raise ValueError("Incorrect evaluation count.")

        for evaluation in evaluations:

            score = evaluation.get("score")

            if (
                not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not 0 <= score <= 10
            ):
                raise ValueError("Invalid evaluation score.")

            if not isinstance(evaluation.get("feedback"), str):
                raise ValueError("Missing feedback.")

            if not isinstance(evaluation.get("suggestion"), str):
                raise ValueError("Missing suggestion.")

            evaluation["max_score"] = 10

        return jsonify({
            "evaluations": evaluations
        })

    except Exception as error:

        print("Answer evaluation error:", error)

        return jsonify({
            "error": "Unable to evaluate answers. Please try again."
        }), 500


# ==================================================
# RUN FLASK APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)
