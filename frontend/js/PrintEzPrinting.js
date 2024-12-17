// Set initial countdown time (1 hour 20 minutes in seconds)
let totalTime = 1 * 60 * 60 + 20 * 60; // 1 hour 20 minutes in seconds

// Elements to display the time
const hoursElement = document.getElementById('hours');
const minutesElement = document.getElementById('minutes');
const secondsElement = document.getElementById('seconds');
const progressBar = document.getElementById('progress-bar');
const queueTimeElement = document.getElementById('QueueTime');

// Update the time format and progress bar
function updateTimer() {
    // Calculate hours, minutes, and seconds
    const hours = Math.floor(totalTime / 3600);
    const minutes = Math.floor((totalTime % 3600) / 60);
    const seconds = totalTime % 60;

    // Format time with leading zeros
    const formattedTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    queueTimeElement.textContent = `Queue: ${formattedTime}`;

    // Update progress bar
    const progress = (1 - totalTime / (1 * 60 * 60 + 20 * 60)) * 360;
    progressBar.style.background = `conic-gradient(#3498db ${progress}deg, transparent ${progress}deg)`;

    // If time reaches 0, stop the timer
    if (totalTime <= 0) {
        clearInterval(timerInterval);
        alert("Time's up!");
    } else {
        totalTime--; // Decrease total time by 1 second
    }
}

// Start the countdown timer
const timerInterval = setInterval(updateTimer, 1000);

// Initialize the timer on page load
updateTimer();
