# app/services/email_service.py

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app, render_template

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.api_key = current_app.config.get('SENDGRID_API_KEY')
        self.from_email = current_app.config.get('MAIL_DEFAULT_SENDER')
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None
    
    def send_email(self, to_email, subject, html_content):
        """Send email via SendGrid"""
        if not self.client:
            current_app.logger.warning("SendGrid not configured. Email not sent.")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            return response.status_code == 202
            
        except Exception as e:
            current_app.logger.error(f"Email send error: {str(e)}")
            return False
    
    def send_welcome_email(self, user):
        """Send welcome email to new user"""
        html = render_template('emails/welcome.html', user=user)
        return self.send_email(
            to_email=user.email,
            subject='Chào mừng bạn đến với IELTS Platform!',
            html_content=html
        )
    
    def send_payment_approved(self, user, payment_request):
        """Send email when payment is approved"""
        html = render_template('emails/payment_approved.html', 
                             user=user, 
                             payment=payment_request)
        return self.send_email(
            to_email=user.email,
            subject='✅ Nạp tiền thành công!',
            html_content=html
        )
    
    def send_payment_rejected(self, user, payment_request):
        """Send email when payment is rejected"""
        html = render_template('emails/payment_rejected.html',
                             user=user,
                             payment=payment_request)
        return self.send_email(
            to_email=user.email,
            subject='❌ Yêu cầu nạp tiền không được chấp nhận',
            html_content=html
        )
    
    def send_credits_low_warning(self, user):
        """Send warning when credits are low"""
        html = render_template('emails/credits_low.html', user=user)
        return self.send_email(
            to_email=user.email,
            subject='⚠️ Credits của bạn sắp hết',
            html_content=html
        )


# Lazy initialization
_email_service = None

def get_email_service():
    """Get or create Email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

# For backward compatibility
def email_service():
    return get_email_service()