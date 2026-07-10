from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AccountTransactionTemplate(Base):
    """ORM-модель для таблицы аккаунтов и баланса"""
    __tablename__ = 'accounts_transaction_template'

    # В базе поле user это строка(имя) и оно является первичным ключом
    user = Column(String, primary_key=True)
    balance = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Account(user='{self.user}', balance={self.balance})>"