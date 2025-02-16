import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get email credentials from the environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


def send_test_email(name_changed):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("Error: One or more email credentials are missing.")
        return

    subject = "Test Email from Python Script"
    body = "This is a test email to confirm your email configuration is working."

    # Add emoji and status based on name_changed
    if name_changed:
        emoji = "🟢"  # Green circle for name updated
        body += "\n\nStatus: Name Updated! " + emoji
    else:
        emoji = "🔴"  # Red circle for no name change
        body += "\n\nStatus: No Name Change Detected. " + emoji

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"Test email sent successfully to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    # Test with both name change states
    print("Sending email with name_changed = True...")
    send_test_email(name_changed=True)

    print("\nSending email with name_changed = False...")
    send_test_email(name_changed=False)
