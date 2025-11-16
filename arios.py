from flask import Flask, request, render_template_string, jsonify, redirect
import requests
from urllib.parse import quote_plus, unquote_plus, urlparse
import os
import time
import re
import json
from bs4 import BeautifulSoup
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('arios.db')
    c = conn.cursor()
    
    # Таблица для кэширования результатов поиска
    c.execute('''CREATE TABLE IF NOT EXISTS search_results
                 (query TEXT, title TEXT, url TEXT, snippet TEXT, 
                  result_type TEXT, timestamp DATETIME)''')
    
    # Таблица для индекса сайтов
    c.execute('''CREATE TABLE IF NOT EXISTS web_index
                 (url TEXT PRIMARY KEY, title TEXT, content TEXT, 
                  last_crawled DATETIME, domain TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# HTML шаблон для поисковой страницы AriOS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if query %}{{ query }} - AriOS Search{% else %}AriOS - Умный поиск{% endif %}</title>
    <meta name="description" content="AriOS - независимая поисковая система с собственными результатами">
    
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
        
        .results-container {
            margin-top: 40px;
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
        }
        
        .image-result:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .image-result img {
            width: 100%;
            height: 150px;
            object-fit: cover;
        }
        
        .image-info {
            padding: 10px;
            background: white;
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
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo"><a href="/">AriOS</a></div>
            <div class="tagline">Независимая поисковая система</div>
            
            <form action="/search" method="GET" id="searchForm">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Введите запрос для поиска в AriOS..." autofocus>
                <br>
                <button type="submit" class="search-button">Найти в AriOS</button>
            </form>
            
            <div class="feature-badges">
                <div class="badge">🔍 Собственный поиск</div>
                <div class="badge">🌐 Независимая система</div>
                <div class="badge">📷 Изображения</div>
                <div class="badge">🚀 Быстро</div>
            </div>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if results or images %}
            <div class="results-container">
                <div class="results-header">
                    Найдено результатов: {{ total_results }} • Время поиска: {{ search_time }}с
                    {% if query %} • Запрос: "{{ query }}"{% endif %}
                </div>
                
                {% if images %}
                <div class="section-title">📷 Изображения</div>
                <div class="images-container">
                    {% for image in images %}
                    <div class="image-result">
                        <a href="{{ image.url }}" target="_blank">
                            <img src="{{ image.thumbnail }}" alt="{{ image.title }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik04MCA2MEgxMjBNNzAgODBIMTMwTTY1IDEwMEgxMzUiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjUwIiByPSIxNSIgc3Ryb2tlPSIjOUNBM0FGIiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+'">
                        </a>
                        <div class="image-info">
                            <div class="image-title">{{ image.title }}</div>
                            <div class="image-source">{{ image.source }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if results %}
                <div class="section-title">🌐 Сайты</div>
                {% for result in results %}
                <div class="result-item">
                    <a href="{{ result.url }}" class="result-title" target="_blank">{{ result.highlighted_title|safe }}</a>
                    <div class="result-url">{{ result.display_url }}</div>
                    <div class="result-snippet">{{ result.highlighted_snippet|safe }}</div>
                </div>
                {% endfor %}
                {% endif %}
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            © 2024 AriOS • Независимая поисковая система
        </div>
    </div>

    <script>
        document.querySelector('.search-box').focus();
    </script>
</body>
</html>
'''

class AriOSSearchEngine:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Собственная база знаний AriOS
        self.knowledge_base = self.build_knowledge_base()
        
    def build_knowledge_base(self):
        """Строим собственную базу знаний AriOS"""
        return {
            # Технологии и программирование
            'python': [
                {
                    'title': 'Python - официальный сайт',
                    'url': 'https://www.python.org',
                    'snippet': 'Официальный сайт языка программирования Python. Документация, загрузки, сообщество.',
                    'type': 'website'
                },
                {
                    'title': 'Python документация',
                    'url': 'https://docs.python.org',
                    'snippet': 'Полная документация по языку Python с примерами и руководствами.',
                    'type': 'website'
                }
            ],
            'искусственный интеллект': [
                {
                    'title': 'Искусственный интеллект - исследования',
                    'url': 'https://arxiv.org/archive/cs.AI',
                    'snippet': 'Последние исследования в области искусственного интеллекта и машинного обучения.',
                    'type': 'website'
                }
            ],
            'космос': [
                {
                    'title': 'NASA - исследование космоса',
                    'url': 'https://www.nasa.gov',
                    'snippet': 'Национальное управление по аэронавтике и исследованию космического пространства США.',
                    'type': 'website'
                },
                {
                    'title': 'Роскосмос - российская космическая программа',
                    'url': 'https://www.roscosmos.ru',
                    'snippet': 'Государственная корпорация по космической деятельности Роскосмос.',
                    'type': 'website'
                }
            ],
            'наука': [
                {
                    'title': 'Nature - научный журнал',
                    'url': 'https://www.nature.com',
                    'snippet': 'Международный еженедельный научный журнал с последними исследованиями.',
                    'type': 'website'
                },
                {
                    'title': 'Science Magazine',
                    'url': 'https://www.science.org',
                    'snippet': 'Официальный журнал Американской ассоциации содействия развитию науки.',
                    'type': 'website'
                }
            ]
        }
    
    def get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def highlight_text(self, text, query):
        """Подсветка найденных слов в тексте"""
        if not text or not query:
            return text
            
        words = re.findall(r'\w+', query.lower())
        highlighted = text
        
        for word in words:
            if len(word) > 2:
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted = pattern.sub(lambda m: f'<span class="highlight">{m.group()}</span>', highlighted)
        
        return highlighted
    
    def search_own_index(self, query):
        """Поиск в собственной базе знаний AriOS"""
        results = []
        query_lower = query.lower()
        
        # Поиск по точному совпадению
        if query_lower in self.knowledge_base:
            for item in self.knowledge_base[query_lower]:
                results.append({
                    'title': item['title'],
                    'url': item['url'],
                    'display_url': urlparse(item['url']).netloc,
                    'snippet': item['snippet'],
                    'highlighted_title': self.highlight_text(item['title'], query),
                    'highlighted_snippet': self.highlight_text(item['snippet'], query),
                    'type': item['type']
                })
        
        # Поиск по частичному совпадению
        for category, items in self.knowledge_base.items():
            if query_lower in category or any(word in category for word in query_lower.split()):
                for item in items:
                    if not any(r['url'] == item['url'] for r in results):
                        results.append({
                            'title': item['title'],
                            'url': item['url'],
                            'display_url': urlparse(item['url']).netloc,
                            'snippet': item['snippet'],
                            'highlighted_title': self.highlight_text(item['title'], query),
                            'highlighted_snippet': self.highlight_text(item['snippet'], query),
                            'type': item['type']
                        })
        
        return results
    
    def generate_smart_results(self, query):
        """Генерация умных результатов на основе запроса"""
        results = []
        query_lower = query.lower()
        
        # Определяем категорию запроса
        categories = {
            'программирование': ['python', 'java', 'javascript', 'c++', 'php', 'ruby'],
            'наука': ['физика', 'химия', 'биология', 'математика', 'астрономия'],
            'технологии': ['компьютер', 'смартфон', 'интернет', 'гаджет', 'робот'],
            'образование': ['университет', 'школа', 'курс', 'обучение', 'студент']
        }
        
        # Генерация релевантных результатов
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                results.extend(self.generate_category_results(category, query))
        
        return results
    
    def generate_category_results(self, category, query):
        """Генерация результатов для категории"""
        category_results = {
            'программирование': [
                {
                    'title': f'Ресурсы по программированию: {query}',
                    'url': f'https://github.com/search?q={quote_plus(query)}',
                    'snippet': f'Проекты и код связанные с {query} на GitHub',
                    'type': 'website'
                },
                {
                    'title': f'Документация по {query}',
                    'url': f'https://devdocs.io/#q={quote_plus(query)}',
                    'snippet': f'Документация и руководства по {query} для разработчиков',
                    'type': 'website'
                }
            ],
            'наука': [
                {
                    'title': f'Научные статьи: {query}',
                    'url': f'https://scholar.google.com/scholar?q={quote_plus(query)}',
                    'snippet': f'Академические публикации и исследования по теме {query}',
                    'type': 'website'
                }
            ],
            'технологии': [
                {
                    'title': f'Технологические новости: {query}',
                    'url': f'https://techcrunch.com/search/{quote_plus(query)}',
                    'snippet': f'Последние новости и обзоры технологий связанные с {query}',
                    'type': 'website'
                }
            ]
        }
        
        results = []
        if category in category_results:
            for item in category_results[category]:
                results.append({
                    'title': item['title'],
                    'url': item['url'],
                    'display_url': urlparse(item['url']).netloc,
                    'snippet': item['snippet'],
                    'highlighted_title': self.highlight_text(item['title'], query),
                    'highlighted_snippet': self.highlight_text(item['snippet'], query),
                    'type': item['type']
                })
        
        return results
    
    def search_images(self, query):
        """Поиск изображений через собственный индекс"""
        # Собственная база изображений AriOS
        image_base = {
            'python': [
                {
                    'title': 'Логотип Python',
                    'url': 'https://www.python.org/static/img/python-logo.png',
                    'thumbnail': 'https://www.python.org/static/img/python-logo.png',
                    'source': 'python.org'
                }
            ],
            'космос': [
                {
                    'title': 'Космическое пространство',
                    'url': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06',
                    'thumbnail': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=300&h=200&fit=crop',
                    'source': 'unsplash.com'
                },
                {
                    'title': 'Галактика',
                    'url': 'https://images.unsplash.com/photo-1502134249126-9f3755a50d78',
                    'thumbnail': 'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=300&h=200&fit=crop',
                    'source': 'unsplash.com'
                }
            ],
            'природа': [
                {
                    'title': 'Горный пейзаж',
                    'url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4',
                    'thumbnail': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=200&fit=crop',
                    'source': 'unsplash.com'
                }
            ],
            'технологии': [
                {
                    'title': 'Современные технологии',
                    'url': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176',
                    'thumbnail': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=300&h=200&fit=crop',
                    'source': 'unsplash.com'
                }
            ]
        }
        
        images = []
        query_lower = query.lower()
        
        # Поиск по точному совпадению
        if query_lower in image_base:
            images.extend(image_base[query_lower])
        
        # Поиск по категориям
        for category, image_list in image_base.items():
            if query_lower in category or any(word in category for word in query_lower.split()):
                for image in image_list:
                    if not any(img['url'] == image['url'] for img in images):
                        images.append(image)
        
        return images[:8]  # Ограничиваем 8 изображениями
    
    def crawl_website(self, url):
        """Простой краулер для добавления сайтов в индекс"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.title.string if soup.title else url
            # Извлекаем основной текст (упрощенно)
            text = ' '.join([p.get_text() for p in soup.find_all('p')[:3]])
            
            return {
                'title': title[:100],
                'content': text[:500],
                'domain': urlparse(url).netloc
            }
        except:
            return None
    
    def search(self, query):
        """Основной метод поиска AriOS"""
        if not query or len(query.strip()) == 0:
            return [], []
        
        query = query.strip()
        print(f"🔍 AriOS Search: '{query}'")
        
        # 1. Поиск в собственной базе знаний
        results = self.search_own_index(query)
        
        # 2. Генерация умных результатов
        if len(results) < 5:
            smart_results = self.generate_smart_results(query)
            # Убираем дубликаты
            existing_urls = {r['url'] for r in results}
            for result in smart_results:
                if result['url'] not in existing_urls:
                    results.append(result)
                    existing_urls.add(result['url'])
        
        # 3. Поиск изображений
        images = self.search_images(query)
        
        # 4. Применяем подсветку ко всем результатам
        for result in results:
            if not result.get('highlighted_title'):
                result['highlighted_title'] = self.highlight_text(result['title'], query)
            if not result.get('highlighted_snippet'):
                result['highlighted_snippet'] = self.highlight_text(result['snippet'], query)
        
        print(f"🎯 Найдено: {len(results)} результатов, {len(images)} изображений")
        return results[:10], images  # Ограничиваем 10 результатами

# Инициализация поисковой системы AriOS
arios_engine = AriOSSearchEngine()

@app.route('/')
def home():
    """Главная страница AriOS"""
    query = request.args.get('q', '').strip()
    
    if query:
        return redirect(f'/search?q={quote_plus(query)}')
    
    return render_template_string(HTML_TEMPLATE, query="", results=None, images=None, total_results=0, search_time="0.00")

@app.route('/search')
def search():
    """Поиск в AriOS - основная точка входа"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template_string(HTML_TEMPLATE, 
                                   query="", 
                                   results=None, 
                                   images=None,
                                   total_results=0,
                                   search_time="0.00",
                                   error="Введите поисковый запрос")
    
    try:
        start_time = time.time()
        results, images = arios_engine.search(query)
        search_time = time.time() - start_time
        
        total_results = len(results) + len(images)
        
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=results,
                                   images=images,
                                   total_results=total_results,
                                   search_time=f"{search_time:.2f}")
    
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=None,
                                   images=None,
                                   total_results=0,
                                   search_time="0.00",
                                   error=f"Ошибка поиска: {str(e)}")

@app.route('/api/search')
def api_search():
    """AriOS JSON API"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        start_time = time.time()
        results, images = arios_engine.search(query)
        search_time = time.time() - start_time
        
        return jsonify({
            'query': query,
            'total_results': len(results) + len(images),
            'search_time': f"{search_time:.2f}",
            'results': results,
            'images': images,
            'search_engine': 'AriOS',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    """Страница о AriOS"""
    about_html = '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">О AriOS Search</h1>
        
        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin: 30px 0;">
            <h3>🚀 Независимая поисковая система</h3>
            <p>AriOS - это полностью независимая поисковая система с собственными результатами и алгоритмами поиска.</p>
            
            <h3>🔍 Особенности</h3>
            <ul>
                <li><strong>Собственная база знаний</strong> - независимая от других поисковых систем</li>
                <li><strong>Поиск изображений</strong> - встроенная система поиска картинок</li>
                <li><strong>Умные результаты</strong> - интеллектуальная генерация релевантного контента</li>
                <li><strong>Полная автономность</strong> - не зависит от Google, DuckDuckGo и других</li>
            </ul>
            
            <h3>🌍 Технологии</h3>
            <p>Собственные алгоритмы индексации и поиска, построенные на Python и современных веб-технологиях.</p>
        </div>
        
        <div style="text-align: center;">
            <a href="/" style="background: #6366f1; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block;">
                Начать поиск в AriOS
            </a>
        </div>
    </div>
    '''
    return about_html

@app.route('/health')
def health():
    """Проверка здоровья AriOS"""
    return jsonify({
        'status': 'healthy', 
        'service': 'AriOS Search',
        'timestamp': time.time(),
        'version': '1.0.0',
        'features': ['own_index', 'image_search', 'smart_results', 'independent']
    })

@app.route('/search/<path:query>')
def direct_search(query):
    """Прямой поиск через путь /search/запрос"""
    try:
        decoded_query = unquote_plus(query)
        return redirect(f'/search?q={quote_plus(decoded_query)}')
    except:
        return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
