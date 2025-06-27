const apiUrl = "http://localhost:3001/api/grok";
const messagesDiv = document.getElementById("messages");
const input = document.getElementById("chat-input");
const button = document.getElementById("send-btn");

let messages = [];

function renderMessages() {
  messagesDiv.innerHTML = messages.map(
    (msg) => `<div><b>${msg.role}:</b> ${msg.content}</div>`
  ).join("");
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  const userMessage = { role: "user", content: text };
  messages.push(userMessage);
  renderMessages();
  input.value = "";
  button.disabled = true;

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages })
    });
    const data = await response.json();
    const botContent = data.choices?.[0]?.message?.content?.content || "No response";
    messages.push({ role: "assistant", content: botContent });
    renderMessages();
  } catch (err) {
    messages.push({ role: "assistant", content: "Error: " + err.message });
    renderMessages();
  }
  button.disabled = false;
}

button.onclick = sendMessage;

// Send on Enter key
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});