from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.customer_service import CustomerService
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse

logger = logging.getLogger(__name__)
router = APIRouter()



@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new customer"""
    try:
        #customer = await CustomerService.create_customer(db, customer_data, str(current_user.id))
        customer = await CustomerService.get_or_create_customer(
            db, customer_data, str(current_user.id)
        )
        logger.info(f"Customer created: {customer.full_name} by {current_user.email}")
        return customer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}"
        )


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    membership_plan: Optional[str] = Query(None, description="Filter by membership plan"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, phone, email, ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all customers with filters"""
    filters = {
        "membership_plan": membership_plan,
        "is_active": is_active,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await CustomerService.get_customers(db, filters)
    return result


@router.get("/customers/search", response_model=list[CustomerResponse])
async def search_customers(
    q: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Search customers by name, phone, email, or ID"""
    customers = await CustomerService.search_customers(db, q)
    return customers


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get customer by ID"""
    customer = await CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update customer"""
    customer = await CustomerService.update_customer(db, customer_id, customer_data, str(current_user.id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete customer (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    deleted = await CustomerService.delete_customer(db, customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return {"message": "Customer deleted successfully"}