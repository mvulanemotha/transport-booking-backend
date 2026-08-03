from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import uuid

from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    @staticmethod
    async def create_customer(
        db: AsyncSession,
        customer_data: CustomerCreate,
        user_id: str
    ) -> Customer:
        """Create a new customer"""
        # Check if phone exists
        query = select(Customer).where(Customer.phone == customer_data.phone)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Phone number already registered")

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

        return customer

    @staticmethod
    async def get_customer(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[Customer]:
        """Get customer by ID"""
        query = select(Customer).where(Customer.id == uuid.UUID(customer_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_customers(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get customers with filters"""
        query = select(Customer)

        conditions = []

        if filters.get("membership_plan"):
            conditions.append(Customer.membership_plan == filters["membership_plan"])
        if filters.get("is_active") is not None:
            conditions.append(Customer.is_active == filters["is_active"])
        if filters.get("search"):
            conditions.append(
                or_(
                    Customer.full_name.ilike(f"%{filters['search']}%"),
                    Customer.phone.ilike(f"%{filters['search']}%"),
                    Customer.email.ilike(f"%{filters['search']}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Customer).where(and_(*conditions))
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

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer_id: str,
        customer_data: CustomerUpdate,
        user_id: str
    ) -> Optional[Customer]:
        """Update customer"""
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        if customer_data.full_name:
            customer.full_name = customer_data.full_name
        if customer_data.phone:
            customer.phone = customer_data.phone
        if customer_data.email:
            customer.email = customer_data.email
        if customer_data.id_number:
            customer.id_number = customer_data.id_number
        if customer_data.passport_number:
            customer.passport_number = customer_data.passport_number
        if customer_data.nationality:
            customer.nationality = customer_data.nationality
        if customer_data.address:
            customer.address = customer_data.address
        if customer_data.date_of_birth:
            customer.date_of_birth = customer_data.date_of_birth
        if customer_data.gender:
            customer.gender = customer_data.gender
        if customer_data.membership_plan:
            customer.membership_plan = customer_data.membership_plan
        if customer_data.notes:
            customer.notes = customer_data.notes
        if customer_data.is_active is not None:
            customer.is_active = customer_data.is_active

        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def delete_customer(
        db: AsyncSession,
        customer_id: str
    ) -> bool:
        """Delete customer"""
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return False

        await db.delete(customer)
        await db.commit()

        return True

    @staticmethod
    async def search_customers(
        db: AsyncSession,
        query: str
    ) -> list[Customer]:
        """Search customers by name, phone, or email"""
        search = f"%{query}%"
        stmt = select(Customer).where(
            or_(
                Customer.full_name.ilike(search),
                Customer.phone.ilike(search),
                Customer.email.ilike(search)
            )
        ).limit(20)
        result = await db.execute(stmt)
        return result.scalars().all()