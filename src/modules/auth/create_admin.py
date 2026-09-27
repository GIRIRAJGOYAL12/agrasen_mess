from getpass import getpass

from sqlalchemy import func, select

from src.common.enums import UserRole
from src.core.security import hash_password
from src.database.session import SessionLocal
from src.modules.users.model import User
from src.database import model_registry

def create_admin() -> None:
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if not name:
        print("Admin name is required.")
        return

    if not email:
        print("Admin email is required.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with SessionLocal() as db:
        statement = select(User).where(
            func.lower(User.email) == email
        )

        existing_user = db.scalar(statement)

        if existing_user:
            print("A user with this email already exists.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin created successfully.")
        print(f"Admin ID: {admin.id}")
        print(f"Admin email: {admin.email}")


if __name__ == "__main__":
    create_admin()