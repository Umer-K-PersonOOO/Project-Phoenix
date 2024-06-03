document.addEventListener("DOMContentLoaded", function() {
    const sendButton = document.getElementById("send-button");
    const userInput = document.getElementById("user-input");
    const conversation = document.getElementById("conversation");
    const roleSelect = document.getElementById("role-select");
    const languageSelect = document.getElementById("language-select");

    sendButton.addEventListener("click", function() {
        const userMessage = userInput.value;
        const selectedRole = roleSelect.value;
        const selectedLanguage = languageSelect.value;
        if (userMessage.trim() === "") {
            return;
        }

        // Display user message
        const userDiv = document.createElement("div");
        userDiv.className = "user-message";
        userDiv.textContent = "User: " + userMessage;
        conversation.appendChild(userDiv);

        // Clear previous AI response
        const aiDiv = document.createElement("div");
        aiDiv.className = "ai-message";
        conversation.appendChild(aiDiv);

        // Send the POST request with role and user input
        fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                role: selectedRole,
                input: userMessage,
                language: selectedLanguage
            })
        }).then(() => {
            // Construct the EventSource URL with query parameters
            const eventSource = new EventSource(`/chat-stream?role=${selectedRole}&input=${encodeURIComponent(userMessage)}&language=${selectedLanguage}`);

            // Use EventSource to handle streaming response
            eventSource.onmessage = function(event) {
                aiDiv.textContent += event.data;
                // Scroll to the bottom of the conversation
                conversation.scrollTop = conversation.scrollHeight;
            };

            eventSource.onerror = function() {
                eventSource.close();
            };
        });

        // Clear input field
        userInput.value = "";
    });
});
