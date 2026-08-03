from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.corporate import (
    CorporateCustomer,
    CorporateUser,
    CorporateBookingAgent,
    CorporateInvoice,
    CorporateInvoiceItem
)
from app.models.customer import Customer
from app.models.user import User
from app.schemas.corporate import (
    CorporateCustomerCreate,
    CorporateCustomerUpdate,
    CorporateUserCreate
)


class CorporateService:
    @staticmethod
    async def create_corporate_customer(
        db: AsyncSession,
        corporate_data: CorporateCustomerCreate,
        user_id: str
    ) -> CorporateCustomer:
        """Create a new corporate customer"""
        # Check if company exists
        query = select(CorporateCustomer).where(
            CorporateCustomer.company_name == corporate_data.company_name
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Company already registered")

        corporate = CorporateCustomer(
            company_name=corporate_data.company_name,
            registration_number=corporate_data.registration_number,
            tax_id=corporate_data.tax_id,
            vat_number=corporate_data.vat_number,
            contact_person=corporate_data.contact_person,
            phone=corporate_data.phone,
            email=corporate_data.email,
            website=corporate_data.website,
            billing_address=corporate_data.billing_address,
            shipping_address=corporate_data.shipping_address,
            city=corporate_data.city,
            country=corporate_data.country,
            postal_code=corporate_data.postal_code,
            discount_rate=corporate_data.discount_rate,
            credit_limit=corporate_data.credit_limit,
            credit_available=corporate_data.credit_limit,
            payment_terms=corporate_data.payment_terms,
            default_payment_method=corporate_data.default_payment_method,
            allow_multiple_bookings=corporate_data.allow_multiple_bookings,
            allow_self_service=corporate_data.allow_self_service,
            require_approval=corporate_data.require_approval,
            custom_pricing=corporate_data.custom_pricing,
            subscription_plan=corporate_data.subscription_plan,
            notes=corporate_data.notes,
            internal_notes=corporate_data.internal_notes,
            tags=corporate_data.tags,
            created_by=uuid.UUID(user_id)
        )

        db.add(corporate)
        await db.commit()
        await db.refresh(corporate)

        return corporate

    @staticmethod
    async def get_corporate_customer(
        db: AsyncSession,
        corporate_id: str
    ) -> Optional[CorporateCustomer]:
        """Get corporate customer by ID"""
        query = select(CorporateCustomer).where(
            CorporateCustomer.id == uuid.UUID(corporate_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_corporate_customers(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get corporate customers with filters"""
        query = select(CorporateCustomer)

        conditions = []

        if filters.get("is_active") is not None:
            conditions.append(CorporateCustomer.is_active == filters["is_active"])
        if filters.get("search"):
            conditions.append(
                or_(
                    CorporateCustomer.company_name.ilike(f"%{filters['search']}%"),
                    CorporateCustomer.contact_person.ilike(f"%{filters['search']}%"),
                    CorporateCustomer.email.ilike(f"%{filters['search']}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(CorporateCustomer).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(CorporateCustomer.company_name)

        result = await db.execute(query)
        corporates = result.scalars().all()

        return {
            "items": corporates,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def add_corporate_user(
        db: AsyncSession,
        corporate_id: str,
        user_data: CorporateUserCreate,
        user_id: str
    ) -> CorporateUser:
        """Add a user to a corporate account"""
        # Check if user exists
        user = await db.execute(
            select(User).where(User.id == uuid.UUID(user_data.user_id))
        )
        user = user.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Check if already added
        existing = await db.execute(
            select(CorporateUser).where(
                and_(
                    CorporateUser.corporate_id == uuid.UUID(corporate_id),
                    CorporateUser.user_id == uuid.UUID(user_data.user_id)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already added to this corporate account")

        corporate_user = CorporateUser(
            corporate_id=uuid.UUID(corporate_id),
            user_id=uuid.UUID(user_data.user_id),
            role=user_data.role,
            department=user_data.department,
            job_title=user_data.job_title,
            can_book=user_data.can_book,
            can_cancel=user_data.can_cancel,
            can_view_history=user_data.can_view_history,
            can_view_billing=user_data.can_view_billing,
            can_manage_users=user_data.can_manage_users,
            can_approve_bookings=user_data.can_approve_bookings,
            can_view_reports=user_data.can_view_reports,
            approval_limit=user_data.approval_limit,
            requires_approval=user_data.requires_approval,
            is_active=True,
            created_by=uuid.UUID(user_id)
        )

        db.add(corporate_user)
        await db.commit()
        await db.refresh(corporate_user)

        return corporate_user

    @staticmethod
    async def get_corporate_customers_by_user(
        db: AsyncSession,
        user_id: str
    ) -> List[CorporateCustomer]:
        """Get all corporate accounts a user belongs to"""
        query = select(CorporateCustomer).join(
            CorporateUser,
            CorporateUser.corporate_id == CorporateCustomer.id
        ).where(
            CorporateUser.user_id == uuid.UUID(user_id)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_corporate_credit(
        db: AsyncSession,
        corporate_id: str,
        amount: float
    ) -> Optional[CorporateCustomer]:
        """Update corporate credit usage"""
        corporate = await CorporateService.get_corporate_customer(db, corporate_id)
        if not corporate:
            return None

        corporate.credit_used += amount
        corporate.credit_available = corporate.credit_limit - corporate.credit_used

        await db.commit()
        await db.refresh(corporate)

        return corporate