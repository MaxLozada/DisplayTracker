// static/js/scripts.js

// Change the background color when called
function changeBackgroundColor() {
    document.body.style.backgroundColor = "#e0f7fa"; // New color
}

// Dynamically update user info
function updateUserInfo(name, username) {
    document.querySelector('.user-info').innerHTML = `
        <p><strong>Display Name:</strong> ${name}</p>
        <p><strong>Username:</strong> @${username}</p>
    `;
}
