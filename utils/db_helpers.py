from sqlalchemy.orm import Session
from db_models.user import UserDBModel
from utils.db_client import get_db_session
class DBHelper:
    def __init__(self, db_session: Session):
        # Хелпер принимает готовую сессию и работает через нее
        self.db_session = db_session

    def get_user_by_id(self, user_id: str):
        """Находит юзера по его уникаольному ID"""
        return self.db_session.query(UserDBModel).filter(UserDBModel.id == user_id).first()

    def get_user_by_email(self, email: str):
        """Находит юзера по его почте"""
        return self.db_session.query(UserDBModel).filter(UserDBModel.email == email).first()

    def delete_user(self, user: UserDBModel):
        """Удаляет юзера из базы и сохраняет изменения"""
        self.db_session.delete(user)
        self.db_session.commit()

if __name__ == "__main__":
    print("Проверяем работу новой архитектуры проекта...")

    # 1. Берем сессию из нашего db_client
    session = get_db_session()

    # 2. Инициализируем наш хелпер
    helper = DBHelper(session)

    # 3. Ищем нашу старую знакомую Синтию по ID через метод хелпера
    target_id = "85849542-0d22-4406-b1f0-fed21ca1016e"
    user_obj = helper.get_user_by_id(target_id)

    if user_obj:
        print("Успех! Хелпер сработал.")
        # Благодаря методу __repr__ объект напечатается красиво!
        print(f"Поймали: {user_obj}")
        # Проверяем метод to_dict()
        print(f"Его словарь: {user_obj.to_dict()}")
    else:
        print("Юзер не найден, давай другой айди")

    session.close()