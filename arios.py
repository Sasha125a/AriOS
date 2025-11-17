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
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDA0L3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4='">
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

class AriOSRealSearch:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # База знаний популярных сайтов для поиска
        self.popular_sites = [
            "https://wikipedia.org",
            "https://github.com", 
            "https://stackoverflow.com",
            "https://reddit.com",
            "https://medium.com",
            "https://quora.com",
            "https://bbc.com",
            "https://cnn.com",
            "https://nationalgeographic.com",
            "https://ted.com"
        ]
        
        # Сайты с изображениями
        self.image_sites = [
            "https://unsplash.com",
            "https://pixabay.com",
            "https://pexels.com",
            "https://flickr.com",
            "https://imgur.com"
        ]
        
        # Видео платформы
        self.video_sites = [
            "https://youtube.com",
            "https://vimeo.com",
            "https://dailymotion.com",
            "https://rutube.ru"
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
        """Поиск веб-сайтов по собственному алгоритму"""
        try:
            results = []
            query_words = re.findall(r'\w+', query.lower())
            
            # Поиск по популярным сайтам
            for site in self.popular_sites:
                try:
                    site_results = self.search_on_site(site, query, query_words)
                    results.extend(site_results)
                    
                    if len(results) >= 10:
                        break
                        
                except Exception as e:
                    continue
            
            # Если не нашли достаточно результатов, ищем в интернете
            if len(results) < 5:
                web_results = self.search_web_directly(query, query_words)
                results.extend(web_results)
            
            return results[:12] if results else self.get_fallback_websites(query)
                
        except Exception as e:
            print(f"Website search error: {e}")
            return self.get_fallback_websites(query)
    
    def search_on_site(self, site_url, query, query_words):
        """Поиск на конкретном сайте"""
        try:
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            # Пытаемся найти страницу поиска на сайте
            search_urls = [
                f"{site_url}/search?q={quote_plus(query)}",
                f"{site_url}/?s={quote_plus(query)}",
                f"{site_url}/find?q={quote_plus(query)}"
            ]
            
            for search_url in search_urls:
                try:
                    response = requests.get(search_url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        return self.parse_site_results(response.text, site_url, query, query_words)
                except:
                    continue
            
            return []
            
        except Exception as e:
            return []
    
    def parse_site_results(self, html, site_url, query, query_words):
        """Парсинг результатов с сайта"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Ищем ссылки на страницы
        links = soup.find_all('a', href=True)
        
        for link in links[:15]:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Пропускаем пустые ссылки и ссылки без текста
                if not href or not title or len(title) < 10:
                    continue
                
                # Преобразуем относительные URL в абсолютные
                if href.startswith('/'):
                    href = urlparse(site_url).scheme + '://' + urlparse(site_url).netloc + href
                elif not href.startswith('http'):
                    continue
                
                # Проверяем релевантность по заголовку
                title_lower = title.lower()
                matches_query = any(word in title_lower for word in query_words if len(word) > 3)
                
                if matches_query:
                    # Получаем описание страницы
                    description = self.get_page_description(href)
                    
                    results.append({
                        'title': title,
                        'url': href,
                        'display_url': urlparse(href).netloc,
                        'snippet': description[:150] + '...' if len(description) > 150 else description,
                        'highlighted_title': self.highlight_text(title, query),
                        'highlighted_snippet': self.highlight_text(description, query)
                    })
                    
                    if len(results) >= 5:
                        break
                        
            except Exception as e:
                continue
        
        return results
    
    def get_page_description(self, url):
        """Получает описание страницы"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем мета-описание
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content')
            
            # Ищем первый абзац
            first_p = soup.find('p')
            if first_p:
                return first_p.get_text(strip=True)[:200]
            
            return "Описание недоступно"
            
        except:
            return "Описание недоступно"
    
    def search_web_directly(self, query, query_words):
        """Прямой поиск в интернете"""
        results = []
        
        # Генерируем потенциальные URL на основе запроса
        potential_urls = self.generate_potential_urls(query, query_words)
        
        for url in potential_urls[:10]:
            try:
                headers = {'User-Agent': self.get_random_user_agent()}
                response = requests.get(url, headers=headers, timeout=6)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.find('title')
                    
                    if title:
                        title_text = title.get_text(strip=True)
                        title_lower = title_text.lower()
                        
                        # Проверяем релевантность
                        if any(word in title_lower for word in query_words if len(word) > 3):
                            description = self.get_page_description(url)
                            
                            results.append({
                                'title': title_text,
                                'url': url,
                                'display_url': urlparse(url).netloc,
                                'snippet': description[:150] + '...' if len(description) > 150 else description,
                                'highlighted_title': self.highlight_text(title_text, query),
                                'highlighted_snippet': self.highlight_text(description, query)
                            })
                            
            except:
                continue
        
        return results
    
    def generate_potential_urls(self, query, query_words):
        """Генерирует потенциальные URL на основе запроса"""
        domains = ['.com', '.org', '.net', '.ru', '.io']
        protocols = ['https://', 'http://']
        urls = []
        
        # Генерируем URL на основе ключевых слов
        for word in query_words:
            if len(word) > 4:
                for domain in domains:
                    for protocol in protocols:
                        urls.append(f"{protocol}www.{word}{domain}")
                        urls.append(f"{protocol}{word}{domain}")
        
        # Добавляем комбинации слов
        if len(query_words) > 1:
            combined = '-'.join(query_words[:2])
            for domain in domains:
                for protocol in protocols:
                    urls.append(f"{protocol}www.{combined}{domain}")
                    urls.append(f"{protocol}{combined}{domain}")
        
        return urls
    
    def search_images(self, query):
        """Поиск изображений по новому алгоритму"""
        try:
            images = []
            query_words = re.findall(r'\w+', query.lower())
            
            # Поиск на сайтах с изображениями
            for site in self.image_sites:
                try:
                    site_images = self.search_images_on_site(site, query, query_words)
                    images.extend(site_images)
                    
                    if len(images) >= 15:
                        break
                        
                except Exception as e:
                    continue
            
            # Поиск изображений на обычных сайтах
            if len(images) < 8:
                web_images = self.search_images_on_web(query, query_words)
                images.extend(web_images)
            
            return images[:12] if images else self.get_fallback_images(query)
                
        except Exception as e:
            print(f"Image search error: {e}")
            return self.get_fallback_images(query)
    
    def search_images_on_site(self, site_url, query, query_words):
        """Поиск изображений на конкретном сайте"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            
            # Пытаемся найти страницу поиска
            search_urls = [
                f"{site_url}/s?q={quote_plus(query)}",
                f"{site_url}/search?q={quote_plus(query)}",
                f"{site_url}/photos/{quote_plus(query)}"
            ]
            
            for search_url in search_urls:
                try:
                    response = requests.get(search_url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        return self.extract_images_from_page(response.text, site_url, query_words)
                except:
                    continue
            
            return []
            
        except Exception as e:
            return []
    
    def extract_images_from_page(self, html, site_url, query_words):
        """Извлекает изображения со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        img_tags = soup.find_all('img')
        
        for img in img_tags[:20]:
            try:
                img_src = img.get('src') or img.get('data-src')
                if not img_src:
                    continue
                
                # Преобразуем относительные URL
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = urlparse(site_url).scheme + '://' + urlparse(site_url).netloc + img_src
                elif not img_src.startswith('http'):
                    continue
                
                # Получаем информацию об изображении
                img_alt = img.get('alt', '').lower()
                img_title = img.get('title', '').lower()
                
                # Проверяем релевантность
                matches_query = any(
                    word in img_alt or word in img_title
                    for word in query_words if len(word) > 3
                )
                
                if matches_query or len(images) < 3:
                    # Проверяем размеры
                    width = img.get('width', '0')
                    height = img.get('height', '0')
                    
                    try:
                        if int(width) < 100 and int(height) < 100:
                            continue
                    except:
                        pass
                    
                    images.append({
                        'title': img_alt[:50] if img_alt else f"Изображение {len(images) + 1}",
                        'url': img_src,
                        'thumbnail': img_src,
                        'source': urlparse(site_url).netloc
                    })
                    
            except Exception as e:
                continue
        
        return images
    
    def search_images_on_web(self, query, query_words):
        """Поиск изображений в интернете"""
        images = []
        
        # Ищем сайты, которые могут содержать изображения
        potential_sites = self.generate_image_sites(query_words)
        
        for site in potential_sites[:8]:
            try:
                site_images = self.extract_images_from_site_directly(site, query_words)
                images.extend(site_images)
                
                if len(images) >= 10:
                    break
                    
            except Exception as e:
                continue
        
        return images
    
    def generate_image_sites(self, query_words):
        """Генерирует сайты для поиска изображений"""
        base_sites = [
            "https://pinterest.com/search/pins/?q=",
            "https://deviantart.com/search?q=",
            "https://gettyimages.com/photos/",
            "https://shutterstock.com/search/",
            "https://istockphoto.com/search/2/image?phrase="
        ]
        
        sites = []
        query = '+'.join(query_words)
        
        for base in base_sites:
            sites.append(base + query)
        
        return sites
    
    def extract_images_from_site_directly(self, url, query_words):
        """Прямое извлечение изображений с сайта"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=6)
            
            if response.status_code == 200:
                return self.extract_images_from_page(response.text, url, query_words)
            
            return []
            
        except:
            return []
    
    def search_videos(self, query):
        """Поиск видео по новому алгоритму"""
        try:
            videos = []
            query_words = re.findall(r'\w+', query.lower())
            
            # Поиск на видео платформах
            for site in self.video_sites:
                try:
                    site_videos = self.search_videos_on_site(site, query, query_words)
                    videos.extend(site_videos)
                    
                    if len(videos) >= 9:
                        break
                        
                except Exception as e:
                    continue
            
            return videos[:9] if videos else self.get_fallback_videos(query)
                
        except Exception as e:
            print(f"Video search error: {e}")
            return self.get_fallback_videos(query)
    
    def search_videos_on_site(self, site_url, query, query_words):
        """Поиск видео на конкретной платформе"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            
            # Генерируем URL для поиска видео
            search_urls = [
                f"{site_url}/results?search_query={quote_plus(query)}",
                f"{site_url}/search?q={quote_plus(query)}",
                f"{site_url}/videos/search/{quote_plus(query)}"
            ]
            
            for search_url in search_urls:
                try:
                    response = requests.get(search_url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        return self.extract_videos_from_page(response.text, site_url, query_words)
                except:
                    continue
            
            return []
            
        except Exception as e:
            return []
    
    def extract_videos_from_page(self, html, site_url, query_words):
        """Извлекает видео со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        videos = []
        
        # Ищем ссылки на видео
        video_links = soup.find_all('a', href=True)
        
        for link in video_links[:15]:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < 10:
                    continue
                
                # Проверяем, что это ссылка на видео
                is_video_link = any(pattern in href for pattern in ['/watch', '/video', '/v/'])
                
                if is_video_link:
                    # Преобразуем относительные URL
                    if href.startswith('/'):
                        href = urlparse(site_url).scheme + '://' + urlparse(site_url).netloc + href
                    elif not href.startswith('http'):
                        continue
                    
                    # Проверяем релевантность по названию
                    title_lower = title.lower()
                    matches_query = any(word in title_lower for word in query_words if len(word) > 3)
                    
                    if matches_query:
                        # Получаем миниатюру
                        thumbnail = self.get_video_thumbnail(href, site_url)
                        
                        videos.append({
                            'title': title,
                            'url': href,
                            'thumbnail': thumbnail,
                            'channel': urlparse(site_url).netloc,
                            'duration': 'Видео'
                        })
                        
                        if len(videos) >= 6:
                            break
                            
            except Exception as e:
                continue
        
        return videos
    
    def get_video_thumbnail(self, video_url, site_url):
        """Получает миниатюру видео"""
        try:
            # Для YouTube извлекаем ID видео
            if 'youtube.com' in site_url or 'youtu.be' in site_url:
                video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', video_url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            
            # Для других платформ используем заглушку
            return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4='
            
        except:
            return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMwMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMjAgODBMMTYwIDEwMEwxMjAgMTIwVjgwWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4='
    
    def get_fallback_images(self, query):
        """Резервные изображения"""
        fallback_images = [
            {
                'title': f'Изображение по запросу: {query}',
                'url': f'https://source.unsplash.com/featured/800x600/?{quote_plus(query)}',
                'thumbnail': f'https://source.unsplash.com/featured/300x200/?{quote_plus(query)}',
                'source': 'unsplash.com'
            },
            {
                'title': f'Фото: {query}',
                'url': f'https://source.unsplash.com/featured/800x600/?{quote_plus(query.split()[0])}',
                'thumbnail': f'https://source.unsplash.com/featured/300x200/?{quote_plus(query.split()[0])}',
                'source': 'unsplash.com'
            }
        ]
        
        return fallback_images
    
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
                'url': f'https://www.google.com/search?q={quote_plus(query)}',
                'display_url': 'google.com',
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
                                is_active=app_status['is_active'],
                                active_tab='all',
                                websites_count=0,
                                images_count=0,
                                videos_count=0)

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
                                   videos_count=0)
    
    try:
        # Увеличиваем счетчик поисков
        app_status['total_searches'] += 1
        
        # Выполняем поиск
        start_time = time.time()
        results, images, videos = arios_real_search.search(query)
        search_time = time.time() - start_time
        
        total_results = len(results) + len(images) + len(videos)
        websites_count = len(results)
        images_count = len(images)
        videos_count = len(videos)
        
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
                                   is_active=app_status['is_active'],
                                   active_tab=active_tab,
                                   websites_count=websites_count,
                                   images_count=images_count,
                                   videos_count=videos_count)
    
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
                                   show_status=show_status,
                                   active_tab='all',
                                   websites_count=0,
                                   images_count=0,
                                   videos_count=0)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': int(time.time() - app_status['start_time']),
        'total_searches': app_status['total_searches']
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
        'start_time': app_status['start_time'],
        'uptime': uptime,
        'uptime_human': uptime_str
    })

# Запускаем само-пинг при старте приложения
start_background_scheduler()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting AriOS server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
