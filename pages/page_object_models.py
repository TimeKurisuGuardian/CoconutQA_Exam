import allure
from playwright.sync_api import Page
from pages.base_page import BasePage


class CinescopRegisterPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.home_url}register"

        self.full_name_input = "input[name='fullName']"
        self.email_input = "input[name='email']"
        self.password_input = "input[name='password']"
        self.repeat_password_input = "input[name='passwordRepeat']"

        self.register_button = "button[data-qa-id='register_submit_button']"
        self.sign_button = "a[href='/login' and text()='Войти']"

    @allure.step("Открытие страницы регистрации")
    def open(self):
        self.open_url(self.url)

    @allure.step("Регистрация нового пользователя: {email}")
    def register(self, full_name: str, email: str, password: str, confirm_password: str):
        self.enter_text_to_element(self.full_name_input, full_name)
        self.enter_text_to_element(self.email_input, email)
        self.enter_text_to_element(self.password_input, password)
        self.enter_text_to_element(self.repeat_password_input, confirm_password)
        self.click_element(self.register_button)

    @allure.step("Проверка перенаправления на страницу авторизации")
    def assert_was_redirect_to_login_page(self):
        self.wait_redirect_for_url(f"{self.home_url}login")

    @allure.step("Проверка появления уведомления об успешной регистрации")
    def assert_allert_was_pop_up(self):
        self.check_pop_up_element_with_text("Подтвердите свою почту")


class CinescopLoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.home_url}login"

        self.email_input = "input[name='email']"
        self.password_input = "input[name='password']"
        self.login_button = "button[data-qa-id='login_submit_button']"
        self.profile_button = page.get_by_role("link", name="Профиль")

    @allure.step("Открытие страницы авторизации")
    def open(self):
        self.open_url(self.url)

    @allure.step("Авторизация пользователя: {email}")
    def login(self, email: str, password: str):
        self.enter_text_to_element(self.password_input, password)
        self.enter_text_to_element(self.email_input, email)
        self.click_element(self.login_button)

    @allure.step("Проверка перенаправления на главную страницу")
    def assert_was_redirect_to_home_page(self):
        self.wait_redirect_for_url(self.home_url)

    @allure.step("Проверка успешности авторизации сессии")
    def assert_allert_was_pop_up(self):
        with allure.step("Проверка видимости элемента 'Профиль' в шапке сайта"):
            self.profile_button.wait_for(state="visible", timeout=5000)
            assert self.profile_button.is_visible(), "Кнопка 'Профиль' не отображается, сессия неактивна"


class MoviePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.review_textarea = "textarea[placeholder='Написать отзыв']"
        self.submit_review_button = "button:has-text('Отправить')"

    @allure.step("Оставление отзыва под фильмом: {text}")
    def leave_review(self, text: str):
        self.enter_text_to_element(self.review_textarea, text)
        self.click_element(self.submit_review_button)

    @allure.step("Проверка, что отзыв успешно добавлен на страницу")
    def assert_review_was_added(self, text: str):
        self.check_pop_up_element_with_text("Отзыв успешно создан")

        with allure.step("Поиск текста отзыва в блоке комментариев"):
            review_locator = self.page.get_by_text(text)
            review_locator.wait_for(state="visible", timeout=5000)
            assert review_locator.is_visible(), f"Отзыв с текстом '{text}' не найден на странице фильма"