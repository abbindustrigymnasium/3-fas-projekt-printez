
// console.log("opening socket")
// let socket = io()

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
function createTakeoutPrompt(printId, message = "Please take out your print!") {
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
        <p>${message}</p>
        <button id="takeout-btn-${printId}">Jag har gjort rent platan</button>
    `;

    document.body.appendChild(promptContainer);

    // Show the prompt (in case it's hidden by default)
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
        } else {
            console.log(`Takeout confirmed for Print ID: ${printId}`);
        }
    } catch (error) {
        console.error('Error sending takeout action:', error);
    }
}

// Loop through the printerState data and call fetchCountdownData
for (const [key, value] of Object.entries(printerState)) {
    const printId = key;
    const printerName = key.split('-')[1]; // Extracting the printer name (e.g., Jerry Seinfeld)
    const printName = value.subtask_name || "Unknown Print Job"; // Default to "Unknown Print Job" if subtask_name is empty

    fetchCountdownData(printId, printerName, printName);
}