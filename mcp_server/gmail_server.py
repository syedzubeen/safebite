"""
SafeBite Gmail MCP Server

Exposes a send_email tool via the Model Context Protocol.
SafeBite (the Slack agent) connects to this as an MCP client
to send weekly digests to users' inboxes.

Run standalone: python -m mcp_server.gmail_server
"""

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="SafeBite Gmail",
    instructions="Sends SafeBite weekly digest emails to users via Gmail SMTP.",
)

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


@mcp.tool()
def send_email(to_address: str, subject: str, body: str) -> str:
    """
    Send an email via Gmail SMTP.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.

    Returns:
        Success or error message.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return "Error: Gmail credentials not configured."

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"SafeBite <{GMAIL_ADDRESS}>"
        msg["To"] = to_address
        msg["Subject"] = subject

        # Plain text part
        text_part = MIMEText(body, "plain")

        # HTML part with basic styling
        html_body = body.replace("\n", "<br>").replace("*", "")
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
            <div style="border-left: 4px solid #2EB67D; padding-left: 16px; margin-bottom: 20px;">
                <h2 style="color: #166534; margin: 0;">🛡️ SafeBite Weekly Digest</h2>
                <p style="color: #6b7280; margin: 4px 0 0;">Your personal food safety update</p>
            </div>
            <div style="line-height: 1.7;">{html_body}</div>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                🔒 SafeBite keeps your dietary condition private. This digest is sent only to you.
            </p>
        </body>
        </html>
        """
        html_part = MIMEText(html, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())

        return f"Email sent successfully to {to_address}"

    except smtplib.SMTPAuthenticationError:
        return "Error: Gmail authentication failed. Check your App Password."
    except Exception as e:
        return f"Error sending email: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
