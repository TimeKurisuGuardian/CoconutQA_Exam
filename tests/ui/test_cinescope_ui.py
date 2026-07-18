import time
import pytest
import allure
from playwright.sync_api import sync_playwright
from pages.page_object_models import CinescopRegisterPage, CinescopLoginPage, MoviePage
from utils.data_generator import DataGenerator


@allure.epic("Тестирование UI")
@allure.feature("Тестирование Страницы Register")
@pytest.mark.ui
class TestRegisterPage:

    @allure.title("Проведение успешной регистрации")
    def test_register_by_ui(self):
        with sync_playwright() as playwright:
            random_email = DataGenerator.generate_random_email()
            random_name = DataGenerator.generate_random_name()
            random_password = DataGenerator.generate_random_password()

            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()

            register_page = CinescopRegisterPage(page)
            register_page.open()

            register_page.register(f"PlaywrightTest {random_name}", random_email, random_password, random_password)

            register_page.assert_was_redirect_to_login_page()
            register_page.make_screenshot_and_attach_to_allure()
            register_page.assert_allert_was_pop_up()

            time.sleep(5)
            browser.close()


@allure.epic("Тестирование UI")
@allure.feature("Тестирование Страницы Login")
@pytest.mark.ui
class TestloginPage:

    @allure.title("Проведение успешного входа в систему")
    def test_login_by_ui(self, ui_registered_user):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            login_page = CinescopLoginPage(page)

            login_page.open()
            login_page.login(ui_registered_user.email, ui_registered_user.password)

            # Ожидание сохранения сессии в контексте браузера перед перезагрузкой
            time.sleep(2)
            page.reload()

            login_page.assert_was_redirect_to_home_page()
            login_page.make_screenshot_and_attach_to_allure()
            login_page.assert_allert_was_pop_up()

            time.sleep(5)
            browser.close()


@allure.epic("Тестирование UI")
@allure.feature("Тестирование отзывов")
@pytest.mark.ui
class TestMovieReview:

    @allure.title("Успешное оставление отзыва под фильмом авторизованным пользователем")
    def test_leave_review_by_auth_user(self, ui_registered_user):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()

            login_page = CinescopLoginPage(page)
            login_page.open()
            login_page.login(ui_registered_user.email, ui_registered_user.password)
            time.sleep(2)
            page.reload()

            # Ожидание доступности сессии (появление элемента профиля на главной странице)
            login_page.profile_button.wait_for(state="visible", timeout=5000)

            movie_page = MoviePage(page)
            movie_page.open_url(f"{movie_page.home_url}movies")

            # Ожидание полной отрисовки динамического контента на странице фильмов
            page.locator("button:has-text('Подробнее')").first.wait_for(state="visible", timeout=5000)
            page.locator("button:has-text('Подробнее')").first.click(force=True)

            # Формирование уникального текста отзыва во избежание дублирования данных
            random_review = f"QA_Automation_Review_{DataGenerator.generate_random_name()}"

            movie_page.leave_review(random_review)

            movie_page.assert_review_was_added(random_review)
            movie_page.make_screenshot_and_attach_to_allure()

            time.sleep(3)
            browser.close()