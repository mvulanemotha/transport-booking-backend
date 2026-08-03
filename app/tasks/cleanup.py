from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from datetime import datetime, timedelta
import logging

from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.qr_code import QRCode
from app.models.schedule import Schedule

logger = logging.getLogger(__name__)


class CleanupTasks:
    @staticmethod
    async def cleanup_expired_qr_codes() -> Dict[str, Any]:
        """
        Clean up expired QR codes
        Deletes QR codes that have expired and are no longer needed
        """
        result = {"deleted": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                # Get expired QR codes older than 7 days
                expiry_date = datetime.utcnow() - timedelta(days=7)

                expired_qrs = await db.execute(
                    select(QRCode).where(
                        and_(
                            QRCode.expires_at < expiry_date,
                            QRCode.is_valid == False,
                            QRCode.is_deleted.is_(None)
                        )
                    )
                )
                expired_qrs = expired_qrs.scalars().all()

                for qr in expired_qrs:
                    qr.is_deleted = datetime.utcnow()
                    result["deleted"] += 1

                await db.commit()
                logger.info(f"✅ Cleaned up {result['deleted']} expired QR codes")

            except Exception as e:
                logger.error(f"❌ Error cleaning up QR codes: {e}")
                result["errors"].append(str(e))
                await db.rollback()

        return result

    @staticmethod
    async def cleanup_old_notifications(days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old notifications
        Deletes notifications older than specified days
        """
        result = {"deleted": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

                old_notifications = await db.execute(
                    select(Notification).where(
                        and_(
                            Notification.created_at < cutoff_date,
                            Notification.sent == True,
                            Notification.is_deleted.is_(None)
                        )
                    )
                )
                old_notifications = old_notifications.scalars().all()

                for notification in old_notifications:
                    notification.is_deleted = datetime.utcnow()
                    result["deleted"] += 1

                await db.commit()
                logger.info(f"✅ Cleaned up {result['deleted']} old notifications")

            except Exception as e:
                logger.error(f"❌ Error cleaning up notifications: {e}")
                result["errors"].append(str(e))
                await db.rollback()

        return result

    @staticmethod
    async def cleanup_old_audit_logs(days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old audit logs
        Archives or deletes audit logs older than specified days
        """
        result = {"deleted": 0, "archived": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

                old_logs = await db.execute(
                    select(AuditLog).where(
                        and_(
                            AuditLog.created_at < cutoff_date,
                            AuditLog.is_deleted.is_(None)
                        )
                    )
                )
                old_logs = old_logs.scalars().all()

                # Mark for deletion (soft delete)
                for log in old_logs:
                    log.is_deleted = datetime.utcnow()
                    result["deleted"] += 1

                await db.commit()
                logger.info(f"✅ Cleaned up {result['deleted']} old audit logs")

            except Exception as e:
                logger.error(f"❌ Error cleaning up audit logs: {e}")
                result["errors"].append(str(e))
                await db.rollback()

        return result

    @staticmethod
    async def cleanup_expired_bookings() -> Dict[str, Any]:
        """
        Clean up expired pending bookings
        Cancels bookings that have been pending for too long
        """
        result = {"cancelled": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                expiry_date = datetime.utcnow() - timedelta(hours=24)

                expired_bookings = await db.execute(
                    select(Booking).where(
                        and_(
                            Booking.status == BookingStatus.PENDING,
                            Booking.created_at < expiry_date,
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                expired_bookings = expired_bookings.scalars().all()

                for booking in expired_bookings:
                    booking.status = BookingStatus.CANCELLED
                    booking.cancelled_at = datetime.utcnow()
                    booking.cancellation_reason = "Auto-cancelled - expired pending booking"
                    result["cancelled"] += 1

                await db.commit()
                logger.info(f"✅ Cancelled {result['cancelled']} expired pending bookings")

            except Exception as e:
                logger.error(f"❌ Error cleaning up expired bookings: {e}")
                result["errors"].append(str(e))
                await db.rollback()

        return result

    @staticmethod
    async def run_all_cleanups() -> Dict[str, Any]:
        """Run all cleanup tasks"""
        results = {
            "qr_codes": await CleanupTasks.cleanup_expired_qr_codes(),
            "notifications": await CleanupTasks.cleanup_old_notifications(),
            "audit_logs": await CleanupTasks.cleanup_old_audit_logs(),
            "expired_bookings": await CleanupTasks.cleanup_expired_bookings(),
        }

        return results