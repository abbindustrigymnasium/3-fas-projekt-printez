// Function to fetch countdown data from Flask backend
async function fetchCountdownData(printId) {
    try {
        const response = await fetch('/status', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            const { total_seconds } = data;
            createPrintBox(printId, total_seconds, total_seconds);
        } else {
            console.error('Failed to fetch countdown data:', data.error);
        }
    } catch (error) {
        console.error('Error fetching countdown data:', error);
    }
}

// Function to dynamically create a new print box
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

    // Ensure the event listener is attached correctly
    document.getElementById(`cancel-btn-${printId}`).addEventListener('click', () => {
        cancelCountdown(printId);
    });
}

// Function to start the countdown for a specific print
function startCountdown(printId, totalSeconds, remainingSeconds) {
    const progressBar = document.getElementById(`progress-bar-${printId}`);
    const timeLabel = document.getElementById(`time-label-${printId}`);
    const timerId = `timer-${printId}`;

    window[timerId] = setInterval(() => {
        if (remainingSeconds > 0) {
            remainingSeconds--;
            const progressPercentage = ((totalSeconds - remainingSeconds) / totalSeconds) * 100;
            progressBar.style.width = `${progressPercentage}%`;
            timeLabel.textContent = `Time Left: ${formatTime(remainingSeconds)}`;
        } else {
            clearInterval(window[timerId]);
            timeLabel.textContent = 'Print Complete!';
            createTakeoutPrompt(printId);
        }
    }, 1000);
}

// Function to cancel countdown
// Function to cancel countdown
function cancelCountdown(printId) {
    const timerId = `timer-${printId}`;
    if (window[timerId]) {
        clearInterval(window[timerId]);
        console.log(`Print #${printId} countdown canceled`);

        // Notify the backend of the cancellation
        sendCancelAction(printId);

        // Optionally, reset progress bar and timer display
        document.getElementById(`progress-bar-${printId}`).style.width = '0%';
        document.getElementById(`time-label-${printId}`).textContent = 'Canceled';

        // Remove the print box or handle further actions
        document.getElementById(`print-${printId}`).remove();
    }
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


// Function to create a takeout prompt box
function createTakeoutPrompt(printId) {
    // Check if prompt already exists and don't create a new one
    if (document.getElementById(`prompt-${printId}`)) {
        return; // If it already exists, don't create a new one
    }

    const promptContainer = document.createElement('div');
    promptContainer.classList.add('takeout-prompt');
    promptContainer.id = `prompt-${printId}`;

    promptContainer.innerHTML = `
        <p>Print #${printId} is complete. Please take out your print!</p>
        <button id="takeout-btn-${printId}">Jag har gjort rent platan</button>
    `;

    document.body.appendChild(promptContainer);

    // Show the prompt (was hidden by default)
    promptContainer.style.display = 'block';

    // Add event listener for the takeout button
    document.getElementById(`takeout-btn-${printId}`).addEventListener('click', () => {
        sendTakeoutAction(printId);
        document.body.removeChild(promptContainer); // Remove prompt after action
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
        }
    } catch (error) {
        console.error('Error sending takeout action:', error);
    }
}

// Helper function to format time as HH:MM:SS
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

// Example: Trigger fetching data and creating a new print box
fetchCountdownData('uniquePrintId133'); // Replace with dynamic IDs as needed
