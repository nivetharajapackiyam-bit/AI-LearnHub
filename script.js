
const quizForm = document.querySelector("form");

if (quizForm) {
    quizForm.addEventListener("submit", function () {

        const button = quizForm.querySelector("button");

        button.textContent = "Generating Questions...";
        button.disabled = true;

    });
}
// STUDENT DASHBOARD

function loadDashboard() {
    let history = JSON.parse(localStorage.getItem("quizHistory")) || [];

    document.getElementById("total-quizzes").textContent = history.length;

    if (history.length === 0) {
        document.getElementById("average-score").textContent = "0%";
        document.getElementById("best-score").textContent = "0%";
        document.getElementById("quiz-history").innerHTML =
            "<p>No quiz attempts yet.</p>";
        return;
    }

    let total = history.reduce((sum, quiz) => sum + quiz.percentage, 0);
    let average = Math.round(total / history.length);
    let best = Math.max(...history.map(quiz => quiz.percentage));

    document.getElementById("average-score").textContent = average + "%";
    document.getElementById("best-score").textContent = best + "%";

    document.getElementById("quiz-history").innerHTML = history
        .slice()
        .reverse()
        .map((quiz, index) => `
            <div class="dashboard-card">
                <h4>Quiz ${history.length - index}</h4>
                <p>Score: ${quiz.score} / ${quiz.total}</p>
                <p>Percentage: ${quiz.percentage}%</p>
                <small>${quiz.date}</small>
            </div>
        `).join("");
}

document.addEventListener("DOMContentLoaded", loadDashboard);
// CLEAR QUIZ HISTORY

function clearQuizHistory() {
    const confirmDelete = confirm(
        "Are you sure you want to delete all quiz history?"
    );

    if (confirmDelete) {
        localStorage.removeItem("quizHistory");
        loadDashboard();
        alert("Quiz history cleared successfully!");
    }
}

// STUDENT PERFORMANCE CHART

let performanceChart = null;

function showPerformanceChart() {
    const canvas = document.getElementById("performanceChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const history = JSON.parse(
        localStorage.getItem("quizHistory") || "[]"
    );

    const labels = history.map((quiz, index) => "Quiz " + (index + 1));

    const scores = history.map(quiz => quiz.percentage);

    // Remove old chart before creating a new one
    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(canvas, {
        type: "bar",

        data: {
            labels: labels,

            datasets: [{
                label: "Quiz Score (%)",
                data: scores,
                backgroundColor: "#8172e9",
                borderColor: "#6254d9",
                borderWidth: 1,
                borderRadius: 8
            }]
        },

        options: {
            responsive: true,

            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: "Percentage"
                    }
                },

                x: {
                    title: {
                        display: true,
                        text: "Quiz Attempts"
                    }
                }
            },

            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

// Load chart when dashboard opens
document.addEventListener("DOMContentLoaded", showPerformanceChart);
