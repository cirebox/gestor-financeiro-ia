# src/infrastructure/email/email_service.py
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from config import settings


class EmailService:
    """Serviço para envio de emails."""
    
    def __init__(self):
        """Inicializa o serviço de email com as configurações."""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.SENDER_EMAIL
        self.sender_name = settings.SENDER_NAME
        self.logger = logging.getLogger(__name__)
    
    def send_email(
        self, 
        recipient_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None
    ) -> bool:
        """
        Envia um email.
        
        Args:
            recipient_email: Email do destinatário
            subject: Assunto do email
            html_content: Conteúdo HTML do email
            text_content: Conteúdo de texto simples do email (opcional)
            cc: Lista de emails para cópia (opcional)
            
        Returns:
            True se o email foi enviado com sucesso, False caso contrário
        """
        try:
            # Se estiver em modo de depuração, apenas loga o email
            if settings.DEBUG:
                self.logger.info(f"Email simulado para: {recipient_email}")
                self.logger.info(f"Assunto: {subject}")
                self.logger.info(f"Conteúdo: {html_content}")
                return True
            
            # Configura a mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            if cc:
                msg['Cc'] = ",".join(cc)
            
            # Adiciona o conteúdo de texto simples, se fornecido
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # Adiciona o conteúdo HTML
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Envia o email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                recipients = [recipient_email]
                if cc:
                    recipients.extend(cc)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")
            return False
    
    def send_password_reset_email(self, recipient_email: str, reset_link: str) -> bool:
        """
        Envia um email de redefinição de senha.
        
        Args:
            recipient_email: Email do destinatário
            reset_link: Link para redefinição de senha
            
        Returns:
            True se o email foi enviado com sucesso, False caso contrário
        """
        subject = "Redefinição de Senha - Financial Tracker"
        
        html_content = f"""
        <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Redefinição de Senha</h2>
                    <p>Recebemos uma solicitação para redefinir sua senha no Financial Tracker.</p>
                    <p>Para redefinir sua senha, clique no botão abaixo:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            Redefinir Senha
                        </a>
                    </p>
                    <p>Ou copie e cole o seguinte link no seu navegador:</p>
                    <p style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; word-break: break-all;">
                        {reset_link}
                    </p>
                    <p>Este link expirará em 30 minutos.</p>
                    <p>Se você não solicitou a redefinição da senha, ignore este email.</p>
                    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                    <p style="color: #7f8c8d; font-size: 0.9em;">
                        Este é um email automático. Por favor, não responda.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Redefinição de Senha - Financial Tracker
        
        Recebemos uma solicitação para redefinir sua senha no Financial Tracker.
        
        Para redefinir sua senha, acesse o link abaixo:
        {reset_link}
        
        Este link expirará em 30 minutos.
        
        Se você não solicitou a redefinição da senha, ignore este email.
        """
        
        return self.send_email(recipient_email, subject, html_content, text_content)