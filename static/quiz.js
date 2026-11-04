
// ==================================================
// AI LEARNHUB - QUIZ JAVASCRIPT
// MCQ + SHORT ANSWER + LONG ANSWER
// ==================================================

let timeLeft = 600; // 10 minutes
let timerInterval;
let submitted = false;


// ==================================================
// ELEMENTS
// ==================================================

const quizForm = document.getElementById("quiz-form");
const timerElement = document.getElementById("timer");
const resultElement = document.getElementById("result");

const questionCards = document.querySelectorAll(".question-card");


// ==================================================
// TIMER
// ==================================================

function startTimer() {

    if (!timerElement) return;

    timerInterval = setInterval(() => {

        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;

        timerElement.textContent =
            `Time Left: ${minutes}:${seconds.toString().padStart(2, "0")}`;

        if (timeLeft <= 0) {

            clearInterval(timerInterval);

            if (!submitted) {
                submitQuiz(true);
            }

        } else {

            timeLeft--;

        }

    }, 1000);
}

startTimer();


// ==================================================
// HELPER: ESCAPE HTML
// ==================================================

function escapeHTML(value) {

    return String(value ?? "").replace(/[&<>"']/g, character => {

        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return entities[character];

    });
}


// ==================================================
// SUBMIT QUIZ
// ==================================================

async function submitQuiz(autoSubmit = false) {

    if (submitted) return;

    if (!autoSubmit) {

        const confirmed = confirm(
            "Are you sure you want to submit your quiz?"
        );

        if (!confirmed) return;

    }

    submitted = true;

    clearInterval(timerInterval);

    // Disable all answer inputs

    const allInputs = quizForm.querySelectorAll("input, textarea");

    allInputs.forEach(input => {

        input.disabled = true;

        input.required = false;

    });

    const submitButton = document.getElementById("submit-btn");

    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Evaluating answers...";
    }

    resultElement.hidden = false;

    resultElement.innerHTML = `
        <h2>Evaluating Your Answers...</h2>
        <p>Please wait while AI checks your answers.</p>
    `;

    const writtenAnswers = [];

    const questionResults = [];

    let totalPercentage = 0;

    let mcqCorrect = 0;

    let writtenCount = 0;

    const totalQuestions = questionCards.length;


    // ==================================================
    // CHECK EACH QUESTION
    // ==================================================

    questionCards.forEach((card, index) => {

        const questionText =
            card.querySelector("h3")?.textContent.trim() || "";

        const correctAnswer =
            card.querySelector(".correct-answer")?.value || "";

        const questionType =
            card.querySelector(".question-type-value")?.value || "MCQ";


        // ----------------------------------------------
        // MCQ EVALUATION
        // ----------------------------------------------

        if (questionType === "MCQ") {

            const selected = card.querySelector(
                'input[type="radio"]:checked'
            );

            const studentAnswer = selected
                ? selected.value
                : "";

            const isCorrect =
                studentAnswer.trim() === correctAnswer.trim();

            if (isCorrect) {
                mcqCorrect++;
                totalPercentage += 100;
            }

            questionResults.push({

                type: "MCQ",

                question: questionText,

                studentAnswer: studentAnswer || "Not answered",

                correctAnswer: correctAnswer,

                isCorrect: isCorrect,

                explanation:
                    card.querySelector(".explanation")?.textContent.trim() || ""

            });

        }


        // ----------------------------------------------
        // WRITTEN ANSWER COLLECTION
        // ----------------------------------------------

        else {

            const answerInput = card.querySelector(".written-answer");

            const studentAnswer = answerInput
                ? answerInput.value.trim()
                : "";

            writtenCount++;

            writtenAnswers.push({

                question: questionText,

                model_answer: correctAnswer,

                student_answer: studentAnswer || "Not answered",

                questionIndex: index

            });

        }

    });


    // ==================================================
    // AI EVALUATION OF WRITTEN ANSWERS
    // ==================================================

    let evaluations = [];

    if (writtenAnswers.length > 0) {

        const apiAnswers = writtenAnswers.map(item => ({

            question: item.question,

            model_answer: item.model_answer,

            student_answer: item.student_answer

        }));

        try {

            const response = await fetch("/evaluate-answers", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    answers: apiAnswers

                })

            });

            const data = await response.json();

            if (!response.ok) {

                throw new Error(
                    data.error || "AI evaluation failed."
                );

            }

            evaluations = data.evaluations;

            if (
                !Array.isArray(evaluations) ||
                evaluations.length !== writtenAnswers.length
            ) {
                throw new Error("Invalid evaluation response.");
            }

            evaluations.forEach(evaluation => {

                const percentage =
                    (Number(evaluation.score) / 10) * 100;

                totalPercentage += percentage;

            });

        } catch (error) {

            console.error("Evaluation error:", error);

            resultElement.innerHTML = `
                <h2>Evaluation Failed</h2>
                <p>${escapeHTML(error.message)}</p>
                <p>Please check your Flask server and try again.</p>
            `;

            if (submitButton) {
                submitButton.textContent = "Evaluation failed";
            }

            // Allow retry after an evaluation error.
            submitted = false;

            allInputs.forEach(input => {
                input.disabled = false;
            });

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Submit Quiz";
            }

            return;

        }

    }


    // ==================================================
    // CALCULATE FINAL SCORE
    // ==================================================

    const percentage = totalQuestions > 0
        ? Math.round(totalPercentage / totalQuestions)
        : 0;

    const scoreEquivalent =
        Math.round((percentage / 100) * totalQuestions * 100) / 100;


    // ==================================================
    // SAVE RESULT IN LOCAL STORAGE
    // ==================================================

    const quizHistory = JSON.parse(
        localStorage.getItem("quizHistory") || "[]"
    );

    quizHistory.push({

        score: scoreEquivalent,

        total: totalQuestions,

        percentage: percentage,

        date: new Date().toLocaleDateString()

    });

    localStorage.setItem(
        "quizHistory",
        JSON.stringify(quizHistory)
    );


    // ==================================================
    // DISPLAY RESULTS
    // ==================================================

    let resultHTML = `

        <h2>Quiz Completed!</h2>

        <div class="score-summary">

            <h3>Your Score: ${percentage}%</h3>

            <p>Total Questions: ${totalQuestions}</p>

            <p>Correct MCQs: ${mcqCorrect}</p>

            <p>Written Questions: ${writtenCount}</p>

        </div>

        <hr>

        <h3>Detailed Results</h3>

    `;


    let evaluationIndex = 0;


    // ==================================================
    // INDIVIDUAL QUESTION FEEDBACK
    // ==================================================

    questionCards.forEach((card, index) => {

        const questionText =
            card.querySelector("h3")?.textContent.trim() || "";

        const questionType =
            card.querySelector(".question-type-value")?.value || "MCQ";


        // ----------------------------------------------
        // MCQ RESULT
        // ----------------------------------------------

        if (questionType === "MCQ") {

            const result = questionResults.find(
                item => item.type === "MCQ" &&
                    item.question === questionText
            );

            resultHTML += `

                <div class="answer-feedback">

                    <h4>Question ${index + 1}</h4>

                    <p>${escapeHTML(questionText)}</p>

                    <p>
                        Your Answer:
                        ${escapeHTML(result.studentAnswer)}
                    </p>

                    <p>
                        Correct Answer:
                        ${escapeHTML(result.correctAnswer)}
                    </p>

                    <p>
                        Result:
                        <strong>
                            ${result.isCorrect ? "Correct" : "Incorrect"}
                        </strong>
                    </p>

                    <p>
                        Explanation:
                        ${escapeHTML(result.explanation)}
                    </p>

                </div>

            `;

        }


        // ----------------------------------------------
        // WRITTEN ANSWER RESULT
        // ----------------------------------------------

        else {

            const original = writtenAnswers[evaluationIndex];

            const evaluation = evaluations[evaluationIndex];

            evaluationIndex++;

            resultHTML += `

                <div class="answer-feedback">

                    <h4>Question ${index + 1}</h4>

                    <p>${escapeHTML(original.question)}</p>

                    <p>
                        Your Answer:
                        ${escapeHTML(original.student_answer)}
                    </p>

                    <p>
                        AI Marks:
                        <strong>
                            ${escapeHTML(evaluation.score)} / 10
                        </strong>
                    </p>

                    <p>
                        Feedback:
                        ${escapeHTML(evaluation.feedback)}
                    </p>

                    <p>
                        Improvement Suggestion:
                        ${escapeHTML(evaluation.suggestion)}
                    </p>

                </div>

            `;

        }

    });


    resultHTML += `

        <button type="button" onclick="downloadQuizPDF()">
            Download Quiz Result
        </button>

        <button type="button" onclick="window.location.href='/'">
            Back to Home
        </button>

    `;

    resultElement.innerHTML = resultHTML;

    resultElement.scrollIntoView({
        behavior: "smooth"
    });

    if (submitButton) {
        submitButton.textContent = "Quiz Submitted";
    }

}


// ==================================================
// CONNECT SUBMIT BUTTON
// ==================================================

if (quizForm) {

    quizForm.addEventListener("submit", function(event) {

        event.preventDefault();

        submitQuiz(false);

    });

}


// ==================================================
// DOWNLOAD QUIZ RESULT AS PDF
// ==================================================

function downloadQuizPDF() {

    window.print();

}

window.downloadQuizPDF = downloadQuizPDF;
