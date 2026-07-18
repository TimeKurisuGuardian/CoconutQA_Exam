import allure
from playwright.sync_api import Page
from pages.page_action import PageAction  # Импортируем наш вынесенный класс


class BasePage(PageAction):
    def __init__(self, page: Page):
        super().__init__(page)

        self.home_url = "https://dev-cinescope.coconutqa.ru/"
        self.home_button = page.get_by_role("link", name="Cinescope")
        self.all_movies_button = page.get_by_role("link", name="Все фильмы")

    @allure.step("Переход на главную страницу через навигационную панель")
    def go_to_home_page(self):
        self.click_element(self.home_button)
        self.wait_redirect_for_url(self.home_url)

    @allure.step("Переход на страницу 'Все фильмы' через навигационную панель")
    def go_to_all_movies(self):
        self.click_element(self.all_movies_button)
        self.wait_redirect_for_url(f"{self.home_url}movies")