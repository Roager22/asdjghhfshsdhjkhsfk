# interface.py
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QPlainTextEdit
from parser import AvitoParser

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings/672445436/settings.json'
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle('Парсер Avito')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText('Введите URL')
        layout.addWidget(self.url_input)

        self.keywords_input = QLineEdit(self)
        self.keywords_input.setPlaceholderText('Введите ключевые слова (через запятую)')
        layout.addWidget(self.keywords_input)

        self.max_price_input = QLineEdit(self)
        self.max_price_input.setPlaceholderText('Введите максимальную цену')
        layout.addWidget(self.max_price_input)

        self.min_price_input = QLineEdit(self)
        self.min_price_input.setPlaceholderText('Введите минимальную цену')
        layout.addWidget(self.min_price_input)

        self.geo_input = QLineEdit(self)
        self.geo_input.setPlaceholderText('Введите гео (если нужно)')
        layout.addWidget(self.geo_input)

        self.parsing_time_input = QLineEdit(self)
        self.parsing_time_input.setPlaceholderText('Введите время парсинга (в секундах)')
        layout.addWidget(self.parsing_time_input)

        self.rest_time_input = QLineEdit(self)
        self.rest_time_input.setPlaceholderText('Введите время отдыха (в секундах)')
        layout.addWidget(self.rest_time_input)

        self.max_pages_input = QLineEdit(self)
        self.max_pages_input.setPlaceholderText('Введите максимальное количество страниц')
        layout.addWidget(self.max_pages_input)

        self.chat_id_input = QLineEdit(self)
        self.chat_id_input.setPlaceholderText('Введите Chat ID для Telegram')
        layout.addWidget(self.chat_id_input)

        self.start_button = QPushButton('Начать парсинг', self)
        self.start_button.clicked.connect(self.start_parsing)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Остановить парсинг', self)
        self.stop_button.clicked.connect(self.stop_parsing)
        layout.addWidget(self.stop_button)

        self.log_output = QPlainTextEdit(self)
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def start_parsing(self):
        url = self.url_input.text()
        keywords = self.keywords_input.text().split(',')
        max_price = int(self.max_price_input.text() or '0')
        min_price = int(self.min_price_input.text() or '0')
        geo = self.geo_input.text()
        parsing_time = int(self.parsing_time_input.text() or '120')
        rest_time = int(self.rest_time_input.text() or '10')
        max_pages = int(self.max_pages_input.text() or '5')
        chat_id = self.chat_id_input.text()

        self.parser = AvitoParser()
        self.parser.url = url
        self.parser.keywords = keywords
        self.parser.max_price = max_price
        self.parser.min_price = min_price
        self.parser.geo = geo
        self.parser.parsing_time = parsing_time
        self.parser.rest_time = rest_time
        self.parser.max_pages = max_pages
        self.parser.chat_id = chat_id

        self.parser.update_log.connect(self.append_log)
        self.parser.finished.connect(self.on_finished)

        self.parser.start()

    def stop_parsing(self):
        if hasattr(self, 'parser'):
            self.parser.stop()

    def append_log(self, message: str):
        self.log_output.appendPlainText(message)

    def on_finished(self):
        self.append_log('Парсинг завершён')

    def load_settings(self):
        if os.path.isfile(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                self.url_input.setText(settings.get('url', ''))
                self.keywords_input.setText(settings.get('keywords', ''))
                self.max_price_input.setText(str(settings.get('max_price', 0)))
                self.min_price_input.setText(str(settings.get('min_price', 0)))
                self.geo_input.setText(settings.get('geo', ''))
                self.parsing_time_input.setText(str(settings.get('parsing_time', 120)))
                self.rest_time_input.setText(str(settings.get('rest_time', 10)))
                self.max_pages_input.setText(str(settings.get('max_pages', 5)))
                self.chat_id_input.setText(settings.get('chat_id', ''))

    def closeEvent(self, event):
        settings = {
            'url': self.url_input.text(),
            'keywords': self.keywords_input.text(),
            'max_price': int(self.max_price_input.text() or '0'),
            'min_price': int(self.min_price_input.text() or '0'),
            'geo': self.geo_input.text(),
            'parsing_time': int(self.parsing_time_input.text() or '120'),
            'rest_time': int(self.rest_time_input.text() or '10'),
            'max_pages': int(self.max_pages_input.text() or '5'),
            'chat_id': self.chat_id_input.text(),
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file, indent=4)
        event.accept()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
