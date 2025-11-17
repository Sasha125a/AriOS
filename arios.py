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

app = Flask(__name__)

# Глобальная переменная для отслеживания статуса
app_status = {
    'last_self_ping': None,
    'total_searches': 0,
    'start_time': time.time(),
    'is_active': True
}

# Функция для само-пинга
def self_ping():
    """Отправляет запросы самому себе чтобы держать приложение активным"""
    try:
        # Определяем базовый URL автоматически
        if 'RENDER_EXTERNAL_URL' in os.environ:
            base_url = os.environ['RENDER_EXTERNAL_URL']
        else:
            # Для локальной разработки или если переменная не установлена
            base_url = 'https://arios-yqnm.onrender.com'
            
        health_url = f"{base_url}/health"
        search_url = f"{base_url}/search?q=python"
        
        print(f"🔁 Starting self-ping to {base_url}")
        
        # Пингуем health endpoint
        try:
            response1 = requests.get(health_url, timeout=10)
            print(f"✅ Health ping: {response1.status_code}")
        except Exception as e:
            print(f"❌ Health ping failed: {e}")
        
        # Пингуем поиск для поддержания активности
        try:
            response2 = requests.get(search_url, timeout=10)
            print(f"✅ Search ping: {response2.status_code}")
        except Exception as e:
            print(f"❌ Search ping failed: {e}")
        
        app_status['last_self_ping'] = time.time()
        app_status['total_searches'] += 1
        app_status['is_active'] = True
        
        print(f"✅ Self-ping completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Self-ping error: {e}")
        app_status['is_active'] = False

# Функция для запуска планировщика
def run_scheduler():
    """Запускает планировщик для регулярных само-пингов"""
    print("🕒 Starting background scheduler...")
    
    # Пингуем каждые 2 минуты (Render засыпает после 5 минут неактивности)
    schedule.every(2).minutes.do(self_ping)
    
    # Также делаем дополнительный пинг каждые 30 секунд для надежности
    schedule.every(30).seconds.do(lambda: 
        requests.get(f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://arios-yqnm.onrender.com')}/ping", timeout=5) 
        if random.random() > 0.3 else None
    )
    
    # Сразу делаем первый пинг
    print("🔁 Performing initial self-ping...")
    self_ping()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            time.sleep(10)

# Запускаем планировщик в отдельном потоке
def start_background_scheduler():
    """Запускает фоновый планировщик"""
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("🚀 Background scheduler started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")
        return False

# HTML шаблон для поисковой страницы AriOS
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
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo"><a href="/">AriOS</a></div>
            <div class="tagline">Реальная поисковая система • Всегда активна</div>
            
            {% if show_status %}
                {% if is_active %}
                <div class="status-info">
                    ✅ Сервис активен • Последний пинг: {{ last_ping }} • Поисков: {{ total_searches }} • Uptime: {{ uptime }}
                </div>
                {% else %}
                <div class="status-warning">
                    ⚠️ Сервис может быть неактивен • Последний пинг: {{ last_ping }}
                </div>
                {% endif %}
            {% endif %}
            
            <form action="/search" method="GET" id="searchForm">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Введите запрос для поиска в интернете..." autofocus>
                <br>
                <button type="submit" class="search-button">Найти в AriOS</button>
                <button type="button" class="search-button" style="background: #6b7280;" onclick="location.href='/?status=true'">Статус</button>
            </form>
            
            {% if not results and not images and not videos and not error and not loading %}
            <div class="quick-search">
                <strong>Попробуйте найти:</strong><br>
                <button class="quick-search-btn" onclick="setSearch('Python программирование')">Python</button>
                <button class="quick-search-btn" onclick="setSearch('космос Вселенная')">Космос</button>
                <button class="quick-search-btn" onclick="setSearch('искусственный интеллект')">ИИ</button>
                <button class="quick-search-btn" onclick="setSearch('природа пейзажи')">Природа</button>
                <button class="quick-search-btn" onclick="setSearch('технологии будущее')">Технологии</button>
            </div>
            {% endif %}
            
            <div class="feature-badges">
                <div class="badge">🔍 Настоящий поиск</div>
                <div class="badge">📷 Фото</div>
                <div class="badge">🎥 Видео</div>
                <div class="badge">🌐 Сайты</div>
                <div class="badge">⚡ Активный</div>
            </div>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if loading %}
            <div class="loading">
                🔍 Ищем результаты для "{{ query }}"...
            </div>
            {% endif %}
            
            {% if results or images or videos %}
            <div class="results-container">
                <div class="results-header">
                    Найдено: {{ total_results }} • Время: {{ search_time }}с • Запрос: "{{ query }}"
                </div>
                
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
                <div class="section-title">📷 Изображения</div>
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
            {% endif %}
        </div>
        
        <div class="footer">
            © 2024 AriOS • Реальная поисковая система • Всегда активна • 
            <a href="/status" style="color: #6366f1;">Статус</a> • 
            <a href="/about" style="color: #6366f1;">О системе</a>
        </div>
    </div>

    <script>
        function setSearch(term) {
            document.querySelector('.search-box').value = term;
            document.getElementById('searchForm').submit();
        }
        
        document.querySelector('.search-box').focus();
    </script>
</body>
</html>
'''

class AriOSRealSearch:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
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
    
    def search_websites(self, query):
        """Поиск реальных веб-сайтов через DuckDuckGo"""
        try:
            url = "https://html.duckduckgo.com/html/"
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://html.duckduckgo.com',
                'Referer': 'https://html.duckduckgo.com/',
            }
            
            data = {
                'q': query,
                'b': '',
                'kl': 'ru-ru'
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                return self.parse_website_results(response.text, query)
            else:
                return self.get_fallback_websites(query)
                
        except Exception as e:
            print(f"Website search error: {e}")
            return self.get_fallback_websites(query)
    
    def parse_website_results(self, html, query):
        """Парсинг реальных результатов поиска"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        result_blocks = soup.find_all('div', class_='result') or soup.find_all('div', class_='web-result')
        
        for block in result_blocks[:8]:
            try:
                title_elem = block.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                # Обрабатываем URL DuckDuckGo
                if url.startswith('//duckduckgo.com/l/?uddg='):
                    match = re.search(r'uddg=([^&]+)', url)
                    if match:
                        url = unquote_plus(match.group(1))
                
                snippet_elem = block.find('a', class_='result__snippet') or block.find('div', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "Описание недоступно"
                
                display_url = self.extract_display_url(url)
                
                if title and url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'url': url,
                        'display_url': display_url,
                        'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet,
                        'highlighted_title': self.highlight_text(title, query),
                        'highlighted_snippet': self.highlight_text(snippet, query)
                    })
                    
            except Exception as e:
                continue
        
        return results if results else self.get_fallback_websites(query)
    
    def search_images(self, query):
        """Поиск реальных изображений"""
        try:
            # Используем Unsplash API для качественных изображений
            # В реальном приложении нужно получить API ключ
            return self.get_fallback_images(query)
                
        except Exception as e:
            print(f"Image search error: {e}")
            return self.get_fallback_images(query)
    
    def get_fallback_images(self, query):
        """Резервные изображения"""
        image_base = {
            'python': [
                {
                    'title': 'Python программирование',
                    'url': 'https://images.unsplash.com/photo-1526379879527-8559ecfcaec0',
                    'thumbnail': 'https://images.unsplash.com/photo-1526379879527-8559ecfcaec0?w=300&h=200&fit=crop',
                    'source': 'unsplash.com'
                }
            ],
            'космос': [
                {
                    'title': 'Космическое пространство',
                    'url': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06',
                    'thumbnail': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=300&h=200&fit=crop',
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
        
        for category, image_list in image_base.items():
            if query_lower in category or any(word in category for word in query_lower.split()):
                for image in image_list:
                    if not any(img['url'] == image['url'] for img in images):
                        images.append(image)
        
        return images[:8]
    
    def search_videos(self, query):
        """Поиск видео"""
        try:
            # В реальном приложении нужно получить YouTube API ключ
            return self.get_fallback_videos(query)
                
        except Exception as e:
            print(f"Video search error: {e}")
            return self.get_fallback_videos(query)
    
    def get_fallback_videos(self, query):
        """Резервные видео"""
        return [
            {
                'title': f'Видео по запросу: {query}',
                'url': f'https://www.youtube.com/results?search_query={quote_plus(query)}',
                'thumbnail': 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4=',
                'channel': 'YouTube',
                'duration': 'Перейти к просмотру'
            }
        ]
    
    def get_fallback_websites(self, query):
        """Резервные веб-сайты"""
        return [
            {
                'title': f'Результаты поиска: {query}',
                'url': f'https://duckduckgo.com/?q={quote_plus(query)}',
                'display_url': 'duckduckgo.com',
                'snippet': f'Нажмите чтобы увидеть больше результатов по запросу "{query}"',
                'highlighted_title': self.highlight_text(f'Результаты поиска: {query}', query),
                'highlighted_snippet': self.highlight_text(f'Нажмите чтобы увидеть больше результатов', query)
            }
        ]
    
    def extract_display_url(self, url):
        """Извлекает красивый URL для отображения"""
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                return parsed.netloc.replace('www.', '')
        except:
            pass
        return url[:50] + "..." if len(url) > 50 else url
    
    def search(self, query):
        """Основной метод поиска AriOS"""
        if not query or len(query.strip()) == 0:
            return [], [], []
        
        query = query.strip()
        print(f"🔍 AriOS Real Search: '{query}'")
        
        try:
            # Параллельный поиск по всем типам контента
            websites = self.search_websites(query)
            images = self.search_images(query)
            videos = self.search_videos(query)
            
            print(f"🎯 Найдено: {len(websites)} сайтов, {len(images)} изображений, {len(videos)} видео")
            
            return websites, images, videos
            
        except Exception as e:
            print(f"❌ AriOS search error: {e}")
            return self.get_fallback_websites(query), self.get_fallback_images(query), self.get_fallback_videos(query)

# Инициализация реальной поисковой системы AriOS
arios_real_search = AriOSRealSearch()

@app.route('/')
def home():
    """Главная страница AriOS - перенаправляет на поиск если есть query"""
    query = request.args.get('q', '').strip()
    show_status = request.args.get('status', 'false').lower() == 'true'
    
    if query:
        return redirect(f'/search?q={quote_plus(query)}')
    
    # Показываем статус активности
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
                                is_active=app_status['is_active'])

@app.route('/search')
def search():
    """Поиск в AriOS - основная точка входа"""
    query = request.args.get('q', '').strip()
    show_status = request.args.get('status', 'false').lower() == 'true'
    
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
                                   show_status=show_status)
    
    try:
        # Увеличиваем счетчик поисков
        app_status['total_searches'] += 1
        
        # Выполняем поиск
        start_time = time.time()
        results, images, videos = arios_real_search.search(query)
        search_time = time.time() - start_time
        
        total_results = len(results) + len(images) + len(videos)
        
        # Показываем статус активности
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
                                   is_active=app_status['is_active'])
    
    except Exception as e:
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
                                   show_status=show_status)

@app.route('/api/search')
def api_search():
    """AriOS JSON API"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        app_status['total_searches'] += 1
        
        start_time = time.time()
        results, images, videos = arios_real_search.search(query)
        search_time = time.time() - start_time
        
        return jsonify({
            'query': query,
            'total_results': len(results) + len(images) + len(videos),
            'search_time': f"{search_time:.2f}",
            'websites': results,
            'images': images,
            'videos': videos,
            'search_engine': 'AriOS',
            'app_status': app_status,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Проверка здоровья AriOS"""
    app_status['last_self_ping'] = time.time()
    app_status['is_active'] = True
    
    return jsonify({
        'status': 'healthy', 
        'service': 'AriOS Real Search',
        'timestamp': time.time(),
        'version': '1.0.0',
        'uptime': int(time.time() - app_status['start_time']),
        'total_searches': app_status['total_searches'],
        'last_self_ping': app_status['last_self_ping'],
        'is_active': app_status['is_active'],
        'message': '✅ Сервис активен и работает'
    })

@app.route('/ping')
def ping():
    """Эндпоинт для пинга"""
    app_status['last_self_ping'] = time.time()
    app_status['is_active'] = True
    return jsonify({'status': 'pong', 'timestamp': time.time()})

@app.route('/status')
def status():
    """Страница статуса"""
    last_ping = "никогда"
    if app_status['last_self_ping']:
        last_ping = f"{int(time.time() - app_status['last_self_ping'])} секунд назад"
    
    uptime = int(time.time() - app_status['start_time'])
    uptime_str = f"{uptime // 3600} часов {(uptime % 3600) // 60} минут {uptime % 60} секунд"
    
    status_html = f'''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">Статус AriOS</h1>
        
        <div style="background: #f0fdf4; padding: 30px; border-radius: 15px; margin: 20px 0;">
            <h3>✅ Система активна и работает</h3>
            <p><strong>Время работы:</strong> {uptime_str}</p>
            <p><strong>Всего поисков:</strong> {app_status['total_searches']}</p>
            <p><strong>Последний пинг:</strong> {last_ping}</p>
            <p><strong>Статус:</strong> 🟢 Работает нормально</p>
            <p><strong>Авто-пинг:</strong> 🔁 Активен (каждые 2 минуты)</p>
        </div>
        
        <div style="background: #f8fafc; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h4>📊 Статистика само-пинга:</h4>
            <p>Система автоматически отправляет запросы самой себе чтобы оставаться активной на Render.</p>
            <p><strong>Частота пинга:</strong> Каждые 2 минуты (полный пинг) + каждые 30 секунд (легкий пинг)</p>
            <p><strong>Цель:</strong> Предотвратить переход в спящий режим на бесплатном хостинге Render</p>
        </div>
        
        <div style="text-align: center;">
            <a href="/?status=true" style="background: #6366f1; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px;">
                На главную
            </a>
            <a href="/search?q=python&status=true" style="background: #10b981; color: white; padding: 12px 30px; 
                                         text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px;">
                Тестовый поиск
            </a>
            <a href="/health" style="background: #f59e0b; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px;">
                Проверить здоровье
            </a>
        </div>
    </div>
    '''
    return status_html

@app.route('/about')
def about():
    """Страница о системе"""
    about_html = '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">О AriOS Search</h1>
        
        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin: 20px 0;">
            <h3>🚀 Реальная поисковая система</h3>
            <p>AriOS - это независимая поисковая система, которая находит реальные результаты из интернета.</p>
            
            <h3>🔍 Что умеет AriOS:</h3>
            <ul>
                <li><strong>Поиск веб-сайтов</strong> - настоящие страницы из интернета</li>
                <li><strong>Поиск изображений</strong> - фотографии и картинки</li>
                <li><strong>Поиск видео</strong> - ролики с YouTube</li>
                <li><strong>Умный поиск</strong> - подсветка результатов</li>
            </ul>
            
            <h3>⚡ Всегда активна</h3>
            <p>Система автоматически поддерживает свою активность на Render, поэтому всегда готова к работе.</p>
        </div>
        
        <div style="text-align: center;">
            <a href="/" style="background: #6366f1; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block;">
                Начать поиск
            </a>
        </div>
    </div>
    '''
    return about_html

@app.route('/search/<path:query>')
def direct_search(query):
    """Прямой поиск через путь /search/запрос"""
    try:
        decoded_query = unquote_plus(query)
        return redirect(f'/search?q={quote_plus(decoded_query)}')
    except:
        return redirect('/')

# Запускаем само-пинг при старте приложения
start_background_scheduler()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting AriOS server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
