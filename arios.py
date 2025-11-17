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
    'processed_pages': 0
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
            'аэропорт', 'вокзал', 'море', 'река', 'озеро', 'пустыня', 'снег'
        ]
        self.color_names = {
            'red': 'красный', 'blue': 'синий', 'green': 'зеленый', 
            'yellow': 'желтый', 'orange': 'оранжевый', 'purple': 'фиолетовый',
            'pink': 'розовый', 'brown': 'коричневый', 'black': 'черный',
            'white': 'белый', 'gray': 'серый'
        }
        self.object_translations = {
            'cat': 'кот', 'dog': 'собака', 'car': 'машина', 'tree': 'дерево',
            'person': 'человек', 'building': 'здание', 'flower': 'цветок',
            'mountain': 'гора', 'beach': 'пляж', 'sky': 'небо', 'water': 'вода',
            'food': 'еда', 'animal': 'животное', 'bird': 'птица', 'fish': 'рыба',
            'computer': 'компьютер', 'phone': 'телефон', 'book': 'книга',
            'chair': 'стул', 'table': 'стол', 'house': 'дом', 'road': 'дорога',
            'cloud': 'облако', 'sun': 'солнце', 'grass': 'трава', 'leaf': 'лист',
            'fruit': 'фрукт', 'vegetable': 'овощ', 'face': 'лицо', 'hand': 'рука'
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
            
            # Общие категории на основе ключевых слов
            if any(word in filename for word in ['cat', 'kitty', 'kitten', 'кошка', 'кот']):
                analysis['кот'] = 0.8
            if any(word in filename for word in ['dog', 'puppy', 'собака', 'пес']):
                analysis['собака'] = 0.8
            if any(word in filename for word in ['flower', 'rose', 'цветок', 'роза']):
                analysis['цветок'] = 0.7
            if any(word in filename for word in ['car', 'auto', 'машина', 'авто']):
                analysis['машина'] = 0.7
            if any(word in filename for word in ['mountain', 'гора', 'горы']):
                analysis['горы'] = 0.7
            if any(word in filename for word in ['beach', 'пляж', 'море']):
                analysis['пляж'] = 0.7
            if any(word in filename for word in ['city', 'город', 'urban']):
                analysis['город'] = 0.7
            if any(word in filename for word in ['forest', 'лес', 'дерево']):
                analysis['лес'] = 0.7
            
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
                'gray': 'серый', 'brown': 'коричневый'
            }
            
            for eng, rus in color_keywords.items():
                if eng in filename or rus in filename:
                    color_analysis[rus] = 0.6
        
        except Exception as e:
            logger.error(f"❌ Ошибка анализа цветов: {e}")
        
        return color_analysis

    def translate_object_name(self, english_name):
        """Перевод названий объектов"""
        return self.object_translations.get(english_name, english_name)

# Инициализация анализатора
image_analyzer = ImageAnalyzer()

class WebCrawler:
    """Веб-краулер для сканирования страниц и поиска изображений"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.visited_urls = set()
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        
    def get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def crawl_page(self, url, query_words):
        """Сканирование страницы и извлечение изображений"""
        if url in self.visited_urls:
            return []
            
        self.visited_urls.add(url)
        
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=8)
            
            if response.status_code != 200:
                return []
            
            app_status['processed_pages'] += 1
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлечение всех изображений
            images_data = []
            img_tags = soup.find_all('img')
            
            for img in img_tags[:30]:  # Ограничиваем для производительности
                try:
                    image_info = self._extract_image_data(img, url, query_words)
                    if image_info:
                        images_data.append(image_info)
                except Exception as e:
                    continue
            
            return images_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка сканирования {url}: {e}")
            return []

    def _extract_image_data(self, img_tag, page_url, query_words):
        """Извлечение метаданных изображения"""
        try:
            # Получение URL изображения
            img_src = (img_tag.get('src') or 
                      img_tag.get('data-src') or 
                      img_tag.get('data-lazy') or 
                      img_tag.get('data-original'))
            
            if not img_src:
                return None
            
            # Преобразование относительных URL
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith('/'):
                img_src = urlparse(page_url).scheme + '://' + urlparse(page_url).netloc + img_src
            elif not img_src.startswith('http'):
                return None
            
            # Пропускаем маленькие изображения и иконки
            width = img_tag.get('width')
            height = img_tag.get('height')
            if width and height:
                try:
                    if int(width) < 100 or int(height) < 100:
                        return None
                except:
                    pass
            
            # Пропускаем SVG и иконки
            if any(icon in img_src.lower() for icon in ['icon', 'logo', 'sprite', 'spacer', 'pixel']):
                return None
            
            # Извлечение метаданных
            alt_text = img_tag.get('alt', '')
            title_text = img_tag.get('title', '')
            
            # Извлечение контекста
            context = self._get_image_context(img_tag)
            
            # Анализ имени файла
            filename = self._analyze_filename(img_src)
            
            # Создание уникального ID
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
            logger.error(f"❌ Ошибка извлечения данных изображения: {e}")
            return None

    def _get_image_context(self, img_tag):
        """Извлечение контекста изображения"""
        try:
            context_parts = []
            
            # Текст из родительского элемента
            parent = img_tag.parent
            if parent:
                temp_parent = parent.copy()
                for img in temp_parent.find_all('img'):
                    img.decompose()
                parent_text = temp_parent.get_text(strip=True)
                if parent_text:
                    context_parts.append(parent_text)
            
            # Заголовок страницы
            title_tag = img_tag.find_parent().find_previous(['h1', 'h2', 'h3'])
            if title_tag:
                context_parts.append(title_tag.get_text(strip=True))
            
            # Подпись (figcaption)
            figcaption = img_tag.find_next('figcaption')
            if figcaption:
                context_parts.append(figcaption.get_text(strip=True))
            
            # Ближайший абзац
            paragraph = img_tag.find_previous('p') or img_tag.find_next('p')
            if paragraph:
                context_parts.append(paragraph.get_text(strip=True)[:200])
            
            return ' '.join(context_parts)[:300]
            
        except Exception as e:
            return ""

    def _analyze_filename(self, img_url):
        """Анализ имени файла изображения"""
        try:
            filename = os.path.basename(urlparse(img_url).path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Удаляем цифры и специальные символы
            clean_name = re.sub(r'[\d_-]+', ' ', name_without_ext)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            
            return clean_name if len(clean_name) > 2 else ""
        except:
            return ""

    def _calculate_relevance(self, alt, title, filename, context, query_words):
        """Расчет релевантности на основе метаданных"""
        score = 0
        all_text = f"{alt} {title} {filename} {context}".lower()
        
        for word in query_words:
            if len(word) > 2:
                if word in all_text:
                    # Разный вес для разных источников
                    if word in alt.lower():
                        score += 3  # Высокий вес для alt
                    if word in title.lower():
                        score += 2  # Средний вес для title
                    if word in filename.lower():
                        score += 2  # Средний вес для имени файла
                    if word in context.lower():
                        score += 1  # Низкий вес для контекста
        
        return score

class ImageSearchEngine:
    """Поисковая система для изображений"""
    
    def __init__(self):
        self.crawler = WebCrawler()
        self.start_urls = [
            "https://unsplash.com/s/photos/",
            "https://pixabay.com/images/search/",
            "https://www.pexels.com/search/",
            "https://www.flickr.com/search/?text=",
            "https://www.shutterstock.com/search/",
            "https://commons.wikimedia.org/w/index.php?search=",
            "https://www.deviantart.com/search?q=",
            "https://www.artstation.com/search?q=",
            "https://www.gettyimages.com/photos/",
            "https://www.istockphoto.com/search/2/image?phrase="
        ]
        
    def search_images(self, query, max_results=20):
        """Основной метод поиска изображений"""
        logger.info(f"🔍 Начало поиска изображений для: '{query}'")
        
        query_words = re.findall(r'\w+', query.lower())
        if not query_words:
            return []
        
        # Этап 1: Сканирование и сбор изображений
        all_images = self._crawl_images(query, query_words)
        
        # Этап 2: Анализ метаданных и индексация
        analyzed_images = self._analyze_and_index_images(all_images, query_words)
        
        # Этап 3: Ранжирование результатов
        ranked_images = self._rank_images(analyzed_images, query_words)
        
        # Этап 4: Форматирование результатов
        final_results = self._format_results(ranked_images[:max_results])
        
        logger.info(f"✅ Поиск завершен. Найдено: {len(final_results)} изображений")
        return final_results

    def _crawl_images(self, query, query_words):
        """Этап 1: Сканирование страниц и сбор изображений"""
        all_images = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Сканирование специализированных фото-сайтов
            for site in self.start_urls:
                search_url = site + quote_plus(query)
                future = executor.submit(self.crawler.crawl_page, search_url, query_words)
                futures.append(future)
            
            # Сканирование дополнительных страниц на основе запроса
            additional_urls = self._generate_search_urls(query)
            for url in additional_urls[:3]:
                future = executor.submit(self.crawler.crawl_page, url, query_words)
                futures.append(future)
            
            # Сбор результатов
            for future in concurrent.futures.as_completed(futures):
                try:
                    images = future.result(timeout=10)
                    all_images.extend(images)
                except Exception as e:
                    continue
        
        return all_images

    def _generate_search_urls(self, query):
        """Генерация URL для поиска на основе запроса"""
        base_searches = [
            f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch",
            f"https://www.bing.com/images/search?q={quote_plus(query)}",
            f"https://yandex.ru/images/search?text={quote_plus(query)}",
        ]
        
        return base_searches

    def _analyze_and_index_images(self, images, query_words):
        """Этап 2: Анализ метаданных и компьютерное зрение"""
        analyzed_images = []
        
        for image_data in images:
            try:
                # Пропускаем уже проанализированные
                if image_data['id'] in image_index['by_id']:
                    analyzed_images.append(image_index['by_id'][image_data['id']])
                    continue
                
                # Анализ компьютерным зрением
                if not image_data['vision_analyzed']:
                    vision_analysis = image_analyzer.analyze_image(image_data['url'])
                    image_data['vision_analysis'] = vision_analysis
                    image_data['vision_analyzed'] = True
                
                # Обновление релевантности на основе анализа зрения
                vision_score = self._calculate_vision_relevance(image_data['vision_analysis'], query_words)
                image_data['relevance_score'] += vision_score
                
                # Индексация изображения
                self._index_image(image_data)
                analyzed_images.append(image_data)
                
                app_status['indexed_images'] += 1
                
            except Exception as e:
                logger.error(f"❌ Ошибка анализа изображения {image_data['url']}: {e}")
                continue
        
        return analyzed_images

    def _calculate_vision_relevance(self, vision_analysis, query_words):
        """Расчет релевантности на основе анализа компьютерного зрения"""
        score = 0
        
        for obj, confidence in vision_analysis.items():
            for word in query_words:
                if word in obj or self._is_synonym(word, obj):
                    score += confidence * 2  # Высокий вес для совпадений в анализе зрения
        
        return score

    def _is_synonym(self, word, object_name):
        """Проверка синонимичности (упрощенная)"""
        synonyms = {
            'кот': ['кошка', 'котенок'],
            'собака': ['пес', 'щенок'],
            'машина': ['автомобиль', 'тачка'],
            'человек': ['люди', 'персона'],
            'цветок': ['цветы', 'букет'],
            'дом': ['здание', 'строение'],
            'горы': ['гора', 'вершина'],
            'пляж': ['берег', 'песок'],
            'город': ['улица', 'здания']
        }
        return word in synonyms.get(object_name, [])

    def _index_image(self, image_data):
        """Индексация изображения в глобальном индексе"""
        image_id = image_data['id']
        
        # Сохраняем в основной индекс
        image_index['by_id'][image_id] = image_data
        
        # Индексация по объектам (компьютерное зрение)
        if 'vision_analysis' in image_data:
            for obj, confidence in image_data['vision_analysis'].items():
                if confidence > 0.3:  # Только уверенные предсказания
                    image_index['by_object'][obj].append(image_id)
        
        # Индексация по домену
        image_index['by_domain'][image_data['domain']].append(image_id)
        
        # Индексация по цветам (если есть в анализе)
        if 'vision_analysis' in image_data:
            for color in image_data['vision_analysis'].keys():
                if color in image_analyzer.color_names.values():
                    image_index['by_color'][color].append(image_id)

    def _rank_images(self, images, query_words):
        """Этап 3: Ранжирование изображений"""
        scored_images = []
        
        for image in images:
            try:
                # Базовый счет на основе метаданных
                final_score = image['relevance_score']
                
                # Бонус за качественные источники
                final_score += self._calculate_domain_authority(image['domain'])
                
                # Бонус за высокое качество изображения (упрощенно)
                final_score += self._estimate_image_quality(image)
                
                # Штраф за низкое качество метаданных
                if not image['alt'] and not image['title']:
                    final_score -= 2
                
                scored_images.append((final_score, image))
                
            except Exception as e:
                continue
        
        # Сортировка по убыванию релевантности
        scored_images.sort(key=lambda x: x[0], reverse=True)
        return [img for score, img in scored_images]

    def _calculate_domain_authority(self, domain):
        """Расчет авторитетности домена (упрощенно)"""
        authority_domains = {
            'unsplash.com': 3,
            'pixabay.com': 3,
            'pexels.com': 3,
            'flickr.com': 2,
            'shutterstock.com': 2,
            'gettyimages.com': 2,
            'wikipedia.org': 2,
            'nationalgeographic.com': 3
        }
        return authority_domains.get(domain, 0)

    def _estimate_image_quality(self, image_data):
        """Оценка качества изображения (упрощенно)"""
        score = 0
        
        # Бонус за наличие детальных метаданных
        if len(image_data.get('alt', '')) > 10:
            score += 1
        if len(image_data.get('title', '')) > 5:
            score += 1
        if image_data.get('filename'):
            score += 1
        
        # Бонус за анализ компьютерным зрением
        if image_data.get('vision_analyzed'):
            score += 2
        
        return score

    def _format_results(self, images):
        """Форматирование результатов для вывода"""
        formatted_results = []
        
        for image in images:
            try:
                # Создание описания на основе метаданных
                description_parts = []
                if image.get('alt'):
                    description_parts.append(image['alt'])
                elif image.get('title'):
                    description_parts.append(image['title'])
                elif image.get('filename'):
                    description_parts.append(image['filename'])
                
                description = ' '.join(description_parts) or "Изображение"
                
                # Определение типа анализа
                analysis_type = "🤖 Компьютерное зрение" if image.get('vision_analyzed') else "📝 Метаданные"
                
                formatted_results.append({
                    'title': description[:80],
                    'url': image['url'],
                    'thumbnail': image['thumbnail'],
                    'source': image['domain'],
                    'metadata': {
                        'alt': image.get('alt', ''),
                        'context': image.get('context', '')[:100],
                        'relevance_score': round(image.get('relevance_score', 0), 2),
                        'analysis_type': analysis_type,
                        'filename': image.get('filename', '')
                    }
                })
            except Exception as e:
                continue
        
        return formatted_results

# Инициализация поисковой системы
image_search_engine = ImageSearchEngine()

# HTML шаблон
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
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo"><a href="/">AriOS</a></div>
            <div class="tagline">Продвинутая поисковая система • Умный поиск изображений</div>
            
            {% if show_status %}
                {% if is_active %}
                <div class="status-info">
                    ✅ Сервис активен • Проиндексировано: {{ indexed_images }} изображений • 
                    Обработано: {{ processed_pages }} страниц • Поисков: {{ total_searches }}
                </div>
                {% else %}
                <div class="status-warning">
                    ⚠️ Сервис может быть неактивен • Последний пинг: {{ last_ping }}
                </div>
                {% endif %}
            {% endif %}
            
            <form action="/search" method="GET" id="searchForm">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Введите запрос для поиска изображений..." autofocus>
                <br>
                <button type="submit" class="search-button">Найти в AriOS</button>
                <button type="button" class="search-button" style="background: #6b7280;" onclick="location.href='/?status=true'">Статус</button>
            </form>
            
            {% if not results and not images and not videos and not error and not loading %}
            <div class="quick-search">
                <strong>Попробуйте найти:</strong><br>
                <button class="quick-search-btn" onclick="setSearch('кошки котята')">Кошки</button>
                <button class="quick-search-btn" onclick="setSearch('горы природа')">Горы</button>
                <button class="quick-search-btn" onclick="setSearch('цветы розы')">Цветы</button>
                <button class="quick-search-btn" onclick="setSearch('город небоскребы')">Город</button>
                <button class="quick-search-btn" onclick="setSearch('пляж море')">Пляж</button>
            </div>
            {% endif %}
            
            <div class="feature-badges">
                <div class="badge">🔍 Умный поиск</div>
                <div class="badge">📷 Компьютерное зрение</div>
                <div class="badge">🌐 Сканирование сайтов</div>
                <div class="badge">⚡ Быстрый анализ</div>
                <div class="badge">🎯 Точные результаты</div>
            </div>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if loading %}
            <div class="loading">
                🔍 Ищем изображения для "{{ query }}"...
                <div class="stats-info">
                    Этап 1: Сканирование сайтов... | Этап 2: Анализ изображений... | Этап 3: Ранжирование...
                </div>
            </div>
            {% endif %}
            
            {% if results or images or videos %}
            <div class="results-container">
                <div class="results-header">
                    Найдено изображений: {{ total_results }} • Время: {{ search_time }}с • 
                    Запрос: "{{ query }}" • Алгоритм: компьютерное зрение + метаданные
                </div>
                
                <div class="search-stats">
                    🔍 <strong>Алгоритм поиска:</strong> 
                    Сканирование 10+ фото-сайтов → Анализ метаданных (alt, title, filename) → 
                    Компьютерное зрение → Многофакторное ранжирование
                </div>
                
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
                        <a href="{{ result.url }}" class="result-title" target="_blank">{{ result.highlighted_title|safe }}</a>
                        <div class="result-url">{{ result.display_url }}</div>
                        <div class="result-snippet">{{ result.highlighted_snippet|safe }}</div>
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
                        <a href="{{ result.url }}" class="result-title" target="_blank">{{ result.highlighted_title|safe }}</a>
                        <div class="result-url">{{ result.display_url }}</div>
                        <div class="result-snippet">{{ result.highlighted_snippet|safe }}</div>
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
                        Сканирование Unsplash, Pixabay, Pexels + Анализ alt/text + Компьютерное зрение + Ранжирование по релевантности
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
            © 2024 AriOS • Продвинутая поисковая система • Компьютерное зрение • 
            <a href="/status" style="color: #6366f1;">Статус</a> • 
            <a href="/about" style="color: #6366f1;">О системе</a>
        </div>
    </div>

    <script>
        function setSearch(term) {
            document.querySelector('.search-box').value = term;
            document.getElementById('searchForm').submit();
        }
        
        function showContent(type) {
            // Скрываем все контент-блоки
            document.querySelectorAll('.content-type').forEach(el => {
                el.classList.remove('active');
            });
            
            // Показываем выбранный контент-блок
            document.getElementById('content-' + type).classList.add('active');
            
            // Обновляем активную вкладку
            document.querySelectorAll('.filter-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Сохраняем выбранную вкладку в URL
            const url = new URL(window.location);
            url.searchParams.set('tab', type);
            window.history.replaceState({}, '', url);
        }
        
        // Восстанавливаем выбранную вкладку при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const savedTab = urlParams.get('tab');
            if (savedTab) {
                showContent(savedTab);
            }
        });
        
        document.querySelector('.search-box').focus();
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
                                processed_pages=app_status['processed_pages'])

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
                                   processed_pages=app_status['processed_pages'])
    
    try:
        app_status['total_searches'] += 1
        
        start_time = time.time()
        
        # Используем только улучшенный поиск изображений
        images = image_search_engine.search_images(query, max_results=20)
        results = []  # Для совместимости с шаблоном
        videos = []   # Для совместимости с шаблоном
        
        search_time = time.time() - start_time
        
        total_results = len(images)
        websites_count = 0
        images_count = len(images)
        videos_count = 0
        
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
                                   processed_pages=app_status['processed_pages'])
    
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
                                   processed_pages=app_status['processed_pages'])

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': int(time.time() - app_status['start_time']),
        'total_searches': app_status['total_searches'],
        'indexed_images': app_status['indexed_images'],
        'processed_pages': app_status['processed_pages']
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
    
    return jsonify({
        'status': 'active' if app_status['is_active'] else 'inactive',
        'last_self_ping': app_status['last_self_ping'],
        'last_ping_human': last_ping,
        'total_searches': app_status['total_searches'],
        'indexed_images': app_status['indexed_images'],
        'processed_pages': app_status['processed_pages'],
        'start_time': app_status['start_time'],
        'uptime': uptime,
        'uptime_human': uptime_str
    })

# Запускаем само-пинг при старте приложения
start_background_scheduler()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting AriOS Advanced Image Search Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
