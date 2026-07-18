from pathlib import Path
from datetime import datetime


class Tools:
    @staticmethod
    def project_dir() -> Path:
        """
        Возвращает абсолютный путь к корню проекта.
        """
        # Поднимаемся на два уровня вверх от файла utils/tools.py к корню проекта
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def files_dir(nested_directory: str = None, filename: str = None) -> Path:
        """
        Возвращает путь к директории хранения файлов проекта,
        при необходимости создает целевые директории.
        """
        files_path = Tools.project_dir() / "files"

        if nested_directory:
            files_path = files_path / nested_directory

        files_path.mkdir(parents=True, exist_ok=True)

        if filename:
            return files_path / filename

        return files_path

    @staticmethod
    def get_timestamp() -> str:
        """
        Генерирует временную метку в формате ГГГГ-ММ-ДД_ЧЧ-ММ-СС.
        """
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")