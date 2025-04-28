let selectedImage = null; // Store the selected image file
let allUsers = []; // Global variable to store all users

// Trigger the file input click when the camera icon is clicked
function openFileUpload(taskId) {
    console.log("Task ID (if applicable):", taskId);
    document.getElementById('fileInput').click();
}

// Handle image selection and store the file
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        selectedImage = file; // Save the selected file
        console.log("Selected Image:", file.name);

        // Optionally preview the image
        const reader = new FileReader();
        reader.onload = (e) => {
            document.querySelector('.camera').style.backgroundImage = `url(${e.target.result})`;
            document.querySelector('.camera').style.backgroundSize = 'cover';
            document.querySelector('.camera').style.backgroundPosition = 'center';
        };
        reader.readAsDataURL(file);
    }
}

// Open Modal
function openModal() {
    const modal = document.getElementById('createContractModal');
    modal.style.display = 'block';
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('createContractModal');
    modal.style.display = 'none';
}

// Open Contract Type Modal
function openContractTypeModal() {
    // Validate first modal inputs
    const contractName = document.getElementById('contract-name').value;
    const expiry = document.getElementById('contract-expiry').value;
    const tasks = document.querySelectorAll('.task-input');
    
    // Basic validation
    if (!contractName) {
        alert('Please enter a contract name');
        return;
    }
    if (!expiry) {
        alert('Please select an expiry date');
        return;
    }
    let hasEmptyTask = false;
    tasks.forEach(task => {
        if (!task.value.trim()) {
            hasEmptyTask = true;
        }
    });
    if (hasEmptyTask) {
        alert('Please fill in all tasks');
        return;
    }

    // If validation passes, show the contract type modal
    const mainModal = document.getElementById('createContractModal');
    const typeModal = document.getElementById('contractTypeModal');
    mainModal.style.display = 'none';
    typeModal.style.display = 'block';
}

// Close Contract Type Modal
function closeContractTypeModal() {
    const mainModal = document.getElementById('createContractModal');
    const typeModal = document.getElementById('contractTypeModal');
    typeModal.style.display = 'none';
    mainModal.style.display = 'block';
}


async function submitContract() {
    const contractName = document.getElementById('contract-name').value;
    const expiry = document.getElementById('contract-expiry').value;
    const visibility = document.querySelector('input[name="visibility"]:checked').value;
    const members = Array.from(document.querySelectorAll('input[name="members"]:checked')).map(
        checkbox => checkbox.value
    );

    const tasks = Array.from(document.querySelectorAll('.task-item')).map(taskItem => ({
        name: taskItem.querySelector('.task-input').value.trim(),
        frequency: taskItem.querySelector('.frequency-btn').textContent.trim()
    }));
    
     // Validation: Check required fields
     if (!contractName) {
        alert('Please enter a contract name.');
        return;
    }

    if (!expiry) {
        alert('Please select an expiry date.');
        return;
    }

    if (tasks.length === 0 || tasks.some(task => !task.name)) {
        alert('Please add at least one task with a valid name.');
        return;
    }

    // Create a FormData object to handle text + file
    const formData = new FormData();
    formData.append('name', contractName);
    formData.append('expiry', expiry);
    formData.append('visibility', visibility);
    formData.append('members', JSON.stringify(members));
    formData.append('tasks', JSON.stringify(tasks));

    // Include the selected image if present
    if (selectedImage) {
        formData.append('background_image', selectedImage);
    }

    try {
        const response = await fetch('/create_contract', {
            method: 'POST',
            body: formData, // Use FormData for the payload
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            closeContractTypeModal();
            window.location.reload();
        } else {
            alert(result.error || 'Failed to create contract.');
        }
    } catch (error) {
        console.error('Error submitting contract:', error);
        alert('An unexpected error occurred.');
    }
}



function addTask() {
    const taskInput = document.getElementById('task-input');
    const taskList = document.getElementById('task-list');

    // Get the value from the input field
    const taskValue = taskInput.value.trim();

    if (taskValue === '') {
        alert('Please enter a task before adding.');
        return;
    }

    // Create a new task element
    const taskItem = document.createElement('div');
    taskItem.className = 'task-item';
    taskItem.innerHTML = `
        <span>${taskValue}</span>
        <button class="remove-task-btn" onclick="removeTask(this)">
            <i class="fa-solid fa-trash" style="color: var(--red);"></i>
        </button>
    `;

    // Append the new task to the task list
    taskList.appendChild(taskItem);

    // Clear the input field for the next task
    taskInput.value = '';
}

function removeTask(button) {
    // Remove the task item when the trash button is clicked
    button.parentElement.remove();
}


function addTask() {
    const taskList = document.getElementById('task-list');

    // Create a new task item
    const taskItem = document.createElement('div');
    taskItem.className = 'task-item';
    taskItem.innerHTML = `
        <input type="text" class="task-input" placeholder="e.g. workout for 30 min." />
    `;

    // Add the new task item before the "Add Task" button
    const addTaskBtn = document.querySelector('.add-task-btn');
    taskList.appendChild(taskItem);

    // Automatically focus on the new input field
    const newInput = taskItem.querySelector('.task-input');
    newInput.focus();
}


let activeTaskItem = null;

function addTask() {
    const taskList = document.getElementById('task-list');
    const taskCount = document.querySelectorAll('.task-item').length;

    // Create a new task item
    const taskItem = document.createElement('div');
    taskItem.className = 'task-item';
    taskItem.innerHTML = `
        <input type="text" class="task-input" placeholder="e.g. workout for 30 min." />
        <button class="frequency-btn" onclick="openFrequencyModal(this)">Daily <i class="fa-solid fa-chevron-right"></i></button>
    `;

    // Add the new task item before the "Add Task" button
    taskList.appendChild(taskItem);

    // Automatically focus on the new input field
    taskItem.querySelector('.task-input').focus();
}

function openFrequencyModal(button) {
    // Store the clicked task item for reference
    activeTaskItem = button.closest('.task-item');

    // Show the modal
    const modal = document.getElementById('frequencyModal');
    modal.style.display = 'flex';

    // Pre-fill frequency
    const frequencyText = button.textContent.trim().split(" ")[0].toLowerCase();
    document.getElementById('task-frequency').value = frequencyText;

    // Populate inputs if the task is "X times a week" or "By Date"
    const timesPerWeekInput = document.getElementById('times-per-week');
    const specificDateInput = document.getElementById('specific-date');
    toggleFrequencyInputs(frequencyText);

    if (frequencyText === 'x-times') {
        timesPerWeekInput.value = button.dataset.times || '';
    } else if (frequencyText === 'by-date') {
        specificDateInput.value = button.dataset.date || '';
    }
}



// sdasdasdlsakdasldmalskdn
function toggleFrequencyInputs(selectedFrequency) {
    const timesPerWeekInput = document.getElementById('times-per-week');
    const specificDateInput = document.getElementById('specific-date');

    // Hide all inputs initially
    timesPerWeekInput.style.display = 'none';
    specificDateInput.style.display = 'none';

    // Show relevant input based on the selected frequency
    if (selectedFrequency === 'x-times') {
        timesPerWeekInput.style.display = 'block';
    } else if (selectedFrequency === 'by-date') {
        specificDateInput.style.display = 'block';
    }
}

function closeFrequencyModal() {
    document.getElementById('frequencyModal').style.display = 'none';
}

function saveFrequency() {
    const selectedFrequency = document.querySelector('input[name="frequency"]:checked').value;
    const timesPerWeek = document.getElementById('times-per-week').value;
    const specificDate = document.getElementById('specific-date').value;

    let frequencyText = '';
    if (selectedFrequency === 'daily') {
        frequencyText = 'Daily';
    } else if (selectedFrequency === 'x-times') {
        frequencyText = `${timesPerWeek} times a week`;
    } else if (selectedFrequency === 'by-date') {
        frequencyText = `By ${specificDate}`;
    }

    // Update the task item's button with the selected frequency
    const frequencyBtn = activeTaskItem.querySelector('.frequency-btn');
    frequencyBtn.textContent = frequencyText;
    frequencyBtn.innerHTML += '<i class="fa-solid fa-chevron-right"></i>';

    closeFrequencyModal();
}

function deleteTask() {
    const taskList = document.getElementById('task-list');
    const taskCount = taskList.querySelectorAll('.task-item').length;

    if (taskCount > 1) {
        activeTaskItem.remove();
        closeFrequencyModal();
    } else {
        alert('You must have at least one task.');
    }
}



// Search People
async function fetchUsers() {
    try {
        const response = await fetch('/get_users'); // Call the Flask API
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        const users = await response.json(); // Parse JSON response
        allUsers = users; // Store the users globally
        renderUserList(allUsers); // Render users in the UI
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}



function toggleVisibility(type) {
    const publicDescription = document.getElementById('public-description');
    const privateDescription = document.getElementById('private-description');
    const searchInput = document.getElementById('search-user');
    const userList = document.getElementById('suggested-users');

    if (type === 'public') {
        publicDescription.style.display = 'block';
        privateDescription.style.display = 'none';
        searchInput.style.display = 'none';
        userList.style.display = 'none';
    } else {
        publicDescription.style.display = 'none';
        privateDescription.style.display = 'block';
        searchInput.style.display = 'block';
        userList.style.display = 'flex';
        // Fetch users dynamically and update the UI
        fetchUsers();// Populate initial list
    }
}

// Generate a consistent color for each username
// function getFixedColor(username) {
//     const hash = username.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
//     const colors = ['#FF5733', '#33FF57', '#3357FF', '#F0A500', '#9C33FF'];
//     return colors[hash % colors.length]; // Pick a color based on the hash
// }

function getContractGradient(contractName) {
    const hash = contractName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const colors = ['#FF5733', '#33FF57', '#3357FF', '#F0A500', '#9C33FF', '#FF33A8', '#A833FF'];

    // Select two colors based on the hash
    const color1 = colors[hash % colors.length];
    const color2 = colors[(hash + 3) % colors.length]; // Offset to get a different second color

    return `linear-gradient(135deg, ${color1}, ${color2})`;
}


function renderUserList(userList) {
    const userContainer = document.getElementById('suggested-users');
    userContainer.innerHTML = ''; // Clear previous results
    userList.forEach((user) => {
        const userDiv = document.createElement('div');
        userDiv.className = 'user';

        const avatar = user.picture
            ? `<img src="${user.picture}" alt="${user.username}">`
            : `<div class="user-placeholder" style="background-color: ${getFixedColor(user.username)}">${user.username[0]}</div>`;

        userDiv.innerHTML = `
            <div class="user-info">
                ${avatar}
                <span>${user.username}</span>
            </div>
            <input type="checkbox" name="members" value="${user.username}" class="user-checkbox" style="width: 25px; height: 25px;">
        `;
        userContainer.appendChild(userDiv);
    });
}

function filterUsers() {
    const searchTerm = document.getElementById('search-user').value.toLowerCase();

    // Filter users from the global allUsers array
    const filteredUsers = allUsers.filter((user) =>
        user.username.toLowerCase().includes(searchTerm)
    );

    renderUserList(filteredUsers); // Render the filtered list
}


function getRandomColor() {
    const colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A8', '#A833FF'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Default to Public Mode
document.addEventListener('DOMContentLoaded', () => {
    toggleVisibility('public');
});


// ////////////////////////////////////
// function handleTaskClick(taskId, taskName, contractId, userId) {
//     // Log the received parameters for debugging
//     console.log("Received taskId:", taskId);
//     console.log("Received taskName:", taskName);
//     console.log("Received contractId:", contractId);
//     console.log("Received userId:", userId);

//     const fileInput = document.getElementById('fileInput');
//     fileInput.click(); // Trigger the file picker

//     fileInput.onchange = function (event) {
//         const file = event.target.files[0];
//         if (!file) return; // Exit if no file is selected

//         // Prepare the form data
//         const formData = new FormData();
//         formData.append('image', file); // Append the image file
//         formData.append('contract_id', contractId); // Add the contract ID
//         formData.append('sender_id', userId); // Add the sender ID
//         formData.append('task_id', taskId); // Add the task ID
//         window.location.href = `/contract/${contractId}`;

        
//         // Make the POST request to upload the image
//         fetch('/upload_image', {
//             method: 'POST',
//             body: formData,
//         })
//             .then(response => response.json())
//             .then(data => {
//                 if (data.error) {
//                     console.error("Error uploading image:", data.error);
//                     alert("Error uploading image.");
//                 } else {
//                     console.log("Image uploaded successfully:", data.media_url);
//                     alert(`Task "${taskName}" has been completed!`);

//                 }
//             })
//             .catch(error => {
//                 console.error("Error:", error);
//             });
//     };
// }
function handleTaskClick(taskId, taskName, contractId, userId) {
    const fileInput = document.getElementById('fileInput');
    fileInput.click();

    fileInput.onchange = async function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);
        formData.append('contract_id', contractId);
        formData.append('sender_id', userId);
        formData.append('task_id', taskId);

        try {
            // Wait for upload to complete
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData,
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error("Error uploading image:", data.error);
                alert("Error uploading image.");
            } else {
                console.log("Image uploaded successfully:", data.media_url);
                // Only redirect AFTER successful upload
                window.location.href = `/contract/${contractId}`;
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to upload image. Please try again.");
        }
    };
}

