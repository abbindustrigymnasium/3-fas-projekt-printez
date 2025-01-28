let yourfiles = []; // Files selected by the user
let queueFiles = []; // Files added to the queue

// Allow drag-and-drop functionality
function allowDrop(event) {
    event.preventDefault();
}

// Handle drop event
function drop(event) {
    event.preventDefault();
    event.stopPropagation();

    if (event.dataTransfer.files.length > 0) {
        for (let i = 0; i < event.dataTransfer.files.length; i++) {
            const file = event.dataTransfer.files[i];
            if (validateFile(file)) {
                yourfiles.push(file);
            } else {
                alert(`${file.name} is not a valid G-code file.`);
            }
        }

        updateFileList();
    }
}

// Trigger file input dialog
function triggerFileInput() {
    document.getElementById("fileInput").click();
}

// Handle file input selection
function handleFileSelect(event) {
    const selectedFiles = event.target.files;

    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        if (validateFile(file)) {
            yourfiles.push(file);
        } else {
            alert(`${file.name} is not a valid G-code file.`);
        }
    }

    updateFileList();
}

// Validate file extensions
function validateFile(file) {
    const validExtensions = ['.gcode', '.3mf'];
    const fileName = file.name.toLowerCase();
    return validExtensions.some(ext => fileName.endsWith(ext));
}

// Update the file list display
function updateFileList() {
    const fileListDiv = document.getElementById("fileList");
    const addToQueueButton = document.getElementById("addToQueueButton");

    fileListDiv.innerHTML = '';

    if (yourfiles.length === 0) {
        addToQueueButton.disabled = true;
    } else {
        addToQueueButton.disabled = false;
    }

    yourfiles.forEach((file, index) => {
        const fileDiv = document.createElement("div");
        fileDiv.classList.add("file-box");
        fileDiv.innerHTML = `
            <i class="fa-regular fa-file file-icon"></i>
            <span class="file-name">${file.name}</span>
            <button onclick="removeFile(${index})">X</button>
        `;
        fileListDiv.appendChild(fileDiv);
    });
}

// Remove file from selection
function removeFile(index) {
    yourfiles.splice(index, 1);
    updateFileList();
}

// Add files to the queue and upload
async function addToQueue() {
    for (let i = 0; i < yourfiles.length; i++) {
        const file = yourfiles[i];

        // Check if the file is already in the queue, and remove it if present
        const existingFileIndex = queueFiles.findIndex((queuedFile) => queuedFile.name === file.name);
        if (existingFileIndex !== -1) {
            // Remove the file from the queue before adding the new one
            await removeQueueFile(existingFileIndex);
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            if (response.ok) {
                console.log(`File ${file.name} uploaded successfully.`);
                queueFiles.push({ uuid: result.uuid, name: result.filename });  // Add the new file to the queue
            } else {
                alert(`Error uploading file ${file.name}: ${result.error}`);
            }
        } catch (error) {
            console.log(`Failed to upload file ${file.name}: ${error.message}`);
        }
    }

    yourfiles = [];
    updateFileList();
    updateQueueList();
}


// Update the queue list display
function updateQueueList() {
    const queueListDiv = document.getElementById("queueList");
    queueListDiv.innerHTML = '';

    if (queueFiles.length === 0) {
        queueListDiv.innerHTML = '<p></p>';
    } else {
        queueFiles.forEach((file, index) => {
            const queueDiv = document.createElement("div");
            queueDiv.classList.add("queue-box");
            queueDiv.innerHTML = `
                <i class="fa-regular fa-file file-icon"></i>
                <span class="queue-file-name">${file.name}</span>
                <button onclick="removeQueueFile(${index})">X</button>
            `;
            queueListDiv.appendChild(queueDiv);
        });
    }
}

// Remove file from the queue
async function removeQueueFile(index) {
    const fileToRemove = queueFiles[index];
    const print_id = fileToRemove.uuid 

    try {
        const response = await fetch(`/cancel/${print_id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        const result = await response;
        if (response.ok) {
            console.log(`File ${fileToRemove.name} removed successfully.`);
            queueFiles.splice(index, 1);
            updateQueueList();
        } else {
            alert(`Error removing file ${fileToRemove.name}: ${result.error}`);
        }
    } catch (error) {
        alert(`Failed to remove file ${fileToRemove.name}: ${error.message}`);
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    updateQueueList();
});