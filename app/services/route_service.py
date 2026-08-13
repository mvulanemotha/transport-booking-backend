import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.route import Route
from app.schemas.route import RouteCreate, RouteUpdate

logger = logging.getLogger(__name__)


class RouteService:
    @staticmethod
    async def create_route(
        db: AsyncSession,
        route_data: RouteCreate,
        user_id: str
    ) -> Route:
        """Create a new route"""
        try:
            # Check if code exists
            query = select(Route).where(Route.code == route_data.code)
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"Route code '{route_data.code}' already exists")

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
                is_international=route_data.is_international,
                border_crossing=route_data.border_crossing,
                waypoints=route_data.waypoints,
                is_active=route_data.is_active if route_data.is_active is not None else True,
                notes=route_data.notes,
                created_by=uuid.UUID(user_id)
            )

            db.add(route)
            await db.commit()
            await db.refresh(route)

            logger.info(f"✅ Route created: {route.code} - {route.name}")
            return route

        except ValueError as e:
            await db.rollback()
            logger.error(f"❌ Value error creating route: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Unexpected error creating route: {str(e)}")
            raise Exception(f"Failed to create route: {str(e)}")

    @staticmethod
    async def get_route(
        db: AsyncSession,
        route_id: str
    ) -> Optional[Route]:
        """Get route by ID"""
        try:
            query = select(Route).where(
                and_(
                    Route.id == uuid.UUID(route_id),
                    Route.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting route {route_id}: {str(e)}")
            return None

    @staticmethod
    async def get_routes(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get routes with filters"""
        try:
            query = select(Route).where(Route.is_deleted.is_(None))

            conditions = []

            if filters.get("is_active") is not None:
                conditions.append(Route.is_active == filters["is_active"])
            if filters.get("is_international") is not None:
                conditions.append(Route.is_international == filters["is_international"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Route.code.ilike(search),
                        Route.name.ilike(search),
                        Route.origin.ilike(search),
                        Route.destination.ilike(search)
                    )
                )
            if filters.get("origin"):
                conditions.append(Route.origin.ilike(f"%{filters['origin']}%"))
            if filters.get("destination"):
                conditions.append(Route.destination.ilike(f"%{filters['destination']}%"))

            if conditions:
                query = query.where(and_(*conditions))

            total_result = await db.execute(
                select(func.count()).select_from(Route).where(and_(*conditions) if conditions else Route.is_deleted.is_(None))
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
        except Exception as e:
            logger.error(f"Error getting routes: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def get_active_routes(
        db: AsyncSession
    ) -> List[Route]:
        """Get all active routes"""
        try:
            query = select(Route).where(
                and_(
                    Route.is_active == True,
                    Route.is_deleted.is_(None)
                )
            ).order_by(Route.code)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active routes: {str(e)}")
            return []

    @staticmethod
    async def update_route(
        db: AsyncSession,
        route_id: str,
        route_data: RouteUpdate,
        user_id: str
    ) -> Optional[Route]:
        """Update route"""
        try:
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
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating route {route_id}: {str(e)}")
            return None

    @staticmethod
    async def delete_route(
        db: AsyncSession,
        route_id: str
    ) -> bool:
        """Soft delete route"""
        try:
            route = await RouteService.get_route(db, route_id)
            if not route:
                return False

            route.is_deleted = datetime.utcnow()
            route.is_active = False
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting route {route_id}: {str(e)}")
            return False