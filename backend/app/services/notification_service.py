# Servicio de notificaciones para alertas
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Base para canales de notificación."""
    
    @abstractmethod
    async def send(self, recipient: str, subject: str, message: str, metadata: Dict = None) -> bool:
        pass


class EmailChannel(NotificationChannel):
    """Canal de notificación por email."""
    
    async def send(self, recipient: str, subject: str, message: str, metadata: Dict = None) -> bool:
        # TODO: Integrar con SendGrid, Mailgun, SES, etc.
        logger.info(f"EMAIL a {recipient}: {subject}")
        logger.debug(f"Mensaje: {message}")
        if metadata:
            logger.debug(f"Metadata: {metadata}")
        return True


class PushChannel(NotificationChannel):
    """Canal de notificación push (Firebase, APNs, etc.)."""
    
    async def send(self, recipient: str, subject: str, message: str, metadata: Dict = None) -> bool:
        # TODO: Integrar con Firebase Cloud Messaging
        logger.info(f"PUSH a {recipient}: {subject}")
        return True


class WebhookChannel(NotificationChannel):
    """Canal de notificación via webhook."""
    
    async def send(self, recipient: str, subject: str, message: str, metadata: Dict = None) -> bool:
        # TODO: Enviar POST a URL configurada
        logger.info(f"WEBHOOK a {recipient}: {subject}")
        return True


class NotificationService:
    """Servicio centralizado de notificaciones."""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {
            "email": EmailChannel(),
            "push": PushChannel(),
            "webhook": WebhookChannel(),
        }
        self.default_channels = ["email"]
    
    def register_channel(self, name: str, channel: NotificationChannel):
        """Registra un nuevo canal de notificación."""
        self.channels[name] = channel
    
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Envía alerta a través de los canales configurados.
        
        alert debe contener:
        - type: tipo de alerta (ej: "low_growth_alert")
        - user_id: ID del usuario destinatario
        - message: mensaje principal
        - metadata: dict opcional con datos adicionales
        - channels: lista opcional de canales a usar (default: email)
        """
        user_id = alert.get("user_id")
        if not user_id:
            logger.warning("Alerta sin user_id, no se puede enviar")
            return False
        
        # TODO: Obtener preferencias de notificación del usuario
        # Por ahora usar canales por defecto
        channels = alert.get("channels", self.default_channels)
        subject = f"GeoForraje: {alert.get('type', 'Alerta')}"
        message = alert.get("message", "Nueva alerta del sistema")
        
        metadata = {
            "alert_type": alert.get("type"),
            "lot_id": alert.get("lot_id"),
            "analysis_id": alert.get("analysis_id"),
            "timestamp": datetime.now().isoformat(),
            **(alert.get("metadata", {})),
        }
        
        success = True
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    # TODO: Obtener email/token del usuario
                    recipient = f"user_{user_id}@example.com"  # placeholder
                    await channel.send(recipient, subject, message, metadata)
                except Exception as e:
                    logger.error(f"Error enviando notificación por {channel_name}: {e}")
                    success = False
        
        return success
    
    async def send_bulk(self, alerts: list) -> Dict[str, int]:
        """Envía múltiples alertas en batch."""
        results = {"sent": 0, "failed": 0}
        for alert in alerts:
            if await self.send_alert(alert):
                results["sent"] += 1
            else:
                results["failed"] += 1
        return results


# Instancia global
notification_service = NotificationService()