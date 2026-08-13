import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

logger = logging.getLogger(__name__)


class CustomerService:
    @staticmethod
    async def create_customer(
        db: AsyncSession,
        customer_data: CustomerCreate,
        user_id: str
    ) -> Customer:
        """Create a new customer"""
        try:
            # Check if phone exists
            query = select(Customer).where(Customer.phone == customer_data.phone)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise ValueError(f"Phone number '{customer_data.phone}' already registered")

            customer = Customer(
                full_name=customer_data.full_name,
                phone=customer_data.phone,
                email=customer_data.email,
                id_number=customer_data.id_number,
                passport_number=customer_data.passport_number,
                nationality=customer_data.nationality,
                address=customer_data.address,
                date_of_birth=customer_data.date_of_birth,
                gender=customer_data.gender,
                membership_plan=customer_data.membership_plan or "basic",
                notes=customer_data.notes,
                created_by=uuid.UUID(user_id)
            )

            db.add(customer)
            await db.commit()
            await db.refresh(customer)

            logger.info(f"✅ Customer created: {customer.full_name} - {customer.phone}")
            return customer

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error creating customer: {str(e)}")
            raise Exception(f"Failed to create customer: {str(e)}")

    @staticmethod
    async def get_customer(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            query = select(Customer).where(
                and_(
                    Customer.id == uuid.UUID(customer_id),
                    Customer.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {str(e)}")
            return None

    @staticmethod
    async def get_customers(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get customers with filters"""
        try:
            query = select(Customer).where(Customer.is_deleted.is_(None))

            conditions = []

            if filters.get("membership_plan"):
                conditions.append(Customer.membership_plan == filters["membership_plan"])
            if filters.get("is_active") is not None:
                conditions.append(Customer.is_active == filters["is_active"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Customer.full_name.ilike(search),
                        Customer.phone.ilike(search),
                        Customer.email.ilike(search),
                        Customer.id_number.ilike(search)
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            total_result = await db.execute(
                select(func.count()).select_from(Customer).where(and_(*conditions) if conditions else Customer.is_deleted.is_(None))
            )
            total = total_result.scalar()

            page = filters.get("page", 1)
            page_size = filters.get("page_size", 20)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Customer.created_at.desc())

            result = await db.execute(query)
            customers = result.scalars().all()

            return {
                "items": customers,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Error getting customers: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def search_customers(
        db: AsyncSession,
        query: str
    ) -> List[Customer]:
        """Search customers by name, phone, or email"""
        try:
            search = f"%{query}%"
            stmt = select(Customer).where(
                and_(
                    or_(
                        Customer.full_name.ilike(search),
                        Customer.phone.ilike(search),
                        Customer.email.ilike(search),
                        Customer.id_number.ilike(search)
                    ),
                    Customer.is_deleted.is_(None)
                )
            ).limit(20)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []