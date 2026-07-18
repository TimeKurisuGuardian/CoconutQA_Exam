from typing import Union
import allure
from playwright.sync_api import Page, Locator
from utils.tools import Tools


class PageAction:
    def __init__(self, page: Page):
        self.page = page

    def _get_locator(self, locator: Union[str, Locator]) -> Locator:
        """Преобразует переданный селектор в объект Locator."""
        if isinstance(locator, str):
            return self.page.locator(locator)
        return locator

    @allure.step("Переход на страницу: {url}")
    def open_url(self, url: str):
        self.page.goto(url)

    @allure.step("Ввод текста в поле элемента")
    def enter_text_to_element(self, locator: Union[str, Locator], text: str):
        self._get_locator(locator).fill(text)

    @allure.step("Клик по элементу")
    def click_element(self, locator: Union[str, Locator]):
        self._get_locator(locator).click()

    @allure.step("Ожидание перенаправления на URL: {url}")
    def wait_redirect_for_url(self, url: str):
        self.page.wait_for_url(url)
        assert self.page.url == url, f"Перенаправление на URL {url} не выполнено. Текущий URL: {self.page.url}"

    @allure.step("Ожидание изменения состояния элемента на: {state}")
    def wait_for_element(self, locator: Union[str, Locator], state: str = "visible"):
        self._get_locator(locator).wait_for(state=state)

    @allure.step("Создание скриншота текущей страницы и добавление в отчет Allure")
    def make_screenshot_and_attach_to_allure(self):
        screenshot_name = f"screenshot_{Tools.get_timestamp()}.png"
        screenshot_path = Tools.files_dir(nested_directory="screenshots", filename=screenshot_name)

        self.page.screenshot(path=str(screenshot_path), full_page=True)

        with open(screenshot_path, "rb") as file:
            allure.attach(
                file.read(),
                name=f"Screenshot_{Tools.get_timestamp()}",
                attachment_type=allure.attachment_type.PNG
            )

    @allure.step("Проверка отображения и последующего исчезновения уведомления с текстом: {text}")
    def check_pop_up_element_with_text(self, text: str):
        with allure.step(f"Проверка появления уведомления с текстом: {text}"):
            notification_locator = self.page.get_by_text(text)
            notification_locator.wait_for(state="visible")
            assert notification_locator.is_visible(), f"Уведомление с текстом '{text}' не отображается"

        with allure.step(f"Проверка исчезновения уведомления с текстом: {text}"):
            notification_locator.wait_for(state="hidden")
            assert not notification_locator.is_visible(), f"Уведомление с текстом '{text}' не исчезло со страницы"