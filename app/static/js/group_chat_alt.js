function loadMessages() {
    // fetch(`/get_messages/${contractId}`)
    fetch(`/get_messages/${contractId}?t=${new Date().getTime()}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to load messages");
            return response.json();
        })
        .then(messages => {
            const messagesList = document.getElementById('messages');
            messagesList.innerHTML = ""; // Clear existing messages
            messages.forEach(msg => {
                const li = document.createElement('li');
                li.style.display = 'flex';
                li.style.flexDirection = 'column';
                li.style.marginBottom = '10px';
                //check if message has image
                if (msg.media_url) {
                    li.classList.add('completion-message');
                    const img = document.createElement('img');
                    img.src = msg.media_url;
                    img.alt = "Image";
                    img.style.maxWidth = "200px"; // Adjust as needed
                    img.style.maxHeight = "200px";
                    const textNode = document.createTextNode(
                        msg.task_name ? `${msg.sender_name} completed task: ${msg.task_name}!` : `${msg.sender_name} sent an image`
                    );
                    // const textNode = document.createTextNode(`${msg.sender_name} completed task: ${msg.task_name} !`);
                    li.appendChild(textNode);
                    li.appendChild(img);
                } 

                // Check if the message has content
                if (msg.content) {
                    const textNode = document.createTextNode(`${msg.sender_name}: ${msg.content}`);
                    li.appendChild(textNode);
                }
                
                messagesList.appendChild(li);
            });
             // Ensure scrolling only after rendering is done
            setTimeout(() => {
                const chatWindow = document.getElementById('chat-window');
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }, 100);
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
socket.on('new_message', (msg) => {
    const messagesList = document.getElementById('messages');
    // Create a new <li> for the received message
    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.flexDirection = 'column';
    li.style.marginBottom = '10px';
    // Add the text if content is present
    if (msg.content) {
        const textNode = document.createTextNode(`${msg.sender_name}: ${msg.content}`);
        li.appendChild(textNode);
    }
    // Add the image if media_url is present
    if (msg.media_url) {
        li.classList.add('completion-message');
        const img = document.createElement('img');
        img.src = msg.media_url;
        img.alt = "Image";
        img.style.maxWidth = "200px";
        img.style.maxHeight = "200px";
        img.loading = "lazy";
        const textNode = document.createTextNode(`${msg.sender_name} completed task: ${msg.task_name} !`);
        li.appendChild(textNode);
        li.appendChild(img);
    }
    messagesList.appendChild(li);
   
    const chatWindow = document.getElementById('chat-window');
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // messagesList.scrollTop = messagesList.scrollHeight; // Auto-scroll to the latest message
});

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
