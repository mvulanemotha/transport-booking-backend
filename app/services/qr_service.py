from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
import uuid
import json
import secrets
import base64
from io import BytesIO

from app.models.qr_code import QRCode
from app.models.booking import Booking
from app.schemas.qr_code import QRCodeGenerateResponse, QRCodeValidateResponse


class QRService:
    @staticmethod
    async def generate_booking_qr(
        db: AsyncSession,
        booking_id: str,
        expires_in_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Generate QR code for a booking

        Args:
            booking_id: The booking ID
            expires_in_hours: Hours until QR code expires

        Returns:
            QR code data
        """
        # Get booking
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"error": "Booking not found"}

        # Check if QR code already exists and is valid
        existing_qr = await db.execute(
            select(QRCode).where(
                and_(
                    QRCode.booking_id == uuid.UUID(booking_id),
                    QRCode.is_valid == True,
                    QRCode.expires_at > datetime.utcnow(),
                    QRCode.is_blocked == False,
                    QRCode.is_deleted.is_(None)
                )
            )
        )
        existing_qr = existing_qr.scalar_one_or_none()

        if existing_qr:
            return {
                "id": str(existing_qr.id),
                "booking_id": str(existing_qr.booking_id),
                "qr_code": existing_qr.code,
                "qr_data": existing_qr.data,
                "expires_at": existing_qr.expires_at,
                "is_valid": existing_qr.is_valid,
            }

        # Build QR data
        qr_data = {
            "booking_id": str(booking.id),
            "reference": booking.reference,
            "customer_name": booking.customer.full_name if booking.customer else "",
            "customer_phone": booking.customer.phone if booking.customer else "",
            "departure_date": booking.schedule.departure_date.isoformat() if booking.schedule else "",
            "departure_time": booking.schedule.departure_time.isoformat() if booking.schedule else "",
            "route": f"{booking.schedule.route.origin} → {booking.schedule.route.destination}" if booking.schedule and booking.schedule.route else "",
            "status": booking.status.value if booking.status else "",
            "passengers": booking.number_of_passengers,
            "total_amount": float(booking.total_amount),
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat()
        }

        # Generate unique code
        qr_code = f"QR-{booking.reference}-{secrets.token_hex(4).upper()}"

        # Create QR code record
        qr = QRCode(
            booking_id=uuid.UUID(booking_id),
            code=qr_code,
            data=qr_data,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            is_valid=True,
            is_blocked=False
        )

        db.add(qr)
        await db.commit()
        await db.refresh(qr)

        # Generate QR image (optional)
        qr_image = await QRService._generate_qr_image(qr_code)

        return {
            "id": str(qr.id),
            "booking_id": str(qr.booking_id),
            "qr_code": qr.code,
            "qr_data": qr.data,
            "expires_at": qr.expires_at,
            "is_valid": qr.is_valid,
            "qr_image": qr_image
        }

    @staticmethod
    async def _generate_qr_image(data: str) -> str:
        """Generate QR code image as base64 string"""
        try:
            import qrcode

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return ""

    @staticmethod
    async def validate_qr_code(
        db: AsyncSession,
        qr_code: str,
        scan_location: Optional[Dict[str, Any]] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a QR code for check-in

        Args:
            qr_code: The QR code string to validate
            scan_location: Location where QR was scanned
            device_info: Device information from scan

        Returns:
            Validation result
        """
        # Find QR code
        query = select(QRCode).where(
            and_(
                QRCode.code == qr_code,
                QRCode.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        qr = result.scalar_one_or_none()

        if not qr:
            return QRCodeValidateResponse(
                valid=False,
                message="Invalid QR code"
            ).model_dump()

        # Check if blocked
        if qr.is_blocked:
            return QRCodeValidateResponse(
                valid=False,
                message="QR code has been blocked"
            ).model_dump()

        # Check if expired
        if qr.expires_at and qr.expires_at < datetime.utcnow():
            return QRCodeValidateResponse(
                valid=False,
                message="QR code has expired"
            ).model_dump()

        # Check if booking is valid
        booking = await db.execute(
            select(Booking).where(Booking.id == qr.booking_id)
        )
        booking = booking.scalar_one_or_none()

        if not booking:
            return QRCodeValidateResponse(
                valid=False,
                message="Booking not found"
            ).model_dump()

        if booking.status in ["cancelled", "completed"]:
            return QRCodeValidateResponse(
                valid=False,
                message=f"Booking is {booking.status}"
            ).model_dump()

        # Update scan tracking
        qr.scan_count += 1
        qr.scanned_at = datetime.utcnow()
        if scan_location:
            qr.scan_location = scan_location
        if device_info:
            qr.device_info = device_info

        await db.commit()

        return QRCodeValidateResponse(
            valid=True,
            message="QR code validated successfully",
            booking_id=str(booking.id),
            reference=booking.reference,
            passenger_name=booking.customer.full_name if booking.customer else "",
            status=booking.status.value,
            schedule={
                "departure_date": booking.schedule.departure_date.isoformat() if booking.schedule else "",
                "departure_time": booking.schedule.departure_time.isoformat() if booking.schedule else "",
                "route": f"{booking.schedule.route.origin} → {booking.schedule.route.destination}" if booking.schedule and booking.schedule.route else ""
            } if booking.schedule else None
        ).model_dump()

    @staticmethod
    async def check_in_passenger(
        db: AsyncSession,
        qr_code: str,
        checked_in_by: str
    ) -> Dict[str, Any]:
        """
        Check in a passenger using QR code

        Args:
            qr_code: The QR code string
            checked_in_by: User ID of the person checking in
        """
        from app.models.passenger import Passenger
        from app.models.booking import BookingStatus
        from app.services.manifest_service import ManifestService

        # Validate QR code first
        validation = await QRService.validate_qr_code(db, qr_code)

        if not validation.get("valid"):
            return {"success": False, "message": validation.get("message")}

        booking_id = validation.get("booking_id")

        # Get first passenger who hasn't been checked in
        passenger = await db.execute(
            select(Passenger).where(
                and_(
                    Passenger.booking_id == uuid.UUID(booking_id),
                    Passenger.is_checked_in == False,
                    Passenger.is_deleted.is_(None)
                )
            ).limit(1)
        )
        passenger = passenger.scalar_one_or_none()

        if not passenger:
            return {"success": False, "message": "All passengers already checked in"}

        # Check in passenger
        result = await ManifestService.update_passenger_check_in(
            db=db,
            passenger_id=str(passenger.id),
            checked_in_by=checked_in_by,
            board=False
        )

        return {
            "success": True,
            "message": f"Passenger {passenger.full_name} checked in successfully",
            "passenger": result
        }

    @staticmethod
    async def block_qr_code(
        db: AsyncSession,
        qr_code: str,
        reason: str
    ) -> bool:
        """Block a QR code"""
        query = select(QRCode).where(
            and_(
                QRCode.code == qr_code,
                QRCode.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        qr = result.scalar_one_or_none()

        if not qr:
            return False

        qr.is_blocked = True
        qr.blocked_at = datetime.utcnow()
        qr.block_reason = reason

        await db.commit()
        return True

    @staticmethod
    async def get_booking_qr(
        db: AsyncSession,
        booking_id: str
    ) -> Optional[QRCode]:
        """Get QR code for a booking"""
        query = select(QRCode).where(
            and_(
                QRCode.booking_id == uuid.UUID(booking_id),
                QRCode.is_valid == True,
                QRCode.is_blocked == False,
                QRCode.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()