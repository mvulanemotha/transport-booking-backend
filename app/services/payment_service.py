from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid
import secrets

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.core.config import settings


class PaymentService:
    @staticmethod
    async def create_payment(
        db: AsyncSession,
        booking_id: str,
        amount: float,
        method: str,
        created_by: str,
        notes: Optional[str] = None
    ) -> Payment:
        """Create a new payment record"""
        # Get booking
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            raise ValueError("Booking not found")

        # Generate reference
        reference = f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

        # Calculate amounts
        current_paid = booking.paid_amount or 0
        new_paid = current_paid + amount
        outstanding = booking.total_amount - new_paid

        # Create payment
        payment = Payment(
            booking_id=uuid.UUID(booking_id),
            amount=amount,
            amount_paid=amount,
            outstanding_balance=outstanding,
            method=method,
            reference=reference,
            status=PaymentStatus.PAID if outstanding == 0 else PaymentStatus.PARTIALLY_PAID,
            payment_date=datetime.utcnow(),
            notes=notes,
            created_by=uuid.UUID(created_by)
        )

        db.add(payment)
        await db.flush()

        # Update booking
        booking.paid_amount = new_paid
        booking.outstanding_balance = outstanding

        if outstanding == 0:
            booking.status = BookingStatus.CONFIRMED

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def get_payment(
        db: AsyncSession,
        payment_id: str
    ) -> Optional[Payment]:
        """Get payment by ID"""
        query = select(Payment).where(Payment.id == uuid.UUID(payment_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_booking_payments(
        db: AsyncSession,
        booking_id: str
    ) -> List[Payment]:
        """Get all payments for a booking"""
        query = select(Payment).where(
            and_(
                Payment.booking_id == uuid.UUID(booking_id),
                Payment.is_deleted.is_(None)
            )
        ).order_by(Payment.payment_date.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_payments(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get payments with filters"""
        query = select(Payment)

        conditions = []

        if filters.get("booking_id"):
            conditions.append(Payment.booking_id == uuid.UUID(filters["booking_id"]))
        if filters.get("status"):
            conditions.append(Payment.status == filters["status"])
        if filters.get("method"):
            conditions.append(Payment.method == filters["method"])
        if filters.get("start_date"):
            conditions.append(Payment.payment_date >= filters["start_date"])
        if filters.get("end_date"):
            conditions.append(Payment.payment_date <= filters["end_date"])

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Payment).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(Payment.payment_date.desc())

        result = await db.execute(query)
        payments = result.scalars().all()

        return {
            "items": payments,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def refund_payment(
        db: AsyncSession,
        payment_id: str,
        refund_amount: float,
        refund_reason: str,
        created_by: str
    ) -> Optional[Payment]:
        """Process a refund for a payment"""
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            return None

        if payment.status == PaymentStatus.REFUNDED:
            raise ValueError("Payment already refunded")

        if refund_amount > payment.amount_paid:
            raise ValueError("Refund amount exceeds payment amount")

        # Update payment
        payment.refund_amount = refund_amount
        payment.refund_date = datetime.utcnow()
        payment.refund_reason = refund_reason
        payment.status = PaymentStatus.REFUNDED

        # Update booking
        booking = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking.scalar_one_or_none()
        if booking:
            booking.paid_amount -= refund_amount
            booking.outstanding_balance += refund_amount
            if booking.paid_amount <= 0:
                booking.status = BookingStatus.PAYMENT_PENDING

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def get_payment_summary(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get payment summary for reporting"""
        query = select(Payment)

        conditions = [Payment.status == PaymentStatus.PAID]

        if start_date:
            conditions.append(Payment.payment_date >= start_date)
        if end_date:
            conditions.append(Payment.payment_date <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total amount
        total_amount = await db.execute(
            select(func.sum(Payment.amount_paid)).where(and_(*conditions))
        )
        total_amount = total_amount.scalar() or 0

        # Get count by method
        method_counts = await db.execute(
            select(
                Payment.method,
                func.count().label("count"),
                func.sum(Payment.amount_paid).label("total")
            )
            .where(and_(*conditions))
            .group_by(Payment.method)
        )
        method_counts = method_counts.all()

        return {
            "total_payments": total_amount,
            "payment_count": await db.execute(
                select(func.count()).select_from(Payment).where(and_(*conditions))
            ),
            "by_method": [
                {
                    "method": m.method,
                    "count": m.count,
                    "total": float(m.total) if m.total else 0
                }
                for m in method_counts
            ]
        }