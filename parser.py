import logging
import time
import os
import random
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from proxy_manager import ProxyManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sportschecker_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SportscheckerParser:
    """
    Парсер для сайта Sportschecker.net с постоянной сессией и "человеческим" поведением.
    """
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = None
        self.login_url = "https://ru.sportschecker.net/users/sign_in"
        self.valuebets_url = "https://ru.sportschecker.net/surebets"
        self.proxy_manager = ProxyManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        ]
        self.cookies_file = "cookies.json"
        self.last_login_fail_time = 0
        self.first_session = not os.path.exists(self.cookies_file)  # Check if it's first session
        self.session_ip = None  # Для отслеживания IP сессии

    def _random_delay(self, min_seconds=5, max_seconds=7):
        """Создает случайную задержку."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _save_screenshot(self, filename="screenshot_error.png"):
        """Сохраняет скриншот в папку 'screenshots'."""
        if not self.driver:
            return
        try:
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            screenshot_path = os.path.join("screenshots", filename)
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Скриншот сохранен: {screenshot_path}")
        except WebDriverException as e:
            logger.error(f"Не удалось сохранить скриншот, возможно, браузер был закрыт: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при сохранении скриншота: {e}", exc_info=True)

    def _is_driver_alive(self):
        """Проверяет, жив ли еще драйвер и открыт ли браузер."""
        if not self.driver:
            return False
        try:
            _ = self.driver.window_handles
            return True
        except WebDriverException:
            logger.warning("Соединение с WebDriver потеряно. Браузер был закрыт.")
            return False

    def _is_logged_in(self):
        """
        Проверяет, авторизован ли пользователь, по наличию кнопки "Выйти".
        """
        try:
            logout_link_selector = (By.CSS_SELECTOR, 'a[href="/users/sign_out"]')
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(logout_link_selector)
            )
            logger.info("Проверка авторизации: пользователь в системе (найдена кнопка 'Выйти').")
            return True
        except TimeoutException:
            logger.warning("Проверка авторизации: пользователь не в системе (кнопка 'Выйти' не найдена).")
            return False

    def _check_concurrent_session_error(self):
        """
        Проверяет наличие ошибки одновременного использования аккаунта.
        """
        try:
            # Проверяем наличие сообщения об ошибке
            error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Учётная запись уже используется')]")
            if error_elements:
                logger.error("Обнаружена ошибка одновременного использования аккаунта.")
                self._save_screenshot("concurrent_session_error.png")
                return True
                
            # Также проверяем наличие других сообщений об ошибках
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert.alert-error, .alert.alert-danger, .error-message")
            for element in error_elements:
                if "Учётная запись уже используется" in element.text:
                    logger.error("Обнаружена ошибка одновременного использования аккаунта.")
                    self._save_screenshot("concurrent_session_error.png")
                    return True
                    
        except (NoSuchElementException, WebDriverException):
            pass
        return False

    def _check_connection_error(self):
        """
        Проверяет, отображается ли страница с ошибкой подключения.
        """
        try:
            # Используем короткий таймаут, так как эта проверка не должна блокировать
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, 'main-message'))
            )
            main_message_element = self.driver.find_element(By.ID, 'main-message')
            h1_text = main_message_element.find_element(By.TAG_NAME, 'h1').text.strip()
            if "Не удается получить доступ к сайту" in h1_text:
                logger.warning("Обнаружена ошибка 'Не удается получить доступ к сайту'. Соединение потеряно.")
                self._save_screenshot("connection_error.png")
                return True
        except (TimeoutException, NoSuchElementException):
            pass
        return False

    def _save_cookies(self):
        """Сохраняет куки в файл."""
        try:
            with open(self.cookies_file, 'w') as f:
                json.dump(self.driver.get_cookies(), f)
            logger.info("Куки успешно сохранены.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении куки: {e}")

    def _load_cookies(self):
        """Загружает куки из файла и добавляет их в сессию."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                # Переходим на домен перед добавлением куки
                self.driver.get(self.login_url)
                self.driver.delete_all_cookies()
                
                for cookie in cookies:
                    # Некоторые куки могут иметь expiry как float вместо int
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.error(f"Не удалось добавить куки: {e}")
                
                logger.info("Куки успешно загружены.")
                return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке куки: {e}")
            return False
        return False
        
    def _perform_full_login(self):
        """Выполняет полный цикл входа только если это первая сессия или куки недействительны."""
        # Проверка на паузу после неудачной попытки
        if self.last_login_fail_time > 0 and (time.time() - self.last_login_fail_time) < 420: # 7 минут
            logger.info("Пауза после неудачного входа. Повторная попытка будет через 7-10 минут.")
            return False

        logger.info("Выполняется полный цикл входа...")
        
        # Создаем новый драйвер
        self.close() # Закрываем старый драйвер, если он был
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"Не удалось запустить новый драйвер: {e}", exc_info=True)
            self.last_login_fail_time = time.time()
            return False

        try:
            # Выполняем полный вход
            self.driver.get(self.login_url)
            self._random_delay(3, 5)

            WebDriverWait(self.driver, 45).until(EC.visibility_of_element_located((By.ID, 'user_email')))
            
            logger.info("Ввод логина...")
            email_field = self.driver.find_element(By.ID, 'user_email')
            email_field.clear()
            email_field.send_keys(self.login)
            self._random_delay(1, 2)
            
            logger.info("Ввод пароля...")
            password_field = self.driver.find_element(By.ID, 'user_password')
            password_field.clear()
            password_field.send_keys(self.password)
            self._random_delay(1, 2)

            logger.info("Нажатие кнопки 'Войти'...")
            self.driver.find_element(By.ID, 'sign-in-form-submit-button').click()
            self._random_delay(3, 5)
            
            # Проверяем наличие ошибки одновременного использования
            if self._check_concurrent_session_error():
                logger.error("Обнаружена ошибка одновременного использования аккаунта. Прерываем вход.")
                self.last_login_fail_time = time.time()
                return False
            
            logger.info("Ожидание подтверждения входа (до 30 секунд)...")
            logout_link_selector = (By.CSS_SELECTOR, 'a[href="/users/sign_out"]')
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(logout_link_selector)
            )
            
            # Сохраняем куки после успешного входа
            self._save_cookies()
            logger.info("Успешный вход на сайт подтвержден. Куки сохранены.")
            
            # Помечаем, что первая сессия завершена
            self.first_session = False
            
            return True

        except Exception as e:
            logger.error(f"Ошибка во время полного цикла входа: {e}", exc_info=True)
            self._save_screenshot("full_login_error.png")
            self.last_login_fail_time = time.time()
            return False

    def _restore_session_with_cookies(self):
        """Восстанавливает сессию с помощью сохраненных куки."""
        if not self._is_driver_alive():
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
                options.add_argument(f"user-agent={random.choice(self.user_agents)}")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error(f"Не удалось запустить драйвер: {e}", exc_info=True)
                return False

        try:
            # Загружаем куки
            if self._load_cookies():
                # Переходим на целевую страницу
                self.driver.get(self.valuebets_url)
                self._random_delay(3, 5)
                
                # Проверяем наличие ошибки одновременного использования
                if self._check_concurrent_session_error():
                    logger.error("Обнаружена ошибка одновременного использования аккаунта. Требуется повторный вход.")
                    return False
                
                # Проверяем, успешно ли вошли
                if self._is_logged_in():
                    logger.info("Сессия успешно восстановлена с помощью куки.")
                    return True
                else:
                    logger.warning("Куки устарели или недействительны. Требуется повторный вход.")
                    return False
            else:
                logger.warning("Не удалось загрузить куки. Требуется повторный вход.")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при восстановлении сессии: {e}", exc_info=True)
            return False

    def _force_logout_from_other_sessions(self):
        """
        Принудительно выходит из всех других сессий, если обнаружена ошибка одновременного использования.
        """
        logger.info("Попытка принудительного выхода из всех сессий...")
        
        try:
            # Переходим на страницу профиля/настроек (предполагаем, что там есть кнопка выхода из всех сессий)
            self.driver.get("https://ru.sportschecker.net/users/edit")
            self._random_delay(3, 5)
            
            # Ищем кнопку "Выйти из всех сессий" или аналогичную
            logout_all_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Выйти из всех сессий') or contains(text(), 'Log out all sessions')]")
            
            if logout_all_buttons:
                logout_all_buttons[0].click()
                self._random_delay(3, 5)
                logger.info("Выполнен выход из всех сессий.")
                return True
            else:
                logger.warning("Не найдена кнопка выхода из всех сессий.")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при попытке выхода из всех сессий: {e}")
            return False

    def get_predictions(self):
        """
        Основной метод для получения прогнозов. Управляет сессией и парсит данные.
        """
        try:
            # Если это первая сессия, выполняем полный вход
            if self.first_session:
                if not self._perform_full_login():
                    logger.warning("Не удалось выполнить вход. Прерывание парсинга.")
                    return []
            else:
                # Для последующих сессий пытаемся восстановить сессию с куки
                if not self._restore_session_with_cookies():
                    logger.warning("Не удалось восстановить сессию. Пытаемся выполнить полный вход...")
                    if not self._perform_full_login():
                        logger.warning("Не удалось войти. Прерывание парсинга.")
                        return []

            # Проверяем наличие ошибки одновременного использования после входа
            if self._check_concurrent_session_error():
                logger.error("Обнаружена ошибка одновременного использования после входа. Пытаемся выйти из всех сессий...")
                
                # Пытаемся выйти из всех сессий
                if self._force_logout_from_other_sessions():
                    # После выхода пробуем войти снова
                    if not self._perform_full_login():
                        logger.warning("Не удалось войти после выхода из всех сессий. Прерывание парсинга.")
                        return []
                else:
                    logger.warning("Не удалось выйти из всех сессий. Прерывание парсинга.")
                    return []

            # Переходим на страницу со ставками, если еще не там
            if self.driver.current_url != self.valuebets_url:
                logger.info(f"Переход на страницу со ставками: {self.valuebets_url}")
                self.driver.get(self.valuebets_url)
                self._random_delay(3, 5)

            # Еще раз проверяем на ошибку одновременного использования
            if self._check_concurrent_session_error():
                logger.error("Обнаружена ошибка одновременного использования после перехода на страницу ставок. Прерывание парсинга.")
                return []

            logger.info("Обновление таблицы путем нажатия кнопки 'Фильтровать'...")
            try:
                filter_button = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.ID, 'ft')))
                self._random_delay(2, 4)
                filter_button.click()
                self._random_delay(3, 6)
            except Exception as e:
                logger.error(f"Не удалось нажать кнопку 'Фильтровать': {e}. Попытка парсинга без обновления.")
                self._save_screenshot("filter_button_error.png")

            logger.info("Имитация скроллинга страницы.")
            self.driver.execute_script("window.scrollTo(0, 1000);")
            self._random_delay(1, 2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._random_delay(1, 2)

            logger.info("Начало парсинга таблицы...")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'valuebets-table')))
            table_rows = self.driver.find_elements(By.CSS_SELECTOR, '#valuebets-table > tbody.valuebet_record')
            
            if not table_rows:
                logger.info("Таблица пуста или не содержит прогнозов.")
                return []

            logger.info(f"Найдено {len(table_rows)} строк в таблице для парсинга.")
            predictions = []
            for row in table_rows:
                try:
                    bookmaker_sport_element = row.find_element(By.CSS_SELECTOR, 'td.booker')
                    bookmaker = bookmaker_sport_element.find_element(By.TAG_NAME, 'a').text.strip()
                    
                    all_minor_spans = bookmaker_sport_element.find_elements(By.CSS_SELECTOR, 'span.minor')
                    sport = ""
                    for span in all_minor_spans:
                        span_text = span.text.strip()
                        if '(' not in span_text and ')' not in span_text:
                            sport = span_text
                            break
                    
                    date_time_element = row.find_element(By.CSS_SELECTOR, 'td.time')
                    date = date_time_element.text.strip().replace('\n', ' ')
                    event_element = row.find_element(By.CSS_SELECTOR, 'td.event')
                    teams = event_element.find_element(By.TAG_NAME, 'a').text.strip()
                    tournament = event_element.find_element(By.TAG_NAME, 'span').text.strip()
                    prediction_element = row.find_element(By.CSS_SELECTOR, 'td.coeff')
                    prediction = prediction_element.text.strip()
                    first_part = prediction.split()[0]  # Get "Тб(1.5)"
                    number_str = first_part[3:-1]  # Remove "Тб(" and ")"
                    coeff = float(number_str)
                    odd_element = row.find_element(By.CSS_SELECTOR, 'td.value')
                    odd = odd_element.text.strip()
                    value_element = row.find_element(By.CSS_SELECTOR, 'td span.overvalue')
                    value = value_element.text.strip()

                    if coeff % 0.5 == 0:

                        predictions.append({
                            'bookmaker': bookmaker, 'sport': sport, 'date': date,
                            'tournament': tournament, 'teams': teams, 'prediction': prediction,
                            'odd': odd, 'value': value
                        })

                except Exception as e:
                    logger.warning(f"Не удалось обработать строку таблицы: {e}")
                    continue
            
            logger.info(f"Успешно спарсено {len(predictions)} прогнозов.")

            return predictions

        except Exception as e:
            logger.error(f"Критическая ошибка в методе get_predictions: {e}", exc_info=True)
            self._save_screenshot("critical_parser_error.png")
            self.close()
            return []

    def close(self):
        """Закрывает драйвер, если он активен."""
        if self.driver:
            try:    
                self.driver.quit()
                logger.info("WebDriver сессия успешно закрыта.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии WebDriver: {e}")
            finally:
                self.driver = None

# Пример использования
if __name__ == "__main__":
    # Инициализация парсера с вашими учетными данными
    parser = SportscheckerParser('kosyakovsn@gmail.com', 'SC22332233')
    
    try:
        # Получение прогнозов
        predictions = parser.get_predictions()
        
        # Вывод результатов
        if predictions:
            print(f"Получено {len(predictions)} прогнозов:")
            for i, prediction in enumerate(predictions, 1):
                print(f"{i}. {prediction['teams']} - {prediction['prediction']} ({prediction['value']})")
        else:
            print("Не удалось получить прогнозы.")
    
    finally:
        # Закрытие парсера
        parser.close()