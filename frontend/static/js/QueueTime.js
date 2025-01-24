// Function to fetch the current print queue from the backend and update the UI
async function updatePrintQueue() {
    try {
        const response = await fetch('/get_queue', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            const queueContainer = document.getElementById('queueContainer'); // Assuming you have a container for the queue

            // Clear the existing queue
            queueContainer.innerHTML = '';

            // Loop through the queue and display each job
            data.forEach(job => {
                const { print_id, estimated_time_to_completion, file_name, owner } = job;
                const formattedTime = formatTime(estimated_time_to_completion * 60); // Assuming the time is in minutes

                // Create a new div for each job in the queue
                const jobElement = document.createElement('div');
                jobElement.classList.add('queue-item');
                jobElement.innerHTML = `
                    <h4>Print Job: ${print_id}</h4>
                    <p>Owner: ${owner}</p>
                    <p>File: ${file_name}</p>
                    <p>Estimated Completion: ${formattedTime}</p>
                `;

                // Append the job element to the container
                queueContainer.appendChild(jobElement);
            });
        } else {
            console.error('Failed to fetch queue data:', data.error);
        }
    } catch (error) {
        console.error('Error fetching queue data:', error);
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

// Example: Fetch and update the print queue every 30 seconds
setInterval(updatePrintQueue, 30000);

// Initial update on page load
updatePrintQueue();
