import tweepy
import os
import time
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
import threading
import random
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Load .env file
load_dotenv()

# Get API keys and credentials from .env file
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# Twitter API setup
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize Flask app
app = Flask(__name__)

# Global variable to track display name status
current_display_name = "Unknown"  # Default value before fetching data

# To track the number of requests made and the time of the requests
request_times = deque()


# Function to check rate limits
def check_rate_limit():
    current_time = time.time()

    # Remove requests older than 15 minutes (900 seconds)
    while request_times and request_times[0] < current_time - 900:
        request_times.popleft()

    # If we are close to the rate limit (450 requests in the last 15 minutes), wait
    if len(request_times) >= 400:
        sleep_time = 900 - (current_time - request_times[0])
        print(f"Rate limit reached, waiting for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)


# Global variable to track the last email sent time
last_email_sent_time = 0


# Function to log name changes
def log_name_change(new_display_name):
    try:
        with open("display_name_log.txt", "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{timestamp}: Display name changed to: {new_display_name}\n")
            print(f"Logged name change: {new_display_name}")
    except Exception as e:
        print(f"Error writing to log file: {e}")


# Threaded function to monitor display name in the background
def monitor_display_name():
    global current_display_name, last_email_sent_time
    last_display_name = check_display_name()

    while True:
        new_display_name = check_display_name()
        current_time = time.time()  # Get current time

        # Check if display name changed
        if new_display_name and new_display_name != last_display_name:
            print(f"Display name changed to: {new_display_name}")
            current_display_name = new_display_name
            log_name_change(new_display_name)  # Log the name change
            send_email(new_display_name, change=True)  # Send email when name changes
            last_display_name = new_display_name
            last_email_sent_time = current_time  # Reset last email sent time
        elif current_time - last_email_sent_time >= 3600:  # 3600 seconds = 1 hour
            print("Display name has not changed for an hour, sending email.")
            send_email(current_display_name, change=False)  # Send email if no change for an hour
            last_email_sent_time = current_time  # Update last email sent time

        time.sleep(60 * 30)  # Check every 30 minutes


# Function to send an email notification
def send_email(display_name, change):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL

        if change:
            msg['Subject'] = "Elon Musk's Display Name Changed 🟢"
            body = f"Elon Musk's display name has changed to: {display_name} 🟢"
        else:
            msg['Subject'] = "Reminder: Display Name Has Not Changed 🔴"
            body = f"Elon Musk's display name has not changed in the last hour. Current name: {display_name} 🔴"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
            print(f"Email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"Error sending email: {e}")


# Function to check Elon Musk's display name with retry logic
def check_display_name():
    retries = 5
    for attempt in range(retries):
        try:
            check_rate_limit()  # Check if we're close to the limit
            user = client.get_user(username='elonmusk')  # Fetch Elon Musk's user info
            request_times.append(time.time())  # Track the time of this request
            print(f"Fetched display name: {user.data.name}")
            return user.data.name  # Return the current display name
        except tweepy.errors.TooManyRequests:
            wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
            print(f"Rate limit exceeded. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return "Unknown"  # Return a default value if all attempts fail


# Route to render the index.html page
@app.route('/')
def index():
    return render_template('index.html', display_name=current_display_name)


# API endpoint to get the display name as JSON
@app.route('/get_display_name')
def get_display_name():
    return jsonify({"display_name": current_display_name})


# POST route to send a test email
@app.route('/send_test_email', methods=['POST'])
def send_test_email():
    try:
        send_email("Test Display Name", change=True)  # Send email with a test display name
        return jsonify({"message": "Test email sent successfully!"}), 200
    except Exception as e:
        print(f"Error sending test email: {e}")
        return jsonify({"message": "Error sending test email."}), 500


if __name__ == "__main__":
    # Start the background monitoring in a separate thread
    threading.Thread(target=monitor_display_name, daemon=True).start()
    app.run(debug=True)
