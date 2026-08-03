from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date
import uuid
import json

from app.models.schedule import Schedule, ScheduleStatus
from app.models.booking import Booking, BookingStatus
from app.models.passenger import Passenger
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route


class ManifestService:
    @staticmethod
    async def generate_manifest(
        db: AsyncSession,
        schedule_id: str,
        include_pending: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete passenger manifest for a schedule

        Args:
            schedule_id: The schedule to generate manifest for
            include_pending: Include pending bookings in manifest

        Returns:
            Complete manifest with schedule details and passenger list
        """
        # Get schedule with related data
        query = select(Schedule).where(
            Schedule.id == uuid.UUID(schedule_id)
        ).options(
            selectinload(Schedule.route),
            selectinload(Schedule.vehicle),
            selectinload(Schedule.driver)
        )
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return {"error": "Schedule not found"}

        # Get bookings for this schedule
        booking_statuses = [
            BookingStatus.CONFIRMED,
            BookingStatus.CHECKED_IN,
            BookingStatus.BOARDED,
            BookingStatus.COMPLETED
        ]
        if include_pending:
            booking_statuses.append(BookingStatus.PENDING)

        bookings = await db.execute(
            select(Booking)
            .where(
                and_(
                    Booking.schedule_id == uuid.UUID(schedule_id),
                    Booking.status.in_(booking_statuses),
                    Booking.is_deleted.is_(None)
                )
            )
            .options(
                selectinload(Booking.passengers),
                selectinload(Booking.customer)
            )
            .order_by(Booking.created_at)
        )
        bookings = bookings.scalars().all()

        # Build passenger list
        passengers = []
        checked_in_count = 0
        boarded_count = 0
        total_passengers = 0

        for booking in bookings:
            booking_passengers = []
            for passenger in booking.passengers:
                passenger_data = {
                    "id": str(passenger.id),
                    "name": passenger.full_name,
                    "phone": passenger.phone,
                    "email": passenger.email,
                    "seat_number": passenger.seat_number,
                    "pickup_location": passenger.pickup_location,
                    "dropoff_location": passenger.dropoff_location,
                    "special_requests": passenger.special_requests,
                    "emergency_contact": passenger.emergency_contact,
                    "emergency_phone": passenger.emergency_phone,
                    "is_checked_in": passenger.is_checked_in,
                    "checked_in_at": passenger.checked_in_at.isoformat() if passenger.checked_in_at else None,
                    "is_boarded": passenger.is_boarded,
                    "boarded_at": passenger.boarded_at.isoformat() if passenger.boarded_at else None,
                    "status": "checked_in" if passenger.is_checked_in else "pending"
                }
                booking_passengers.append(passenger_data)

                if passenger.is_checked_in:
                    checked_in_count += 1
                if passenger.is_boarded:
                    boarded_count += 1

                total_passengers += 1

            passengers.append({
                "booking_reference": booking.reference,
                "customer_name": booking.customer.full_name if booking.customer else "Unknown",
                "customer_phone": booking.customer.phone if booking.customer else "",
                "booking_status": booking.status.value,
                "passengers": booking_passengers,
                "total_amount": float(booking.total_amount),
                "paid_amount": float(booking.paid_amount),
                "outstanding_balance": float(booking.outstanding_balance)
            })

        # Build manifest
        return {
            "schedule": {
                "id": str(schedule.id),
                "code": schedule.code,
                "departure_date": schedule.departure_date.isoformat(),
                "departure_time": schedule.departure_time.isoformat(),
                "departure_location": schedule.departure_location,
                "destination": schedule.destination,
                "estimated_arrival": schedule.estimated_arrival.isoformat() if schedule.estimated_arrival else None,
                "status": schedule.status.value,
                "route": {
                    "id": str(schedule.route.id),
                    "origin": schedule.route.origin,
                    "destination": schedule.route.destination
                } if schedule.route else None,
                "vehicle": {
                    "id": str(schedule.vehicle.id),
                    "registration": schedule.vehicle.registration,
                    "name": schedule.vehicle.name,
                    "capacity": schedule.vehicle.capacity
                } if schedule.vehicle else None,
                "driver": {
                    "id": str(schedule.driver.id),
                    "name": schedule.driver.full_name,
                    "phone": schedule.driver.phone
                } if schedule.driver else None
            },
            "summary": {
                "total_passengers": total_passengers,
                "checked_in": checked_in_count,
                "boarded": boarded_count,
                "not_checked_in": total_passengers - checked_in_count,
                "capacity": schedule.capacity,
                "available_seats": schedule.available_seats,
                "occupancy_rate": round((total_passengers / schedule.capacity) * 100, 2) if schedule.capacity > 0 else 0
            },
            "passengers": passengers,
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def get_driver_manifest(
        db: AsyncSession,
        driver_id: str,
        date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get manifests for all trips assigned to a driver

        Args:
            driver_id: The driver's ID
            date: Specific date to get manifests for (default: today)
        """
        if not date:
            date = date.today()

        # Get driver's schedules for the day
        query = select(Schedule).where(
            and_(
                Schedule.driver_id == uuid.UUID(driver_id),
                Schedule.departure_date == date,
                Schedule.status != ScheduleStatus.CANCELLED,
                Schedule.is_deleted.is_(None)
            )
        ).order_by(Schedule.departure_time)
        result = await db.execute(query)
        schedules = result.scalars().all()

        manifests = []
        for schedule in schedules:
            manifest = await ManifestService.generate_manifest(db, str(schedule.id))
            manifests.append(manifest)

        return manifests

    @staticmethod
    async def get_check_in_list(
        db: AsyncSession,
        schedule_id: str
    ) -> Dict[str, Any]:
        """
        Get a check-in list for a schedule (simplified manifest for check-in)

        Returns:
            Simplified list of passengers for quick check-in scanning
        """
        # Get schedule
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return {"error": "Schedule not found"}

        # Get passengers who need to be checked in
        passengers = await db.execute(
            select(Passenger)
            .join(Booking)
            .where(
                and_(
                    Booking.schedule_id == uuid.UUID(schedule_id),
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.CHECKED_IN,
                        BookingStatus.BOARDED
                    ]),
                    Booking.is_deleted.is_(None),
                    Passenger.is_deleted.is_(None)
                )
            )
            .order_by(Passenger.seat_number)
        )
        passengers = passengers.scalars().all()

        check_in_list = []
        for passenger in passengers:
            check_in_list.append({
                "id": str(passenger.id),
                "booking_reference": passenger.booking.reference if passenger.booking else "",
                "name": passenger.full_name,
                "seat_number": passenger.seat_number or "",
                "is_checked_in": passenger.is_checked_in,
                "has_boarded": passenger.is_boarded,
                "booking_status": passenger.booking.status.value if passenger.booking else "",
                "special_requests": passenger.special_requests or ""
            })

        return {
            "schedule": {
                "id": str(schedule.id),
                "code": schedule.code,
                "departure_date": schedule.departure_date.isoformat(),
                "departure_time": schedule.departure_time.isoformat()
            },
            "passengers": check_in_list,
            "total": len(check_in_list),
            "checked_in_count": len([p for p in check_in_list if p["is_checked_in"]]),
            "not_checked_in_count": len([p for p in check_in_list if not p["is_checked_in"]])
        }

    @staticmethod
    async def get_boarding_report(
        db: AsyncSession,
        schedule_id: str
    ) -> Dict[str, Any]:
        """
        Get a boarding report for a completed trip

        Returns:
            Complete report of passengers who boarded vs no-shows
        """
        # Get manifest
        manifest = await ManifestService.generate_manifest(db, schedule_id)

        if "error" in manifest:
            return manifest

        # Calculate boarding statistics
        total = manifest["summary"]["total_passengers"]
        boarded = 0
        no_show = 0
        cancelled = 0

        for booking in manifest["passengers"]:
            for passenger in booking["passengers"]:
                if passenger["is_boarded"]:
                    boarded += 1
                elif passenger["is_checked_in"] and not passenger["is_boarded"]:
                    no_show += 1

        # Get cancelled bookings
        cancelled_bookings = await db.execute(
            select(Booking)
            .where(
                and_(
                    Booking.schedule_id == uuid.UUID(schedule_id),
                    Booking.status == BookingStatus.CANCELLED,
                    Booking.is_deleted.is_(None)
                )
            )
        )
        cancelled_bookings = cancelled_bookings.scalars().all()
        cancelled = len(cancelled_bookings)

        return {
            **manifest,
            "boarding_report": {
                "total_passengers": total,
                "boarded": boarded,
                "no_show": no_show,
                "cancelled": cancelled,
                "unaccounted": total - boarded - no_show - cancelled
            }
        }

    @staticmethod
    async def export_manifest_to_csv(
        db: AsyncSession,
        schedule_id: str
    ) -> str:
        """
        Export manifest as CSV string

        Returns:
            CSV formatted string of the manifest
        """
        manifest = await ManifestService.generate_manifest(db, schedule_id)

        if "error" in manifest:
            return ""

        # Build CSV headers
        headers = [
            "Booking Reference",
            "Customer Name",
            "Customer Phone",
            "Passenger Name",
            "Passenger Phone",
            "Seat Number",
            "Pickup Location",
            "Dropoff Location",
            "Checked In",
            "Boarded",
            "Special Requests"
        ]

        rows = []
        for booking in manifest["passengers"]:
            for passenger in booking["passengers"]:
                rows.append([
                    booking["booking_reference"],
                    booking["customer_name"],
                    booking["customer_phone"],
                    passenger["name"],
                    passenger["phone"] or "",
                    passenger["seat_number"] or "",
                    passenger["pickup_location"] or "",
                    passenger["dropoff_location"] or "",
                    "Yes" if passenger["is_checked_in"] else "No",
                    "Yes" if passenger["is_boarded"] else "No",
                    passenger["special_requests"] or ""
                ])

        # Build CSV
        csv_lines = [",".join(headers)]
        for row in rows:
            csv_lines.append(",".join([f'"{cell}"' for cell in row]))

        return "\n".join(csv_lines)

    @staticmethod
    async def update_passenger_check_in(
        db: AsyncSession,
        passenger_id: str,
        checked_in_by: str,
        board: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Update passenger check-in status

        Args:
            passenger_id: The passenger to check in
            checked_in_by: User ID of the person checking in
            board: Whether to board the passenger as well

        Returns:
            Updated passenger data
        """
        query = select(Passenger).where(
            Passenger.id == uuid.UUID(passenger_id)
        ).options(
            selectinload(Passenger.booking)
        )
        result = await db.execute(query)
        passenger = result.scalar_one_or_none()

        if not passenger:
            return {"error": "Passenger not found"}

        passenger.is_checked_in = True
        passenger.checked_in_at = datetime.utcnow()
        passenger.checked_in_by = uuid.UUID(checked_in_by)

        if board:
            passenger.is_boarded = True
            passenger.boarded_at = datetime.utcnow()
            passenger.boarded_by = uuid.UUID(checked_in_by)

        # Update booking status if all passengers checked in
        if passenger.booking:
            all_checked_in = await db.execute(
                select(func.count()).select_from(Passenger)
                .where(
                    and_(
                        Passenger.booking_id == passenger.booking_id,
                        Passenger.is_checked_in == False,
                        Passenger.is_deleted.is_(None)
                    )
                )
            )
            all_checked_in = all_checked_in.scalar() == 0

            if all_checked_in:
                passenger.booking.status = BookingStatus.CHECKED_IN
                if board:
                    passenger.booking.status = BookingStatus.BOARDED

        await db.commit()
        await db.refresh(passenger)

        return {
            "id": str(passenger.id),
            "name": passenger.full_name,
            "is_checked_in": passenger.is_checked_in,
            "checked_in_at": passenger.checked_in_at.isoformat() if passenger.checked_in_at else None,
            "is_boarded": passenger.is_boarded,
            "boarded_at": passenger.boarded_at.isoformat() if passenger.boarded_at else None,
            "booking_reference": passenger.booking.reference if passenger.booking else ""
        }

    @staticmethod
    async def get_manifest_for_print(
        db: AsyncSession,
        schedule_id: str
    ) -> Dict[str, Any]:
        """
        Get manifest formatted for printing (with additional fields for paper manifest)

        Returns:
            Manifest ready for print output with additional fields
        """
        manifest = await ManifestService.generate_manifest(db, schedule_id)

        if "error" in manifest:
            return manifest

        # Add extra fields for print
        manifest["print_info"] = {
            "printed_at": datetime.utcnow().isoformat(),
            "printer_version": "1.0",
            "page_count": (len(manifest["passengers"]) + 20) // 20 + 1  # Approximate pages
        }

        # Add summary lines for each passenger
        for booking in manifest["passengers"]:
            for passenger in booking["passengers"]:
                passenger["additional_info"] = {
                    "booking_date": passenger.get("created_at", ""),
                    "payment_status": "Paid" if booking["paid_amount"] >= booking["total_amount"] else "Pending"
                }

        return manifest