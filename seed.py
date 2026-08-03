import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.role import Role
from app.core.security import SecurityService


async def create_tables():
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_roles():
    from app.core.database import async_session_maker

    async with async_session_maker() as session:
        roles = [
            {"name": "super_admin", "description": "Super Administrator", "permissions": {"all": True}, "is_system": True},
            {"name": "admin", "description": "Administrator", "permissions": {"manage_users": True, "view_reports": True}, "is_system": True},
            {"name": "driver", "description": "Driver", "permissions": {"view_trips": True, "update_status": True}, "is_system": True},
            {"name": "customer", "description": "Customer", "permissions": {"book_trips": True, "view_bookings": True}, "is_system": True},
        ]

        for role_data in roles:
            role = Role(**role_data)
            session.add(role)

        await session.commit()


async def seed_admin():
    from app.core.database import async_session_maker
    from sqlalchemy import select

    async with async_session_maker() as session:
        query = select(Role).where(Role.name == "super_admin")
        result = await session.execute(query)
        role = result.scalar_one_or_none()

        if role:
            admin = User(
                email="admin@transport.com",
                hashed_password=SecurityService.get_password_hash("admin123"),
                full_name="System Administrator",
                phone="+268 7612 3456",
                role_id=role.id,
                is_active=True,
                is_verified=True
            )
            session.add(admin)
            await session.commit()


async def main():
    print("📦 Creating tables...")
    await create_tables()
    print("✅ Tables created!")

    print("🌱 Seeding roles...")
    await seed_roles()
    print("✅ Roles seeded!")

    print("👤 Seeding admin user...")
    await seed_admin()
    print("✅ Admin user created!")
    print("   Email: admin@transport.com")
    print("   Password: admin123")


if __name__ == "__main__":
    asyncio.run(main())