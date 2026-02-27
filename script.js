function toggleChat() {
    let chat = document.getElementById("chat-container");
    if (chat.style.display === "none" || chat.style.display === "") {
        chat.style.display = "flex";
    } else {
        chat.style.display = "none";
    }
}

function sendMessage() {
    let message = document.getElementById("message").value;

    fetch("/get_response", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        let chatbox = document.getElementById("chatbox");
        chatbox.innerHTML += "<p><b>You:</b> " + message + "</p>";
        chatbox.innerHTML += "<p><b>Bot:</b> " + data.response + "</p>";
        chatbox.innerHTML += "<p><i>Sentiment:</i> " + data.sentiment + "</p>";
    });

    document.getElementById("message").value = "";
}
