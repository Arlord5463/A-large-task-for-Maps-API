import math

import pygame, pygame_gui, requests, sys, os
from consts import *


# Создать оконное приложение, отображающее карту по координатам в масштабе, который задается программно.
class MapParams(object):
    def __init__(self):
        self.lat = 61.665279  # Координаты центра карты на старте. Задал координаты университета
        self.lon = 50.813492
        self.zoom = 16  # Масштаб карты на старте. Изменяется от 1 до 19
        self.theme = 'light'
        self.pt = ''
        self.address = ''
        self.postal_code = True
        self.type = 'map'

    def update(self, event):
        # Создадим ф-ии по пересчету пикселей в градусы долготы и широты
        def count_latitude_delta():
            H = 450  # Высота экрана в пикселях
            scale = 256 * 2 ** self.zoom  # Размер тайловой карты
            lat_rad = math.radians(self.lat)
            meters_per_pixel = (156543.03392 * math.cos(lat_rad)) / (2 ** self.zoom)
            return (H * meters_per_pixel) / 111320  # Перевод в градусы

        def count_longitude_delta():
            W = 600  # Ширина экрана в пикселях
            return 360 / (2 ** (self.zoom + 8)) * W

        if event.key == pygame.K_1 and self.zoom < 17:
            self.zoom += 1
        elif event.key == pygame.K_2 and self.zoom > 2:
            self.zoom -= 1
        elif event.key == pygame.K_LEFT:
            self.lon = max(self.lon - count_longitude_delta(), -180)
        elif event.key == pygame.K_RIGHT:
            self.lon = min(self.lon + count_longitude_delta(), 180)
        elif event.key == pygame.K_UP:
            self.lat = min(self.lat + count_latitude_delta(), 85)
        elif event.key == pygame.K_DOWN:
            self.lat = max(self.lat - count_latitude_delta(), -85)

    def search(self, text):
        # Находим координаты объекта
        params = {
            'apikey': GEOCODE_APIKEY,
            "geocode": text,
            "format": 'json',
        }
        response = requests.get(GEOCODE_SERVER, params=params)
        # Выдаем информативную ошибку, если запрос неверный
        if not response:
            print("Ошибка выполнения запроса:")
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        json_response = response.json()
        # Меняем координаты карты на координаты объекта
        self.lon, self.lat = \
            json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"][
                "pos"].split()
        # Ставим метку
        self.pt = f"{self.lon},{self.lat},pm2pnm"
        # Записываем адрес
        self.address = \
            json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
                "GeocoderMetaData"]["text"]
        if self.postal_code:
            try:
                self.address += f', {json_response["response"]["GeoObjectCollection"]["featureMember"][0]
                ["GeoObject"]['metaDataProperty']['GeocoderMetaData']['Address']['postal_code']}'
            except:
                pass


# Создание карты с соответствующими параметрами.
def load_map(mp):
    # Создаем URL запрос
    params = {
        'size': '600,450',
        'pt': mp.pt,
        "ll": ",".join([str(mp.lon), str(mp.lat)]),
        "z": str(mp.zoom),
        "theme": mp.theme,
        "maptype": mp.type,
        "apikey": STATIC_APIKEY,
    }
    response = requests.get(STATIC_API_SERVER, params=params)
    # Выдаем информативную ошибку, если запрос неверный
    if not response:
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        print(response.url)
        sys.exit(1)

    # Запись полученного изображения в файл.
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)
    return map_file


def main():
    # Инициализируем pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 450))
    mp = MapParams()
    manager = pygame_gui.UIManager((800, 450))
    clock = pygame.time.Clock()

    # Элементы GUI
    light_theme_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((600, 0), (100, 50)),
                                                      text='Светлая',
                                                      manager=manager)
    dark_theme_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((700, 0), (100, 50)),
                                                     text='Темная',
                                                     manager=manager)

    coord_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((600, 50), (200, 50)),
                                                      manager=manager, placeholder_text='Введите коорд. через пробел')

    base_view = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((600, 100), (100, 50)),
                                             text='Базовая',
                                             manager=manager)
    auto_view = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((700, 100), (100, 50)),
                                             text='Автомобильная',
                                             manager=manager)
    transport_view = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((600, 150), (100, 50)),
                                                  text='Транспортная',
                                                  manager=manager)
    administrative_view = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((700, 150), (100, 50)),
                                                       text='Административная',
                                                       manager=manager)
    text_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((600, 210), (200, 50)),
                                                     manager=manager)
    text_output = pygame_gui.elements.UITextBox(relative_rect=pygame.Rect((600, 310), (200, 100)),
                                                manager=manager, html_text='')
    reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((600, 260), (200, 50)),
                                                text='Сброс поискового результата',
                                                manager=manager)
    postal_code_on_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((600, 420), (100, 30)),
                                                         text='Включить индекс',
                                                         manager=manager)
    postal_code_off_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((700, 420), (100, 30)),
                                                          text='Выключить индекс',
                                                          manager=manager)

    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Обрабатываем различные нажатые клавиши и кнопки GUI.
            elif event.type == pygame.KEYDOWN:
                mp.update(event)
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == light_theme_button:
                    mp.theme = "light"
                elif event.ui_element == dark_theme_button:
                    mp.theme = 'dark'

                elif event.ui_element == base_view:
                    mp.type = 'map'
                elif event.ui_element == auto_view:
                    mp.type = 'driving'
                elif event.ui_element == transport_view:
                    mp.type = 'transit'
                elif event.ui_element == administrative_view:
                    mp.type = 'admin'  # Не работает

                elif event.ui_element == reset_button:
                    mp.pt = ''
                    mp.address = ''
                elif event.ui_element == postal_code_on_button:
                    mp.postal_code = True
                    mp.search(text_input.text)
                elif event.ui_element == postal_code_off_button:
                    mp.postal_code = False
                    mp.search(text_input.text)

            # Обрабатываем введенный текст запроса
            elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_element == text_input:
                    mp.search(event.text)
                elif event.ui_element == coord_input:
                    try:
                        if -90 < float(coord_input.text.split()[0]) < 90 and -180 < float(
                                coord_input.text.split()[1]) < 180:
                            mp.lat = float(coord_input.text.split()[0])
                            mp.lon = float(coord_input.text.split()[1])
                    except Exception:
                        print('Неверный формат ввода')

            manager.process_events(event)
        manager.update(time_delta)
        manager.draw_ui(screen)

        # Создаем файл
        map_file = load_map(mp)
        # Записываем адрес места
        text_output.set_text(mp.address)
        # Рисуем картинку, загружаемую из только что созданного файла.
        screen.blit(pygame.image.load(map_file), (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
