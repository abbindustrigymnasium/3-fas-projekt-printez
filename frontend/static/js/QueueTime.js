// Function to fetch the current queue time from the backend and update the UI
async function updateQueueTime() {
    try {
        const response = await fetch('/status', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            const { total_seconds } = data;
            const formattedTime = formatTime(total_seconds);

            // Update the queue time displayed on the page
            document.getElementById("QueueTime").textContent = formattedTime;
        } else {
            console.error('Failed to fetch queue time:', data.error);
        }
    } catch (error) {
        console.error('Error fetching queue time:', error);
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

// Example: Fetch and update the queue time every 30 seconds
setInterval(updateQueueTime, 3000);

// Initial update on page load
updateQueueTime();
