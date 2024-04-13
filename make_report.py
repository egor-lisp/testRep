import os.path
from utils import load_json, dump_json
from tg_sender import send_file
import xlwt
from datetime import datetime


def make_report_jrc(site):
    if site == 'жрс.рф':
        history_path = 'jrc/history.json'
    elif site == 'realsv35':
        history_path = 'realsv35/history.json'
    elif site == 'stroyzakaz':
        history_path = 'stroyzakaz/history.json'
    else:
        return
    if not os.path.exists(history_path):
        return
    history = load_json(history_path)
    last_report_date = history.get('last_report_date')
    if not last_report_date:
        last_report_date = datetime.today().strftime('%d-%m-%Y %H:%M')
    curent_date = datetime.today().strftime('%d-%m-%Y %H:%M')
    flats_disappear = []  # Квартиры, которые исчезли
    flats_new = []  # Квартиры, которые появились
    object_names = []  # Названия ЖК
    # Собираем исчезнувшие квартиры
    for flat in history.get('disappear') or []:
        object_name = flat.get('object_name')
        if site == 'stroyzakaz':
            object_name = flat['name']
        object_names.append(object_name)
        if site == 'жрс.рф':
            num = flat['flat_num']
        elif site == 'realsv35':
            num = flat['room_num']
        elif site == 'stroyzakaz':
            object_names.remove(object_name)
            num = object_name.split('кв.')[1]
            object_name = object_name.split('кв.')[0]
            object_names.append(object_name)
        else:
            return
        if site == 'жрс.рф':
            rooms_count = int(flat['rooms_count'].split('-комнатная')[0])
        elif site == 'realsv35':
            rooms_count = int(flat['rooms_count'].split('кк')[0])
        elif site == 'stroyzakaz':
            rooms_count = flat['rooms_count']
            if rooms_count == 'Студия':
                rooms_count = 1
            else:
                rooms_count = int(rooms_count)
        else:
            return
        area = float(flat['area'].replace(',', '.'))
        if site == 'жрс.рф':
            price = float(flat['price'])
        elif site == 'realsv35':
            price = float(flat['price'].replace('р.', '').replace(' ', ''))
        elif site == 'stroyzakaz':
            price = float(flat['price'])
        else:
            return
        price_for_m2 = round(price / area)
        if site == 'жрс.рф':
            plan_link = flat['plan_img']
        elif site == 'realsv35':
            plan_link = flat['image_url']
        elif site == 'stroyzakaz':
            plan_link = flat['image_url']
        else:
            return
        flats_disappear.append({
            'object_name': object_name, 'num': num, 'rooms_count': rooms_count,
            'area': area, 'price': price, 'price_for_m2': price_for_m2,
            'plan_link': plan_link
        })
    # Собираем новые квартиры
    for flat in history.get('new') or []:
        object_name = flat.get('object_name')
        if site == 'stroyzakaz':
            object_name = flat['name']
        object_names.append(object_name)
        if site == 'жрс.рф':
            num = flat['flat_num']
        elif site == 'realsv35':
            num = flat['room_num']
        elif site == 'stroyzakaz':
            object_names.remove(object_name)
            num = object_name.split('кв.')[1]
            object_name = object_name.split('кв.')[0]
            object_names.append(object_name)
        else:
            return
        if site == 'жрс.рф':
            rooms_count = int(flat['rooms_count'].split('-комнатная')[0])
        elif site == 'realsv35':
            rooms_count = int(flat['rooms_count'].split('кк')[0])
        elif site == 'stroyzakaz':
            rooms_count = flat['rooms_count']
            if rooms_count == 'Студия':
                rooms_count = 1
            else:
                rooms_count = int(rooms_count)
        else:
            return
        area = float(flat['area'].replace(',', '.'))
        if site == 'жрс.рф':
            price = float(flat['price'])
        elif site == 'realsv35':
            price = float(flat['price'].replace('р.', '').replace(' ', ''))
        elif site == 'stroyzakaz':
            price = float(flat['price'])
        else:
            return
        price_for_m2 = round(price / area)
        if site == 'жрс.рф':
            plan_link = flat['plan_img']
        elif site == 'realsv35':
            plan_link = flat['image_url']
        elif site == 'stroyzakaz':
            plan_link = flat['image_url']
        else:
            return
        flats_new.append({
            'object_name': object_name, 'num': num, 'rooms_count': rooms_count,
            'area': area, 'price': price, 'price_for_m2': price_for_m2,
            'plan_link': plan_link
        })

    if not flats_new and not flats_disappear:
        return
    
    # Создаем excel файл
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet 1")
    sheet1.write(0, 0, "Наименование сайта")  # Имя сайта
    sheet1.write(0, 1, site)

    object_names = list(set(object_names))
    m = 0
    for object_name in object_names:
        sheet1.write(m+1, 0, "Наименование ЖК")
        sheet1.write(m+1, 1, object_name)

        # Пишем пропавшие квартиры
        sheet1.write(m+2, 0, f'За неделю с "{last_report_date}" по "{curent_date}" из выдачи пропали квартиры:')
        sheet1.write(m+3, 0, 'Номер квартиры')
        sheet1.write(m+3, 1, 'Кол-во комнат')
        sheet1.write(m+3, 2, 'Площадь')
        sheet1.write(m+3, 3, 'Стоимость')
        sheet1.write(m+3, 4, 'Цена, за 1 м2')
        sheet1.write(m+3, 5, 'Ссылка на картинку планировки')
        n = m+4
        total_1rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        total_2rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        total_3rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        for flat in [f for f in flats_disappear if f['object_name'] == object_name]:
            flat_num = flat['num']
            rooms_count = flat['rooms_count']
            area = flat['area']
            price = flat['price']
            price_for_m2 = flat['price_for_m2']
            plan_link = flat['plan_link']
            if rooms_count == 1:
                total_1rooms['area'] += area
                total_1rooms['price'] += price
                total_1rooms['price_for_m2'] += price_for_m2
            if rooms_count == 2:
                total_2rooms['area'] += area
                total_2rooms['price'] += price
                total_2rooms['price_for_m2'] += price_for_m2
            if rooms_count == 3:
                total_3rooms['area'] += area
                total_3rooms['price'] += price
                total_3rooms['price_for_m2'] += price_for_m2
            sheet1.write(n, 0, flat_num)
            sheet1.write(n, 1, rooms_count)
            sheet1.write(n, 2, area)
            sheet1.write(n, 3, price)
            sheet1.write(n, 4, price_for_m2)
            sheet1.write(n, 5, plan_link)
            n += 1
        m = n
        # Итого по 1кк
        sheet1.write(m, 0, 'Итого по 1кк квартирам')
        sheet1.write(m, 2, total_1rooms['area'])
        sheet1.write(m, 3, total_1rooms['price'])
        sheet1.write(m, 4, total_1rooms['price_for_m2'])
        # Итого по 2кк
        sheet1.write(m+1, 0, 'Итого по 2кк квартирам')
        sheet1.write(m+1, 2, total_2rooms['area'])
        sheet1.write(m+1, 3, total_2rooms['price'])
        sheet1.write(m+1, 4, total_2rooms['price_for_m2'])
        # Итого по 3кк
        sheet1.write(m+2, 0, 'Итого по 3кк квартирам')
        sheet1.write(m+2, 2, total_3rooms['area'])
        sheet1.write(m+2, 3, total_3rooms['price'])
        sheet1.write(m+2, 4, total_3rooms['price_for_m2'])
        m += 3

        # Пишем появившиеся квартиры
        sheet1.write(m+2, 0, f'За неделю с "{last_report_date}" по "{curent_date}" из выдачи пропали квартиры:')
        sheet1.write(m+3, 0, 'Номер квартиры')
        sheet1.write(m+3, 1, 'Кол-во комнат')
        sheet1.write(m+3, 2, 'Площадь')
        sheet1.write(m+3, 3, 'Стоимость')
        sheet1.write(m+3, 4, 'Цена, за 1 м2')
        sheet1.write(m+3, 5, 'Ссылка на картинку планировки')
        n = m+4
        total_1rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        total_2rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        total_3rooms = {'area': 0, 'price': 0, 'price_for_m2': 0}
        for flat in [f for f in flats_new if f['object_name'] == object_name]:
            flat_num = flat['num']
            rooms_count = flat['rooms_count']
            area = flat['area']
            price = flat['price']
            price_for_m2 = flat['price_for_m2']
            plan_link = flat['plan_link']
            if rooms_count == 1:
                total_1rooms['area'] += area
                total_1rooms['price'] += price
                total_1rooms['price_for_m2'] += price_for_m2
            if rooms_count == 2:
                total_2rooms['area'] += area
                total_2rooms['price'] += price
                total_2rooms['price_for_m2'] += price_for_m2
            if rooms_count == 3:
                total_3rooms['area'] += area
                total_3rooms['price'] += price
                total_3rooms['price_for_m2'] += price_for_m2
            sheet1.write(n, 0, flat_num)
            sheet1.write(n, 1, rooms_count)
            sheet1.write(n, 2, area)
            sheet1.write(n, 3, price)
            sheet1.write(n, 4, price_for_m2)
            sheet1.write(n, 5, plan_link)
            n += 1
        m = n
        # Итого по 1кк
        if total_1rooms['price'] > 0:
            sheet1.write(m, 0, 'Итого по 1кк квартирам')
            sheet1.write(m, 2, total_1rooms['area'])
            sheet1.write(m, 3, total_1rooms['price'])
            sheet1.write(m, 4, round(total_1rooms['price'] / total_1rooms['area']))
        # Итого по 2кк
        if total_2rooms['price'] > 0:
            sheet1.write(m+1, 0, 'Итого по 2кк квартирам')
            sheet1.write(m+1, 2, total_2rooms['area'])
            sheet1.write(m+1, 3, total_2rooms['price'])
            sheet1.write(m+1, 4, round(total_2rooms['price'] / total_2rooms['area']))
        # Итого по 3кк
        if total_3rooms['price'] > 0:
            sheet1.write(m+2, 0, 'Итого по 3кк квартирам')
            sheet1.write(m+2, 2, total_3rooms['area'])
            sheet1.write(m+2, 3, total_3rooms['price'])
            sheet1.write(m+2, 4, round(total_3rooms['price'] / total_3rooms['area']))
        m += 3
    history = dict()
    history['last_report_date'] = curent_date
    dump_json(filepath=history_path, data=history)
    book.save(f"report_{site}.xls")
    send_file(text='Отчет по выдаче', filename=f"report_{site}.xls")


if __name__ == '__main__':
    sites = ['жрс.рф', 'realsv35', 'stroyzakaz']
    for s in sites:
        make_report_jrc(s)
