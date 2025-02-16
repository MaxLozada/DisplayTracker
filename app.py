from flask import Flask, render_template, jsonify
import requests
import time
from datetime import datetime
from threading import Thread, Lock
from dotenv import load_dotenv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables from .env file
load_dotenv()

# Get the BEARER_TOKEN and email credentials from environment variables
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

if not BEARER_TOKEN:
    print("Bearer token is missing.")
    exit(1)

# Configuration
USERNAME = "elonmusk"  # Replace with the username you want to track
CHECK_INTERVAL = 10 * 60  # Time in seconds between checks (10 minutes)
RATE_LIMIT_BUFFER = 5  # Seconds to wait after the rate-limit reset

# Shared data for web display and threading
user_data = {
    "current_name": None,
    "current_username": None,
    "last_change_time": None,
    "name_changed": False,
}
user_data_lock = Lock()

app = Flask(__name__)  # Create the Flask app instance


def send_email(subject, body, name_changed):
    """Send email notifications."""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("Error: Email credentials are missing.")
        return

    # Add status emoji to email
    emoji = "🟢" if name_changed else "🔴"
    body += f"\n\nStatus: {'Name Updated!' if name_changed else 'No Name Change Detected.'} {emoji}"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"Email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def get_user_details(username, bearer_token):
    """Fetch user details from the Twitter API."""
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {bearer_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:  # Rate limit exceeded
        reset_time = int(response.headers.get("x-rate-limit-reset", time.time()))
        current_time = time.time()
        sleep_time = max(0, reset_time - current_time + RATE_LIMIT_BUFFER)
        print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)
        return get_user_details(username, bearer_token)  # Retry after sleeping
    else:
        print(f"Error fetching user details: {response.status_code} - {response.text}")
        return None


def check_for_changes():
    """Background thread function to check for display name changes."""
    previous_name = None
    while True:
        print(f"Checking for updates to @{USERNAME}'s profile...")
        user_details = get_user_details(USERNAME, BEARER_TOKEN)

        if user_details:
            current_name = user_details["data"]["name"]
            current_username = user_details["data"]["username"]
            current_time = datetime.now().strftime("%I:%M:%S %p")

            name_changed = previous_name and current_name != previous_name
            with user_data_lock:
                user_data.update(
                    {
                        "current_name": current_name,
                        "current_username": current_username,
                        "last_change_time": current_time,
                        "name_changed": name_changed,
                    }
                )

            if name_changed:
                print(f"@{current_username} changed their Display Name from '{previous_name}' to '{current_name}' at {current_time}.")
                send_email(
                    f"Twitter Name Change Alert for @{current_username}",
                    f"@{current_username} changed their Display Name from '{previous_name}' to '{current_name}' at {current_time}.",
                    True,
                )
            else:
                print(f"@{current_username} has not changed their Display Name since the last check.")
                send_email(
                    f"No Change in Twitter Name for @{current_username}",
                    f"@{current_username} has not changed their Display Name since the last check at {current_time}.",
                    False,
                )

            previous_name = current_name
        else:
            print("Failed to fetch user details. Skipping this check.")

        time.sleep(CHECK_INTERVAL)


@app.route("/")
def index():
    """Render the main page."""
    with user_data_lock:
        return render_template("index.html", user_data=user_data)


@app.route("/error")
def error():
    """Render the error page."""
    return render_template("error.html")


@app.route("/api/user-data")
def api_user_data():
    """API endpoint to serve the user data as JSON."""
    with user_data_lock:
        return jsonify(user_data)


if __name__ == "__main__":
    # Start the background thread
    thread = Thread(target=check_for_changes)
    thread.daemon = True
    thread.start()

    # Run the Flask app
    app.run(debug=True, threaded=True)
