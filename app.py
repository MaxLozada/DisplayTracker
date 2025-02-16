import tweepy
import os
import time
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
import threading
import random
from collections import deque

# Load .env file
load_dotenv()

# Get API keys and credentials from .env file
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Twitter API setup
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize Flask app
app = Flask(__name__)

# Global variable to track display name status
current_display_name = ""

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


# Function to check Elon Musk's display name with retry logic
def check_display_name():
    retries = 5
    for attempt in range(retries):
        try:
            check_rate_limit()  # Check if we're close to the limit
            user = client.get_user(username='elonmusk')  # Elon Musk's Twitter username
            request_times.append(time.time())  # Track the time of this request
            return user.data.name  # Return the current display name
        except tweepy.errors.TooManyRequests:
            wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
            print(f"Rate limit exceeded. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return None  # Return None if all attempts fail


# Threaded function to monitor display name in the background
def monitor_display_name():
    global current_display_name
    last_display_name = check_display_name()

    while True:
        current_display_name = check_display_name()
        if current_display_name != last_display_name:
            print(f"Display name changed to: {current_display_name}")
            last_display_name = current_display_name
        time.sleep(60 * 15)  # Check every 15 minutes


# Route to render the index.html page
@app.route('/')
def index():
    return render_template('index.html', display_name=current_display_name)


# API endpoint to get the display name as JSON
@app.route('/get_display_name')
def get_display_name():
    return jsonify({"display_name": current_display_name})


if __name__ == "__main__":
    # Start the background monitoring in a separate thread
    threading.Thread(target=monitor_display_name, daemon=True).start()
    app.run(debug=True)
