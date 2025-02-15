function getFixedColor(username) {
    const hash = username.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const colors = ['#FF5733', '#33FF57', '#3357FF', '#F0A500', '#9C33FF'];
    return colors[hash % colors.length]; // Pick a color based on the hash
}

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
                li.style.marginBottom = '0px';

                //check if message has image
                if (msg.media_url) {
                    li.classList.add('completion-message');
                    const img = document.createElement('img');
                    img.src = msg.media_url;
                    img.alt = "Image";
                    img.style.maxWidth = "200px"; // Adjust as needed
                    img.style.maxHeight = "200px";
                    img.style.marginTop = "5px";

                    // Add load event listener to each image
                    let messageText;
                    const userColor = getFixedColor(msg.sender_name);
                    const usernameSpan = `<span style="color: ${userColor}; font-weight: bold;">${msg.sender_name}</span>`;
                    if (msg.ai_verified === false) {
                        messageText = `❌ ${usernameSpan} failed AI verification for task: ${msg.task_name}`;
                    } else {
                        messageText = `✅ ${usernameSpan} completed task: ${msg.task_name}!`;
                    }
                    // const textNode = document.createTextNode(messageText);
                    const textNode = document.createElement('span');
                    textNode.innerHTML = messageText;

                    // const textNode = document.createTextNode(
                    //     msg.task_name ? `${msg.sender_name} completed task: ${msg.task_name}!` : `${msg.sender_name} sent an image`
                    // );
                    // const textNode = document.createTextNode(`${msg.sender_name} completed task: ${msg.task_name} !`);
                    li.appendChild(textNode);
                    li.appendChild(img);
                } 


                // Check if the message has content
                // if (msg.content) {
                //     const textNode = document.createTextNode(`${msg.sender_name}: ${msg.content}`);
                //     li.appendChild(textNode);
                // }
                if (msg.content) {
                    const userColor = getFixedColor(msg.sender_name);
                    const messageHTML = `<span style="color: ${userColor}; font-weight: bold;">${msg.sender_name}:</span> ${msg.content}`;
                    const messageElement = document.createElement('span');
                    messageElement.innerHTML = messageHTML;
                    li.appendChild(messageElement);
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
        const userColor = getFixedColor(msg.sender_name);
        const messageHTML = `<span style="color: ${userColor}; font-weight: bold;">${msg.sender_name}:</span> ${msg.content}`;
        const messageElement = document.createElement('span');
        messageElement.innerHTML = messageHTML;
        li.appendChild(messageElement);
    }
    // if (msg.content) {
    //     const textNode = document.createTextNode(`${msg.sender_name}: ${msg.content}`);
    //     li.appendChild(textNode);
    // }
    // Add the image if media_url is present
    if (msg.media_url) {
        li.classList.add('completion-message');
        const img = document.createElement('img');
        img.src = msg.media_url;
        img.alt = "Image";
        img.style.maxWidth = "200px";
        img.style.maxHeight = "200px";
        img.loading = "lazy";

        const userColor = getFixedColor(msg.sender_name);
        const messageHTML = `<span style="color: ${userColor}; font-weight: bold;">${msg.sender_name}</span> completed task: ${msg.task_name}`;
        const messageElement = document.createElement('span');
        messageElement.innerHTML = messageHTML;
        li.appendChild(messageElement);

        // const textNode = document.createTextNode(`✅ ${msg.sender_name} completed task: ${msg.task_name} !`);
        // li.appendChild(textNode);
        li.appendChild(img);
    }

    messagesList.appendChild(li);
    
    const chatWindow = document.getElementById('chat-window');
    chatWindow.scrollTop = chatWindow.scrollHeight;

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


