
// Load existing messages (initial load)
// function loadMessages() {
//     fetch(`/get_messages/${contractId}`)
//         .then(response => {
//             if (!response.ok) throw new Error("Failed to load messages");
//             return response.json();
//         })
//         .then(messages => {
//             const messagesList = document.getElementById('messages');
//             messagesList.innerHTML = ""; // Clear existing messages
//             messages.forEach(msg => {
//                 const li = document.createElement('li');
//                 li.textContent = `${msg.sender_name}: ${msg.content}`;
//                 messagesList.appendChild(li);
//             });
//             messagesList.scrollTop = messagesList.scrollHeight;
//         })
//         .catch(error => {
//             console.error("Error fetching messages:", error);
//         });
// }
function loadMessages() {
    fetch(`/get_messages/${contractId}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to load messages");
            return response.json();
        })
        .then(messages => {
            const messagesList = document.getElementById('messages');
            messagesList.innerHTML = ""; // Clear existing messages
            messages.forEach(msg => {
                const li = document.createElement('li');
                if (msg.media_url) {
                    const img = document.createElement('img');
                    img.src = msg.media_url;
                    img.alt = "Uploaded Image";
                    img.style.maxWidth = "200px"; // Adjust as needed
                    li.appendChild(img);
                } else {
                    li.textContent = `${msg.sender_name}: ${msg.content}`;
                }
                messagesList.appendChild(li);
            });
            messagesList.scrollTop = messagesList.scrollHeight;
        })
        .catch(error => {
            console.error("Error fetching messages:", error);
        });
}

loadMessages(); // Fetch existing messages on page load

// WebSocket connection
const socket = io();

// Join the contract room
socket.emit('join', { contract_id: contractId });

//Handle new messages in real-time
socket.on('new_message', (msg) => {
    const messagesList = document.getElementById('messages');
    const li = document.createElement('li');
    li.textContent = `${msg.sender_name}: ${msg.content}`;
    messagesList.appendChild(li);
    messagesList.scrollTop = messagesList.scrollHeight; // Auto-scroll to the latest message
});



// Send a new message
document.getElementById('send-button').addEventListener('click', () => {
    const messageText = document.getElementById('message-text').value.trim();
    if (messageText === "") return;

    socket.emit('send_message', {
        contract_id: contractId,
        sender_id: userId,
        content: messageText
    });
    document.getElementById('message-text').value = ""; // Clear the input field
});
//////////////////////////////////////////////

//////////////////////////////////////////////


// Handle WebSocket connection errors
socket.on('connect_error', () => {
    console.error("WebSocket connection failed!");
});

document.getElementById('accept-button')?.addEventListener('click', () => {
    fetch(`/contract/${contractId}/accept`, { method: 'POST' })
        .then(response => {
            if (response.ok) {
                location.reload(); // Reload the page to reflect changes
            } else {
                alert("Error accepting invitation");
            }
        });
});

document.getElementById('decline-button')?.addEventListener('click', () => {
    fetch(`/contract/${contractId}/decline`, { method: 'POST' })
        .then(response => {
            if (response.ok) {
                window.location.href = "/"; // Redirect to the contracts list
            } else {
                alert("Error declining invitation");
            }
        });
});

fetch(`/mark_message_seen/${contractId}`, { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);  // Debugging feedback
    })
    .catch(error => console.error('Error marking message as seen:', error));


