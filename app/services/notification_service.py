from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
import uuid
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.user import User
from app.models.booking import Booking
from app.core.config import settings


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: Optional[str],
        customer_id: Optional[str],
        recipient: str,
        notification_type: str,
        title: str,
        content: str,
        channel: str = "email",
        data: Optional[Dict[str, Any]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> Notification:
        """Create a notification record"""
        notification = Notification(
            user_id=uuid.UUID(user_id) if user_id else None,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            recipient=recipient,
            type=notification_type,
            title=title,
            content=content,
            channel=channel,
            data=data,
            scheduled_for=scheduled_for
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @staticmethod
    async def send_booking_confirmation(
        db: AsyncSession,
        booking_id: str,
        customer_email: str,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send booking confirmation notification"""
        # Get booking details
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"error": "Booking not found"}

        # Create notification data
        notification_data = {
            "booking_reference": booking.reference,
            "departure_date": booking.schedule.departure_date.isoformat() if booking.schedule else "",
            "departure_time": booking.schedule.departure_time.isoformat() if booking.schedule else "",
            "total_amount": float(booking.total_amount),
            "passengers": booking.number_of_passengers
        }

        # Create email content
        email_content = f"""
        Dear Customer,

        Your booking has been confirmed!

        Booking Reference: {booking.reference}
        Departure Date: {booking.schedule.departure_date if booking.schedule else 'N/A'}
        Departure Time: {booking.schedule.departure_time if booking.schedule else 'N/A'}
        Total Amount: ${float(booking.total_amount)}
        Passengers: {booking.number_of_passengers}

        Thank you for choosing Transport Booking System!
        """

        # Create notification
        notification = await NotificationService.create_notification(
            db=db,
            user_id=None,
            customer_id=str(booking.customer_id),
            recipient=customer_email,
            notification_type=NotificationType.BOOKING_CONFIRMATION.value,
            title=f"Booking Confirmed - {booking.reference}",
            content=email_content,
            channel="email",
            data=notification_data
        )

        # Try to send email
        email_sent = await NotificationService._send_email(
            to_email=customer_email,
            subject=f"Booking Confirmed - {booking.reference}",
            body=email_content
        )

        # Update notification status
        if email_sent:
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            await db.commit()

        return {
            "notification_id": str(notification.id),
            "sent": email_sent,
            "booking_reference": booking.reference
        }

    @staticmethod
    async def send_payment_confirmation(
        db: AsyncSession,
        booking_id: str,
        customer_email: str,
        amount: float
    ) -> Dict[str, Any]:
        """Send payment confirmation notification"""
        # Get booking
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"error": "Booking not found"}

        notification_data = {
            "booking_reference": booking.reference,
            "amount": amount,
            "paid_amount": float(booking.paid_amount),
            "outstanding_balance": float(booking.outstanding_balance)
        }

        email_content = f"""
        Dear Customer,

        Payment received for booking {booking.reference}.

        Amount Paid: ${amount}
        Outstanding Balance: ${float(booking.outstanding_balance)}

        Thank you for your payment!
        """

        notification = await NotificationService.create_notification(
            db=db,
            user_id=None,
            customer_id=str(booking.customer_id),
            recipient=customer_email,
            notification_type=NotificationType.PAYMENT_SUCCESS.value,
            title=f"Payment Received - {booking.reference}",
            content=email_content,
            channel="email",
            data=notification_data
        )

        email_sent = await NotificationService._send_email(
            to_email=customer_email,
            subject=f"Payment Received - {booking.reference}",
            body=email_content
        )

        if email_sent:
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            await db.commit()

        return {
            "notification_id": str(notification.id),
            "sent": email_sent
        }

    @staticmethod
    async def send_travel_reminder(
        db: AsyncSession,
        booking_id: str,
        customer_email: str,
        hours_before: int = 24
    ) -> Dict[str, Any]:
        """Send travel reminder notification"""
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"error": "Booking not found"}

        notification_data = {
            "booking_reference": booking.reference,
            "departure_date": booking.schedule.departure_date.isoformat() if booking.schedule else "",
            "departure_time": booking.schedule.departure_time.isoformat() if booking.schedule else "",
            "hours_before": hours_before
        }

        email_content = f"""
        Dear Customer,

        Reminder: Your trip is in {hours_before} hours!

        Booking Reference: {booking.reference}
        Departure Date: {booking.schedule.departure_date if booking.schedule else 'N/A'}
        Departure Time: {booking.schedule.departure_time if booking.schedule else 'N/A'}

        Please arrive at least 30 minutes before departure.
        """

        notification = await NotificationService.create_notification(
            db=db,
            user_id=None,
            customer_id=str(booking.customer_id),
            recipient=customer_email,
            notification_type=NotificationType.REMINDER.value,
            title=f"Travel Reminder - {booking.reference}",
            content=email_content,
            channel="email",
            data=notification_data
        )

        email_sent = await NotificationService._send_email(
            to_email=customer_email,
            subject=f"Travel Reminder - {booking.reference}",
            body=email_content
        )

        if email_sent:
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            await db.commit()

        return {
            "notification_id": str(notification.id),
            "sent": email_sent
        }

    @staticmethod
    async def send_schedule_change_notification(
        db: AsyncSession,
        booking_id: str,
        customer_email: str,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send schedule change notification"""
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"error": "Booking not found"}

        email_content = f"""
        Dear Customer,

        Your booking {booking.reference} has been updated.

        Changes:
        {json.dumps(changes, indent=2)}

        Please check your booking for updated details.
        """

        notification = await NotificationService.create_notification(
            db=db,
            user_id=None,
            customer_id=str(booking.customer_id),
            recipient=customer_email,
            notification_type=NotificationType.SCHEDULE_CHANGE.value,
            title=f"Schedule Updated - {booking.reference}",
            content=email_content,
            channel="email",
            data=changes
        )

        email_sent = await NotificationService._send_email(
            to_email=customer_email,
            subject=f"Schedule Updated - {booking.reference}",
            body=email_content
        )

        if email_sent:
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            await db.commit()

        return {
            "notification_id": str(notification.id),
            "sent": email_sent
        }

    @staticmethod
    async def _send_email(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """Send email using SMTP"""
        try:
            # For development, just log the email
            print(f"📧 Sending email to: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            print("-" * 50)
            return True

            # Uncomment for production with SMTP
            """
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
            """
        except Exception as e:
            print(f"Error sending email: {e}")
            return False