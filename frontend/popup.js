let currentTabUrl = "";

document.getElementById("sendBtn").addEventListener("click", async () => {
  const status = document.getElementById("status");
  status.innerText = "Parsing current page...";

  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) {
    status.innerText = "❌ No active tab.";
    return;
  }

  currentTabUrl = tab.url;

  fetch("http://localhost:8000/api/send_url", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url: currentTabUrl })
  })
    .then((res) => res.json())
    .then((data) => {
      status.innerText = "✅ Page parsed. Ask your question!";
      document.getElementById("qaSection").style.display = "block";
      addMessage("bot", "Page loaded! Ask me anything about it.");
    })
    .catch((err) => {
      console.error(err);
      status.innerText = "❌ Error parsing page.";
    });
});

document.getElementById("askBtn").addEventListener("click", async () => {
  const question = document.getElementById("questionInput").value;
  if (!question || !currentTabUrl) return;

  addMessage("user", question);

  const res = await fetch("http://localhost:8000/api/ask_question", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url: currentTabUrl, question })
  });

  const data = await res.json();
  addMessage("bot", data.answer || "❌ Error getting answer");
  document.getElementById("questionInput").value = "";
});

function addMessage(sender, text) {
  const chat = document.getElementById("chat");
  const msg = document.createElement("div");
  msg.className = `msg ${sender}`;
  msg.innerHTML = `<span class="${sender}">${sender === 'user' ? 'You' : 'AI'}:</span> ${text}`;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}
