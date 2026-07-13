import random
import pytest
import allure
from db_models.account import AccountTransactionTemplate


@allure.epic("Движок транзакций")
@allure.feature("Переводы между счетами пользователей")
class TestAccountTransactions:

    @allure.story("Успешный перевод средств")
    @allure.title("Позитивный сценарий: Перевод 200 единиц со счета на счёт")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("owner", "pavel")
    @allure.description("""
    Тест проверяет корректность работы транзакционного механизма при валидных условиях.
    Шаги:
    1. Генерация уникальных пользователей и создание счетов в БД
    2. Выполнение перевода средств через бизнес-логику db_helper
    3. Проверка изменения балансов у обоих участников.
    4. Teardown: Очистка базы данных от сгенерированных тестовых данных
    """)
    def test_accounts_transaction_success(self, db_helper, db_session):
        """Позитивный сценарий: Успешный перевод средств между счетами"""

        with allure.step("1. Подготовка тестовых данных: создание счетов Stan и Bob"):
            stan_name = f"Stan_{random.randint(1, 999)}"
            bob_name = f"Bob_{random.randint(1, 999)}"

            stan = AccountTransactionTemplate(user=stan_name, balance=1000)
            bob = AccountTransactionTemplate(user=bob_name, balance=500)

            db_session.add_all([stan, bob])
            db_session.commit()

        with allure.step("2. Проверка исходного состояния балансов в БД"):
            assert stan.balance == 1000
            assert bob.balance == 500

        try:
            with allure.step("3. Выполнение транзакции перевода 200 единиц"):
                db_helper.transfer_money(from_user=stan.user, to_user=bob.user, amount=200)

            with allure.step("4. Валидация: проверка изменения балансов участников"):
                assert stan.balance == 800
                assert bob.balance == 700
                allure.attach(
                    f"Stan: {stan.balance}, Bob: {bob.balance}",
                    name="Финальные балансы",
                    attachment_type=allure.attachment_type.TEXT
                )

        except Exception as e:
            with allure.step("ОШИБКА: Экстренный откат транзакции"):
                db_session.rollback()
            pytest.fail(f"Транзакция завершилась ошибкой, хотя должна была пройти! Ошибка: {e}")

        finally:
            with allure.step("5. Пост-условие (Teardown): Удаление тестовых записей из базы данных"):
                db_session.delete(stan)
                db_session.delete(bob)
                db_session.commit()

    @allure.story("Откат транзакции при ошибках")
    @allure.title("Негативный сценарий: попытка перевода при недостаточном балансе")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("owner", "pavel")
    @allure.description("""
    Тест проверяет атомарность транзакций. При нехватке средств система 
    должна выбросить исключение, а балансы участников не должны измениться.
    """)
    def test_accounts_transaction_insufficient_funds(self, db_helper, db_session):
        """Негативный сценарий: Откат транзакции при нехватке средств"""

        with allure.step("1. Подготовка данных: создание счета Stan с недостаточным балансом"):
            stan_name = f"Stan_{random.randint(1, 999)}"
            bob_name = f"Bob_{random.randint(1, 999)}"

            # У Стэна баланс (50) меньше, чем сумма предполагаемого перевода (200)
            stan = AccountTransactionTemplate(user=stan_name, balance=50)
            bob = AccountTransactionTemplate(user=bob_name, balance=500)

            db_session.add_all([stan, bob])
            db_session.commit()

        # Красиво ловим ожидаемую ошибку средствами pytest.raises
        with allure.step("2. Попытка перевода 200 единиц (Ожидаем ValueError от бизнес-логики)"):
            with pytest.raises(ValueError) as exc_info:
                db_helper.transfer_money(from_user=stan.user, to_user=bob.user, amount=200)

            with allure.step(f"3. Перехват и логирование ожидаемого исключения"):
                db_session.rollback()
                allure.attach(str(exc_info.value), name="Текст перехваченной ошибки",
                              attachment_type=allure.attachment_type.TEXT)

        with allure.step("4. Синхронизация состояния объектов с кэшем БД"):
            db_session.refresh(stan)
            db_session.refresh(bob)

        with allure.step("5. Валидация: проверяем, что балансы физически остались нетронутыми"):
            assert stan.balance == 50, "Баланс отправителя изменился, транзакция не откаталась!"
            assert bob.balance == 500, "Баланс получателя изменился, транзакция не откаталась!"

        with allure.step("6. Пост-условие (Teardown): Удаление мусора из базы данных"):
            db_session.delete(stan)
            db_session.delete(bob)
            db_session.commit()