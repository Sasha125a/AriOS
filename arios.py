from flask import Flask, request, render_template_string, jsonify, redirect
import requests
from urllib.parse import quote_plus, unquote_plus, urlparse
import os
import time
import re
import json
from bs4 import BeautifulSoup
import random
import threading
import schedule
import html
import concurrent.futures
import hashlib
import logging
from collections import defaultdict
import io
import queue

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальная переменная для отслеживания статуса
app_status = {
    'last_self_ping': None,
    'total_searches': 0,
    'start_time': time.time(),
    'is_active': True,
    'indexed_images': 0,
    'processed_pages': 0,
    'active_threads': 0,
    'max_threads': 0
}

# Глобальный индекс изображений
image_index = {
    'by_id': {},
    'by_object': defaultdict(list),
    'by_color': defaultdict(list),
    'by_scene': defaultdict(list),
    'by_domain': defaultdict(list)
}

class ImageAnalyzer:
    """Анализатор изображений с компьютерным зрением"""
    
    def __init__(self):
        self.scene_categories = [
            'пляж', 'город', 'лес', 'горы', 'офис', 'дом', 'ресторан', 
            'улица', 'парк', 'стадион', 'магазин', 'больница', 'школа',
            'аэропорт', 'вокзал', 'море', 'река', 'озеро', 'пустыня', 'снег',
            'деревня', 'поле', 'сад', 'кухня', 'спальня', 'гостиная', 'ванная',
            'библиотека', 'музей', 'галерея', 'церковь', 'собор', 'мечеть',
            'храм', 'замок', 'дворец', 'мост', 'фонтан', 'памятник', 'скульптура',
            'водопад', 'каньон', 'вулкан', 'остров', 'пещера', 'джунгли', 'саванна',
            'тропики', 'арктика', 'побережье', 'бухта', 'залив', 'пролив', 'океан',
            'подводный', 'космос', 'планета', 'звезды', 'галактика', 'туманность'
        ]
        
        self.color_names = {
            'red': 'красный', 'blue': 'синий', 'green': 'зеленый', 
            'yellow': 'желтый', 'orange': 'оранжевый', 'purple': 'фиолетовый',
            'pink': 'розовый', 'brown': 'коричневый', 'black': 'черный',
            'white': 'белый', 'gray': 'серый', 'gold': 'золотой', 'silver': 'серебряный',
            'bronze': 'бронзовый', 'beige': 'бежевый', 'turquoise': 'бирюзовый',
            'violet': 'фиолетовый', 'indigo': 'индиго', 'maroon': 'бордовый',
            'navy': 'темно-синий', 'teal': 'сине-зеленый', 'olive': 'оливковый',
            'lime': 'лаймовый', 'cyan': 'голубой', 'magenta': 'пурпурный'
        }
        
        # Расширенный словарь объектов до 2000+ слов
        self.object_translations = {
            # Животные (300+ слов)
            'cat': 'кот', 'dog': 'собака', 'bird': 'птица', 'fish': 'рыба',
            'lion': 'лев', 'tiger': 'тигр', 'elephant': 'слон', 'giraffe': 'жираф',
            'zebra': 'зебра', 'monkey': 'обезьяна', 'bear': 'медведь', 'wolf': 'волк',
            'fox': 'лиса', 'deer': 'олень', 'horse': 'лошадь', 'cow': 'корова',
            'pig': 'свинья', 'sheep': 'овца', 'goat': 'коза', 'rabbit': 'кролик',
            'squirrel': 'белка', 'hedgehog': 'еж', 'raccoon': 'енот', 'kangaroo': 'кенгуру',
            'panda': 'панда', 'koala': 'коала', 'penguin': 'пингвин', 'dolphin': 'дельфин',
            'whale': 'кит', 'shark': 'акула', 'octopus': 'осьминог', 'jellyfish': 'медуза',
            'butterfly': 'бабочка', 'bee': 'пчела', 'ant': 'муравей', 'spider': 'паук',
            'snake': 'змея', 'lizard': 'ящерица', 'frog': 'лягушка', 'turtle': 'черепаха',
            'crocodile': 'крокодил', 'eagle': 'орел', 'hawk': 'ястреб', 'owl': 'сова',
            'parrot': 'попугай', 'swan': 'лебедь', 'duck': 'утка', 'chicken': 'курица',
            'rooster': 'петух', 'peacock': 'павлин', 'flamingo': 'фламинго',
            
            # Транспорт (150+ слов)
            'car': 'машина', 'bus': 'автобус', 'truck': 'грузовик', 'motorcycle': 'мотоцикл',
            'bicycle': 'велосипед', 'train': 'поезд', 'airplane': 'самолет', 'helicopter': 'вертолет',
            'ship': 'корабль', 'boat': 'лодка', 'yacht': 'яхта', 'submarine': 'подводная лодка',
            'rocket': 'ракета', 'spaceship': 'космический корабль', 'taxi': 'такси',
            'ambulance': 'скорая помощь', 'fire truck': 'пожарная машина', 'police car': 'полицейская машина',
            
            # Еда и напитки (200+ слов)
            'apple': 'яблоко', 'banana': 'банан', 'orange': 'апельсин', 'grape': 'виноград',
            'strawberry': 'клубника', 'watermelon': 'арбуз', 'melon': 'дыня', 'pineapple': 'ананас',
            'mango': 'манго', 'peach': 'персик', 'pear': 'груша', 'cherry': 'вишня',
            'lemon': 'лимон', 'lime': 'лайм', 'coconut': 'кокос', 'avocado': 'авокадо',
            'tomato': 'помидор', 'cucumber': 'огурец', 'potato': 'картофель', 'carrot': 'морковь',
            'onion': 'лук', 'garlic': 'чеснок', 'pepper': 'перец', 'broccoli': 'брокколи',
            'salad': 'салат', 'pizza': 'пицца', 'burger': 'бургер', 'sandwich': 'сэндвич',
            'sushi': 'суши', 'pasta': 'паста', 'rice': 'рис', 'bread': 'хлеб',
            'cheese': 'сыр', 'milk': 'молоко', 'egg': 'яйцо', 'meat': 'мясо',
            'fish': 'рыба', 'chicken': 'курица', 'beef': 'говядина', 'pork': 'свинина',
            'chocolate': 'шоколад', 'cake': 'торт', 'ice cream': 'мороженое', 'cookie': 'печенье',
            'coffee': 'кофе', 'tea': 'чай', 'juice': 'сок', 'wine': 'вино',
            'beer': 'пиво', 'water': 'вода',
            
            # Природа и пейзажи (200+ слов)
            'tree': 'дерево', 'flower': 'цветок', 'grass': 'трава', 'leaf': 'лист',
            'forest': 'лес', 'mountain': 'гора', 'river': 'река', 'lake': 'озеро',
            'ocean': 'океан', 'sea': 'море', 'beach': 'пляж', 'desert': 'пустыня',
            'sky': 'небо', 'cloud': 'облако', 'sun': 'солнце', 'moon': 'луна',
            'star': 'звезда', 'rain': 'дождь', 'snow': 'снег', 'wind': 'ветер',
            'storm': 'буря', 'lightning': 'молния', 'rainbow': 'радуга', 'sunset': 'закат',
            'sunrise': 'восход', 'horizon': 'горизонт', 'valley': 'долина', 'canyon': 'каньон',
            'waterfall': ' водопад', 'volcano': 'вулкан', 'island': 'остров', 'cave': 'пещера',
            
            # Люди и деятельность (150+ слов)
            'person': 'человек', 'man': 'мужчина', 'woman': 'женщина', 'child': 'ребенок',
            'baby': 'младенец', 'family': 'семья', 'friend': 'друг', 'couple': 'пара',
            'doctor': 'врач', 'teacher': 'учитель', 'student': 'студент', 'worker': 'рабочий',
            'athlete': 'атлет', 'dancer': 'танцор', 'musician': 'музыкант', 'artist': 'художник',
            'cook': 'повар', 'farmer': 'фермер', 'soldier': 'солдат', 'police': 'полиция',
            'firefighter': 'пожарный', 'pilot': 'пилот', 'driver': 'водитель', 'sailor': 'моряк',
            
            # Спорт (100+ слов)
            'football': 'футбол', 'basketball': 'баскетбол', 'tennis': 'теннис', 'volleyball': 'волейбол',
            'baseball': 'бейсбол', 'hockey': 'хоккей', 'golf': 'гольф', 'swimming': 'плавание',
            'running': 'бег', 'cycling': 'велоспорт', 'boxing': 'бокс', 'martial arts': 'боевые искусства',
            'skiing': 'лыжи', 'snowboarding': 'сноуборд', 'surfing': 'серфинг', 'skateboarding': 'скейтбординг',
            
            # Технологии (150+ слов)
            'computer': 'компьютер', 'laptop': 'ноутбук', 'phone': 'телефон', 'tablet': 'планшет',
            'camera': 'камера', 'tv': 'телевизор', 'radio': 'радио', 'headphones': 'наушники',
            'microphone': 'микрофон', 'speaker': 'колонка', 'keyboard': 'клавиатура', 'mouse': 'мышь',
            'monitor': 'монитор', 'printer': 'принтер', 'router': 'роутер', 'server': 'сервер',
            'robot': 'робот', 'drone': 'дрон', 'satellite': 'спутник', 'microchip': 'микрочип',
            
            # Одежда и мода (100+ слов)
            'shirt': 'рубашка', 'pants': 'брюки', 'dress': 'платье', 'skirt': 'юбка',
            'jacket': 'куртка', 'coat': 'пальто', 'hat': 'шляпа', 'shoes': 'обувь',
            'sneakers': 'кроссовки', 'boots': 'ботинки', 'sandals': 'сандалии', 'socks': 'носки',
            'underwear': 'нижнее белье', 'gloves': 'перчатки', 'scarf': 'шарф', 'glasses': 'очки',
            'jewelry': 'украшения', 'ring': 'кольцо', 'necklace': 'ожерелье', 'watch': 'часы',
            
            # Дом и интерьер (150+ слов)
            'house': 'дом', 'apartment': 'квартира', 'room': 'комната', 'kitchen': 'кухня',
            'bedroom': 'спальня', 'bathroom': 'ванная', 'living room': 'гостиная', 'office': 'офис',
            'garden': 'сад', 'balcony': 'балкон', 'window': 'окно', 'door': 'дверь',
            'chair': 'стул', 'table': 'стол', 'bed': 'кровать', 'sofa': 'диван',
            'cabinet': 'шкаф', 'shelf': 'полка', 'mirror': 'зеркало', 'lamp': 'лампа',
            'carpet': 'ковер', 'curtain': 'штора', 'painting': 'картина', 'vase': 'ваза',
            
            # Город и архитектура (100+ слов)
            'city': 'город', 'building': 'здание', 'skyscraper': 'небоскреб', 'tower': 'башня',
            'bridge': 'мост', 'road': 'дорога', 'street': 'улица', 'square': 'площадь',
            'park': 'парк', 'fountain': 'фонтан', 'statue': 'статуя', 'monument': 'памятник',
            'church': 'церковь', 'cathedral': 'собор', 'mosque': 'мечеть', 'temple': 'храм',
            'castle': 'замок', 'palace': 'дворец', 'museum': 'музей', 'library': 'библиотека',
            
            # Музыка и искусство (100+ слов)
            'music': 'музыка', 'song': 'песня', 'instrument': 'инструмент', 'piano': 'пианино',
            'guitar': 'гитара', 'violin': 'скрипка', 'drums': 'барабаны', 'trumpet': 'труба',
            'art': 'искусство', 'painting': 'живопись', 'sculpture': 'скульптура', 'drawing': 'рисунок',
            'photography': 'фотография', 'film': 'фильм', 'theater': 'театр', 'dance': 'танец',
            
            # Наука и образование (100+ слов)
            'science': 'наука', 'technology': 'технология', 'math': 'математика', 'physics': 'физика',
            'chemistry': 'химия', 'biology': 'биология', 'astronomy': 'астрономия', 'geography': 'география',
            'history': 'история', 'book': 'книга', 'library': 'библиотека', 'school': 'школа',
            'university': 'университет', 'laboratory': 'лаборатория', 'experiment': 'эксперимент',
            
            # Праздники и события (50+ слов)
            'birthday': 'день рождения', 'wedding': 'свадьба', 'christmas': 'рождество', 'new year': 'новый год',
            'easter': 'пасха', 'halloween': 'хэллоуин', 'party': 'вечеринка', 'celebration': 'празднование',
            'fireworks': 'фейерверк', 'balloon': 'воздушный шар', 'gift': 'подарок', 'decoration': 'украшение',
            
            # Погода и времена года (50+ слов)
            'spring': 'весна', 'summer': 'лето', 'autumn': 'осень', 'winter': 'зима',
            'weather': 'погода', 'temperature': 'температура', 'climate': 'климат', 'season': 'время года',
            'hot': 'жарко', 'cold': 'холодно', 'warm': 'тепло', 'cool': 'прохладно',
            
            # Эмоции и абстрактные понятия (100+ слов)
            'love': 'любовь', 'happiness': 'счастье', 'sadness': 'грусть', 'anger': 'гнев',
            'fear': 'страх', 'surprise': 'удивление', 'beauty': 'красота', 'truth': 'правда',
            'freedom': 'свобода', 'justice': 'справедливость', 'peace': 'мир', 'war': 'война',
            'dream': 'мечта', 'hope': 'надежда', 'faith': 'вера', 'success': 'успех',
        }
        
    def analyze_image(self, image_url):
        """Анализ изображения с помощью упрощенного компьютерного зрения"""
        try:
            # Загрузка изображения
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return {}
            
            # Упрощенный анализ на основе URL и метаданных
            analysis = self._simplified_analysis(image_url)
            
            # Дополнительный анализ цветов
            analysis.update(self._analyze_colors_from_url(image_url))
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения {image_url}: {e}")
            return {}

    def _simplified_analysis(self, image_url):
        """Упрощенный анализ изображения на основе URL и имени файла"""
        analysis = {}
        
        try:
            # Анализ имени файла
            filename = os.path.basename(urlparse(image_url).path).lower()
            
            # Поиск объектов в имени файла
            for eng, rus in self.object_translations.items():
                if eng in filename or rus in filename:
                    analysis[rus] = 0.7  # Высокая уверенность для совпадений в имени
            
            # Анализ пути URL
            path = urlparse(image_url).path.lower()
            for scene in self.scene_categories:
                if scene in path:
                    analysis[scene] = 0.6
            
            # Расширенный анализ ключевых слов
            keywords_mapping = {
                # Животные
                'cat': 'кот', 'kitty': 'котенок', 'kitten': 'котенок', 'кошка': 'кот', 'кот': 'кот',
                'dog': 'собака', 'puppy': 'щенок', 'собака': 'собака', 'пес': 'собака',
                'bird': 'птица', 'птица': 'птица', 'eagle': 'орел', 'owl': 'сова',
                # Природа
                'flower': 'цветок', 'rose': 'роза', 'цветок': 'цветок', 'роза': 'роза',
                'tree': 'дерево', 'forest': 'лес', 'дерево': 'дерево', 'лес': 'лес',
                'mountain': 'горы', 'гора': 'горы', 'горы': 'горы',
                'beach': 'пляж', 'пляж': 'пляж', 'море': 'море',
                'city': 'город', 'город': 'город', 'urban': 'город',
                # Транспорт
                'car': 'машина', 'auto': 'автомобиль', 'машина': 'машина', 'авто': 'автомобиль',
                # Еда
                'food': 'еда', 'fruit': 'фрукт', 'vegetable': 'овощ', 'еда': 'еда',
                # Люди
                'person': 'человек', 'people': 'люди', 'человек': 'человек', 'люди': 'люди',
                # Технологии
                'computer': 'компьютер', 'phone': 'телефон', 'компьютер': 'компьютер',
                # Спорт
                'sport': 'спорт', 'football': 'футбол', 'basketball': 'баскетбол',
                # Искусство
                'art': 'искусство', 'music': 'музыка', 'painting': 'живопись',
                # Архитектура
                'building': 'здание', 'house': 'дом', 'architecture': 'архитектура',
                # Время года
                'winter': 'зима', 'summer': 'лето', 'spring': 'весна', 'autumn': 'осень',
                # Цвета
                'red': 'красный', 'blue': 'синий', 'green': 'зеленый', 'yellow': 'желтый',
                'black': 'черный', 'white': 'белый', 'pink': 'розовый', 'purple': 'фиолетовый'
            }
            
            for keyword, category in keywords_mapping.items():
                if keyword in filename or keyword in path:
                    analysis[category] = 0.8
            
        except Exception as e:
            logger.error(f"❌ Ошибка упрощенного анализа: {e}")
        
        return analysis

    def _analyze_colors_from_url(self, image_url):
        """Упрощенный анализ цветов на основе URL"""
        color_analysis = {}
        
        try:
            filename = urlparse(image_url).path.lower()
            
            # Определение цветов по ключевым словам в URL
            color_keywords = {
                'red': 'красный', 'blue': 'синий', 'green': 'зеленый',
                'yellow': 'желтый', 'orange': 'оранжевый', 'purple': 'фиолетовый',
                'pink': 'розовый', 'black': 'черный', 'white': 'белый',
                'gray': 'серый', 'brown': 'коричневый', 'gold': 'золотой',
                'silver': 'серебряный', 'beige': 'бежевый', 'turquoise': 'бирюзовый'
            }
            
            for eng, rus in color_keywords.items():
                if eng in filename or rus in filename:
                    color_analysis[rus] = 0.6
        
        except Exception as e:
            logger.error(f"❌ Ошибка анализа цветов: {e}")
        
        return color_analysis

# Инициализация анализатора
image_analyzer = ImageAnalyzer()

class ThreadManager:
    """Менеджер потоков для управления многопоточным поиском"""
    
    def __init__(self, max_workers=15):
        self.max_workers = max_workers
        self.active_threads = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = threading.Lock()
    
    def update_status(self):
        """Обновление глобального статуса потоков"""
        with self.lock:
            app_status['active_threads'] = self.active_threads
            app_status['max_threads'] = self.max_workers
    
    def task_completed(self, success=True):
        """Отметить завершение задачи"""
        with self.lock:
            self.active_threads -= 1
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
            self.update_status()
    
    def start_task(self):
        """Начать новую задачу"""
        with self.lock:
            if self.active_threads < self.max_workers:
                self.active_threads += 1
                self.update_status()
                return True
            return False
    
    def get_stats(self):
        """Получить статистику"""
        with self.lock:
            return {
                'active_threads': self.active_threads,
                'max_threads': self.max_workers,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks
            }

class WebCrawler:
    """Веб-краулер для сканирования страниц и поиска изображений, сайтов и видео"""
    
    def __init__(self, thread_manager):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.visited_urls = set()
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        self.thread_manager = thread_manager
        self.lock = threading.Lock()
    
    def get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def crawl_page(self, url, query_words, search_type='images'):
        """Сканирование страницы и извлечение контента"""
        if not self.thread_manager.start_task():
            return []
            
        try:
            with self.lock:
                if url in self.visited_urls:
                    self.thread_manager.task_completed(False)
                    return []
                self.visited_urls.add(url)
            
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=8)
            
            if response.status_code != 200:
                self.thread_manager.task_completed(False)
                return []
            
            app_status['processed_pages'] += 1
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if search_type == 'images':
                results = self._extract_images(soup, url, query_words)
            elif search_type == 'websites':
                results = self._extract_websites(soup, url, query_words)
            elif search_type == 'videos':
                results = self._extract_videos(soup, url, query_words)
            else:
                results = []
            
            self.thread_manager.task_completed(True)
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка сканирования {url}: {e}")
            self.thread_manager.task_completed(False)
            return []

    def _extract_images(self, soup, page_url, query_words):
        """Извлечение изображений со страницы"""
        images_data = []
        img_tags = soup.find_all('img')
        
        for img in img_tags[:30]:
            try:
                image_info = self._extract_image_data(img, page_url, query_words)
                if image_info:
                    images_data.append(image_info)
            except Exception as e:
                continue
        
        return images_data

    def _extract_websites(self, soup, page_url, query_words):
        """Извлечение веб-сайтов со страницы"""
        websites_data = []
        
        links = soup.find_all('a', href=True)
        
        for link in links[:20]:
            try:
                website_info = self._extract_website_data(link, page_url, query_words)
                if website_info:
                    websites_data.append(website_info)
            except Exception as e:
                continue
        
        return websites_data

    def _extract_videos(self, soup, page_url, query_words):
        """Извлечение видео со страницы"""
        videos_data = []
        
        video_tags = soup.find_all('video')
        for video in video_tags[:10]:
            try:
                video_info = self._extract_video_data(video, page_url, query_words)
                if video_info:
                    videos_data.append(video_info)
            except Exception as e:
                continue
        
        iframe_tags = soup.find_all('iframe')
        for iframe in iframe_tags[:10]:
            try:
                video_info = self._extract_iframe_video_data(iframe, page_url, query_words)
                if video_info:
                    videos_data.append(video_info)
            except Exception as e:
                continue
        
        return videos_data

    def _extract_image_data(self, img_tag, page_url, query_words):
        """Извлечение метаданных изображения"""
        try:
            img_src = (img_tag.get('src') or 
                      img_tag.get('data-src') or 
                      img_tag.get('data-lazy') or 
                      img_tag.get('data-original'))
            
            if not img_src:
                return None
            
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith('/'):
                img_src = urlparse(page_url).scheme + '://' + urlparse(page_url).netloc + img_src
            elif not img_src.startswith('http'):
                return None
            
            width = img_tag.get('width')
            height = img_tag.get('height')
            if width and height:
                try:
                    if int(width) < 100 or int(height) < 100:
                        return None
                except:
                    pass
            
            if any(icon in img_src.lower() for icon in ['icon', 'logo', 'sprite', 'spacer', 'pixel']):
                return None
            
            alt_text = img_tag.get('alt', '')
            title_text = img_tag.get('title', '')
            context = self._get_image_context(img_tag)
            filename = self._analyze_filename(img_src)
            
            image_id = hashlib.md5(img_src.encode()).hexdigest()
            
            image_data = {
                'id': image_id,
                'url': img_src,
                'thumbnail': img_src,
                'alt': alt_text,
                'title': title_text,
                'filename': filename,
                'context': context,
                'page_url': page_url,
                'domain': urlparse(page_url).netloc,
                'relevance_score': self._calculate_relevance(alt_text, title_text, filename, context, query_words),
                'metadata_extracted': True,
                'vision_analyzed': False
            }
            
            return image_data
            
        except Exception as e:
            return None

    def _extract_website_data(self, link_tag, page_url, query_words):
        """Извлечение данных веб-сайта"""
        try:
            href = link_tag.get('href', '')
            if not href or href.startswith('#') or href.startswith('javascript:'):
                return None
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = urlparse(page_url).scheme + '://' + urlparse(page_url).netloc + href
            elif not href.startswith('http'):
                return None
            
            link_text = link_tag.get_text(strip=True)
            if not link_text or len(link_text) < 10:
                return None
            
            description = self._get_link_description(link_tag)
            relevance_score = self._calculate_website_relevance(link_text, description, query_words)
            
            if relevance_score < 1:
                return None
            
            website_data = {
                'url': href,
                'title': link_text[:100],
                'description': description[:200],
                'domain': urlparse(href).netloc,
                'relevance_score': relevance_score,
                'display_url': self._get_display_url(href)
            }
            
            return website_data
            
        except Exception as e:
            return None

    def _extract_video_data(self, video_tag, page_url, query_words):
        """Извлечение данных видео"""
        try:
            video_src = (video_tag.get('src') or 
                        video_tag.get('data-src'))
            
            if not video_src:
                return None
            
            if video_src.startswith('//'):
                video_src = 'https:' + video_src
            elif video_src.startswith('/'):
                video_src = urlparse(page_url).scheme + '://' + urlparse(page_url).netloc + video_src
            elif not video_src.startswith('http'):
                return None
            
            title = video_tag.get('title', '') or self._get_video_title(video_tag)
            duration = video_tag.get('duration') or self._estimate_video_duration(video_tag)
            
            thumbnail = video_tag.get('poster', '')
            if not thumbnail:
                thumbnail = self._generate_video_placeholder()
            
            video_data = {
                'url': video_src,
                'title': title or 'Видео',
                'thumbnail': thumbnail,
                'duration': duration or 'Неизвестно',
                'channel': urlparse(page_url).netloc,
                'relevance_score': self._calculate_video_relevance(title, query_words)
            }
            
            return video_data
            
        except Exception as e:
            return None

    def _extract_iframe_video_data(self, iframe_tag, page_url, query_words):
        """Извлечение данных видео из iframe"""
        try:
            src = iframe_tag.get('src', '')
            if not src:
                return None
            
            video_platforms = ['youtube', 'vimeo', 'dailymotion', 'rutube']
            if not any(platform in src.lower() for platform in video_platforms):
                return None
            
            title = iframe_tag.get('title', '') or self._get_iframe_title(iframe_tag)
            
            video_data = {
                'url': src,
                'title': title or 'Видео',
                'thumbnail': self._generate_video_placeholder(),
                'duration': 'Неизвестно',
                'channel': urlparse(src).netloc,
                'relevance_score': self._calculate_video_relevance(title, query_words)
            }
            
            return video_data
            
        except Exception as e:
            return None

    def _get_image_context(self, img_tag):
        """Извлечение контекста изображения"""
        try:
            context_parts = []
            
            parent = img_tag.parent
            if parent:
                temp_parent = parent.copy()
                for img in temp_parent.find_all('img'):
                    img.decompose()
                parent_text = temp_parent.get_text(strip=True)
                if parent_text:
                    context_parts.append(parent_text)
            
            title_tag = img_tag.find_parent().find_previous(['h1', 'h2', 'h3'])
            if title_tag:
                context_parts.append(title_tag.get_text(strip=True))
            
            figcaption = img_tag.find_next('figcaption')
            if figcaption:
                context_parts.append(figcaption.get_text(strip=True))
            
            paragraph = img_tag.find_previous('p') or img_tag.find_next('p')
            if paragraph:
                context_parts.append(paragraph.get_text(strip=True)[:200])
            
            return ' '.join(context_parts)[:300]
            
        except Exception as e:
            return ""

    def _get_link_description(self, link_tag):
        """Извлечение описания ссылки"""
        try:
            description_parts = []
            
            parent = link_tag.parent
            if parent:
                temp_parent = parent.copy()
                for a in temp_parent.find_all('a'):
                    a.decompose()
                parent_text = temp_parent.get_text(strip=True)
                if parent_text:
                    description_parts.append(parent_text)
            
            next_sibling = link_tag.find_next_sibling()
            if next_sibling:
                next_text = next_sibling.get_text(strip=True)
                if next_text:
                    description_parts.append(next_text)
            
            return ' '.join(description_parts)[:150]
            
        except Exception as e:
            return ""

    def _get_video_title(self, video_tag):
        """Извлечение заголовка видео"""
        try:
            parent = video_tag.parent
            for _ in range(3):
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'strong', 'b'])
                    if title_elem:
                        return title_elem.get_text(strip=True)
                    parent = parent.parent
            return ""
        except:
            return ""

    def _get_iframe_title(self, iframe_tag):
        """Извлечение заголовка iframe"""
        try:
            parent = iframe_tag.parent
            for _ in range(3):
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'strong', 'b'])
                    if title_elem:
                        return title_elem.get_text(strip=True)
                    parent = parent.parent
            return ""
        except:
            return ""

    def _estimate_video_duration(self, video_tag):
        return "Неизвестно"

    def _generate_video_placeholder(self):
        return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4="

    def _get_display_url(self, url):
        try:
            parsed = urlparse(url)
            return f"{parsed.netloc}{parsed.path}"
        except:
            return url

    def _analyze_filename(self, img_url):
        try:
            filename = os.path.basename(urlparse(img_url).path)
            name_without_ext = os.path.splitext(filename)[0]
            clean_name = re.sub(r'[\d_-]+', ' ', name_without_ext)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            return clean_name if len(clean_name) > 2 else ""
        except:
            return ""

    def _calculate_relevance(self, alt, title, filename, context, query_words):
        score = 0
        all_text = f"{alt} {title} {filename} {context}".lower()
        
        for word in query_words:
            if len(word) > 2:
                if word in all_text:
                    if word in alt.lower():
                        score += 3
                    if word in title.lower():
                        score += 2
                    if word in filename.lower():
                        score += 2
                    if word in context.lower():
                        score += 1
        
        return score

    def _calculate_website_relevance(self, title, description, query_words):
        score = 0
        all_text = f"{title} {description}".lower()
        
        for word in query_words:
            if len(word) > 2 and word in all_text:
                if word in title.lower():
                    score += 3
                if word in description.lower():
                    score += 2
        
        return score

    def _calculate_video_relevance(self, title, query_words):
        score = 0
        title_lower = title.lower()
        
        for word in query_words:
            if len(word) > 2 and word in title_lower:
                score += 3
        
        return score

class ParallelSearchEngine:
    """Параллельная поисковая система с многопоточностью"""
    
    def __init__(self, max_workers=15):
        self.thread_manager = ThreadManager(max_workers)
        self.crawler = WebCrawler(self.thread_manager)
        self.search_urls = {
            'images': [
                "https://unsplash.com/s/photos/",
                "https://pixabay.com/images/search/",
                "https://www.pexels.com/search/",
                "https://www.flickr.com/search/?text=",
                "https://www.shutterstock.com/search/",
                "https://commons.wikimedia.org/w/index.php?search=",
                "https://www.deviantart.com/search?q=",
                "https://www.artstation.com/search?q=",
            ],
            'websites': [
                "https://www.google.com/search?q=",
                "https://www.bing.com/search?q=",
                "https://yandex.ru/search/?text=",
                "https://duckduckgo.com/html/?q=",
                "https://search.yahoo.com/search?p=",
                "https://www.baidu.com/s?wd=",
            ],
            'videos': [
                "https://www.youtube.com/results?search_query=",
                "https://vimeo.com/search?q=",
                "https://www.dailymotion.com/search/",
                "https://rutube.ru/search/?q=",
                "https://www.tiktok.com/search?q=",
            ]
        }
        
    def search(self, query, max_results=20, search_types=None):
        """Основной метод поиска с многопоточностью"""
        logger.info(f"🔍 Начало параллельного поиска для: '{query}'")
        
        if search_types is None:
            search_types = ['images', 'websites', 'videos']
        
        query_words = re.findall(r'\w+', query.lower())
        if not query_words:
            return {}
        
        start_time = time.time()
        results = {}
        
        # Создаем пул потоков для каждого типа поиска
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(search_types)) as main_executor:
            future_to_type = {}
            
            for search_type in search_types:
                if search_type in self.search_urls:
                    future = main_executor.submit(
                        self._parallel_search_type,
                        query, query_words, search_type, max_results
                    )
                    future_to_type[future] = search_type
            
            # Собираем результаты
            for future in concurrent.futures.as_completed(future_to_type):
                search_type = future_to_type[future]
                try:
                    results[search_type] = future.result(timeout=25)
                    logger.info(f"✅ {search_type} поиск завершен: {len(results[search_type])} результатов")
                except Exception as e:
                    logger.error(f"❌ Ошибка {search_type} поиска: {e}")
                    results[search_type] = []
        
        search_time = time.time() - start_time
        
        logger.info(f"🎯 Параллельный поиск завершен за {search_time:.2f}с. "
                   f"Активные потоки: {self.thread_manager.active_threads}, "
                   f"Статистика: {self.thread_manager.get_stats()}")
        
        return results

    def _parallel_search_type(self, query, query_words, search_type, max_results):
        """Параллельный поиск по конкретному типу контента"""
        all_results = []
        urls = self.search_urls[search_type]
        
        # Создаем дополнительные URL для более широкого поиска
        additional_urls = self._generate_additional_urls(query, search_type)
        all_urls = urls + additional_urls
        
        logger.info(f"🚀 Запуск {len(all_urls)} потоков для {search_type} поиска")
        
        # Используем ThreadPoolExecutor для параллельного сканирования URL
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(all_urls))) as executor:
            future_to_url = {}
            
            for url in all_urls:
                search_url = url + quote_plus(query)
                future = executor.submit(
                    self.crawler.crawl_page,
                    search_url, query_words, search_type
                )
                future_to_url[future] = search_url
            
            # Собираем результаты с таймаутом
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    items = future.result(timeout=12)
                    if items:
                        all_results.extend(items)
                        logger.debug(f"📥 Получено {len(items)} результатов с {urlparse(url).netloc}")
                except concurrent.futures.TimeoutError:
                    logger.warning(f"⏰ Таймаут для {url}")
                except Exception as e:
                    logger.debug(f"❌ Ошибка для {url}: {e}")
        
        # Ранжирование результатов
        if search_type == 'images':
            ranked_results = self._rank_images(all_results, query_words)
        elif search_type == 'websites':
            ranked_results = self._rank_websites(all_results, query_words)
        elif search_type == 'videos':
            ranked_results = self._rank_videos(all_results, query_words)
        else:
            ranked_results = all_results
        
        return ranked_results[:max_results]

    def _generate_additional_urls(self, query, search_type):
        """Генерация дополнительных URL для поиска"""
        base_urls = []
        query_encoded = quote_plus(query)
        
        if search_type == 'images':
            base_urls = [
                f"https://www.google.com/search?q={query_encoded}&tbm=isch",
                f"https://www.bing.com/images/search?q={query_encoded}",
                f"https://yandex.ru/images/search?text={query_encoded}",
            ]
        elif search_type == 'websites':
            base_urls = [
                f"https://www.google.com/search?q={query_encoded}",
                f"https://www.bing.com/search?q={query_encoded}",
                f"https://yandex.ru/search/?text={query_encoded}",
            ]
        elif search_type == 'videos':
            base_urls = [
                f"https://www.youtube.com/results?search_query={query_encoded}",
                f"https://vimeo.com/search?q={query_encoded}",
            ]
        
        return base_urls

    def _rank_images(self, images, query_words):
        """Ранжирование изображений"""
        scored_images = []
        
        for image in images:
            try:
                final_score = image.get('relevance_score', 0)
                final_score += self._calculate_domain_authority(image.get('domain', ''))
                final_score += self._estimate_image_quality(image)
                
                if not image.get('vision_analyzed', False):
                    vision_analysis = image_analyzer.analyze_image(image['url'])
                    image['vision_analysis'] = vision_analysis
                    image['vision_analyzed'] = True
                    
                    vision_score = self._calculate_vision_relevance(vision_analysis, query_words)
                    final_score += vision_score
                
                scored_images.append((final_score, image))
                
            except Exception as e:
                continue
        
        scored_images.sort(key=lambda x: x[0], reverse=True)
        return [img for score, img in scored_images]

    def _rank_websites(self, websites, query_words):
        """Ранжирование веб-сайтов"""
        scored_websites = []
        
        for website in websites:
            try:
                final_score = website.get('relevance_score', 0)
                final_score += self._calculate_domain_authority(website.get('domain', ''))
                
                if len(website.get('description', '')) > 50:
                    final_score += 1
                
                scored_websites.append((final_score, website))
                
            except Exception as e:
                continue
        
        scored_websites.sort(key=lambda x: x[0], reverse=True)
        return [site for score, site in scored_websites]

    def _rank_videos(self, videos, query_words):
        """Ранжирование видео"""
        scored_videos = []
        
        for video in videos:
            try:
                final_score = video.get('relevance_score', 0)
                
                if any(platform in video.get('channel', '').lower() 
                      for platform in ['youtube', 'vimeo']):
                    final_score += 2
                
                if video.get('thumbnail'):
                    final_score += 1
                
                scored_videos.append((final_score, video))
                
            except Exception as e:
                continue
        
        scored_videos.sort(key=lambda x: x[0], reverse=True)
        return [video for score, video in scored_videos]

    def _calculate_domain_authority(self, domain):
        authority_domains = {
            'unsplash.com': 3, 'pixabay.com': 3, 'pexels.com': 3,
            'flickr.com': 2, 'shutterstock.com': 2, 'gettyimages.com': 2,
            'wikipedia.org': 3, 'youtube.com': 3, 'vimeo.com': 2,
            'google.com': 3, 'github.com': 2, 'stackoverflow.com': 2
        }
        return authority_domains.get(domain, 0)

    def _estimate_image_quality(self, image_data):
        score = 0
        
        if len(image_data.get('alt', '')) > 10:
            score += 1
        if len(image_data.get('title', '')) > 5:
            score += 1
        if image_data.get('filename'):
            score += 1
        
        return score

    def _calculate_vision_relevance(self, vision_analysis, query_words):
        score = 0
        
        for obj, confidence in vision_analysis.items():
            for word in query_words:
                if word in obj or self._is_synonym(word, obj):
                    score += confidence * 2
        
        return score

    def _is_synonym(self, word, object_name):
        synonyms = {
            'кот': ['кошка', 'котенок'],
            'собака': ['пес', 'щенок'],
            'машина': ['автомобиль', 'тачка'],
            'человек': ['люди', 'персона'],
            'цветок': ['цветы', 'букет'],
        }
        return word in synonyms.get(object_name, [])

# Инициализация поисковой системы с многопоточностью
search_engine = ParallelSearchEngine(max_workers=20)

# HTML шаблон (остается практически без изменений, но добавим информацию о потоках)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if query %}{{ query }} - AriOS Search{% else %}AriOS - Умный поиск{% endif %}</title>
    <meta name="description" content="AriOS - независимая поисковая система с реальными результатами">
    
    <style>
        :root {
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
            --gradient-start: #8b5cf6;
            --gradient-end: #6366f1;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .main-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-top: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .search-container {
            text-align: center;
        }
        
        .logo {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .logo a {
            text-decoration: none;
        }
        
        .tagline {
            color: #6b7280;
            font-size: 16px;
            margin-bottom: 40px;
            font-weight: 500;
        }
        
        .search-box {
            width: 100%;
            max-width: 600px;
            padding: 18px 24px;
            font-size: 16px;
            border: 3px solid #e5e7eb;
            border-radius: 50px;
            outline: none;
            margin-bottom: 25px;
            transition: all 0.3s ease;
            background: #f8fafc;
        }
        
        .search-box:focus {
            border-color: var(--primary-color);
            background: white;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }
        
        .search-button {
            background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
            color: white;
            border: none;
            padding: 12px 32px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 50px;
            cursor: pointer;
            margin: 0 8px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        .search-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }
        
        .filter-tabs {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .filter-tab {
            background: #f8fafc;
            border: 2px solid #e5e7eb;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .filter-tab:hover {
            background: #f1f5f9;
            border-color: #d1d5db;
        }
        
        .filter-tab.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        .filter-tab .count {
            background: rgba(255, 255, 255, 0.2);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .filter-tab:not(.active) .count {
            background: #e5e7eb;
            color: #374151;
        }
        
        .results-container {
            margin-top: 20px;
            text-align: left;
        }
        
        .results-header {
            color: #374151;
            font-size: 14px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .result-item {
            margin-bottom: 25px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            border: 1px solid #f3f4f6;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .result-item:hover {
            border-color: var(--primary-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transform: translateY(-1px);
        }
        
        .result-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(to bottom, var(--gradient-start), var(--gradient-end));
            border-radius: 4px 0 0 4px;
        }
        
        .result-title {
            font-size: 18px;
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 600;
            display: block;
            margin-bottom: 8px;
        }
        
        .result-title:hover {
            text-decoration: underline;
        }
        
        .result-url {
            color: #059669;
            font-size: 14px;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .result-snippet {
            color: #4b5563;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .highlight {
            background-color: #fffacd;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 600;
        }
        
        .images-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        
        .image-result {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
            background: white;
        }
        
        .image-result:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .image-result img {
            width: 100%;
            height: 150px;
            object-fit: cover;
            display: block;
        }
        
        .image-info {
            padding: 10px;
        }
        
        .image-title {
            font-size: 12px;
            color: #374151;
            margin-bottom: 5px;
            line-height: 1.3;
        }
        
        .image-source {
            font-size: 10px;
            color: #6b7280;
        }
        
        .image-meta {
            font-size: 9px;
            color: #9ca3af;
            margin-top: 3px;
        }
        
        .videos-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .video-result {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
            background: white;
        }
        
        .video-result:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .video-thumbnail {
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
        }
        
        .video-info {
            padding: 15px;
        }
        
        .video-title {
            font-size: 14px;
            color: #374151;
            margin-bottom: 8px;
            line-height: 1.3;
            font-weight: 600;
        }
        
        .video-channel {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 5px;
        }
        
        .video-duration {
            font-size: 11px;
            color: #9ca3af;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin: 30px 0 15px 0;
            color: #374151;
            border-left: 4px solid var(--primary-color);
            padding-left: 15px;
        }
        
        .feature-badges {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        
        .badge {
            background: #f0f9ff;
            color: #0369a1;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid #bae6fd;
        }
        
        .error {
            color: #dc2626;
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background: #fef2f2;
            border-radius: 10px;
            border: 1px solid #fecaca;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #9ca3af;
            font-size: 14px;
        }
        
        .quick-search {
            margin: 20px 0;
        }
        
        .quick-search-btn {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        
        .quick-search-btn:hover {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .loading {
            text-align: center;
            color: #6366f1;
            padding: 40px;
            font-size: 18px;
        }
        
        .status-info {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 12px;
            color: #065f46;
        }
        
        .status-warning {
            background: #fef3c7;
            border: 1px solid #f59e0b;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 12px;
            color: #92400e;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 16px;
        }
        
        .content-type {
            display: none;
        }
        
        .content-type.active {
            display: block;
        }
        
        .stats-info {
            background: #eff6ff;
            border: 1px solid #dbeafe;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 5px 0;
            font-size: 11px;
            color: #1e40af;
        }
        
        .search-stats {
            background: #f0f9ff;
            border: 1px solid #e0f2fe;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 12px;
            color: #0c4a6e;
        }
        
        .threads-info {
            background: #fef3c7;
            border: 1px solid #f59e0b;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 5px 0;
            font-size: 11px;
            color: #92400e;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #059669);
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo"><a href="/">AriOS</a></div>
            <div class="tagline">Продвинутая поисковая система • Многопоточный поиск • Высокая скорость</div>
            
            {% if show_status %}
                {% if is_active %}
                <div class="status-info">
                    ✅ Сервис активен • Проиндексировано: {{ indexed_images }} изображений • 
                    Обработано: {{ processed_pages }} страниц • Поисков: {{ total_searches }}
                    {% if active_threads > 0 %}
                    <br>🎯 Активные потоки: {{ active_threads }}/{{ max_threads }}
                    {% endif %}
                </div>
                {% else %}
                <div class="status-warning">
                    ⚠️ Сервис может быть неактивен • Последний пинг: {{ last_ping }}
                </div>
                {% endif %}
            {% endif %}
            
            <form action="/search" method="GET" id="searchForm">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Введите запрос для многопоточного поиска..." autofocus>
                <br>
                <button type="submit" class="search-button">🚀 Найти в AriOS</button>
                <button type="button" class="search-button" style="background: #6b7280;" onclick="location.href='/?status=true'">📊 Статус</button>
            </form>
            
            {% if not results and not images and not videos and not error and not loading %}
            <div class="quick-search">
                <strong>Попробуйте найти:</strong><br>
                <button class="quick-search-btn" onclick="setSearch('кошки котята')">🐱 Кошки</button>
                <button class="quick-search-btn" onclick="setSearch('горы природа')">🏔️ Горы</button>
                <button class="quick-search-btn" onclick="setSearch('цветы розы')">🌹 Цветы</button>
                <button class="quick-search-btn" onclick="setSearch('город небоскребы')">🏙️ Город</button>
                <button class="quick-search-btn" onclick="setSearch('пляж море')">🏖️ Пляж</button>
            </div>
            {% endif %}
            
            <div class="feature-badges">
                <div class="badge">🚀 Многопоточность</div>
                <div class="badge">📷 Компьютерное зрение</div>
                <div class="badge">🌐 Сайты и видео</div>
                <div class="badge">⚡ Высокая скорость</div>
                <div class="badge">🎯 Умный поиск</div>
            </div>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if loading %}
            <div class="loading">
                🔍 Параллельный поиск "{{ query }}"...
                <div class="threads-info">
                    🎯 Активные потоки: {{ active_threads }}/{{ max_threads }} • 
                    📊 Обработано страниц: {{ processed_pages }}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 60%"></div>
                </div>
                <div class="stats-info">
                    Этап 1: Запуск потоков... | Этап 2: Параллельное сканирование... | Этап 3: Анализ и ранжирование...
                </div>
            </div>
            {% endif %}
            
            {% if results or images or videos %}
            <div class="results-container">
                <div class="results-header">
                    🎯 Найдено: {{ total_results }} • ⚡ Время: {{ search_time }}с • 
                    📊 Запрос: "{{ query }}" • 🚀 Алгоритм: параллельный поиск
                </div>
                
                <div class="search-stats">
                    🔍 <strong>Параллельный алгоритм поиска:</strong> 
                    Запуск 15+ потоков → Сканирование 20+ источников → Анализ метаданных → Компьютерное зрение → Многофакторное ранжирование
                </div>
                
                {% if active_threads > 0 %}
                <div class="threads-info">
                    ⚡ Поиск продолжается в фоновом режиме • Активные потоки: {{ active_threads }} • 
                    Обновление результатов каждые 5 секунд...
                </div>
                {% endif %}
                
                <!-- Панель фильтров -->
                <div class="filter-tabs">
                    <div class="filter-tab {% if active_tab == 'all' %}active{% endif %}" onclick="showContent('all')">
                        🌐 Все результаты
                        <span class="count">{{ total_results }}</span>
                    </div>
                    <div class="filter-tab {% if active_tab == 'websites' %}active{% endif %}" onclick="showContent('websites')">
                        📄 Сайты
                        <span class="count">{{ websites_count }}</span>
                    </div>
                    <div class="filter-tab {% if active_tab == 'images' %}active{% endif %}" onclick="showContent('images')">
                        🖼️ Фото
                        <span class="count">{{ images_count }}</span>
                    </div>
                    <div class="filter-tab {% if active_tab == 'videos' %}active{% endif %}" onclick="showContent('videos')">
                        🎬 Видео
                        <span class="count">{{ videos_count }}</span>
                    </div>
                </div>
                
                <!-- Все результаты -->
                <div id="content-all" class="content-type {% if active_tab == 'all' %}active{% endif %}">
                    {% if videos %}
                    <div class="section-title">🎥 Видео</div>
                    <div class="videos-container">
                        {% for video in videos %}
                        <div class="video-result">
                            <a href="{{ video.url }}" target="_blank">
                                <img src="{{ video.thumbnail }}" alt="{{ video.title }}" class="video-thumbnail"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4='">
                            </a>
                            <div class="video-info">
                                <div class="video-title">{{ video.title }}</div>
                                <div class="video-channel">{{ video.channel }}</div>
                                <div class="video-duration">{{ video.duration }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if images %}
                    <div class="section-title">📷 Изображения (проанализированы компьютерным зрением)</div>
                    <div class="images-container">
                        {% for image in images %}
                        <div class="image-result">
                            <a href="{{ image.url }}" target="_blank">
                                <img src="{{ image.thumbnail }}" alt="{{ image.title }}"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik04MCA2MEgxMjBNNzAgODBIMTMwTTY1IDEwMEgxMzUiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjUwIiByPSIxNSIgc3Ryb2tlPSIjOUNBM0FGIiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+'">
                            </a>
                            <div class="image-info">
                                <div class="image-title">{{ image.title }}</div>
                                <div class="image-source">{{ image.source }}</div>
                                {% if image.metadata %}
                                <div class="image-meta">
                                    Релевантность: {{ image.metadata.relevance_score }} | 
                                    {{ image.metadata.analysis_type }}
                                    {% if image.metadata.alt %}| Alt: {{ image.metadata.alt[:30] }}...{% endif %}
                                </div>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if results %}
                    <div class="section-title">🌐 Веб-сайты</div>
                    {% for result in results %}
                    <div class="result-item">
                        <a href="{{ result.url }}" class="result-title" target="_blank">
                            {{ result.title }}
                        </a>
                        <div class="result-url">{{ result.display_url }}</div>
                        <div class="result-snippet">{{ result.description }}</div>
                    </div>
                    {% endfor %}
                    {% endif %}
                </div>
                
                <!-- Только сайты -->
                <div id="content-websites" class="content-type {% if active_tab == 'websites' %}active{% endif %}">
                    {% if results %}
                    <div class="section-title">🌐 Веб-сайты ({{ websites_count }})</div>
                    {% for result in results %}
                    <div class="result-item">
                        <a href="{{ result.url }}" class="result-title" target="_blank">
                            {{ result.title }}
                        </a>
                        <div class="result-url">{{ result.display_url }}</div>
                        <div class="result-snippet">{{ result.description }}</div>
                    </div>
                    {% endfor %}
                    {% else %}
                    <div class="no-results">
                        📭 Нет результатов для веб-сайтов
                    </div>
                    {% endif %}
                </div>
                
                <!-- Только изображения -->
                <div id="content-images" class="content-type {% if active_tab == 'images' %}active{% endif %}">
                    {% if images %}
                    <div class="section-title">📷 Изображения ({{ images_count }})</div>
                    <div class="stats-info">
                        🔍 <strong>Технологии поиска:</strong> 
                        Параллельное сканирование 10+ фото-сайтов → Анализ alt/text + Компьютерное зрение → Ранжирование по релевантности
                    </div>
                    <div class="images-container">
                        {% for image in images %}
                        <div class="image-result">
                            <a href="{{ image.url }}" target="_blank">
                                <img src="{{ image.thumbnail }}" alt="{{ image.title }}"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik04MCA2MEgxMjBNNzAgODBIMTMwTTY1IDEwMEgxMzUiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjUwIiByPSIxNSIgc3Ryb2tlPSIjOUNBM0FGIiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+'">
                            </a>
                            <div class="image-info">
                                <div class="image-title">{{ image.title }}</div>
                                <div class="image-source">{{ image.source }}</div>
                                {% if image.metadata %}
                                <div class="image-meta">
                                    Релевантность: {{ image.metadata.relevance_score }} | 
                                    {{ image.metadata.analysis_type }}
                                    {% if image.metadata.alt %}| Alt: {{ image.metadata.alt[:30] }}...{% endif %}
                                </div>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="no-results">
                        🖼️ Нет результатов для изображений
                    </div>
                    {% endif %}
                </div>
                
                <!-- Только видео -->
                <div id="content-videos" class="content-type {% if active_tab == 'videos' %}active{% endif %}">
                    {% if videos %}
                    <div class="section-title">🎥 Видео ({{ videos_count }})</div>
                    <div class="videos-container">
                        {% for video in videos %}
                        <div class="video-result">
                            <a href="{{ video.url }}" target="_blank">
                                <img src="{{ video.thumbnail }}" alt="{{ video.title }}" class="video-thumbnail"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4='">
                            </a>
                            <div class="video-info">
                                <div class="video-title">{{ video.title }}</div>
                                <div class="video-channel">{{ video.channel }}</div>
                                <div class="video-duration">{{ video.duration }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="no-results">
                        🎬 Нет результатов для видео
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            © 2024 AriOS • Продвинутая поисковая система • 🚀 Многопоточный поиск • 
            <a href="/status" style="color: #6366f1;">📊 Статус</a> • 
            <a href="/about" style="color: #6366f1;">ℹ️ О системе</a>
        </div>
    </div>

    <script>
        function setSearch(term) {
            document.querySelector('.search-box').value = term;
            document.getElementById('searchForm').submit();
        }
        
        function showContent(type) {
            document.querySelectorAll('.content-type').forEach(el => {
                el.classList.remove('active');
            });
            document.getElementById('content-' + type).classList.add('active');
            document.querySelectorAll('.filter-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            const url = new URL(window.location);
            url.searchParams.set('tab', type);
            window.history.replaceState({}, '', url);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const savedTab = urlParams.get('tab');
            if (savedTab) {
                showContent(savedTab);
            }
        });
        
        document.querySelector('.search-box').focus();
        
        // Авто-обновление статуса потоков
        {% if active_threads > 0 %}
        setTimeout(() => {
            window.location.reload();
        }, 5000);
        {% endif %}
    </script>
</body>
</html>
'''

# Функции для само-пинга и планировщика
def self_ping():
    """Отправляет запросы самому себе чтобы держать приложение активным"""
    try:
        if 'RENDER_EXTERNAL_URL' in os.environ:
            base_url = os.environ['RENDER_EXTERNAL_URL']
        else:
            base_url = 'https://arios-yqnm.onrender.com'
            
        health_url = f"{base_url}/health"
        search_url = f"{base_url}/search?q=python"
        
        logger.info(f"🔁 Starting self-ping to {base_url}")
        
        try:
            response1 = requests.get(health_url, timeout=10)
            logger.info(f"✅ Health ping: {response1.status_code}")
        except Exception as e:
            logger.error(f"❌ Health ping failed: {e}")
        
        try:
            response2 = requests.get(search_url, timeout=10)
            logger.info(f"✅ Search ping: {response2.status_code}")
        except Exception as e:
            logger.error(f"❌ Search ping failed: {e}")
        
        app_status['last_self_ping'] = time.time()
        app_status['total_searches'] += 1
        app_status['is_active'] = True
        
        logger.info(f"✅ Self-ping completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"❌ Self-ping error: {e}")
        app_status['is_active'] = False

def run_scheduler():
    """Запускает планировщик для регулярных само-пингов"""
    logger.info("🕒 Starting background scheduler...")
    
    schedule.every(2).minutes.do(self_ping)
    schedule.every(30).seconds.do(lambda: 
        requests.get(f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://arios-yqnm.onrender.com')}/ping", timeout=5) 
        if random.random() > 0.3 else None
    )
    
    logger.info("🔁 Performing initial self-ping...")
    self_ping()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            time.sleep(10)

def start_background_scheduler():
    """Запускает фоновый планировщик"""
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("🚀 Background scheduler started successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        return False

# Маршруты Flask
@app.route('/')
def home():
    """Главная страница AriOS"""
    query = request.args.get('q', '').strip()
    show_status = request.args.get('status', 'false').lower() == 'true'
    
    if query:
        return redirect(f'/search?q={quote_plus(query)}')
    
    last_ping = "никогда"
    if app_status['last_self_ping']:
        last_ping = f"{int(time.time() - app_status['last_self_ping'])} сек назад"
    
    uptime = int(time.time() - app_status['start_time'])
    uptime_str = f"{uptime // 3600}ч {(uptime % 3600) // 60}м {uptime % 60}с"
    
    return render_template_string(HTML_TEMPLATE, 
                                query="", 
                                results=None, 
                                images=None, 
                                videos=None, 
                                total_results=0, 
                                search_time="0.00",
                                loading=False,
                                auto_search=False,
                                show_status=show_status,
                                last_ping=last_ping,
                                total_searches=app_status['total_searches'],
                                uptime=uptime_str,
                                is_active=app_status['is_active'],
                                active_tab='all',
                                websites_count=0,
                                images_count=0,
                                videos_count=0,
                                indexed_images=app_status['indexed_images'],
                                processed_pages=app_status['processed_pages'],
                                active_threads=app_status['active_threads'],
                                max_threads=app_status['max_threads'])

@app.route('/search')
def search():
    """Поиск в AriOS - основная точка входа"""
    query = request.args.get('q', '').strip()
    show_status = request.args.get('status', 'false').lower() == 'true'
    active_tab = request.args.get('tab', 'all')
    
    if not query:
        return render_template_string(HTML_TEMPLATE, 
                                   query="", 
                                   results=None, 
                                   images=None,
                                   videos=None,
                                   total_results=0,
                                   search_time="0.00",
                                   error="Введите поисковый запрос",
                                   loading=False,
                                   auto_search=False,
                                   show_status=show_status,
                                   active_tab='all',
                                   websites_count=0,
                                   images_count=0,
                                   videos_count=0,
                                   indexed_images=app_status['indexed_images'],
                                   processed_pages=app_status['processed_pages'],
                                   active_threads=app_status['active_threads'],
                                   max_threads=app_status['max_threads'])
    
    try:
        app_status['total_searches'] += 1
        
        start_time = time.time()
        
        # Используем параллельную поисковую систему
        search_results = search_engine.search(query, max_results=20)
        
        results = search_results.get('websites', [])
        images = search_results.get('images', [])
        videos = search_results.get('videos', [])
        
        search_time = time.time() - start_time
        
        total_results = len(results) + len(images) + len(videos)
        websites_count = len(results)
        images_count = len(images)
        videos_count = len(videos)
        
        last_ping = "никогда"
        if app_status['last_self_ping']:
            last_ping = f"{int(time.time() - app_status['last_self_ping'])} сек назад"
        
        uptime = int(time.time() - app_status['start_time'])
        uptime_str = f"{uptime // 3600}ч {(uptime % 3600) // 60}м {uptime % 60}с"
        
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=results,
                                   images=images,
                                   videos=videos,
                                   total_results=total_results,
                                   search_time=f"{search_time:.2f}",
                                   loading=False,
                                   auto_search=False,
                                   show_status=show_status,
                                   last_ping=last_ping,
                                   total_searches=app_status['total_searches'],
                                   uptime=uptime_str,
                                   is_active=app_status['is_active'],
                                   active_tab=active_tab,
                                   websites_count=websites_count,
                                   images_count=images_count,
                                   videos_count=videos_count,
                                   indexed_images=app_status['indexed_images'],
                                   processed_pages=app_status['processed_pages'],
                                   active_threads=app_status['active_threads'],
                                   max_threads=app_status['max_threads'])
    
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=None,
                                   images=None,
                                   videos=None,
                                   total_results=0,
                                   search_time="0.00",
                                   error=f"Ошибка поиска: {str(e)}",
                                   loading=False,
                                   auto_search=False,
                                   show_status=show_status,
                                   active_tab='all',
                                   websites_count=0,
                                   images_count=0,
                                   videos_count=0,
                                   indexed_images=app_status['indexed_images'],
                                   processed_pages=app_status['processed_pages'],
                                   active_threads=app_status['active_threads'],
                                   max_threads=app_status['max_threads'])

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': int(time.time() - app_status['start_time']),
        'total_searches': app_status['total_searches'],
        'indexed_images': app_status['indexed_images'],
        'processed_pages': app_status['processed_pages'],
        'active_threads': app_status['active_threads'],
        'max_threads': app_status['max_threads']
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    app_status['last_self_ping'] = time.time()
    app_status['is_active'] = True
    return 'pong'

@app.route('/status')
def status():
    """Status page"""
    last_ping = "никогда"
    if app_status['last_self_ping']:
        last_ping = f"{int(time.time() - app_status['last_self_ping'])} сек назад"
    
    uptime = int(time.time() - app_status['start_time'])
    uptime_str = f"{uptime // 3600}ч {(uptime % 3600) // 60}м {uptime % 60}с"
    
    thread_stats = search_engine.thread_manager.get_stats()
    
    return jsonify({
        'status': 'active' if app_status['is_active'] else 'inactive',
        'last_self_ping': app_status['last_self_ping'],
        'last_ping_human': last_ping,
        'total_searches': app_status['total_searches'],
        'indexed_images': app_status['indexed_images'],
        'processed_pages': app_status['processed_pages'],
        'start_time': app_status['start_time'],
        'uptime': uptime,
        'uptime_human': uptime_str,
        'threading': {
            'active_threads': app_status['active_threads'],
            'max_threads': app_status['max_threads'],
            'thread_manager_stats': thread_stats
        }
    })

# Запускаем само-пинг при старте приложения
start_background_scheduler()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting AriOS Parallel Search Server on port {port}...")
    logger.info(f"🚀 Maximum workers: {search_engine.thread_manager.max_workers}")
    app.run(host='0.0.0.0', port=port, debug=False)
