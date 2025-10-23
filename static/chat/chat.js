document.addEventListener("DOMContentLoaded", () => {
  const chatToggle = document.getElementById("chat-toggle");
  const chatBox = document.getElementById("chat-box");
  const chatClose = document.getElementById("chat-close");
  const chatMessages = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const chatSend = document.getElementById("chat-send");

  chatToggle.addEventListener("click", () => {
    chatBox.classList.toggle("hidden");
  });

  chatClose.addEventListener("click", () => {
    chatBox.classList.add("hidden");
  });

  chatSend.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    const div = document.createElement("div");
    div.className = "message";
    div.textContent = msg;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    chatInput.value = "";
  }
});
