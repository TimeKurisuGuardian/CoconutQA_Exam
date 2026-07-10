from sqlalchemy.orm import Session
from db_models.user import UserDBModel
from db_models.movie import MovieDBModel
from db_models.account import AccountTransactionTemplate

class DBHelper:
    def __init__(self, db_session: Session):
        # Хелпер принимает готовую сессию и работает через нее
        self.db_session = db_session

    def get_user_by_id(self, user_id: str):
        """Находит юзера по его уникальному ID"""
        return self.db_session.query(UserDBModel).filter(UserDBModel.id == user_id).first()

    def get_user_by_email(self, email: str):
        """Находит юзера по его почте"""
        return self.db_session.query(UserDBModel).filter(UserDBModel.email == email).first()

    def delete_user(self, user: UserDBModel):
        """Удаляет юзера из базы и сохраняет изменения"""
        self.db_session.delete(user)
        self.db_session.commit()

    def create_test_user(self, user_data: dict) -> UserDBModel:
        """Принимает словарь с данными, создает юзера в базе и возвращает объект"""
        # Распаковываем словарь через две звездочки прямо в модель Алхимии
        user = UserDBModel(**user_data)
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def get_movie_by_name(self, name: str):
        """Находит фильм в базе по его точному названию"""
        return self.db_session.query(MovieDBModel).filter(MovieDBModel.name == name).first()

    def delete_movie(self, movie: MovieDBModel):
        """Удаляет фильм из базы"""
        self.db_session.delete(movie)
        self.db_session.commit()

    def transfer_money(self, from_user: str, to_user: str, amount: int):
        """Симулирует транзакцию перевода денег между счетами"""
        # 1. Находим оба аккаунта в базе.
        # Метод .one() вернет объект, а если юзера нет, то выбросит ошибку NoResultFound
        account_from = self.db_session.query(AccountTransactionTemplate).filter_by(user=from_user).one()
        account_to = self.db_session.query(AccountTransactionTemplate).filter_by(user=to_user).one()

        # 2. Проверяем, хватает ли средств
        if account_from.balance < amount:
            raise ValueError("Недостаточно средств на счете для перевода!")

        # 3. Меняем балансы в памяти Алхимии
        account_from.balance -= amount
        account_to.balance += amount

        # 4. Фиксируем транзакцию в Postgres
        self.db_session.commit()