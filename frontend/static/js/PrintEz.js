
console.log("opening socket")
let socket = io()

// Function to fetch countdown data from Flask backend
async function fetchCountdownData(printId, printerName, printName) {
    try {
        const response = await fetch('/create_countdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                printId: printId,
                printerName: printerName,
                printName: printName
            }),
        });

        const data = await response.json();

        if (response.ok) {
            const { total_seconds, end_time } = data;
            createPrintBox(printId, total_seconds, total_seconds);
        } else {
            console.error('Failed to fetch countdown data:', data.error);
        }
    } catch (error) {
        console.error('Error fetching countdown data:', error);
    }
}

function createPrintBox(printId, totalSeconds, remainingSeconds) {
    const container = document.createElement('div');
    container.classList.add('print-box');
    container.id = `print-${printId}`;

    container.innerHTML = `
        <h3>Print #${printId}</h3>
        <p>Total Time: ${formatTime(totalSeconds)}</p>
        <div class="progress-container">
            <div class="progress-bar" id="progress-bar-${printId}"></div>
            <div class="time-label" id="time-label-${printId}"></div>
        </div>
        <button class="cancel-btn" id="cancel-btn-${printId}">Cancel</button>
    `;

    document.getElementById('print-area').appendChild(container);
    startCountdown(printId, totalSeconds, remainingSeconds);

    // Attach event listener to cancel button
    document.getElementById(`cancel-btn-${printId}`).addEventListener('click', () => {
        cancelCountdown(printId);
    });
}


function startCountdown(printId, totalSeconds, remainingSeconds) {
    const progressBar = document.getElementById(`progress-bar-${printId}`);
    const timeLabel = document.getElementById(`time-label-${printId}`);
    const interval = setInterval(() => {
        if (remainingSeconds <= 0) {
            clearInterval(interval);
            timeLabel.textContent = 'Completed!';
            progressBar.style.width = '100%';
            return;
        }

        remainingSeconds -= 1;
        timeLabel.textContent = formatTime(remainingSeconds);
        progressBar.style.width = `${((totalSeconds - remainingSeconds) / totalSeconds) * 100}%`;
    }, 1000);

    // Store the interval ID for this print ID to allow cancellation
    window[`interval-${printId}`] = interval;
}


function cancelCountdown(printId) {
    // Stop the interval
    clearInterval(window[`interval-${printId}`]);

    // Remove the print box from the DOM
    const printBox = document.getElementById(`print-${printId}`);
    if (printBox) {
        printBox.remove();
    }

    console.log(`Countdown for print #${printId} has been canceled.`);
}

// Function to send cancel action to Flask backend
async function sendCancelAction(printId) {
    try {
        const response = await fetch('/cancel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ printId }),
        });

        if (!response.ok) {
            const data = await response.json();
            console.error('Failed to notify cancellation:', data.error);
        } else {
            console.log(`Cancellation confirmed for Print ID: ${printId}`);
        }
    } catch (error) {
        console.error('Error sending cancellation action:', error);
    }
}

// Socket event listener for plate cleanup requests
socket.on("request_plate_cleanup", function(cleanup_msg) {
    console.log("request_plate_cleanup");
    console.log(cleanup_msg);

    // Extract printId from the message, assuming cleanup_msg contains this information
    const printId = cleanup_msg.printId || 'unknown';

    // Call createTakeoutPrompt to display the cleanup prompt
    createTakeoutPrompt(printId, cleanup_msg.message || "A cleanup is required!");
});

// Function to create a takeout prompt box
function createTakeoutPrompt(printId, message = "Please take out your print!") {
    // Check if prompt already exists and don't create a new one
    if (document.getElementById(`prompt-${printId}`)) {
        return; // If it already exists, don't create a new one
    }

    const promptContainer = document.createElement('div');
    promptContainer.classList.add('takeout-prompt');
    promptContainer.id = `prompt-${printId}`;

    promptContainer.innerHTML = `
        <p>${message}</p>
        <button id="takeout-btn-${printId}">Jag har gjort rent platan</button>
    `;

    document.body.appendChild(promptContainer);

    // Show the prompt (in case it's hidden by default)
    promptContainer.style.display = 'block';

    // Add event listener for the takeout button
    document.getElementById(`takeout-btn-${printId}`).addEventListener('click', () => {
        sendTakeoutAction(printId);

        // Remove the prompt after action
        document.body.removeChild(promptContainer);

        // Optionally, remove the corresponding print box if it exists
        const printBox = document.getElementById(`print-${printId}`);
        if (printBox) {
            printBox.remove();
        }
    });
}

// Function to send takeout action to Flask backend
async function sendTakeoutAction(printId) {
    try {
        const response = await fetch('/takeout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ printId }),
        });

        if (!response.ok) {
            const data = await response.json();
            console.error('Failed to notify takeout action:', data.error);
        } else {
            console.log(`Takeout confirmed for Print ID: ${printId}`);
        }
    } catch (error) {
        console.error('Error sending takeout action:', error);
    }
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    let formattedTime = '';
    if (hours > 0) formattedTime += `${hours}h `;
    if (minutes > 0 || hours > 0) formattedTime += `${minutes}m `;
    formattedTime += `${secs}s`;
    return formattedTime.trim();
}


// Sample printer data to loop through
const printerState = {
    "1-Jerry Seinfeld": {
        "time_remaining": 0,
        "subtask_name": "",
        "total_layers": 0,
        "current_layer": 0,
        "current_stage": 0,
        "current_stage_text": ""
    },
    "2-George Costanza": {
        "time_remaining": 0,
        "subtask_name": "",
        "total_layers": 0,
        "current_layer": 0,
        "current_stage": 0,
        "current_stage_text": ""
    },
    "S1. Arya Stark": {
        "time_remaining": 130,
        "subtask_name": "Amir-fahdel_240S_servo-hållare(NEW)_take-4.3mf",
        "total_layers": 466,
        "current_layer": 133,
        "current_stage": 0,
        "current_stage_text": ""
    },
    "S2. Daenerys Targaryen": {
        "time_remaining": 146,
        "subtask_name": "uploads_files_3144917_Cell+phone+holder+3DTROOP+v2(1).stl",
        "total_layers": 334,
        "current_layer": 41,
        "current_stage": 0,
        "current_stage_text": ""
    },
    // More if neded
};

// Loop through the printerState data and call fetchCountdownData
for (const [key, value] of Object.entries(printerState)) {
    const printId = key;
    const printerName = key.split('-')[1]; // Extracting the printer name (e.g., Jerry Seinfeld)
    const printName = value.subtask_name || "Unknown Print Job"; // Default to "Unknown Print Job" if subtask_name is empty

    fetchCountdownData(printId, printerName, printName);
}
