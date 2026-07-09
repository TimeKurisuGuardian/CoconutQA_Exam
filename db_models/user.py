from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserDBModel(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String)
    full_name = Column(String)
    password = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    verified = Column(Boolean)
    banned = Column(Boolean)
    roles = Column(String)

    def to_dict(self):
        """Превращает объект базы данных в обычный питоновский словарь"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'password': self.password,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'verified': self.verified,
            'banned': self.banned,
            'roles': self.roles
        }

    def __repr__(self):
        """Красивый вывод объекта в консоль при отладке"""
        return f"<User(id='{self.id}', email='{self.email}', name='{self.full_name})>'"