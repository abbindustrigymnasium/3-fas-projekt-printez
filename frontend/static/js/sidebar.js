// Selecting the sidebar and the options
const option1 = document.getElementById('option1');
const option2 = document.getElementById('option2');
const option3 = document.getElementById('option3');
const option4 = document.getElementById('option4');

// Function to change content when options are clicked
function changeContent(option) {
  const content = document.querySelector('.content');
  content.innerHTML = `<h1>${option} Content</h1><p>You selected ${option}. You can change the content dynamically here.</p>`;
}

// Adding event listeners to each sidebar option
option1.addEventListener('click', () => changeContent('Option 1'));
option2.addEventListener('click', () => changeContent('Option 2'));
option3.addEventListener('click', () => changeContent('Option 3'));
option4.addEventListener('click', () => changeContent('Option 4'));
