import requests
from bs4 import BeautifulSoup
from utils import remove_spec_symbols, dump_json
import time


class StroyZakaz:

    site_url = 'https://жилстройзаказчик.рф'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,'
                  'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }
    params = {
        'object': '0',
        'floor_from': '0',
        'floor_to': '16',
        'price_from': '0',
        'price_to': '10466200',
        'square_from': '0',
        'square_to': '122',
    }  # Под эти фильтры попадают все квартиры

    def get_ajax_html(self, page_num):
        """ Получаем html квартир с определенной страницы """
        data = {'page': page_num, 'ajax': 'Y'}
        response = requests.post(url=f'{self.site_url}/kvartiry/', params=self.params, data=data)
        return response.text

    def fetch_page(self, html, results, is_main_page=False):
        """ Из html данных переводим в dict """
        soup = BeautifulSoup(html, features='html.parser')
        total_count = None
        # Получаем общее кол-во квартир, если страница - главная
        if is_main_page:
            rooms_count_text = soup.find(name='div', attrs={'class': 'roomsCountText'})
            total_count = int(rooms_count_text.find('span').text.split(':')[1])
        # Названия квартир, цена и статус
        items = soup.find_all(name='div', attrs={'class': 'listItemWrapper'})
        for item in items:
            name = item.findNext(name='div', attrs={'class': 'listCol1'}).text
            col5 = item.findNext(name='div', attrs={'class': 'listCol5'})
            price = col5.find('p', {'class': 'price'}).text
            if 'Не указана' in price:
                price = 'Не указана'
            else:
                price = float(price.replace(' ', '')[:-1])
            status = col5.find('p', {'class': 'status'}).text
            link = item.find('a')['href']
            image_url = item.find('img')['src']
            rooms_count = item.findNext(name='div', attrs={'class': 'listCol2'}).text
            floor = item.findNext(name='div', attrs={'class': 'listCol3'}).text
            area = item.findNext(name='div', attrs={'class': 'listCol4'}).text.split(' /')[0]
            id_ = int(link.split('/')[-2])
            results.append({
                'name': remove_spec_symbols(name), 'price': price,
                'status': remove_spec_symbols(status), 'link': link,
                'image_url': image_url, 'rooms_count': rooms_count,
                'floor': floor, 'id': id_, 'area': area
            })
        return total_count, results

    def get_all_rooms(self):
        """ Получаем все квартиры """
        rooms = []
        response = requests.get(url=f'{self.site_url}/kvartiry/', params=self.params, headers=self.headers)
        total_count, _ = self.fetch_page(response.text, rooms, is_main_page=True)
        p = 1
        while len(rooms) < total_count:
            html = self.get_ajax_html(p)
            self.fetch_page(html, rooms)
            p += 1
            time.sleep(1)
        return rooms
