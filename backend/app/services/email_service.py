"""
Email service for SmartLife Organizer
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    """Handles email sending operations"""
    
    @staticmethod
    def _send_email(to_email, subject, html_body, text_body=None):
        """Send email using SMTP"""
        
        if not Config.MAIL_ENABLED:
            logger.info(f"Email sending disabled. Would send to {to_email}: {subject}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{Config.MAIL_FROM_NAME} <{Config.MAIL_FROM}>"
            msg['To'] = to_email
            
            # Add text version if provided
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(Config.MAIL_HOST, Config.MAIL_PORT) as server:
                if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                    server.starttls()
                    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(email, verification_token):
        """Send email verification email"""
        
        verification_url = f"{Config.APP_URI}/verify-email?token={verification_token}"
        
        subject = "Verifica il tuo account SmartLife"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verifica Account</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #3B82F6;">SmartLife Organizer</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333; margin-bottom: 20px;">Benvenuto in SmartLife!</h2>
                    
                    <p>Grazie per esserti registrato su SmartLife Organizer. Per completare la registrazione, verifica il tuo indirizzo email cliccando sul pulsante qui sotto:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background: #3B82F6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Verifica Email
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666;">
                        Se il pulsante non funziona, copia e incolla questo link nel tuo browser:<br>
                        <a href="{verification_url}" style="color: #3B82F6; word-break: break-all;">{verification_url}</a>
                    </p>
                    
                    <p style="font-size: 14px; color: #666;">
                        Questo link scadrà tra 24 ore per motivi di sicurezza.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #999;">
                    <p>Hai ricevuto questa email perché hai richiesto la registrazione su SmartLife Organizer.</p>
                    <p>Se non sei stato tu, puoi ignorare questa email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Benvenuto in SmartLife Organizer!
        
        Grazie per esserti registrato. Per completare la registrazione, verifica il tuo indirizzo email visitando:
        
        {verification_url}
        
        Questo link scadrà tra 24 ore per motivi di sicurezza.
        
        Se non sei stato tu a registrarti, puoi ignorare questa email.
        """
        
        return EmailService._send_email(email, subject, html_body, text_body)
    
    @staticmethod
    def send_password_reset_email(email, reset_token):
        """Send password reset email"""
        
        reset_url = f"{Config.APP_URI}/reset-password?token={reset_token}"
        
        subject = "Reset della password SmartLife"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #3B82F6;">SmartLife Organizer</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333; margin-bottom: 20px;">Reset della Password</h2>
                    
                    <p>Hai richiesto il reset della password per il tuo account SmartLife. Clicca sul pulsante qui sotto per impostare una nuova password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background: #DC2626; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666;">
                        Se il pulsante non funziona, copia e incolla questo link nel tuo browser:<br>
                        <a href="{reset_url}" style="color: #3B82F6; word-break: break-all;">{reset_url}</a>
                    </p>
                    
                    <p style="font-size: 14px; color: #666;">
                        Questo link scadrà tra 1 ora per motivi di sicurezza.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #999;">
                    <p>Hai ricevuto questa email perché hai richiesto il reset della password.</p>
                    <p>Se non sei stato tu, puoi ignorare questa email. La tua password non sarà modificata.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Reset della Password - SmartLife Organizer
        
        Hai richiesto il reset della password per il tuo account. Per impostare una nuova password, visita:
        
        {reset_url}
        
        Questo link scadrà tra 1 ora per motivi di sicurezza.
        
        Se non sei stato tu a richiedere il reset, puoi ignorare questa email.
        """
        
        return EmailService._send_email(email, subject, html_body, text_body)
    
    @staticmethod
    def send_welcome_pro_email(email, user_name=None):
        """Send welcome email for Pro subscription"""
        
        subject = "Benvenuto in SmartLife Pro! 🎉"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Benvenuto in SmartLife Pro</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #3B82F6;">SmartLife Pro</h1>
                    <div style="font-size: 48px;">🎉</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin-bottom: 20px;">Congratulazioni!</h2>
                    <p style="font-size: 18px;">Il tuo upgrade a SmartLife Pro è stato completato con successo!</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h3 style="color: #333; margin-bottom: 20px;">Cosa puoi fare ora con SmartLife Pro:</h3>
                    
                    <ul style="padding-left: 20px;">
                        <li style="margin-bottom: 10px;"><strong>✨ Query AI illimitate:</strong> Chatta con l'assistente quanto vuoi</li>
                        <li style="margin-bottom: 10px;"><strong>📄 Upload documenti illimitati:</strong> Analizza tutti i documenti che vuoi</li>
                        <li style="margin-bottom: 10px;"><strong>🚀 Funzionalità avanzate:</strong> Accesso a tutte le features premium</li>
                        <li style="margin-bottom: 10px;"><strong>⚡ Priorità nel supporto:</strong> Assistenza dedicata quando ne hai bisogno</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{Config.APP_URI}" 
                           style="background: #3B82F6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Inizia a Usare SmartLife Pro
                        </a>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #999;">
                    <p>Grazie per aver scelto SmartLife Pro!</p>
                    <p>Se hai domande, non esitare a contattarci.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService._send_email(email, subject, html_body)