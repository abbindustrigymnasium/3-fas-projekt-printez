
let yourfiles = []; // filer valda av anvendaren
let queueFiles = []; // Filer som är i kön



function allowDrop(event) {
    event.preventDefault(); 
}

// Hanterar drop va fil
function drop(event) {
    event.preventDefault(); // Prevent the default drop behavior
    event.stopPropagation(); // Stop the event from bubbling up

    if (event.dataTransfer.files.length > 0) {
        // Kollar igenom för att se om filen är valid
        for (let i = 0; i < event.dataTransfer.files.length; i++) {
            const file = event.dataTransfer.files[i];
            if (validateFile(file)) {
                yourfiles.push(file);
            } else {
                alert(`${file.name} is not a valid G-code file.`);
            }
        }

        console.log("Files dropped:", yourfiles);

        // Updatera fil listan (med boxes och X buttons)
        updateFileList();
    }
}

// Browsebutten
function triggerFileInput() {
    document.getElementById("fileInput").click(); // Simulate a click on the hidden file input
}

// Function to handle file selection
function handleFileSelect(event) {
    const selectedFiles = event.target.files;

    // Loopa igenom filerna samt kolla om de är valid
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        if (validateFile(file)) {
            yourfiles.push(file);
        } else {
            alert(`${file.name} is not a valid G-code file.`);
        }
    }

    console.log("Files selected:", yourfiles);

    // Updatera fil listan (med boxes och X buttons)
    updateFileList();
}

function validateFile(file) {
    const validExtensions = ['.gcode', '.3mf'];
    const fileName = file.name.toLowerCase();
    return validExtensions.some(ext => fileName.endsWith(ext));
}

// Function för att Updatera fil listan (med boxes och X buttons)
function updateFileList() {
    const fileListDiv = document.getElementById("fileList");
    const addToQueueButton = document.getElementById("addToQueueButton");

    fileListDiv.innerHTML = ''; // Clear the list

    if (yourfiles.length === 0) {
        addToQueueButton.style.backgroundColor = "#d3d3d3"; 
        addToQueueButton.style.cursor = "not-allowed";
        addToQueueButton.disabled = true;
    } else {
        // Enable the "Add to Queue" button 
        addToQueueButton.style.backgroundColor = "#79FF88"; 
        addToQueueButton.style.cursor = "pointer";
        addToQueueButton.disabled = false;
    }

    yourfiles.forEach((file, index) => {
        // Skapa en ny div för varje fil
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

function removeFile(index) {
    yourfiles.splice(index, 1);
    console.log("Files after removal:", yourfiles);

    updateFileList();
}

// Function to handle adding files to the queue
// Function to handle adding files to the queue
function addToQueue() {
  const encodedFiles = yourfiles.map(file => {
      return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
              resolve({
                  name: file.name,
                  content: reader.result, // Base64 string
                  type: file.type
              });
          };
          reader.onerror = reject;
          reader.readAsDataURL(file); // Encode file as Base64
      });
  });

  Promise.all(encodedFiles).then(files => {
      queueFiles = queueFiles.concat(files);
      yourfiles = []; // Clear the yourfiles array

      console.log("Files added to queue:", queueFiles);

      // Save the updated queue to localStorage
      localStorage.setItem("queueFiles", JSON.stringify(queueFiles));

      // Update the file list and queue list
      updateFileList();
      updateQueueList();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const storedQueue = localStorage.getItem("queueFiles");
  if (storedQueue) {
      const parsedQueue = JSON.parse(storedQueue);
      
      queueFiles = parsedQueue.map(file => {
          // Check if file.content exists and is valid
          if (!file.content || !file.content.includes(',')) {
              console.error(`Invalid file content for file: ${file.name}`, file);
              return null; // Skip invalid entries
          }

          const base64Data = file.content.split(',')[1]; // Extract Base64 part
          const binaryData = atob(base64Data); // Decode Base64
          const byteArray = new Uint8Array(binaryData.length);

          for (let i = 0; i < binaryData.length; i++) {
              byteArray[i] = binaryData.charCodeAt(i);
          }

          const blob = new Blob([byteArray], { type: file.type }); // Create Blob
          return {
              name: file.name,
              blob,
              type: file.type
          };
      }).filter(file => file !== null); // Remove null entries
      
      updateQueueList();
  }
});



// Function to update the queue list display
function updateQueueList() {
  const queueListDiv = document.getElementById("queueList");
  queueListDiv.innerHTML = ''; // Clear existing list

  queueFiles.forEach((file, index) => {
      const fileDiv = document.createElement("div");
      fileDiv.classList.add("file-box");
      fileDiv.innerHTML = `
          <i class="fa-regular fa-file file-icon"></i>
          <span class="Qfile-name">${file.name}</span>
          <button onclick="removeQueuedFile(${index})">X</button>
      `;
      queueListDiv.appendChild(fileDiv);
  });
}

// Function to remove a file from the queue
function removeQueuedFile(index) {
  queueFiles.splice(index, 1); // Remove the file from the queue
  console.log("Queue after removal:", queueFiles);

  // Update the queue and save it to localStorage
  localStorage.setItem("queueFiles", JSON.stringify(queueFiles));
  updateQueueList();
}


// Function to update the queue list display
// Function to update the file list with boxes and X buttons
function updateFileList() {
  const fileListDiv = document.getElementById("fileList");
  const addToQueueButton = document.getElementById("addToQueueButton");

  fileListDiv.innerHTML = ''; // Clear the existing list

  if (yourfiles.length === 0) {
      // Disable the "Add to Queue" button if no files are present
      addToQueueButton.style.backgroundColor = "#d3d3d3"; // Gray color
      addToQueueButton.style.cursor = "not-allowed";
      addToQueueButton.disabled = true;
  } else {
      // Enable the "Add to Queue" button if files are present
      addToQueueButton.style.backgroundColor = "#79FF88"; // Green color
      addToQueueButton.style.cursor = "pointer";
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

