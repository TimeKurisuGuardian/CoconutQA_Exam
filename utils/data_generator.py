import random
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