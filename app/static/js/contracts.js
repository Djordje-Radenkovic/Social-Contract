function openFileUpload(taskId) {
    // Store the task ID or process it if needed
    console.log("Task ID:", taskId);

    // Trigger the hidden file input
    document.getElementById('fileInput').click();
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        console.log("File selected:", file.name);

        // You can upload the file to your server here using AJAX or fetch
        // Example:
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log("File uploaded successfully:", data);
        })
        .catch(error => {
            console.error("Error uploading file:", error);
        });
    }
}
