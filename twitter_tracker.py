import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the BEARER_TOKEN from environment variables
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

if not BEARER_TOKEN:
    print("Bearer token is missing.")
    exit(1)

def get_user_details(username, bearer_token):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {bearer_token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit exceeded
            reset_time = int(response.headers.get("x-rate-limit-reset", time.time()))
            current_time = time.time()
            sleep_time = max(0, reset_time - current_time + 5)  # Ensure positive sleep time
            print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            return get_user_details(username, bearer_token)  # Retry after sleeping
        else:
            print(f"Error fetching user details: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

def main():
    USERNAME = "elonmusk"  # Replace with the username you want to track
    CHECK_INTERVAL = 30 * 60  # Time in seconds between checks (30 minutes)

    previous_name = None
    last_change_time = None

    while True:
        print(f"Checking for updates to @{USERNAME}'s profile...")
        user_details = get_user_details(USERNAME, BEARER_TOKEN)

        if user_details:
            current_name = user_details['data']['name']  # This is the display name
            current_username = user_details['data']['username']  # This is the username
            current_time = datetime.now().strftime("%I:%M:%S %p")  # 12-hour format with AM/PM

            print(f"Display Name: {current_name} (Username: @{current_username}) at {current_time}")

            # Check if the name has changed
            if previous_name and current_name != previous_name:
                last_change_time = current_time
                print(
                    f"Alert! @{current_username} changed their Display Name from '{previous_name}' to '{current_name}' at {last_change_time}"
                )
            else:
                print(f"@{current_username} has not changed their Display Name since the last check.")

            previous_name = current_name  # Update for next check
        else:
            print("Failed to fetch user details. Skipping this check.")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
