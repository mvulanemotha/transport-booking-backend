from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func ,text
from datetime import datetime
import uuid

from app.models.route import Route
from app.models.schedule import Schedule
from app.models.booking import Booking
from app.schemas.route import RouteCreate, RouteUpdate


class RouteService:
    @staticmethod
    async def create_route(
        db: AsyncSession,
        route_data: RouteCreate,
        user_id: str
    ) -> Route:
        """Create a new route"""
        # Check if code exists
        query = select(Route).where(Route.code == route_data.code)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Route code already exists")

        route = Route(
            code=route_data.code,
            name=route_data.name,
            origin=route_data.origin,
            destination=route_data.destination,
            origin_lat=route_data.origin_lat,
            origin_lng=route_data.origin_lng,
            dest_lat=route_data.dest_lat,
            dest_lng=route_data.dest_lng,
            distance_km=route_data.distance_km,
            estimated_duration=route_data.estimated_duration,
            base_price=route_data.base_price,
            is_international=route_data.is_international or False,
            border_crossing=route_data.border_crossing,
            waypoints=route_data.waypoints,
            is_active=route_data.is_active if route_data.is_active is not None else True,
            notes=route_data.notes,
            created_by=uuid.UUID(user_id)
        )

        db.add(route)
        await db.commit()
        await db.refresh(route)

        return route

    @staticmethod
    async def get_route(
        db: AsyncSession,
        route_id: str
    ) -> Optional[Route]:
        """Get route by ID"""
        query = select(Route).where(
            and_(
                Route.id == uuid.UUID(route_id),
                Route.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_route_by_code(
        db: AsyncSession,
        code: str
    ) -> Optional[Route]:
        """Get route by code"""
        query = select(Route).where(
            and_(
                Route.code == code,
                Route.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_routes(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get routes with filters"""
        query = select(Route).where(Route.is_deleted.is_(None))

        conditions = []

        if filters.get("is_active") is not None:
            conditions.append(Route.is_active == filters["is_active"])
        if filters.get("is_international") is not None:
            conditions.append(Route.is_international == filters["is_international"])
        if filters.get("search"):
            conditions.append(
                or_(
                    Route.code.ilike(f"%{filters['search']}%"),
                    Route.name.ilike(f"%{filters['search']}%"),
                    Route.origin.ilike(f"%{filters['search']}%"),
                    Route.destination.ilike(f"%{filters['search']}%")
                )
            )
        if filters.get("origin"):
            conditions.append(Route.origin.ilike(f"%{filters['origin']}%"))
        if filters.get("destination"):
            conditions.append(Route.destination.ilike(f"%{filters['destination']}%"))

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Route).where(
                and_(*conditions) if conditions else Route.is_deleted.is_(None)
            )
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(Route.code)

        result = await db.execute(query)
        routes = result.scalars().all()

        return {
            "items": routes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_active_routes(
        db: AsyncSession
    ) -> List[Route]:
        """Get all active routes"""
        query = select(Route).where(
            and_(
                Route.is_active == True,
                Route.is_deleted.is_(None)
            )
        ).order_by(Route.code)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_route(
        db: AsyncSession,
        route_id: str,
        route_data: RouteUpdate,
        user_id: str
    ) -> Optional[Route]:
        """Update route"""
        route = await RouteService.get_route(db, route_id)
        if not route:
            return None

        if route_data.name is not None:
            route.name = route_data.name
        if route_data.origin is not None:
            route.origin = route_data.origin
        if route_data.destination is not None:
            route.destination = route_data.destination
        if route_data.origin_lat is not None:
            route.origin_lat = route_data.origin_lat
        if route_data.origin_lng is not None:
            route.origin_lng = route_data.origin_lng
        if route_data.dest_lat is not None:
            route.dest_lat = route_data.dest_lat
        if route_data.dest_lng is not None:
            route.dest_lng = route_data.dest_lng
        if route_data.distance_km is not None:
            route.distance_km = route_data.distance_km
        if route_data.estimated_duration is not None:
            route.estimated_duration = route_data.estimated_duration
        if route_data.base_price is not None:
            route.base_price = route_data.base_price
        if route_data.is_international is not None:
            route.is_international = route_data.is_international
        if route_data.border_crossing is not None:
            route.border_crossing = route_data.border_crossing
        if route_data.waypoints is not None:
            route.waypoints = route_data.waypoints
        if route_data.is_active is not None:
            route.is_active = route_data.is_active
        if route_data.notes is not None:
            route.notes = route_data.notes

        await db.commit()
        await db.refresh(route)

        return route

    @staticmethod
    async def delete_route(
        db: AsyncSession,
        route_id: str
    ) -> bool:
        """Soft delete route"""
        route = await RouteService.get_route(db, route_id)
        if not route:
            return False

        # Check if route has active schedules
        schedules = await db.execute(
            select(Schedule).where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.status != "cancelled",
                    Schedule.is_deleted.is_(None)
                )
            )
        )
        schedules = schedules.scalars().all()
        if schedules:
            raise ValueError("Cannot delete route with active schedules")

        route.is_deleted = datetime.utcnow()
        route.is_active = False
        await db.commit()

        return True

    @staticmethod
    async def get_route_stats(
        db: AsyncSession,
        route_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a route"""
        route = await RouteService.get_route(db, route_id)
        if not route:
            return {"error": "Route not found"}

        # Get schedules count
        total_schedules = await db.execute(
            select(func.count()).select_from(Schedule)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.is_deleted.is_(None)
                )
            )
        )
        total_schedules = total_schedules.scalar() or 0

        # Get completed schedules
        completed_schedules = await db.execute(
            select(func.count()).select_from(Schedule)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.status == "completed",
                    Schedule.is_deleted.is_(None)
                )
            )
        )
        completed_schedules = completed_schedules.scalar() or 0

        # Get total passengers
        total_passengers = await db.execute(
            select(func.sum(Schedule.booked_seats))
            .select_from(Schedule)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.is_deleted.is_(None)
                )
            )
        )
        total_passengers = total_passengers.scalar() or 0

        # Get total revenue (from bookings on this route)
        total_revenue = await db.execute(
            select(func.sum(Booking.total_amount))
            .select_from(Booking)
            .join(Schedule, Booking.schedule_id == Schedule.id)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Booking.status != "cancelled",
                    Booking.is_deleted.is_(None)
                )
            )
        )
        total_revenue = total_revenue.scalar() or 0

        return {
            "route_id": str(route.id),
            "code": route.code,
            "name": route.name,
            "origin": route.origin,
            "destination": route.destination,
            "stats": {
                "total_schedules": total_schedules,
                "completed_schedules": completed_schedules,
                "total_passengers": total_passengers,
                "total_revenue": float(total_revenue)
            }
        }

    @staticmethod
    async def get_popular_routes(
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular routes by booking count"""
        popular = await db.execute(
            select(
                Route.id,
                Route.code,
                Route.origin,
                Route.destination,
                func.count(Booking.id).label("booking_count"),
                func.sum(Booking.total_amount).label("total_revenue")
            )
            .join(Schedule, Schedule.route_id == Route.id)
            .join(Booking, Booking.schedule_id == Schedule.id)
            .where(
                and_(
                    Booking.status != "cancelled",
                    Booking.is_deleted.is_(None),
                    Schedule.is_deleted.is_(None),
                    Route.is_deleted.is_(None)
                )
            )
            .group_by(Route.id)
            .order_by(text("booking_count DESC"))
            .limit(limit)
        )
        popular = popular.all()

        return [
            {
                "id": str(r.id),
                "code": r.code,
                "origin": r.origin,
                "destination": r.destination,
                "booking_count": r.booking_count,
                "total_revenue": float(r.total_revenue) if r.total_revenue else 0
            }
            for r in popular
        ]