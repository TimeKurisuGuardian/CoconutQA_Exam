from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from resources.db_creds import DBCreds

# 1. Настройка подключения
connection_string = f"postgresql+psycopg2://{DBCreds.DB_USER}:{DBCreds.DB_PASSWORD}@{DBCreds.DB_HOST}:{DBCreds.DB_PORT}/{DBCreds.DB_NAME}"
engine = create_engine(connection_string)

# 2. Создание базового класса для модели таблицы
Base = declarative_base()

# 3. Описываем модель таблицы uers
class User(Base):
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

def test_alchemy_orm():
    print("Пробуем сделать запрос через чистый ORM SQLAlchemy...")

    # 4. Открываем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    # Вставляем живой ID из DBeaver
    target_id = "85849542-0d22-4406-b1f0-fed21ca1016e"

    # 5. Делаем ORM-запрос
    user = session.query(User).filter(User.id == target_id).first()

    # 6. Читаем данные через точку
    if user:
        print("\nУспешный ответ через ORM:")
        print(f"Имя из объекта: {user.full_name}")
        print(f"Почта из объекта: {user.email}")
        print(f"Статус бана: {user.banned}\n")
    else:
        print("Пользователь с таким ID не найден.")

    # Закрываем сессию
    session.close()

if __name__ == "__main__":
    test_alchemy_orm()