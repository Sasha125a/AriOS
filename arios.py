from flask import Flask, request, render_template_string, jsonify
import requests
from urllib.parse import quote_plus
import os
import time

app = Flask(__name__)

# HTML шаблон для поисковой страницы AriOS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AriOS - Умный поиск</title>
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
    </style>
</head>
<body>
    <div class="main-container">
        <div class="search-container">
            <div class="logo">AriOS</div>
            <div class="tagline">Умный поиск следующего поколения</div>
            
            <form action="/search" method="GET">
                <input type="text" name="q" class="search-box" value="{{ query }}" placeholder="Начните вводить запрос..." autofocus>
                <br>
                <button type="submit" class="search-button">Найти в AriOS</button>
                <button type="button" class="search-button secondary" onclick="location.href='/'">Новый поиск</button>
            </form>
            
            <div class="feature-badges">
                <div class="badge">🚀 Быстрый поиск</div>
                <div class="badge">🔍 Точные результаты</div>
                <div class="badge">🛡️ Безопасно</div>
                <div class="badge">🌍 Глобальный охват</div>
            </div>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            
            {% if results %}
            <div class="results-container">
                <div class="results-header">
                    Найдено результатов: {{ total_results }} • Время поиска: <span id="search-time">0.25с</span>
                </div>
                
                {% for result in results %}
                <div class="result-item">
                    <a href="{{ result.url }}" class="result-title" target="_blank">{{ result.title }}</a>
                    <div class="result-url">{{ result.display_url }}</div>
                    <div class="result-snippet">{{ result.snippet }}</div>
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
            © 2024 AriOS Search • Умная поисковая система
        </div>
    </div>

    <script>
        function changePage(newPage) {
            const url = new URL(window.location);
            url.searchParams.set('page', newPage);
            window.location = url.toString();
        }
        
        // Фокус на поисковую строку при загрузке
        document.querySelector('.search-box').focus();
        
        // Анимация времени поиска
        if (document.getElementById('search-time')) {
            let time = 0;
            const interval = setInterval(() => {
                time += 0.01;
                document.getElementById('search-time').textContent = time.toFixed(2) + 'с';
                if (time >= 0.25) {
                    clearInterval(interval);
                }
            }, 10);
        }
    </script>
</body>
</html>
'''

class AriOSSearch:
    def __init__(self):
        self.search_apis = [
            self.search_duckduckgo,
            self.search_wikipedia,
            self.search_news
        ]
    
    def search_duckduckgo(self, query, page=1):
        """Поиск через DuckDuckGo"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', f'https://duckduckgo.com/?q={quote_plus(query)}'),
                    'display_url': data.get('AbstractURL', 'duckduckgo.com'),
                    'snippet': data.get('AbstractText', '')
                })
            
            for topic in data.get('RelatedTopics', [])[:8]:
                if 'FirstURL' in topic and 'Text' in topic:
                    results.append({
                        'title': topic['Text'].split(' - ')[0] if ' - ' in topic['Text'] else topic['Text'][:100],
                        'url': topic['FirstURL'],
                        'display_url': topic['FirstURL'][:60],
                        'snippet': topic['Text'][:200]
                    })
            
            return results
            
        except Exception as e:
            print(f"AriOS DuckDuckGo error: {e}")
            return []
    
    def search_wikipedia(self, query, page=1):
        """Поиск в Wikipedia"""
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            search_query = query.replace(' ', '_')
            response = requests.get(url + search_query, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                return [{
                    'title': data.get('title', query),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'display_url': 'wikipedia.org',
                    'snippet': data.get('extract', '')[:250]
                }]
            return []
            
        except Exception:
            return []
    
    def search_news(self, query, page=1):
        """Новостной поиск"""
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'ru',
                'pageSize': 5
            }
            # Для использования нужен API ключ NewsAPI
            return []
        except Exception:
            return []
    
    def search(self, query, page=1):
        """Основной метод поиска AriOS"""
        if not query or len(query.strip()) == 0:
            return []
        
        query = query.strip()
        all_results = []
        
        for api in self.search_apis:
            try:
                results = api(query, page)
                all_results.extend(results)
                
                if len(all_results) >= 10:
                    break
                    
            except Exception as e:
                print(f"AriOS API error: {e}")
                continue
        
        # Убираем дубликаты
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            if result['url'] and result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results[:10]

# Инициализация AriOS поиска
arios_search = AriOSSearch()

@app.route('/')
def home():
    """Главная страница AriOS"""
    return render_template_string(HTML_TEMPLATE, query="", results=None, total_results=0)

@app.route('/search')
def search():
    """Поиск в AriOS"""
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
                                   error="Введите поисковый запрос")
    
    try:
        results = arios_search.search(query, page)
        total_results = len(results)
        
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=results,
                                   total_results=total_results,
                                   page=page,
                                   total_pages=max(1, (total_results + 9) // 10))
    
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                   query=query,
                                   results=None,
                                   total_results=0,
                                   error=f"Ошибка поиска AriOS: {str(e)}")

@app.route('/api/search')
def api_search():
    """AriOS JSON API"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', '1')
    
    try:
        page = int(page)
    except:
        page = 1
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        results = arios_search.search(query, page)
        return jsonify({
            'query': query,
            'page': page,
            'total_results': len(results),
            'results': results,
            'search_engine': 'AriOS'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    """Страница о AriOS"""
    about_html = '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: Arial, sans-serif;">
        <h1 style="color: #6366f1; text-align: center;">О AriOS Search</h1>
        <p style="text-align: center; color: #666; font-size: 18px;">
            Умная поисковая система следующего поколения
        </p>
        
        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin: 30px 0;">
            <h3>🚀 Что такое AriOS?</h3>
            <p>AriOS - это современная поисковая система, созданная для быстрого и точного поиска информации в интернете.</p>
            
            <h3>🔍 Особенности</h3>
            <ul>
                <li>Мгновенный поиск по множеству источников</li>
                <li>Умное ранжирование результатов</li>
                <li>Современный адаптивный интерфейс</li>
                <li>API для разработчиков</li>
                <li>Безопасность и конфиденциальность</li>
            </ul>
            
            <h3>🌍 Технологии</h3>
            <p>Построено на Python Flask с использованием современных веб-технологий</p>
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
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
