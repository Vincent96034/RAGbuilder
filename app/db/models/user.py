from sqlalchemy import Column, Integer, String
from app.db.database import Base


class UserModel(Base):
    """SQLAlchemy model for the `users` table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


