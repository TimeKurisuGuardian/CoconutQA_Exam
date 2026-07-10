import random
import datetime
from uuid import uuid4
from faker import Faker

# Инициализация библиотеки Faker для генерации тестовых данных
faker = Faker()

class DataGenerator:

    @staticmethod
    def generate_random_email() -> str:
        """Генерация валидного email адреса."""
        return faker.email()

    @staticmethod
    def generate_random_name() -> str:
        """Генерация полного имени (First Name + Last Name)."""
        return faker.name()

    @staticmethod
    def generate_random_password() -> str:
        """
        Генерация безопасного пароля.
        Пароль содержит буквенно-цифровые символы разного регистра
        для успешного прохождения валидации на бэкенде Cinescope.
        """
        return faker.password(
            length=12,
            digits=True,
            upper_case=True,
            lower_case=True,
            special_chars=False
        )

    @staticmethod
    def generate_random_movie_data() -> dict:
        """
        Генерация структуры данных для создания фильма.
        Поля валидируются в соответствии со спецификацией API Cinescope,
        включая валидные значения для поля location (MSK/SPB).
        """
        return {
            "name": f"The Secret of {faker.word().capitalize()}",
            "price": random.randint(150, 500),
            "description": faker.sentence(),
            "imageUrl": "https://images.unsplash.com/photo-1536440136628-849c177e76a1",
            "location": random.choice(["MSK", "SPB"]),
            "published": True,
            "genreId": random.randint(1, 5)
        }

    @staticmethod
    def generate_user_data() -> dict:
        """Генерирует словарь с уникальными данными для создания юзера в БД"""
        return {
            'id': f"{uuid4()}",
            'email': DataGenerator.generate_random_email(),
            'full_name': DataGenerator.generate_random_name(),
            'password': DataGenerator.generate_random_password(),
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now(),
            'verified': False,
            'banned': False,
            'roles': '{USER}'
        }