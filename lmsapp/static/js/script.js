// Example: Display a simple alert message
function showAlert(message) {
    alert(message);
}

// Example: Add an event listener to a button
document.addEventListener('DOMContentLoaded', function() {
    var myButton = document.querySelector('#myButton'); // Replace with your button's ID
    if (myButton) {
        myButton.addEventListener('click', function() {
            showAlert('Button clicked!');
        });
    }
});

// Example: Form validation (basic)
function validateForm() {
    var username = document.getElementById('username').value; // Replace with your input's ID
    if (username === '') {
        alert('Username is required!');
        return false;
    }
    return true;
}