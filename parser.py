import csv
import os
import random
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PyQt5.QtCore import QThread, pyqtSignal
from locator import AvitoLocator
from utils import get_user_files


class AvitoParser(QThread):
    finished = pyqtSignal()
    update_log = pyqtSignal(str)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.url = ""
        self.base_url = ""
        self.current_page = 1
        self.max_pages = 5
        self.keywords = []
        self.max_price = 0
        self.min_price = 0
        self.geo = ""
        self.data = []
        self.viewed_list = []
        self.sent_to_telegram = []
        self.running = True
        self.parsing_time = 120
        self.rest_time = 10
        self.chat_id = ""

        # Настройка опций Chrome
        self.options = Options()
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")

        # Получаем пути к файлам
        self.files = get_user_files(self.user_id)

    def run(self):
        # Установка ChromeDriver с использованием webdriver_manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)

        try:
            if self.url:
                self._open_new_tab(self.url)
            self.base_url = self._form_base_url(self.url)
            self._load_viewed_list()
            self._parse()
        except Exception as e:
            self.update_log.emit(f'Ошибка: {e}')
        finally:
            # Не закрываем драйвер здесь
            pass

    def _open_new_tab(self, url):
        self.driver.execute_script("window.open(arguments[0], '_blank');", url)
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def _form_base_url(self, url):
        # Убираем параметры страницы из URL
        pattern = re.compile(r"(.*?)(?:\?|&)?p=\d*$")
        match = pattern.match(url)
        if match:
            return match.group(1)
        return url

    def _parse(self):
        self._create_file_csv()
        self._paginator()

    def _paginator(self):
        self.update_log.emit('Страница успешно загружена. Просматриваю объявления')
        while self.running:
            start_time = time.time()
            while time.time() - start_time < self.parsing_time:
                if not self.running:
                    self.send_to_telegram()  # Отправка сообщений перед остановкой
                    return
                self._parse_page()
                time.sleep(random.randint(5, 7))
                next_buttons = self.driver.find_elements(*AvitoLocator.NEXT_BTN)
                if next_buttons:
                    next_buttons[0].click()
                else:
                    self.update_log.emit("Нет кнопки дальше")
                    self.send_to_telegram()
                    self.current_page += 1
                    if self.current_page > self.max_pages:
                        self.current_page = 1
                    next_url = self._form_page_url(self.current_page)
                    self.driver.get(next_url)
                    time.sleep(2)

            # Отдых
            self.update_log.emit(f'Отдых: {self.rest_time} секунд')
            if not self.running:
                self.send_to_telegram()  # Отправка сообщений перед остановкой
                return
            time.sleep(self.rest_time)

    def send_to_telegram(self):
        bot_token = '7062904155:AAF7FkRnOKyVoB-K_PXq-Z5hpSV8N47CpJc'  # Замените на ваш токен
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

        for item in self.data:
            if item['url'] in self.sent_to_telegram:
                continue
            message = (
                f"Название: {item.get('name', 'N/A')}\n"
                f"Цена: {item.get('price', 'N/A')}\n"
                f"Ссылка: {item.get('url', 'N/A')}\n"
                f"Дата публикации: {item.get('date_public', 'N/A')}\n"
                f"Продавец: {item.get('seller_name', 'N/A')}\n"
                f"Адрес: {item.get('geo', 'N/A')}\n"
                "----------------------------------------\n"
            )
            try:
                response = requests.post(url, data={'chat_id': self.chat_id, 'text': message}, timeout=10)
                response.raise_for_status()
                self.sent_to_telegram.append(item['url'])
            except requests.exceptions.RequestException as e:
                self.update_log.emit(f'Ошибка при отправке сообщения в Telegram: {e}')

    def _form_page_url(self, page):
        if page == 1:
            return self.base_url
        elif "?" in self.base_url:
            return f"{self.base_url}&p={page}"
        else:
            return f"{self.base_url}?p={page}"

    def _parse_page(self):
        titles = self.driver.find_elements(*AvitoLocator.TITLES)
        items = []
        for title in titles:
            if not self.running:
                return
            try:
                name = title.find_element(*AvitoLocator.NAME).text
                url = title.find_element(*AvitoLocator.URL).get_attribute("href")
                price = title.find_element(*AvitoLocator.PRICE).get_attribute("content")
                ads_id = title.get_attribute("data-item-id")
                items.append({
                    'name': name,
                    'url': url,
                    'price': price,
                    'ads_id': ads_id
                })
            except Exception as e:
                self.update_log.emit(f"Ошибка при парсинге элемента: {e}")
                continue

        for data in items:
            if not self.running:
                return
            ads_id = data['ads_id']
            if ads_id in self.viewed_list:
                continue
            self.viewed_list.append(ads_id)
            if self.keywords:
                if any(keyword.lower() in (data['name'].lower()) for keyword in
                       self.keywords) and self.min_price <= int(data['price']) <= self.max_price:
                    self.data.append(self._parse_full_page(data['url'], data))
            elif self.min_price <= int(data['price']) <= self.max_price:
                self.data.append(self._parse_full_page(data['url'], data))
            self._save_data(data=data, ads_id=ads_id)

    def _parse_full_page(self, url: str, data: dict) -> dict:
        self.driver.get(url)
        time.sleep(2)

        # Поиск гео-локации
        geo_elements = self.driver.find_elements(*AvitoLocator.GEO)
        if geo_elements:
            data["geo"] = geo_elements[0].text.lower()

        # Поиск имени продавца
        seller_name_elements = self.driver.find_elements(*AvitoLocator.SELLER_NAME)
        if seller_name_elements:
            data["seller_name"] = seller_name_elements[0].text

        # Поиск даты публикации
        date_public_elements = self.driver.find_elements(*AvitoLocator.DATE_PUBLIC)
        if date_public_elements:
            data["date_public"] = date_public_elements[0].text

        return data

    def _save_data(self, data: dict, ads_id: str):
        # Сохранение данных в CSV файл
        with open(self.files['result'], mode="a", newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerow([
                data.get("name", '-'),
                data.get("price", '-'),
                data.get("url", '-'),
                data.get("views", '-'),
                data.get("date_public", '-'),
                data.get("seller_name", 'no'),
                data.get("geo", '-')
            ])

        # Сохранение
        with open(self.files['viewed'], 'a') as file:
            file.write(f"{ads_id}\n")

    def _load_viewed_list(self):
        if not os.path.isfile(self.files['viewed']):
            return []
        with open(self.files['viewed'], 'r') as file:
            return file.read().splitlines()

    def _create_file_csv(self):
        if not os.path.isfile(self.files['result']):
            with open(self.files['result'], 'a', encoding='utf-8', errors='ignore') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Название",
                    "Цена",
                    "Ссылка",
                    "Дата публикации",
                    "Продавец",
                    "Адрес"
                ])

    def _get_file_title(self) -> str:
        if self.keywords:
            title_file = "-".join(map(str.lower, self.keywords))
        else:
            title_file = 'all'
        return title_file

    def stop(self):
        self.running = False
        self.update_log.emit('Остановка парсинга...')
        if hasattr(self, 'driver'):
            try:
                self.driver.close()
                if len(self.driver.window_handles) > 0:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception as e:
                self.update_log.emit(f'Ошибка при закрытии вкладки: {e}')
            self.finished.emit()
