const form = document.querySelector("#workflow-form");
const status = document.querySelector("#status");
const summary = document.querySelector("#summary");
const rounds = document.querySelector("#rounds");
const error = document.querySelector("#error");
const button = document.querySelector("#run");

function textElement(tag, value, className = "") {
  const el = document.createElement(tag);
  el.textContent = String(value);
  el.className = className;
  return el;
}

function render(result) {
  rounds.replaceChildren();
  status.textContent = result.stop_reason === "condition_met" ? "조건 충족" : "반복 상한 도달";
  summary.textContent = `총 ${result.rounds.length}회 실행 / 최종 승인: ${result.last_round.approved ? "예" : "아니요"}`;
  result.rounds.forEach((round, index) => {
    const card = textElement("div", "", "round");
    const h = textElement("h3", `회차 ${index + 1}`);
    h.append(textElement("span", round.approved ? "승인" : "검토 중", round.approved ? "ok" : "no"));
    const details = document.createElement("dl");
    for (const key of ["draft", "score", "approved"]) {
      details.append(textElement("dt", key), textElement("dd", round[key]));
    }
    card.append(h, details);
    rounds.append(card);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.textContent = "";
  button.disabled = true;
  status.textContent = "실행 중";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: document.querySelector("#topic").value,
        max_rounds: Number(document.querySelector("#max_rounds").value)
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "HTTP error");
    render(data.result);
  } catch (e) {
    status.textContent = "오류";
    error.textContent = e.message;
  } finally {
    button.disabled = false;
  }
});
