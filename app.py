from flask import Flask, render_template
import requests
import time
from datetime import datetime
from threading import Thread
from dotenv import load_dotenv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables from .env file
load_dotenv()

# Get the BEARER_TOKEN from environment variables
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
if not BEARER_TOKEN:
    print("Bearer token is missing.")
    exit(1)

# Get email credentials from .env file
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')


# Email sending function
def send_email(subject, body, name_changed):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("Error: One or more email credentials are missing.")
        return

    # Define the emoji based on the name change status
    if name_changed:
        emoji = "🟢"  # Green circle for name updated
        body += "\n\nStatus: Name Updated! " + emoji
    else:
        emoji = "🔴"  # Red circle for no name change
        body += "\n\nStatus: No Name Change Detected. " + emoji

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail's SMTP server and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"Email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Initialize variables for storing user data
USERNAME = "elonmusk"  # Replace with the username you want to track
CHECK_INTERVAL = 10 * 60  # Time in seconds between checks (5 minutes)

user_data = {
    "current_name": None,
    "current_username": None,
    "last_change_time": None,
}

app = Flask(__name__)  # Create the Flask app instance


def get_user_details(username, bearer_token):
    if not bearer_token:
        print("Bearer token is missing.")
        return None

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:  # Rate limit exceeded
        reset_time = int(response.headers.get("x-rate-limit-reset", time.time()))
        current_time = time.time()
        sleep_time = reset_time - current_time + 5  # Add a small buffer to avoid hitting rate limit again
        print(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)  # Sleep until the rate limit resets
        return get_user_details(username, bearer_token)  # Retry after sleeping
    else:
        print(f"Error fetching user details: {response.status_code} - {response.text}")
        return None


def check_for_changes():
    previous_name = None
    while True:
        print(f"Checking for updates to @{USERNAME}'s profile...")
        user_details = get_user_details(USERNAME, BEARER_TOKEN)

        if user_details:
            current_name = user_details['data']['name']  # This is the display name
            current_username = user_details['data']['username']  # This is the username with @ symbol
            current_time = datetime.now().strftime("%I:%M:%S %p")  # 12-hour format with AM/PM

            # Check if name has changed
            name_changed = False
            if previous_name and current_name != previous_name:
                name_changed = True
                last_change_time = current_time
                print(
                    f"Alert! @{current_username} changed their Display Name from '{previous_name}' to '{current_name}' at {last_change_time}")

                # Send email notification when name changes
                subject = f"Twitter Name Change Alert for @{current_username}"
                body = f"@{current_username} changed their Display Name from '{previous_name}' to '{current_name}' at {last_change_time}"
                send_email(subject, body, name_changed)
            else:
                last_change_time = current_time
                print(f"@{current_username} has not changed their Display Name since the last check.")

                # Send email notification for no change
                subject = f"No Change in Twitter Name for @{current_username}"
                body = f"@{current_username} has not changed their Display Name since the last check at {last_change_time}."
                send_email(subject, body, name_changed)

            # Update user_data for the web interface
            user_data["current_name"] = current_name
            user_data["current_username"] = current_username
            user_data["last_change_time"] = last_change_time
            user_data["name_changed"] = name_changed  # Pass the 'name_changed' status to the front-end

            previous_name = current_name
        else:
            print("Failed to fetch user details. Skipping this check.")
            return render_template('error.html')

        time.sleep(CHECK_INTERVAL)


@app.route('/')
def index():
    return render_template('index.html', user_data=user_data)


@app.route('/error')
def error():
    return render_template('error.html')


if __name__ == "__main__":
    # Run the background thread that checks for name changes
    thread = Thread(target=check_for_changes)
    thread.daemon = True
    thread.start()

    # Run the Flask app
    app.run(debug=True, threaded=True)
