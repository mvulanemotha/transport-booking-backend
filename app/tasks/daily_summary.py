from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date, timedelta
import logging

from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus
from app.models.schedule import Schedule, ScheduleStatus
from app.models.payment import Payment, PaymentStatus
from app.models.customer import Customer
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class DailySummaryTasks:
    @staticmethod
    async def generate_daily_summary(target_date: date) -> Dict[str, Any]:
        """
        Generate daily summary for a specific date

        Args:
            target_date: The date to generate summary for

        Returns:
            Daily summary data
        """
        async with async_session_maker() as db:
            try:
                start_date = datetime.combine(target_date, datetime.min.time())
                end_date = datetime.combine(target_date, datetime.max.time())

                # Today's bookings
                todays_bookings = await db.execute(
                    select(func.count()).select_from(Booking)
                    .where(
                        and_(
                            Booking.booking_date.between(start_date, end_date),
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                todays_bookings = todays_bookings.scalar() or 0

                # Today's departures
                todays_departures = await db.execute(
                    select(func.count()).select_from(Schedule)
                    .where(
                        and_(
                            Schedule.departure_date == target_date,
                            Schedule.status != ScheduleStatus.CANCELLED,
                            Schedule.is_deleted.is_(None)
                        )
                    )
                )
                todays_departures = todays_departures.scalar() or 0

                # Completed trips
                completed_trips = await db.execute(
                    select(func.count()).select_from(Schedule)
                    .where(
                        and_(
                            Schedule.departure_date == target_date,
                            Schedule.status == ScheduleStatus.COMPLETED,
                            Schedule.is_deleted.is_(None)
                        )
                    )
                )
                completed_trips = completed_trips.scalar() or 0

                # Total passengers
                total_passengers = await db.execute(
                    select(func.sum(Booking.number_of_passengers))
                    .select_from(Booking)
                    .where(
                        and_(
                            Booking.booking_date.between(start_date, end_date),
                            Booking.status != BookingStatus.CANCELLED,
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                total_passengers = total_passengers.scalar() or 0

                # Revenue
                total_revenue = await db.execute(
                    select(func.sum(Booking.total_amount))
                    .select_from(Booking)
                    .where(
                        and_(
                            Booking.booking_date.between(start_date, end_date),
                            Booking.status != BookingStatus.CANCELLED,
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                total_revenue = total_revenue.scalar() or 0

                # Pending payments
                pending_payments = await db.execute(
                    select(func.count()).select_from(Payment)
                    .where(
                        and_(
                            Payment.status == PaymentStatus.PENDING,
                            Payment.is_deleted.is_(None)
                        )
                    )
                )
                pending_payments = pending_payments.scalar() or 0

                # New customers
                new_customers = await db.execute(
                    select(func.count()).select_from(Customer)
                    .where(
                        and_(
                            Customer.created_at.between(start_date, end_date),
                            Customer.is_deleted.is_(None)
                        )
                    )
                )
                new_customers = new_customers.scalar() or 0

                # Cancellations
                cancellations = await db.execute(
                    select(func.count()).select_from(Booking)
                    .where(
                        and_(
                            Booking.cancelled_at.between(start_date, end_date),
                            Booking.is_deleted.is_(None)
                        )
                    )
                )
                cancellations = cancellations.scalar() or 0

                summary = {
                    "date": target_date.isoformat(),
                    "summary": {
                        "todays_bookings": todays_bookings,
                        "todays_departures": todays_departures,
                        "completed_trips": completed_trips,
                        "total_passengers": int(total_passengers),
                        "total_revenue": float(total_revenue),
                        "pending_payments": pending_payments,
                        "new_customers": new_customers,
                        "cancellations": cancellations,
                    },
                    "generated_at": datetime.utcnow().isoformat()
                }

                logger.info(f"✅ Generated daily summary for {target_date}")
                return summary

            except Exception as e:
                logger.error(f"❌ Error generating daily summary: {e}")
                return {"error": str(e)}

    @staticmethod
    async def send_daily_summary_email(target_date: date) -> Dict[str, Any]:
        """
        Send daily summary email to administrators
        """
        summary = await DailySummaryTasks.generate_daily_summary(target_date)

        if "error" in summary:
            return summary

        # Format email content
        content = f"""
        📊 Daily Summary Report - {target_date.strftime('%B %d, %Y')}

        📈 Overview:
        • Today's Bookings: {summary['summary']['todays_bookings']}
        • Today's Departures: {summary['summary']['todays_departures']}
        • Completed Trips: {summary['summary']['completed_trips']}
        • Total Passengers: {summary['summary']['total_passengers']}

        💰 Revenue:
        • Total Revenue: ${summary['summary']['total_revenue']:.2f}
        • Pending Payments: {summary['summary']['pending_payments']}

        👥 Customers:
        • New Customers: {summary['summary']['new_customers']}
        • Cancellations: {summary['summary']['cancellations']}

        Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """

        # Send email to admins
        # In production, get admin emails from database
        admin_emails = ["admin@transport.com"]

        results = []
        for email in admin_emails:
            try:
                await NotificationService._send_email(
                    to_email=email,
                    subject=f"Daily Summary - {target_date.strftime('%B %d, %Y')}",
                    body=content
                )
                results.append({"email": email, "sent": True})
            except Exception as e:
                results.append({"email": email, "sent": False, "error": str(e)})

        return {
            "summary": summary,
            "email_results": results
        }

    @staticmethod
    async def get_weekly_summary() -> Dict[str, Any]:
        """Generate weekly summary"""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        summaries = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            summary = await DailySummaryTasks.generate_daily_summary(day)
            summaries.append(summary)

        # Calculate totals
        total_bookings = sum(s.get("summary", {}).get("todays_bookings", 0) for s in summaries)
        total_revenue = sum(s.get("summary", {}).get("total_revenue", 0) for s in summaries)
        total_passengers = sum(s.get("summary", {}).get("total_passengers", 0) for s in summaries)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_passengers": total_passengers,
            "daily_summaries": summaries
        }