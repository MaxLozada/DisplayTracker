// Change the background color when called
function changeBackgroundColor() {
    document.body.style.backgroundColor = "#e0f7fa"; // New color
}

// Dynamically update user info
function updateUserInfo(name, username, lastChangeTime, nameChanged) {
    document.querySelector('.user-info').innerHTML = `
        <p><strong>Display Name:</strong> ${name || "N/A"}</p>
        <p><strong>Username:</strong> @${username || "N/A"}</p>
        <p><strong>Last Change Time:</strong> ${lastChangeTime || "N/A"}</p>
        <p><strong>Name Changed:</strong> ${nameChanged ? "Yes" : "No"}</p>
    `;
}

async function fetchData() {
    try {
        const response = await fetch('/api/user-data');

        // Check if the response is ok (status code 200-299)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update the HTML content with the new data
        document.getElementById('currentName').textContent = data.current_name || "N/A";
        document.getElementById('currentUsername').textContent = data.current_username || "N/A";
        document.getElementById('lastChangeTime').textContent = data.last_change_time || "N/A";
        document.getElementById('nameChanged').textContent = data.name_changed ? "Yes" : "No";

        // Call updateUserInfo with the data
        updateUserInfo(data.current_name, data.current_username, data.last_change_time, data.name_changed);
    } catch (error) {
        console.error("Error fetching user data:", error);
        // Display an error message in the UI
        document.querySelector('.user-info').innerHTML = `
            <p><strong>Error fetching user data. Please try again later.</strong></p>
        `;
    }
}

// Poll the server every 5 seconds
setInterval(fetchData, 5000);
window.onload = fetchData;
