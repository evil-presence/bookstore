import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.test import LiveServerTestCase

class BookstoreSeleniumTests(LiveServerTestCase):
    def setUp(self):
        service = Service(executable_path='C:/Users/hadye/PycharmProjects/bookstore/echoserver/chromedriver.exe')
        self.driver = webdriver.Chrome(service=service)
        self.driver.implicitly_wait(10)

        from books.models import CustomUser
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Qwasd123',
            first_name='Test',
            role='user'
        )

        from books.models import Book
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            price=100.00
        )

    def tearDown(self):
        self.driver.quit()

    def test_login(self):

        self.driver.get(f'{self.live_server_url}/login/')

        username_field = self.driver.find_element(By.ID, 'id_username')
        password_field = self.driver.find_element(By.ID, 'id_password')
        username_field.send_keys('testuser')
        password_field.send_keys('Qwasd123')

        login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()

        WebDriverWait(self.driver, 10).until(
            EC.url_to_be(f'{self.live_server_url}/')
        )

        welcome_message = self.driver.find_element(By.TAG_NAME, 'p').text
        self.assertIn('Привет, Test', welcome_message)

    def test_checkout(self):

        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.ID, 'id_username').send_keys('testuser')
        self.driver.find_element(By.ID, 'id_password').send_keys('Qwasd123')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_to_be(f'{self.live_server_url}/'))

        self.driver.get(f'{self.live_server_url}/')

        add_to_cart_button = self.driver.find_element(By.XPATH, '//a[text()="В корзину"]')
        add_to_cart_button.click()

        self.driver.get(f'{self.live_server_url}/cart/')

        cart_item = self.driver.find_element(By.TAG_NAME, 'h3').text
        self.assertEqual(cart_item, 'Test Book')

        checkout_button = self.driver.find_element(By.CLASS_NAME, 'btn-save')
        checkout_button.click()

        confirm_button = self.driver.find_element(By.CLASS_NAME, 'btn-save')
        confirm_button.click()

        WebDriverWait(self.driver, 10).until(
            EC.url_to_be(f'{self.live_server_url}/orders/')
        )

        order_message = self.driver.find_element(By.TAG_NAME, 'p').text
        self.assertIn('Состав:', order_message)

    def test_add_book_to_catalog(self):

        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.ID, 'id_username').send_keys('testuser')
        self.driver.find_element(By.ID, 'id_password').send_keys('Qwasd123')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_to_be(f'{self.live_server_url}/'))

        self.driver.get(f'{self.live_server_url}/create/')

        title_field = self.driver.find_element(By.ID, 'id_title')
        author_field = self.driver.find_element(By.ID, 'id_author')
        price_field = self.driver.find_element(By.ID, 'id_price')
        title_field.send_keys('New Test Book')
        author_field.send_keys('New Test Author')
        price_field.send_keys('150.00')

        save_button = self.driver.find_element(By.XPATH, '//button[text()="Сохранить"]')
        save_button.click()

        WebDriverWait(self.driver, 10).until(
            EC.url_to_be(f'{self.live_server_url}/')
        )

        book_title = self.driver.find_element(By.XPATH, '//h3[text()="New Test Book"]').text
        self.assertEqual(book_title, 'New Test Book')
        book_author = self.driver.find_element(By.XPATH, '//p[contains(text(), "Автор: New Test Author")]').text
        book_price = self.driver.find_element(By.XPATH, '//p[contains(text(), "Цена: 150,00 руб.")]').text
        self.assertEqual(book_author, 'Автор: New Test Author')
        self.assertEqual(book_price, 'Цена: 150,00 руб.')
