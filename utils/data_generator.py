# utils/data_generator.py
import random
from faker import Faker

# Инициализируем фейкер один раз для всего класса
faker = Faker()

class DataGenerator:

    @staticmethod
    def generate_random_email() -> str:
        # Faker сам создаст красивый валидный email (например, pavel.kotlyarov@example.com)
        return faker.email()

    @staticmethod
    def generate_random_name() -> str:
        # Генерирует полноценное ФИО (Имя + Фамилия)
        return faker.name()

    @staticmethod
    def generate_random_password() -> str:
        # Генерируем пароль длиной 12 символов, в котором ОБЯЗАТЕЛЬНО будут цифры,
        # большие буквы, маленькие буквы, и ВЫКЛЮЧАЕМ спецсимволы (они нам рушат валидацию)
        return faker.password(
            length=12,
            digits=True,
            upper_case=True,
            lower_case=True,
            special_chars=False
        )

    @staticmethod
    def generate_random_movie_data() -> dict:
        return {
            "name": f"The Secret of {faker.word().capitalize()}",
            "price": random.randint(150, 500),
            "description": faker.sentence(),
            "imageUrl": "https://images.unsplash.com/photo-1536440136628-849c177e76a1",
            "location": random.choice(["MSK", "NSK", "SPB"]),
            "published": True,
            "genreId": random.randint(1, 5)  # Обычно ID популярных жанров
        }