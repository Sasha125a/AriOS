from flask import Flask, request, render_template_string, jsonify, redirect
import requests
from urllib.parse import quote_plus, unquote_plus, urlparse
import os
import time
import re
import json
from bs4 import BeautifulSoup
import random

app = Flask(__name__)

# HTML шаблон для поисковой страницы AriOS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if query %}{{ query }} - AriOS Search{% else %}AriOS - Умный поиск{% endif %}</title>
    <meta name="description" content="AriOS - современная поисковая система для быстрого и точного поиска в интернете">
    
    <style>
        :root {
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
            --gradient-start: #8b5cf6;
            --gradient-end: #6366f1;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .main-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-top: 50px;
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
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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
        
        .search-button.secondary {
            background: #f8fafc;
            color: #374151;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .search-button.secondary:hover {
            background: #e5e7eb;
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
        
        .pagination {
            margin-top: 40px;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }
        
        .pagination button {
            padding: 10px 20px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .pagination button:hover:not(:disabled) {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .page-info {
            color: #6b7280;
            font-weight: 600;
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
        
        .search-tips {
            background: #f8fafc;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }
        
        .browser-search-info {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .loading {
            text-align: center;
            color: #6366f1;
            font-size: 16px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo"><a href="/">AriOS</a></div>
            <div class="tagline">Умный поиск следующего поколения</div>
            
            <form action="/search" method="GET" id="searchForm">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Введите любое слово или фразу для поиска в интернете..." autofocus>
                <br>
                <button type="submit" class="search-button">Найти в AriOS</button>
                <button type="button" class="search-button secondary" onclick="location.href='/'">Новый поиск</button>
            </form>
            
            {% if not results and not error %}
            <div class="quick-search">
                <strong>Попробуйте найти:</strong><br>
                <button class="quick-search-btn" onclick="setSearch('искусственный интеллект')">Искусственный интеллект</button>
                <button class="quick-search-btn" onclick="setSearch('программирование Python')">Python</button>
                <button class="quick-search-btn" onclick="setSearch('космос Вселенная')">Космос</button>
                <button class="quick-search-btn" onclick="setSearch('новости технологий')">Технологии</button>
                <button class="quick-search-btn" onclick="setSearch('история науки')">Наука</button>
            </div>
            {% endif %}
            
            <div class="feature-badges">
                <div class="badge">🚀 Настоящий поиск</div>
                <div class="badge">🔍 По всему интернету</div>
                <div class="badge">🌍 Актуальные результаты</div>
                <div class="badge">📚 Из разных источников</div>
            </div>
            
            {% if not results and not error %}
            <div class="browser-search-info">
                <strong>💡 Как использовать AriOS в браузере:</strong><br>
                Добавьте в поисковые системы браузера: <code>https://ВАШ-ДОМЕН/?q=%s</code><br>
                Или используйте прямые ссылки: <code>https://ВАШ-ДОМЕН/search/ваш запрос</code>
            </div>
            
            <div class="search-tips">
                <h3>🔎 Советы по поиску:</h3>
                <p>• <strong>Любые слова</strong> - введите любое слово или фразу для поиска</p>
                <p>• <strong>Точные фразы</strong> - используйте кавычки для точного совпадения</p>
                <p>• <strong>Подсветка</strong> - найденные слова выделяются в результатах</p>
            </div>
            {% endif %}
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if loading %}
            <div class="loading">
                🔍 Ищем результаты по запросу "{{ query }}"...
            </div>
            {% endif %}
            
            {% if results %}
            <div class="results-container">
                <div class="results-header">
                    Найдено результатов: {{ total_results }} • Время поиска: <span id="search-time">{{ search_time }}с</span>
                    {% if query %} • Запрос: "{{ query }}"{% endif %}
                </div>
                
                {% for result in results %}
                <div class="result-item">
                    <a href="{{ result.url }}" class="result-title" target="_blank">{{ result.highlighted_title|safe if result.highlighted_title else result.title }}</a>
                    <div class="result-url">{{ result.display_url }}</div>
                    <div class="result-snippet">{{ result.highlighted_snippet|safe if result.highlighted_snippet else result.snippet }}</div>
                </div>
                {% endfor %}
                
                {% if total_pages > 1 %}
                <div class="pagination">
                    {% if page > 1 %}
                    <button onclick="changePage({{ page - 1 }})">← Назад</button>
                    {% else %}
                    <button disabled>← Назад</button>
                    {% endif %}
                    
                    <span class="page-info">Страница {{ page }} из {{ total_pages }}</span>
                    
                    {% if page < total_pages %}
                    <button onclick="changePage({{ page + 1 }})">Вперед →</button>
                    {% else %}
                    <button disabled>Вперед →</button>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            © 2024 AriOS Search • Настоящий поиск по интернету • 
            <a href="/about" style="color: #6366f1;">О системе</a> •
            <a href="/browser-setup" style="color: #6366f1;">Настройка браузера</a>
        </div>
    </div>

    <script>
        function changePage(newPage) {
            const url = new URL(window.location);
            url.searchParams.set('page', newPage);
            window.location = url.toString();
        }
        
        function setSearch(term) {
            document.querySelector('.search-box').value = term;
            document.getElementById('searchForm').submit();
        }
        
        // Фокус на поисковую строку при загрузке
        document.querySelector('.search-box').focus();
        
        // Анимация времени поиска
        if (document.getElementById('search-time')) {
            let time = 0;
            const targetTime = parseFloat('{{ search_time }}');
            const interval = setInterval(() => {
                time += 0.01;
                if (time >= targetTime) {
                    document.getElementById('search-time').textContent = targetTime.toFixed(2) + 'с';
                    clearInterval(interval);
                } else {
                    document.getElementById('search-time').textContent = time.toFixed(2) + 'с';
                }
            }, 10);
        }
    </script>
</body>
</html>
'''

class AriOSSearch:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
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
    
    def search_duckduckgo(self, query, page=1):
        """Поиск через DuckDuckGo HTML"""
        try:
            url = "https://html.duckduckgo.com/html/"
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://html.duckduckgo.com',
                'Referer': 'https://html.duckduckgo.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            data = {
                'q': query,
                'b': '',
                'kl': 'ru-ru'
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                return self.parse_ddgo_results(response.text, query)
            else:
                print(f"DuckDuckGo returned status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def parse_ddgo_results(self, html, query):
        """Парсинг результатов из DuckDuckGo HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Ищем основные результаты
        result_blocks = soup.find_all('div', class_='result') or soup.find_all('div', class_='web-result')
        
        for block in result_blocks[:12]:
            try:
                # Заголовок и ссылка
                title_elem = block.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                # Обрабатываем URL DuckDuckGo (редиректы)
                if url.startswith('//duckduckgo.com/l/?uddg='):
                    # Извлекаем реальный URL из параметра
                    match = re.search(r'uddg=([^&]+)', url)
                    if match:
                        url = unquote_plus(match.group(1))
                
                # Описание
                snippet_elem = block.find('a', class_='result__snippet') or block.find('div', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "Описание недоступно"
                
                # URL для отображения
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
                print(f"Error parsing result block: {e}")
                continue
        
        return results
    
    def extract_display_url(self, url):
        """Извлекает красивый URL для отображения"""
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                return parsed.netloc.replace('www.', '')
        except:
            pass
        return url[:50] + "..." if len(url) > 50 else url
    
    def search_wikipedia(self, query):
        """Поиск в Wikipedia"""
        try:
            # Поиск через Wikipedia API
            search_url = "https://ru.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 5,
                'srprop': 'snippet'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            data = response.json()
            
            results = []
            for item in data.get('query', {}).get('search', [])[:3]:
                title = item['title']
                page_url = f"https://ru.wikipedia.org/wiki/{quote_plus(title)}"
                snippet = self.clean_html(item.get('snippet', ''))
                
                results.append({
                    'title': title,
                    'url': page_url,
                    'display_url': 'wikipedia.org',
                    'snippet': snippet + '...',
                    'highlighted_title': self.highlight_text(title, query),
                    'highlighted_snippet': self.highlight_text(snippet, query)
                })
            
            return results
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def search_brave_suggest(self, query):
        """Получение подсказок от Brave"""
        try:
            url = "https://search.brave.com/api/suggest"
            params = {
                'q': query,
                'rich': 'true'
            }
            headers = {
                'User-Agent': self.get_random_user_agent()
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Brave возвращает подсказки, которые можно использовать как результаты
                for i, suggestion in enumerate(data[1][:3] if len(data) > 1 else []):
                    results.append({
                        'title': f'Результаты по запросу "{suggestion}"',
                        'url': f'https://search.brave.com/search?q={quote_plus(suggestion)}',
                        'display_url': 'search.brave.com',
                        'snippet': f'Нажмите для просмотра результатов поиска по запросу "{suggestion}" в Brave Search',
                        'highlighted_title': self.highlight_text(f'Результаты по запросу "{suggestion}"', query),
                        'highlighted_snippet': self.highlight_text(f'Нажмите для просмотра результатов поиска', query)
                    })
                
                return results
            return []
        except Exception as e:
            print(f"Brave suggest error: {e}")
            return []
    
    def generate_smart_results(self, query):
        """Генерация умных результатов на основе запроса"""
        results = []
        
        # База знаний с умными результатами для популярных запросов
        knowledge_base = {
            'python': [
                {
                    'title': 'Python - официальный сайт',
                    'url': 'https://www.python.org',
                    'snippet': 'Python - мощный язык программирования с простым синтаксисом. Используется для веб-разработки, анализа данных, ИИ и автоматизации.'
                },
                {
                    'title': 'Python документация',
                    'url': 'https://docs.python.org',
                    'snippet': 'Официальная документация языка программирования Python с руководствами и справочными материалами.'
                }
            ],
            'искусственный интеллект': [
                {
                    'title': 'Искусственный интеллект - Википедия',
                    'url': 'https://ru.wikipedia.org/wiki/Искусственный_интеллект',
                    'snippet': 'Искусственный интеллект - свойство интеллектуальных систем выполнять творческие функции, которые традиционно считаются прерогативой человека.'
                }
            ],
            'космос': [
                {
                    'title': 'NASA - Национальное управление по аэронавтике',
                    'url': 'https://www.nasa.gov',
                    'snippet': 'NASA занимается исследованием космоса, астрономией, разработкой космических технологий и изучением Вселенной.'
                },
                {
                    'title': 'Роскосмос - официальный сайт',
                    'url': 'https://www.roscosmos.ru',
                    'snippet': 'Государственная корпорация по космической деятельности Роскосмос - российская космическая программа.'
                }
            ],
            'программирование': [
                {
                    'title': 'Программирование - Википедия',
                    'url': 'https://ru.wikipedia.org/wiki/Программирование',
                    'snippet': 'Программирование - процесс создания компьютерных программ с использованием языков программирования.'
                }
            ],
            'машинное обучение': [
                {
                    'title': 'Машинное обучение - Википедия',
                    'url': 'https://ru.wikipedia.org/wiki/Машинное_обучение',
                    'snippet': 'Машинное обучение - класс методов искусственного интеллекта, характерной чертой которых является не прямое решение задачи, а обучение.'
                }
            ]
        }
        
        query_lower = query.lower()
        for keyword, items in knowledge_base.items():
            if keyword in query_lower:
                for item in items:
                    results.append({
                        'title': item['title'],
                        'url': item['url'],
                        'display_url': urlparse(item['url']).netloc,
                        'snippet': item['snippet'],
                        'highlighted_title': self.highlight_text(item['title'], query),
                        'highlighted_snippet': self.highlight_text(item['snippet'], query)
                    })
        
        return results
    
    def generate_fallback_results(self, query):
        """Генерация фолбэк результатов когда другие методы не работают"""
        return [
            {
                'title': f'Результаты поиска: {query}',
                'url': f'https://www.google.com/search?q={quote_plus(query)}',
                'display_url': 'google.com',
                'snippet': f'Нажмите чтобы увидеть результаты поиска по запросу "{query}" в Google',
                'highlighted_title': self.highlight_text(f'Результаты поиска: {query}', query),
                'highlighted_snippet': self.highlight_text(f'Нажмите чтобы увидеть результаты поиска', query)
            },
            {
                'title': f'Поиск в DuckDuckGo: {query}',
                'url': f'https://duckduckgo.com/?q={quote_plus(query)}',
                'display_url': 'duckduckgo.com',
                'snippet': f'Нажмите чтобы увидеть результаты поиска по запросу "{query}" в DuckDuckGo',
                'highlighted_title': self.highlight_text(f'Поиск в DuckDuckGo: {query}', query),
                'highlighted_snippet': self.highlight_text(f'Нажмите чтобы увидеть результаты поиска', query)
            }
        ]
    
    def clean_html(self, text):
        """Очистка HTML тегов из текста"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text) if text else ""
    
    def search(self, query, page=1):
        """Основной метод поиска AriOS"""
        if not query or len(query.strip()) == 0:
            return []
        
        query = query.strip()
        print(f"🔍 AriOS Search: '{query}'")
        
        all_results = []
        
        try:
            # 1. Пытаемся найти через DuckDuckGo (основной источник)
            ddg_results = self.search_duckduckgo(query, page)
            all_results.extend(ddg_results)
            print(f"📊 DuckDuckGo results: {len(ddg_results)}")
            
            # 2. Добавляем Wikipedia результаты
            if len(all_results) < 8:
                wiki_results = self.search_wikipedia(query)
                # Убираем дубликаты по URL
                existing_urls = {r['url'] for r in all_results}
                for result in wiki_results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                print(f"📚 Wikipedia results: {len(wiki_results)}")
            
            # 3. Добавляем умные результаты
            if len(all_results) < 6:
                smart_results = self.generate_smart_results(query)
                existing_urls = {r['url'] for r in all_results}
                for result in smart_results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                print(f"💡 Smart results: {len(smart_results)}")
            
            # 4. Если результатов все еще мало, добавляем Brave подсказки
            if len(all_results) < 4:
                brave_results = self.search_brave_suggest(query)
                existing_urls = {r['url'] for r in all_results}
                for result in brave_results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                print(f"🦁 Brave results: {len(brave_results)}")
            
            # 5. Если вообще нет результатов, используем фолбэк
            if not all_results:
                all_results = self.generate_fallback_results(query)
                print(f"🆘 Fallback results: {len(all_results)}")
            
            # Убедимся, что у всех результатов есть подсветка
            for result in all_results:
                if not result.get('highlighted_title'):
                    result['highlighted_title'] = self.highlight_text(result['title'], query)
                if not result.get('highlighted_snippet'):
                    result['highlighted_snippet'] = self.highlight_text(result['snippet'], query)
            
            print(f"🎯 Total results: {len(all_results)}")
            return all_results[:10]  # Максимум 10 результатов
            
        except Exception as e:
            print(f"❌ AriOS search error: {e}")
            return self.generate_fallback_results(query)

# Инициализация AriOS поиска
arios_search = AriOSSearch()

@app.route('/')
def home():
    """Главная страница AriOS"""
    query = request.args.get('q', '').strip()
    
    if query:
        return redirect(f'/search?q={quote_plus(query)}')
    
    return render_template_string(HTML_TEMPLATE, query="", results=None, total_results=0, search_time="0.00")

@app.route('/search')
def search():
    """Поиск в AriOS - основная точка входа"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', '1')
    
    try:
        page = int(page)
        if page < 1:
            page = 1
    except:
        page = 1
    
    if not query:
        return render_template_string(HTML_TEMPLATE, 
                                   query="", 
                                   results=None, 
                                   total_results=0,
                                   search_time="0.00",
                                   error="Введите поисковый запрос")
    
    try:
        start_time = time.time()
        results = arios_search.search(query, page)
        search_time = time.time() - start_time
        
        total_results = len(results)
        
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=results,
                                   total_results=total_results,
                                   page=page,
                                   total_pages=max(1, (total_results + 9) // 10),
                                   search_time=f"{search_time:.2f}")
    
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=None,
                                   total_results=0,
                                   search_time="0.00",
                                   error=f"Ошибка поиска: {str(e)}")

@app.route('/api/search')
def api_search():
    """AriOS JSON API для програмmatic доступа"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', '1')
    
    try:
        page = int(page)
    except:
        page = 1
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        start_time = time.time()
        results = arios_search.search(query, page)
        search_time = time.time() - start_time
        
        return jsonify({
            'query': query,
            'page': page,
            'total_results': len(results),
            'search_time': f"{search_time:.2f}",
            'results': results,
            'search_engine': 'AriOS',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/browser-setup')
def browser_setup():
    """Инструкция по настройке браузера"""
    setup_html = '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">Настройка AriOS в браузере</h1>
        
        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin: 20px 0;">
            <h3>🌐 Использование через URL</h3>
            <p>Просто введите в адресной строке браузера:</p>
            <div style="background: #1f2937; color: white; padding: 15px; border-radius: 8px; font-family: monospace;">
                https://ВАШ-ДОМЕН/?q=ваш запрос
            </div>
            <p>Или используйте красивый URL:</p>
            <div style="background: #1f2937; color: white; padding: 15px; border-radius: 8px; font-family: monospace;">
                https://ВАШ-ДОМЕН/search/ваш запрос
            </div>
        </div>
        
        <div style="background: #f0fdf4; padding: 30px; border-radius: 15px; margin: 20px 0;">
            <h3>🔧 Добавление в поисковые системы браузера</h3>
            
            <h4>Google Chrome:</h4>
            <ol>
                <li>Откройте Настройки → Поисковая система → Управление поисковыми системами</li>
                <li>Нажмите "Добавить"</li>
                <li>Заполните:
                    <ul>
                        <li><strong>Поисковая система:</strong> AriOS</li>
                        <li><strong>Ключевое слово:</strong> arios</li>
                        <li><strong>URL с %s вместо запроса:</strong> https://ВАШ-ДОМЕН/?q=%s</li>
                    </ul>
                </li>
            </ol>
            
            <h4>Mozilla Firefox:</h4>
            <ol>
                <li>Откройте Настройки → Поиск</li>
                <li>Внизу нажмите "Найти больше поисковых систем"</li>
                <li>Добавьте пользовательскую поисковую систему с URL: <code>https://ВАШ-ДОМЕН/?q=%s</code></li>
            </ol>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/" style="background: #6366f1; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block;">
                Вернуться к поиску
            </a>
        </div>
    </div>
    '''
    return setup_html

@app.route('/about')
def about():
    """Страница о AriOS"""
    about_html = '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">О AriOS Search</h1>
        
        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin: 30px 0;">
            <h3>🚀 Что такое AriOS?</h3>
            <p>AriOS - это современная поисковая система с интеллектуальным поиском по словам и фразам, созданная для быстрого и точного поиска информации в интернете.</p>
            
            <h3>🔍 Особенности поиска</h3>
            <ul>
                <li><strong>Настоящий поиск по интернету</strong> - использует DuckDuckGo, Wikipedia и другие источники</li>
                <li><strong>Поиск по словам и фразам</strong> - умное ранжирование результатов</li>
                <li><strong>Подсветка результатов</strong> - найденные слова выделяются в результатах</li>
                <li><strong>Быстрая работа</strong> - оптимизированная архитектура поиска</li>
            </ul>
            
            <h3>🌍 Технологии</h3>
            <p>Построено на Python Flask с использованием современных веб-технологий и API поисковых систем</p>
        </div>
        
        <div style="text-align: center;">
            <a href="/" style="background: #6366f1; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px;">
                Начать поиск
            </a>
            <a href="/browser-setup" style="background: #f1f5f9; color: #374151; padding: 12px 30px; 
                                         text-decoration: none; border-radius: 25px; display: inline-block; margin: 10px;">
                Настройка браузера
            </a>
        </div>
    </div>
    '''
    return about_html

@app.route('/suggest')
def suggest():
    """API для поисковых подсказок"""
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    
    # Простые подсказки на основе популярных запросов
    suggestions = []
    
    popular_queries = [
        "python программирование", "искусственный интеллект", "веб разработка",
        "машинное обучение", "космос", "наука и технологии", "новости IT",
        "история", "география", "математика", "физика", "химия", "биология"
    ]
    
    for popular in popular_queries:
        if query in popular.lower():
            suggestions.append(popular)
    
    return jsonify(suggestions[:5])

@app.route('/health')
def health():
    """Проверка здоровья AriOS"""
    return jsonify({
        'status': 'healthy', 
        'service': 'AriOS Search',
        'timestamp': time.time(),
        'version': '1.0.0',
        'features': ['real_search', 'word_search', 'phrase_search', 'browser_integration', 'api']
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
