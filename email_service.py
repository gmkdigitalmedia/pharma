"""
Email Service for Vivvo.ai

This module provides email functionality using SendGrid.
"""
import os
import sys
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_invitation_email(to_email, invitation_link, role, organization_name):
    """
    Send an invitation email to a new user.
    
    Args:
        to_email: Email address of the recipient
        invitation_link: URL for accepting the invitation
        role: Role being assigned to the user (manager, agent)
        organization_name: Name of the organization
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_key:
        logger.warning("SENDGRID_API_KEY environment variable not set. Email not sent.")
        return False
    
    from_email = os.environ.get('SYSTEM_EMAIL', 'noreply@vivvo.ai')
    
    # Create email subject and content
    subject = f"Invitation to join {organization_name} on Vivvo.ai"
    
    # Create HTML content for better email appearance
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a6cf7; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            .button {{ display: inline-block; background-color: #4a6cf7; color: white; padding: 12px 24px;
                    text-decoration: none; border-radius: 4px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Vivvo.ai</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have been invited to join <strong>{organization_name}</strong> as a <strong>{role}</strong> on Vivvo.ai - 
                the AI-powered HCP engagement platform.</p>
                <p>To accept this invitation and create your account, please click the link below:</p>
                <p style="text-align: center;">
                    <a href="{invitation_link}" class="button">Accept Invitation</a>
                </p>
                <p>This invitation link will expire in 7 days.</p>
                <p>If you have any questions, please contact your organization administrator.</p>
                <p>Best regards,<br>The Vivvo.ai Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; {2025} Vivvo.ai. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text content as fallback
    text_content = f"""
    Welcome to Vivvo.ai

    Hello,

    You have been invited to join {organization_name} as a {role} on Vivvo.ai - the AI-powered HCP engagement platform.

    To accept this invitation and create your account, please visit this link:
    {invitation_link}

    This invitation link will expire in 7 days.

    If you have any questions, please contact your organization administrator.

    Best regards,
    The Vivvo.ai Team
    """
    
    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_email),
        subject=subject
    )
    
    # Add HTML content
    message.content = Content("text/html", html_content)
    
    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email} with status code {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False
        
def send_password_reset_email(to_email, reset_link):
    """
    Send a password reset email.
    
    Args:
        to_email: Email address of the recipient
        reset_link: URL for resetting the password
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_key:
        logger.warning("SENDGRID_API_KEY environment variable not set. Email not sent.")
        return False
    
    from_email = os.environ.get('SYSTEM_EMAIL', 'noreply@vivvo.ai')
    
    # Create email subject and content
    subject = "Reset Your Vivvo.ai Password"
    
    # Create HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a6cf7; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            .button {{ display: inline-block; background-color: #4a6cf7; color: white; padding: 12px 24px;
                    text-decoration: none; border-radius: 4px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Reset Your Password</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We received a request to reset your password for your Vivvo.ai account.</p>
                <p>To reset your password, please click the link below:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>
                <p>This link will expire in 1 hour.</p>
                <p>If you did not request a password reset, you can safely ignore this email.</p>
                <p>Best regards,<br>The Vivvo.ai Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; {2025} Vivvo.ai. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text content as fallback
    text_content = f"""
    Reset Your Vivvo.ai Password

    Hello,

    We received a request to reset your password for your Vivvo.ai account.

    To reset your password, please visit this link:
    {reset_link}

    This link will expire in 1 hour.

    If you did not request a password reset, you can safely ignore this email.

    Best regards,
    The Vivvo.ai Team
    """
    
    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_email),
        subject=subject
    )
    
    # Add HTML content
    message.content = Content("text/html", html_content)
    
    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        logger.info(f"Password reset email sent to {to_email} with status code {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Error sending password reset email to {to_email}: {str(e)}")
        return False