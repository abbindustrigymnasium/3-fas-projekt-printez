// Function to switch to About Us page
function navigateToAboutUs() {
    window.location.href = "About-us.html"; // Redirects to the about-us.html page
  }
  
  // Function to go to Home page (index.html)
  function navigateToHome() {
    window.location.href = "index.html"; // Redirects to the index.html page
  }

  function navigateToAccount() {
    window.location.href = "Account.html"; // Redirects to the index.html page
  }

  // Show the modal when the account button is clicked
  function confirmLogout() {
    document.getElementById('logout-modal').style.display = 'block';
  }

  // If user clicks Yes, execute logout action (or you can modify to actually log out)
  function confirmAction() {
    document.getElementById('logout-modal').style.display = 'none';
    console.log("here you give more code");  // Placeholder for your actual code
    // You can add more code for logging out here or redirect if necessary
  }

  // If user clicks No, close the modal
  function cancelAction() {
    document.getElementById('logout-modal').style.display = 'none';
  }

  // Close the modal if user clicks anywhere outside the modal content
  window.onclick = function(event) {
    var modal = document.getElementById('logout-modal');
    if (event.target == modal) {
      modal.style.display = "none";
    }
  
  // Optionally, if you want the account and printing options to load different content,
  // you can add similar functions like the one for About Us
  }