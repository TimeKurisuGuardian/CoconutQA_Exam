import random
import pytest
from db_models.account import AccountTransactionTemplate

def test_accounts_transaction_success(db_helper, db_session):
    """Позитивный сценарий: Успешный перевод средств между счетами"""

    # 1. ПОДГОТОВКА ДАННЫХ: Генерируем уникальные имена для изоляции тестов
    stan_name = f"Stan_{random.randint(1, 999)}"
    bob_name = f"Bob_{random.randint(1, 999)}"

    stan = AccountTransactionTemplate(user=stan_name, balance=1000)
    bob = AccountTransactionTemplate(user=bob_name, balance=500)

    # Сохраняем первичные состояния счетов в БД
    db_session.add_all([stan, bob])
    db_session.commit()

    # Фиксируем исходную точку балансов
    assert stan.balance == 1000
    assert bob.balance == 500

    # 2. ДЕЙСТВИЕ: Вызов метода бизнес-логики перевода
    try:
        db_helper.transfer_money(from_user=stan.user, to_user=bob.user, amount=200)

        # Проверяем фактическое изменение балансов после транзакции
        assert stan.balance == 800
        assert bob.balance == 700
        print(f"\n[Транзакция]: Успешно выполнена! {stan_name}: {stan.balance}, {bob_name}: {bob.balance}")

    except Exception as e:
        # Экстренный откат при непредвиденном падении
        db_session.rollback()
        pytest.fail(f"Транзакция завершилась ошибкой, хотя должна была пройти! Ошибка: {e}")

    finally:
        # Пост-условие (Teardown): Удаление мусора из базы данных
        db_session.delete(stan)
        db_session.delete(bob)
        db_session.commit()


def test_accounts_transaction_insufficient_funds(db_helper, db_session):
    """Негативный сценарий: Откат транзакции (ACID) при нехватке средств на счете"""
    stan_name = f"Stan_{random.randint(1, 999)}"
    bob_name = f"Bob_{random.randint(1, 999)}"

    # У Стэна баланс (50) меньше, чем сумма предполагаемого перевода (200)
    stan = AccountTransactionTemplate(user=stan_name, balance=50)
    bob = AccountTransactionTemplate(user=bob_name, balance=500)

    db_session.add_all([stan, bob])
    db_session.commit()

    # Попытка заведомо некорректного перевода
    try:
        db_helper.transfer_money(from_user=stan.user, to_user=bob.user, amount=200)
        pytest.fail("Тест должен был упасть с ошибкой ValueError, но логика пропустила перевод!")

    except Exception as e:
        print(f"\n[Транзакция]: Поймали ожидаемое исключение бизнес-логики: {e}")
        # Жестко откатываем незавершенную сессию
        db_session.rollback()

    # Синхронизируем состояние локальных объектов с текущим кэшем БД
    db_session.refresh(stan)
    db_session.refresh(bob)

    # Валидация: проверяем, что балансы физически остались нетронутыми
    assert stan.balance == 50, "Баланс отправителя изменился, транзакция не откаталась!"
    assert bob.balance == 500, "Баланс получателя изменился, транзакция не откаталась!"

    # Пост-условие (Teardown): Удаление мусора из базы данных
    db_session.delete(stan)
    db_session.delete(bob)
    db_session.commit()