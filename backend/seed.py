from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


def seed_users():
    db = SessionLocal()

    try:
        users = [
            {
                "email": "staff@busy.com",
                "password": "Staff@123",
                "role": UserRole.STAFF,
            },
            {
                "email": "instructor@busy.com",
                "password": "Instructor@123",
                "role": UserRole.INSTRUCTOR,
            },
        ]

        for user_data in users:
            existing_user = (
                db.query(User)
                .filter(User.email == user_data["email"])
                .first()
            )

            if existing_user:
                print(f"User already exists: {user_data['email']}")
                continue

            user = User(
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
            )

            db.add(user)

        db.commit()
        print("Demo users seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_users()