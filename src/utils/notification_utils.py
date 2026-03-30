import smtplib
import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse


class NotificationUtils:
    """Utilitários para notificações (email e webhook)."""
    
    @staticmethod
    def send_email(
        smtp_server: str,
        smtp_port: int,
        from_email: str,
        to_email: str,
        password: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """Envia notificação por email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if html else 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def send_webhook(
        url: str,
        payload: Dict[str, Any],
        method: str = 'POST',
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Envia notificação por webhook."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            data = json.dumps(payload).encode('utf-8')
            
            request_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NVENC-Encoder/2.0'
            }
            
            if headers:
                request_headers.update(headers)
            
            req = urllib.request.Request(
                url,
                data=data,
                headers=request_headers,
                method=method
            )
            
            parsed = urlparse(req.full_url)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            with urllib.request.urlopen(req, timeout=30) as response:  # nosec B310
                return response.status == 200
        except Exception:
            return False
    
    @staticmethod
    def format_completion_email(
        job_id: str,
        input_path: str,
        output_path: str,
        profile_name: str,
        success: bool,
        duration_seconds: float,
        input_size: int,
        output_size: int,
        error_message: Optional[str] = None
    ) -> tuple[str, str]:
        """Formata email de conclusão de job."""
        from .path_utils import PathUtils
        
        status = "Sucesso" if success else "Falha"
        status_color = "✅" if success else "❌"
        
        subject = f"[{status}] Encode {job_id[:8]} - {profile_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>{status_color} Encoding {status}</h2>
            
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Job ID</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{job_id[:8]}...</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Perfil</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{profile_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Input</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{PathUtils.normalize_path(input_path)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Output</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{PathUtils.normalize_path(output_path)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Duração</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{duration_seconds / 60:.1f} minutos</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Tamanho Input</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{PathUtils.format_size(input_size)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Tamanho Output</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{PathUtils.format_size(output_size)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Compressão</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{(output_size / input_size * 100) if input_size > 0 else 0:.1f}%</td>
                </tr>
            </table>
            
            {f'<p style="color: red;"><strong>Erro:</strong> {error_message}</p>' if error_message else ''}
            
            <hr style="margin-top: 20px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">NVENC Encoder Pro v2.0</p>
        </body>
        </html>
        """
        
        return subject, body
    
    @staticmethod
    def format_completion_webhook(
        job_id: str,
        input_path: str,
        output_path: str,
        profile_name: str,
        success: bool,
        duration_seconds: float,
        input_size: int,
        output_size: int,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formata payload de webhook de conclusão."""
        from .path_utils import PathUtils
        
        return {
            "event": "encoding_completed",
            "job_id": job_id,
            "success": success,
            "profile": {
                "name": profile_name
            },
            "input": {
                "path": PathUtils.normalize_path(input_path),
                "size": input_size
            },
            "output": {
                "path": PathUtils.normalize_path(output_path),
                "size": output_size
            },
            "duration_seconds": duration_seconds,
            "compression_ratio": (output_size / input_size) if input_size > 0 else 0,
            "error": error_message,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    
    @staticmethod
    def send_completion_notification(
        config: Dict[str, Any],
        job_id: str,
        input_path: str,
        output_path: str,
        profile_name: str,
        success: bool,
        duration_seconds: float,
        input_size: int,
        output_size: int,
        error_message: Optional[str] = None
    ) -> bool:
        """Envia notificação de conclusão baseada na config."""
        notifications_config = config.get('notifications', {})
        
        if not notifications_config.get('enabled', False):
            return False
        
        email_config = notifications_config.get('email', {})
        webhook_config = notifications_config.get('webhook', {})
        
        email_sent = False
        webhook_sent = False
        
        if email_config.get('smtp_server'):
            subject, body = NotificationUtils.format_completion_email(
                job_id=job_id,
                input_path=input_path,
                output_path=output_path,
                profile_name=profile_name,
                success=success,
                duration_seconds=duration_seconds,
                input_size=input_size,
                output_size=output_size,
                error_message=error_message
            )
            
            email_sent = NotificationUtils.send_email(
                smtp_server=email_config.get('smtp_server'),
                smtp_port=email_config.get('smtp_port', 587),
                from_email=email_config.get('from_email'),
                to_email=email_config.get('to_email'),
                password=email_config.get('password'),
                subject=subject,
                body=body,
                html=True
            )
        
        if webhook_config.get('url'):
            payload = NotificationUtils.format_completion_webhook(
                job_id=job_id,
                input_path=input_path,
                output_path=output_path,
                profile_name=profile_name,
                success=success,
                duration_seconds=duration_seconds,
                input_size=input_size,
                output_size=output_size,
                error_message=error_message
            )
            
            webhook_sent = NotificationUtils.send_webhook(
                url=webhook_config.get('url'),
                payload=payload,
                method=webhook_config.get('method', 'POST')
            )
        
        return email_sent or webhook_sent
