from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from resources.db_creds import MoviesDbCreds

# Собираем строку подключения
connection_string = f"postgresql+psycopg2://{MoviesDbCreds.USERNAME}:{MoviesDbCreds.PASSWORD}@{MoviesDbCreds.HOST}:{MoviesDbCreds.PORT}/{MoviesDbCreds.DATABASE_NAME}"

# Создаем один глобальный движок для всего проекта
engine = create_engine(connection_string, echo=False)

# Настраиваем фабрику сессий. autocommit=False означает, что мы будем сохранять всё руками через commit()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """Функция, которая выдает свежую сессию для работы с базой"""
    return SessionLocal()
