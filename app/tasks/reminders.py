from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date, timedelta
import logging

from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus
from app.models.customer import Customer
from app.models.schedule import Schedule
from app.models.passenger import Passenger
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ReminderTasks:
    @staticmethod
    async def send_booking_reminders(hours_before: int = 24) -> Dict[str, Any]:
        """
        Send booking reminders for trips starting in X hours

        Args:
            hours_before: Number of hours before departure to send reminder
        """
        result = {"sent": 0, "errors": []}

        # Calculate time window
        now = datetime.utcnow()
        target_time = now + timedelta(hours=hours_before)

        # Get bookings that depart in the target hour window
        async with async_session_maker() as db:
            try:
                # Get schedules that depart in the target hour window
                # Note: This is simplified - in production, you'd handle date/time more carefully
                tomorrow = date.today() + timedelta(days=1 if hours_before >= 24 else 0)

                bookings = await db.execute(
                    select(Booking)
                    .where(
                        and_(
                            Booking.status == BookingStatus.CONFIRMED,
                            Booking.schedule.has(
                                and_(
                                    Schedule.departure_date == tomorrow,
                                    # Approximate time check
                                    Schedule.departure_time >= "00:00",
                                    Schedule.departure_time <= "23:59"
                                )
                            ),
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                bookings = bookings.scalars().all()

                for booking in bookings:
                    try:
                        customer_email = booking.customer.email if booking.customer else None
                        customer_phone = booking.customer.phone if booking.customer else None

                        if customer_email:
                            # Send email reminder
                            await NotificationService.send_travel_reminder(
                                db=db,
                                booking_id=str(booking.id),
                                customer_email=customer_email,
                                hours_before=hours_before
                            )
                            result["sent"] += 1

                    except Exception as e:
                        logger.error(f"Error sending reminder for booking {booking.id}: {e}")
                        result["errors"].append(str(e))

                await db.commit()
                logger.info(f"✅ Sent {result['sent']} reminders ({hours_before}h before departure)")

            except Exception as e:
                logger.error(f"❌ Error sending reminders: {e}")
                result["errors"].append(str(e))

        return result

    @staticmethod
    async def send_check_in_reminders() -> Dict[str, Any]:
        """
        Send reminders for passengers who haven't checked in yet
        """
        result = {"sent": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                today = date.today()

                # Get bookings for today that haven't been checked in
                bookings = await db.execute(
                    select(Booking)
                    .where(
                        and_(
                            Booking.status == BookingStatus.CONFIRMED,
                            Booking.schedule.has(
                                Schedule.departure_date == today
                            ),
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                bookings = bookings.scalars().all()

                for booking in bookings:
                    try:
                        # Check if any passengers haven't checked in
                        passengers = await db.execute(
                            select(Passenger).where(
                                and_(
                                    Passenger.booking_id == booking.id,
                                    Passenger.is_checked_in == False,
                                    Passenger.is_deleted.is_(None)
                                )
                            )
                        )
                        passengers = passengers.scalars().all()

                        if passengers and booking.customer and booking.customer.email:
                            # Send check-in reminder
                            content = f"""
                            Hello {booking.customer.full_name},

                            This is a reminder to check in for your trip today.

                            Booking: {booking.reference}
                            Departure: {booking.schedule.departure_time if booking.schedule else 'N/A'}

                            Please proceed to the check-in counter.
                            """

                            await NotificationService._send_email(
                                to_email=booking.customer.email,
                                subject=f"Check-in Reminder - {booking.reference}",
                                body=content
                            )
                            result["sent"] += 1

                    except Exception as e:
                        logger.error(f"Error sending check-in reminder for booking {booking.id}: {e}")
                        result["errors"].append(str(e))

                await db.commit()
                logger.info(f"✅ Sent {result['sent']} check-in reminders")

            except Exception as e:
                logger.error(f"❌ Error sending check-in reminders: {e}")
                result["errors"].append(str(e))

        return result

    @staticmethod
    async def send_payment_reminders() -> Dict[str, Any]:
        """
        Send reminders for bookings with outstanding payments
        """
        result = {"sent": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                # Get bookings with outstanding balance
                bookings = await db.execute(
                    select(Booking)
                    .where(
                        and_(
                            Booking.outstanding_balance > 0,
                            Booking.status != BookingStatus.CANCELLED,
                            Booking.is_deleted.is_(None)
                        )
                    )
                    .limit(50)
                )
                bookings = bookings.scalars().all()

                for booking in bookings:
                    try:
                        if booking.customer and booking.customer.email:
                            content = f"""
                            Hello {booking.customer.full_name},

                            Reminder: You have an outstanding balance of ${float(booking.outstanding_balance):.2f} for booking {booking.reference}.

                            Total Amount: ${float(booking.total_amount):.2f}
                            Amount Paid: ${float(booking.paid_amount):.2f}
                            Outstanding: ${float(booking.outstanding_balance):.2f}

                            Please complete your payment to confirm your booking.
                            """

                            await NotificationService._send_email(
                                to_email=booking.customer.email,
                                subject=f"Payment Reminder - {booking.reference}",
                                body=content
                            )
                            result["sent"] += 1

                    except Exception as e:
                        logger.error(f"Error sending payment reminder for booking {booking.id}: {e}")
                        result["errors"].append(str(e))

                await db.commit()
                logger.info(f"✅ Sent {result['sent']} payment reminders")

            except Exception as e:
                logger.error(f"❌ Error sending payment reminders: {e}")
                result["errors"].append(str(e))

        return result

    @staticmethod
    async def send_post_trip_feedback_reminders() -> Dict[str, Any]:
        """
        Send feedback request for completed trips
        """
        result = {"sent": 0, "errors": []}

        async with async_session_maker() as db:
            try:
                yesterday = date.today() - timedelta(days=1)

                # Get bookings completed yesterday
                bookings = await db.execute(
                    select(Booking)
                    .where(
                        and_(
                            Booking.status == BookingStatus.COMPLETED,
                            Booking.schedule.has(
                                Schedule.departure_date == yesterday
                            ),
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                bookings = bookings.scalars().all()

                for booking in bookings:
                    try:
                        if booking.customer and booking.customer.email:
                            content = f"""
                            Hello {booking.customer.full_name},

                            Thank you for traveling with us!

                            We hope you had a pleasant journey. We would love to hear your feedback.

                            Booking: {booking.reference}
                            Route: {booking.schedule.route.origin} → {booking.schedule.route.destination}

                            Please take a moment to rate your experience.
                            """

                            await NotificationService._send_email(
                                to_email=booking.customer.email,
                                subject=f"Feedback Request - {booking.reference}",
                                body=content
                            )
                            result["sent"] += 1

                    except Exception as e:
                        logger.error(f"Error sending feedback reminder for booking {booking.id}: {e}")
                        result["errors"].append(str(e))

                await db.commit()
                logger.info(f"✅ Sent {result['sent']} feedback reminders")

            except Exception as e:
                logger.error(f"❌ Error sending feedback reminders: {e}")
                result["errors"].append(str(e))

        return result

    @staticmethod
    async def run_all_reminders() -> Dict[str, Any]:
        """Run all reminder tasks"""
        results = {
            "booking_reminders_24h": await ReminderTasks.send_booking_reminders(24),
            "booking_reminders_3h": await ReminderTasks.send_booking_reminders(3),
            "check_in_reminders": await ReminderTasks.send_check_in_reminders(),
            "payment_reminders": await ReminderTasks.send_payment_reminders(),
            "feedback_reminders": await ReminderTasks.send_post_trip_feedback_reminders(),
        }

        return results