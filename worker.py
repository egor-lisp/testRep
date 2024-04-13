from stroyzakaz_parser import StroyZakaz
from realsv35_parser import Realsv35
from jrc_parser import Jrc
from tg_sender import send_alerts
from utils import load_json, dump_json
import os
import time


class WorkerJrc:
    """ Изменения для сайта жрс.рф  """

    def __init__(self):
        self.cache_filename = 'jrc/old_flats.json'
        self.history_filename = 'jrc/history.json'
        self.old_flats = self.load_cache()
        self.flats = []
        # Изменения
        self.flats_disapeare = []  # Квартиры, которые изчезли
        self.flats_new = []  # Квартиры, которые появились
        self.flats_new_status = []  # Квартиры, у которых поменялись статусы
        self.flats_new_price = []  # Квартиры, которых поменялись цены

    @staticmethod
    def flat_desc(flat):
        """ Создаем текстовое описание квартиры """
        flat_num = flat['flat_num']
        rooms_count = flat['rooms_count']
        floor = flat['floor']
        area = flat['area']
        link = f'[ссылка](https://жрс.рф/obyekty/zhk-garmonia/flat-{flat_num}/)'
        text_desc = f'Номер квартиры: {flat_num}, Кол-во комнат: {rooms_count}, ' \
                    f'Этаж: {floor}, Площадь: {area}м2, {link}'
        return text_desc

    def add_history_flat(self, flat, new=False, disappear=False):
        history = {}
        if os.path.exists(self.history_filename):
            history = load_json(self.history_filename)
        if disappear:
            if not history.get('disappear'):
                history['disappear'] = []
            history['disappear'].append(flat)
        if new:
            if not history.get('new'):
                history['new'] = []
            history['new'].append(flat)
        dump_json(self.history_filename, history)

    def get_flats_now(self):
        for _ in range(10):
            try:
                self.flats = Jrc().get_all_rooms()
                break
            except Exception as ex:
                print('Ошибка в получение квартир JRC')
            time.sleep(2.5)

    def load_cache(self):
        """ Загружаем кэш (старые квартиры), если он есть вернуть True, иначе False """
        if not os.path.exists(self.cache_filename):
            return []
        old_flats = load_json(self.cache_filename)
        return old_flats

    def dump_cache(self):
        dump_json(self.cache_filename, self.flats)

    def track_rooms_count_change(self):
        """ Отслеживаем измнение кол-ва квартир """
        for flat in self.flats:
            flat_num = flat['flat_num']
            flat_new = flat
            if flat_num not in [flat['flat_num'] for flat in self.old_flats]:
                self.flats_new.append(flat_new)
                self.add_history_flat(flat_new, new=True)
                print(f'Появилась новая квартира {flat_num}')
        for flat in self.old_flats:
            flat_num = flat['flat_num']
            flat_old = flat
            if flat_num not in [flat['flat_num'] for flat in self.flats]:
                self.add_history_flat(flat_old, disappear=True)
                self.flats_disapeare.append(flat_old)
                print(f'Исчезла квартира {flat_num}')

    def track_rooms_status_change(self):
        """ Изменение статуса квартир """
        for flat in self.flats:
            flat_num = flat['flat_num']
            same_old_flat = [flat for flat in self.old_flats if flat['flat_num'] == flat_num]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['status'] != flat['status']:
                self.flats_new_status.append({'flat': flat, 'old_status': same_old_flat['status']})
                print(f'Новый статус у квартиры {flat_num}: {flat["status"]}')

    def track_rooms_price_change(self):
        """ Изменение цен """
        for flat in self.flats:
            flat_num = flat['flat_num']
            same_old_flat = [flat for flat in self.old_flats if flat['flat_num'] == flat_num]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['price'] != flat['price']:
                self.flats_new_price.append({'flat': flat, 'old_price': same_old_flat['price']})
                print(f'Новая цена у квартиры {flat_num}: {flat["price"]}')

    def main_compare(self):
        """ Проверяем все и отправляем пользователю """
        self.get_flats_now()  # Получаем квартиры сейчас
        # Проверяем что все правильно загрузилось
        if not self.flats:
            return
        if not self.old_flats:
            self.dump_cache()
            return
        # Проверяем все изменения
        self.track_rooms_count_change()
        self.track_rooms_status_change()
        self.track_rooms_price_change()
        # Остатки по квартирам
        flats_was = len(self.old_flats)
        flats_now = len(self.flats)
        self.dump_cache()  # Сохраняем квартиры в кэш
        # Собираем инфу в текст
        info_text = ''
        if flats_now != flats_was:
            info_text += f'*Изменение по остаткам квартир, было: {flats_was}, стало: {flats_now}*\n'
        if self.flats_disapeare:
            info_text += f'*С продажи исчезли {len(self.flats_disapeare)} квартир:*\n'
            for flat in self.flats_disapeare:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new:
            info_text += f'*На продажу добавилось {len(self.flats_new)} квартир:*\n'
            for flat in self.flats_new:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new_status:
            info_text += f'*Изменился статус у {len(self.flats_new_status)} квартир:*\n'
            for status_info in self.flats_new_status:
                flat = status_info['flat']
                old_status = status_info['old_status']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старый статус: {old_status}, '
                              f'Новый статус: {flat["status"]}\n')
            info_text += '\n'
        if self.flats_new_price:
            info_text += f'*Изменилась цена у {len(self.flats_new_price)} квартир:*\n'
            for price_info in self.flats_new_price:
                flat = price_info['flat']
                old_price = price_info['old_price']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старая цена: {old_price}, '
                              f'Новая цена: {flat["price"]}\n')
        if bool(info_text.replace('\n', '').strip()):
            info_text = '*Изменения на сайте жрс.рф*:\n\n'+info_text
            send_alerts(info_text)


class WorkerRealsv35:

    def __init__(self):
        self.cache_filename = 'realsv35/old_flats.json'
        self.history_filename = 'realsv35/history.json'
        self.old_flats = self.load_cache()
        self.flats = []
        # Изменения
        self.flats_disapeare = []  # Квартиры, которые изчезли
        self.flats_new = []  # Квартиры, которые появились
        self.flats_new_status = []  # Квартиры, у которых поменялись статусы
        self.flats_new_price = []  # Квартиры, которых поменялись цены

    @staticmethod
    def flat_desc(flat):
        """ Создаем текстовое описание квартиры """
        object_name = flat['object_name']
        room_num = flat['room_num']
        rooms_count = flat['rooms_count']
        floor = flat['floor']
        area = flat['area']
        section = flat['section']
        text_desc = f'Объект: {object_name}, Номер квартиры: {room_num}, ' \
                    f'Кол-во комнат: {rooms_count}, Секция: {section}, Этаж: {floor}, ' \
                    f'Площадь: {area}м2'
        return text_desc

    def add_history_flat(self, flat, new=False, disappear=False):
        history = {}
        if os.path.exists(self.history_filename):
            history = load_json(self.history_filename)
        if disappear:
            if not history.get('disappear'):
                history['disappear'] = []
            history['disappear'].append(flat)
        if new:
            if not history.get('new'):
                history['new'] = []
            history['new'].append(flat)
        dump_json(self.history_filename, history)

    def get_flats_now(self):
        for _ in range(10):
            try:
                self.flats = Realsv35().get_all_rooms()
                break
            except Exception as ex:
                print('Ошибка в получение квартир realsv35')
            time.sleep(2.5)

    def load_cache(self):
        """ Загружаем кэш (старые квартиры), если он есть вернуть True, иначе False """
        if not os.path.exists(self.cache_filename):
            return []
        old_flats = load_json(self.cache_filename)
        return old_flats

    def dump_cache(self):
        dump_json(self.cache_filename, self.flats)

    def track_rooms_count_change(self):
        """ Отслеживаем измнение кол-ва квартир """
        for flat in self.flats:
            object_name = flat['object_name']
            flat_num = flat['room_num']
            flat_new = flat
            if flat_num not in [flat['room_num'] for flat in self.old_flats
                                if flat['object_name'] == object_name]:
                self.add_history_flat(flat_new, new=True)
                self.flats_new.append(flat_new)
                print(f'Появилась новая квартира {flat_num}')
        for flat in self.old_flats:
            flat_num = flat['room_num']
            object_name = flat['object_name']
            flat_old = flat
            if flat_num not in [flat['room_num'] for flat in self.flats
                                if flat['object_name'] == object_name]:
                self.add_history_flat(flat_old, disappear=True)
                self.flats_disapeare.append(flat_old)
                print(f'Исчезла квартира {flat_num}')

    def track_rooms_status_change(self):
        """ Изменение статуса квартир """
        for flat in self.flats:
            flat_num = flat['room_num']
            object_name = flat['object_name']
            same_old_flat = [flat for flat in self.old_flats if flat['room_num'] == flat_num
                             and flat['object_name'] == object_name]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['status'] != flat['status']:
                self.flats_new_status.append({'flat': flat, 'old_status': same_old_flat['status']})
                print(f'Новый статус у квартиры {flat_num}: {flat["status"]}')

    def track_rooms_price_change(self):
        """ Изменение цен """
        for flat in self.flats:
            object_name = flat['object_name']
            flat_num = flat['room_num']
            same_old_flat = [flat for flat in self.old_flats if flat['room_num'] == flat_num
                             and flat['object_name'] == object_name]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['price'] != flat['price']:
                self.flats_new_price.append({'flat': flat, 'old_price': same_old_flat['price']})
                print(f'Новая цена у квартиры {flat_num}: {flat["price"]}')

    def main_compare(self):
        """ Проверяем все и отправляем пользователю """
        self.get_flats_now()  # Получаем квартиры сейчас
        # Проверяем что все правильно загрузилось
        if not self.flats:
            return
        if not self.old_flats:
            self.dump_cache()
            return
        # Проверяем все изменения
        self.track_rooms_count_change()
        self.track_rooms_status_change()
        self.track_rooms_price_change()
        # Остатки по квартирам
        flats_was = len(self.old_flats)
        flats_now = len(self.flats)
        self.dump_cache()  # Сохраняем квартиры в кэш
        # Собираем инфу в текст
        info_text = ''
        if flats_now != flats_was:
            info_text += f'*Изменение по остаткам квартир, было: {flats_was}, стало: {flats_now}*\n'
        if self.flats_disapeare:
            info_text += f'*С продажи исчезли {len(self.flats_disapeare)} квартир:*\n'
            for flat in self.flats_disapeare:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new:
            info_text += f'*На продажу добавилось {len(self.flats_new)} квартир:*\n'
            for flat in self.flats_new:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new_status:
            info_text += f'*Изменился статус у {len(self.flats_new_status)} квартир:*\n'
            for status_info in self.flats_new_status:
                flat = status_info['flat']
                old_status = status_info['old_status']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старый статус: {old_status}, '
                              f'Новый статус: {flat["status"]}\n')
            info_text += '\n'
        if self.flats_new_price:
            info_text += f'*Изменилась цена у {len(self.flats_new_price)} квартир:*\n'
            for price_info in self.flats_new_price:
                flat = price_info['flat']
                old_price = price_info['old_price']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старая цена: {old_price}, '
                              f'Новая цена: {flat["price"]}\n')
        if bool(info_text.replace('\n', '').strip()):
            info_text = '*Изменения на сайте realsv35.su*:\n\n'+info_text
            send_alerts(info_text)


class WorkerStroyzakaz:

    def __init__(self):
        self.cache_filename = 'stroyzakaz/old_flats.json'
        self.history_filename = 'stroyzakaz/history.json'
        self.old_flats = self.load_cache()
        self.flats = []
        # Изменения
        self.flats_disapeare = []  # Квартиры, которые изчезли
        self.flats_new = []  # Квартиры, которые появились
        self.flats_new_status = []  # Квартиры, у которых поменялись статусы
        self.flats_new_price = []  # Квартиры, которых поменялись цены

    @staticmethod
    def flat_desc(flat):
        """ Создаем текстовое описание квартиры """
        object_name = flat['name']
        rooms_count = flat['rooms_count']
        floor = flat['floor']
        area = flat['area']
        link = flat['link']
        text_desc = f'Объект: {object_name}, Кол-во комнат: {rooms_count}, ' \
                    f'Этаж: {floor}, Площадь: {area}м2, [{link}](ссылка)'
        return text_desc

    def add_history_flat(self, flat, new=False, disappear=False):
        history = {}
        if os.path.exists(self.history_filename):
            history = load_json(self.history_filename)
        if disappear:
            if not history.get('disappear'):
                history['disappear'] = []
            history['disappear'].append(flat)
        if new:
            if not history.get('new'):
                history['new'] = []
            history['new'].append(flat)
        dump_json(self.history_filename, history)

    def get_flats_now(self):
        for _ in range(10):
            try:
                self.flats = StroyZakaz().get_all_rooms()
                break
            except Exception as ex:
                print('Ошибка в получение квартир стройзаказ')
            time.sleep(2.5)

    def load_cache(self):
        """ Загружаем кэш (старые квартиры), если он есть вернуть True, иначе False """
        if not os.path.exists(self.cache_filename):
            return []
        old_flats = load_json(self.cache_filename)
        return old_flats

    def dump_cache(self):
        dump_json(self.cache_filename, self.flats)

    def track_rooms_count_change(self):
        """ Отслеживаем измнение кол-ва квартир """
        for flat in self.flats:
            flat_id = flat['id']
            flat_new = flat
            if flat_id not in [flat['id'] for flat in self.old_flats]:
                self.add_history_flat(flat_new, new=True)
                self.flats_new.append(flat_new)
                print(f'Появилась новая квартира {flat_id}')
        for flat in self.old_flats:
            flat_id = flat['id']
            flat_old = flat
            if flat_id not in [flat['id'] for flat in self.flats]:
                self.add_history_flat(flat_old, disappear=True)
                self.flats_disapeare.append(flat_old)
                print(f'Исчезла квартира {flat_id}')

    def track_rooms_status_change(self):
        """ Изменение статуса квартир """
        for flat in self.flats:
            flat_id = flat['id']
            same_old_flat = [flat for flat in self.old_flats if flat['id'] == flat_id]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['status'] != flat['status']:
                self.flats_new_status.append({'flat': flat, 'old_status': same_old_flat['status']})
                print(f'Новый статус у квартиры {flat_id}: {flat["status"]}')

    def track_rooms_price_change(self):
        """ Изменение цен """
        for flat in self.flats:
            flat_id = flat['id']
            same_old_flat = [flat for flat in self.old_flats if flat['id'] == flat_id]
            if not same_old_flat:
                continue
            same_old_flat = same_old_flat[0]
            if same_old_flat['price'] != flat['price']:
                self.flats_new_price.append({'flat': flat, 'old_price': same_old_flat['price']})
                print(f'Новая цена у квартиры {flat_id}: {flat["price"]}')

    def main_compare(self):
        """ Проверяем все и отправляем пользователю """
        self.get_flats_now()  # Получаем квартиры сейчас
        # Проверяем что все правильно загрузилось
        if not self.flats:
            return
        if not self.old_flats:
            self.dump_cache()
            return
        # Проверяем все изменения
        self.track_rooms_count_change()
        self.track_rooms_status_change()
        self.track_rooms_price_change()
        # Остатки по квартирам
        flats_was = len(self.old_flats)
        flats_now = len(self.flats)
        self.dump_cache()  # Сохраняем квартиры в кэш
        # Собираем инфу в текст
        info_text = ''
        if flats_now != flats_was:
            info_text += f'*Изменение по остаткам квартир, было: {flats_was}, стало: {flats_now}*\n'
        if self.flats_disapeare:
            info_text += f'*С продажи исчезли {len(self.flats_disapeare)} квартир:*\n'
            for flat in self.flats_disapeare:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new:
            info_text += f'*На продажу добавилось {len(self.flats_new)} квартир:*\n'
            for flat in self.flats_new:
                info_text += f'{self.flat_desc(flat)}\n'
            info_text += '\n'
        if self.flats_new_status:
            info_text += f'*Изменился статус у {len(self.flats_new_status)} квартир:*\n'
            for status_info in self.flats_new_status:
                flat = status_info['flat']
                old_status = status_info['old_status']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старый статус: {old_status}, '
                              f'Новый статус: {flat["status"]}\n')
            info_text += '\n'
        if self.flats_new_price:
            info_text += f'*Изменилась цена у {len(self.flats_new_price)} квартир:*\n'
            for price_info in self.flats_new_price:
                flat = price_info['flat']
                old_price = price_info['old_price']
                info_text += (f'Квартира: {self.flat_desc(flat)} | Старая цена: {old_price}, '
                              f'Новая цена: {flat["price"]}\n')
        if bool(info_text.replace('\n', '').strip()):
            info_text = '*Изменения на сайте жилстройзаказчик.рф*:\n\n'+info_text
            send_alerts(info_text)


def main():
    workers = [WorkerStroyzakaz(), WorkerRealsv35(), WorkerJrc()]
    for worker in workers:
        worker.main_compare()


if __name__ == '__main__':
    main()
