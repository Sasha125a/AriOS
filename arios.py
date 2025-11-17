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
            'аэропорт', 'вокзал', 'море', 'река', 'озеро', 'пустыня', 'снег',
            'деревня', 'поле', 'сад', 'кухня', 'спальня', 'гостиная', 'ванная',
            'библиотека', 'музей', 'галерея', 'церковь', 'собор', 'мечеть',
            'храм', 'замок', 'дворец', 'мост', 'фонтан', 'памятник', 'скульптура',
            'водопад', 'каньон', 'вулкан', 'остров', 'пещера', 'джунгли', 'саванна',
            'тропики', 'арктика', 'побережье', 'бухта', 'залив', 'пролив', 'океан',
            'подводный', 'космос', 'планета', 'звезды', 'галактика', 'туманность',
            'сельская местность', 'метро', 'трамвай', 'автобус', 'такси', 'поезд',
            'аэропорт', 'морской порт', 'рынок', 'торговый центр', 'кинотеатр', 'театр',
            'опера', 'балет', 'концерт', 'фестиваль', 'карнавал', 'парад', 'митинг',
            'стройка', 'фабрика', 'завод', 'ферма', 'пасека', 'виноградник', 'сад',
            'оранжерея', 'зимний сад', 'аквапарк', 'луна-парк', 'зоопарк', 'сафари-парк',
            'ботанический сад', 'дендрарий', 'заповедник', 'национальный парк', 'заказник',
            'альпийские луга', 'тайга', 'степь', 'прерия', 'сахара', 'горизонт', 'рассвет',
            'закат', 'полдень', 'полночь', 'сумерки', 'радуга', 'гроза', 'ураган', 'торнадо',
            'цунами', 'землетрясение', 'извержение', 'лавовый поток', 'геотермальный источник',
            'горячий источник', 'гейзер', 'ледник', 'айсберг', 'полярное сияние', 'мираж'
        ]
        
        self.color_names = {
            'red': 'красный', 'blue': 'синий', 'green': 'зеленый', 
            'yellow': 'желтый', 'orange': 'оранжевый', 'purple': 'фиолетовый',
            'pink': 'розовый', 'brown': 'коричневый', 'black': 'черный',
            'white': 'белый', 'gray': 'серый', 'gold': 'золотой', 'silver': 'серебряный',
            'bronze': 'бронзовый', 'beige': 'бежевый', 'turquoise': 'бирюзовый',
            'violet': 'фиолетовый', 'indigo': 'индиго', 'maroon': 'бордовый',
            'navy': 'темно-синий', 'teal': 'сине-зеленый', 'olive': 'оливковый',
            'lime': 'лаймовый', 'cyan': 'голубой', 'magenta': 'пурпурный',
            'coral': 'коралловый', 'salmon': 'лососевый', 'lavender': 'лавандовый',
            'plum': 'сливовый', 'azure': 'лазурный', 'ivory': 'слоновая кость',
            'charcoal': 'угольный', 'crimson': 'малиновый', 'amber': 'янтарный'
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
            'rooster': 'петух', 'peacock': 'павлин', 'flamingo': 'фламинго', 'pigeon': 'голубь',
            'sparrow': 'воробей', 'crow': 'ворона', 'seagull': 'чайка', 'woodpecker': 'дятел',
            'nightingale': 'соловей', 'canary': 'канарейка', 'hummingbird': 'колибри',
            'bat': 'летучая мышь', 'rhinoceros': 'носорог', 'hippopotamus': 'бегемот',
            'cheetah': 'гепард', 'leopard': 'леопард', 'panther': 'пантера', 'lynx': 'рысь',
            'camel': 'верблюд', 'llama': 'лама', 'alpaca': 'альпака', 'buffalo': 'буйвол',
            'bison': 'бизон', 'moose': 'лось', 'elk': 'лось', 'reindeer': 'северный олень',
            'seal': 'тюлень', 'walrus': 'морж', 'otter': 'выдра', 'beaver': 'бобр',
            'mole': 'крот', 'hamster': 'хомяк', 'guinea pig': 'морская свинка',
            'chinchilla': 'шиншилла', 'ferret': 'хорек', 'weasel': 'ласка',
            'badger': 'барсук', 'skunk': 'скунс', 'porcupine': 'дикобраз',
            'armadillo': 'броненосец', 'sloth': 'ленивец', 'anteater': 'муравьед',
            'platypus': 'утконос', 'kangaroo rat': 'кенгуровая крыса', 'wombat': 'вомбат',
            'tasmanian devil': 'тасманийский дьявол', 'komodo dragon': 'комодский варан',
            'chameleon': 'хамелеон', 'iguana': 'игуана', 'gecko': 'геккон',
            'salamander': 'саламандра', 'newt': 'тритон', 'axolotl': 'аксолотль',
            'toad': 'жаба', 'tadpole': 'головастик', 'crab': 'краб', 'lobster': 'лобстер',
            'shrimp': 'креветка', 'prawn': 'креветка', 'crayfish': 'рак', 'scorpion': 'скорпион',
            'centipede': 'сороконожка', 'millipede': 'многоножка', 'grasshopper': 'кузнечик',
            'cricket': 'сверчок', 'ladybug': 'божья коровка', 'beetle': 'жук',
            'dragonfly': 'стрекоза', 'damselfly': 'стрекоза', 'mosquito': 'комар',
            'fly': 'муха', 'wasp': 'оса', 'hornet': 'шершень', 'bumblebee': 'шмель',
            'caterpillar': 'гусеница', 'silkworm': 'шелкопряд', 'earthworm': 'дождевой червь',
            'snail': 'улитка', 'slug': 'слизень', 'clam': 'моллюск', 'oyster': 'устрица',
            'mussel': 'мидия', 'squid': 'кальмар', 'cuttlefish': 'каракатица',
            'starfish': 'морская звезда', 'sea urchin': 'морской еж', 'sea cucumber': 'морской огурец',
            'coral': 'коралл', 'anemone': 'актиния', 'jellyfish': 'медуза',

            # Транспорт (150+ слов)
            'car': 'машина', 'bus': 'автобус', 'truck': 'грузовик', 'motorcycle': 'мотоцикл',
            'bicycle': 'велосипед', 'train': 'поезд', 'airplane': 'самолет', 'helicopter': 'вертолет',
            'ship': 'корабль', 'boat': 'лодка', 'yacht': 'яхта', 'submarine': 'подводная лодка',
            'rocket': 'ракета', 'spaceship': 'космический корабль', 'taxi': 'такси',
            'ambulance': 'скорая помощь', 'fire truck': 'пожарная машина', 'police car': 'полицейская машина',
            'minivan': 'минивэн', 'suv': 'внедорожник', 'sedan': 'седан', 'coupe': 'купе',
            'convertible': 'кабриолет', 'limousine': 'лимузин', 'tractor': 'трактор',
            'bulldozer': 'бульдозер', 'excavator': 'экскаватор', 'crane': 'кран',
            'forklift': 'погрузчик', 'tank': 'танк', 'jeep': 'джип', 'scooter': 'самокат',
            'skateboard': 'скейтборд', 'rollerblades': 'ролики', 'snowmobile': 'снегоход',
            'jet ski': 'гидроцикл', 'speedboat': 'катер', 'sailboat': 'парусник',
            'canoe': 'каноэ', 'kayak': 'каяк', 'raft': 'плот', 'gondola': 'гондола',
            'ferry': 'паром', 'cruise ship': 'круизный лайнер', 'container ship': 'контейнеровоз',
            'tanker': 'танкер', 'submarine': 'подлодка', 'airship': 'дирижабль',
            'hot air balloon': 'воздушный шар', 'glider': 'планер', 'fighter jet': 'истребитель',
            'bomber': 'бомбардировщик', 'cargo plane': 'грузовой самолет', 'seaplane': 'гидросамолет',
            'space shuttle': 'космический шаттл', 'satellite': 'спутник', 'rover': 'ровер',
            'metro': 'метро', 'tram': 'трамвай', 'trolleybus': 'троллейбус', 'monorail': 'монорельс',
            'funicular': 'фуникулер', 'cable car': 'канатная дорога', 'locomotive': 'локомотив',
            'high-speed train': 'скоростной поезд', 'freight train': 'грузовой поезд',
            'bullet train': 'поезд-пуля', 'steam engine': 'паровоз', 'carriage': 'вагон',
            'caravan': 'автодом', 'trailer': 'прицеп', 'semi-trailer': 'полуприцеп',
            'dump truck': 'самосвал', 'concrete mixer': 'бетономешалка', 'tow truck': 'эвакуатор',
            'garbage truck': 'мусоровоз', 'cement truck': 'цементовоз', 'fire engine': 'пожарная машина',
            'police motorcycle': 'полицейский мотоцикл', 'ambulance motorcycle': 'мотоцикл скорой помощи',
            'armored car': 'броневик', 'limousine': 'лимузин', 'race car': 'гоночный автомобиль',
            'formula 1': 'формула 1', 'nascar': 'наскар', 'rally car': 'раллийный автомобиль',
            'off-road vehicle': 'внедорожник', 'atv': 'квадроцикл', 'snowplow': 'снегоочиститель',
            'street sweeper': 'подметальная машина', 'tram': 'трамвай', 'subway': 'метро',
            'light rail': 'легкое метро', 'commuter train': 'пригородный поезд',
            'high-speed rail': 'скоростная железная дорога', 'maglev': 'маглев',
            'space station': 'космическая станция', 'space probe': 'космический зонд',
            'lunar module': 'лунный модуль', 'mars rover': 'марсоход',

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
            'beer': 'пиво', 'water': 'вода', 'soda': 'газировка', 'smoothie': 'смузи',
            'yogurt': 'йогурт', 'butter': 'масло', 'oil': 'масло', 'salt': 'соль',
            'sugar': 'сахар', 'honey': 'мед', 'jam': 'джем', 'sauce': 'соус',
            'soup': 'суп', 'stew': 'рагу', 'roast': 'жаркое', 'grill': 'гриль',
            'barbecue': 'барбекю', 'salmon': 'лосось', 'tuna': 'тунец', 'shrimp': 'креветка',
            'lobster': 'омар', 'crab': 'краб', 'mussel': 'мидия', 'oyster': 'устрица',
            'caviar': 'икра', 'pasta': 'паста', 'spaghetti': 'спагетти', 'lasagna': 'лазанья',
            'ravioli': 'равиоли', 'risotto': 'ризотто', 'paella': 'паэлья', 'curry': 'карри',
            'taco': 'тако', 'burrito': 'буррито', 'quesadilla': 'кесадилья', 'salsa': 'сальса',
            'guacamole': 'гуакамоле', 'hummus': 'хумус', 'falafel': 'фалафель', 'kebab': 'кебаб',
            'sausage': 'колбаса', 'ham': 'ветчина', 'bacon': 'бекон', 'salami': 'салями',
            'pancake': 'блин', 'waffle': 'вафля', 'croissant': 'круассан', 'baguette': 'багет',
            'donut': 'пончик', 'muffin': 'маффин', 'cupcake': 'капкейк', 'pie': 'пирог',
            'tart': 'тарт', 'pudding': 'пудинг', 'custard': 'заварной крем', 'whipped cream': 'взбитые сливки',
            'caramel': 'карамель', 'nougat': 'нуга', 'marzipan': 'марципан', 'gingerbread': 'пряник',
            'candy': 'конфета', 'lollipop': 'леденец', 'gum': 'жвачка', 'popcorn': 'попкорн',
            'chips': 'чипсы', 'nuts': 'орехи', 'seeds': 'семечки', 'dried fruit': 'сухофрукты',
            'cereal': 'хлопья', 'oatmeal': 'овсянка', 'granola': 'мюсли', 'toast': 'тост',
            'omelette': 'омлет', 'scrambled eggs': 'яичница', 'fried eggs': 'яичница',
            'boiled eggs': 'варёные яйца', 'poached eggs': 'яйца пашот', 'quiche': 'киш',
            'fondue': 'фондю', 'raclette': 'раклет', 'tapas': 'тапас', 'antipasto': 'антипасто',
            'bruschetta': 'брускетта', 'caprese': 'капрезе', 'prosciutto': 'прошутто',
            'mozzarella': 'моцарелла', 'parmesan': 'пармезан', 'cheddar': 'чеддер',
            'brie': 'бри', 'camembert': 'камамбер', 'gouda': 'гауда', 'feta': 'фета',
            'blue cheese': 'голубой сыр', 'yogurt': 'йогурт', 'kefir': 'кефир', 'buttermilk': 'пахта',
            'sour cream': 'сметана', 'cream cheese': 'сливочный сыр', 'cottage cheese': 'творог',
            'ricotta': 'рикотта', 'mayonnaise': 'майонез', 'ketchup': 'кетчуп', 'mustard': 'горчица',
            'soy sauce': 'соевый соус', 'vinegar': 'уксус', 'olive oil': 'оливковое масло',
            'sesame oil': 'кунжутное масло', 'truffle oil': 'трюфельное масло', 'vanilla': 'ваниль',
            'cinnamon': 'корица', 'nutmeg': 'мускатный орех', 'ginger': 'имбирь',
            'turmeric': 'куркума', 'paprika': 'паприка', 'saffron': 'шафран', 'basil': 'базилик',
            'parsley': 'петрушка', 'cilantro': 'кинза', 'mint': 'мята', 'rosemary': 'розмарин',
            'thyme': 'тимьян', 'oregano': 'орегано', 'dill': 'укроп', 'chives': 'лук-шнитт',

            # Природа и пейзажи (200+ слов)
            'tree': 'дерево', 'flower': 'цветок', 'grass': 'трава', 'leaf': 'лист',
            'forest': 'лес', 'mountain': 'гора', 'river': 'река', 'lake': 'озеро',
            'ocean': 'океан', 'sea': 'море', 'beach': 'пляж', 'desert': 'пустыня',
            'sky': 'небо', 'cloud': 'облако', 'sun': 'солнце', 'moon': 'луна',
            'star': 'звезда', 'rain': 'дождь', 'snow': 'снег', 'wind': 'ветер',
            'storm': 'буря', 'lightning': 'молния', 'rainbow': 'радуга', 'sunset': 'закат',
            'sunrise': 'восход', 'horizon': 'горизонт', 'valley': 'долина', 'canyon': 'каньон',
            'waterfall': 'водопад', 'volcano': 'вулкан', 'island': 'остров', 'cave': 'пещера',
            'cliff': 'утес', 'hill': 'холм', 'meadow': 'луг', 'field': 'поле',
            'garden': 'сад', 'park': 'парк', 'jungle': 'джунгли', 'swamp': 'болото',
            'marsh': 'болото', 'pond': 'пруд', 'stream': 'ручей', 'brook': 'ручей',
            'spring': 'родник', 'geyser': 'гейзер', 'glacier': 'ледник', 'iceberg': 'айсберг',
            'fjord': 'фьорд', 'bay': 'бухта', 'gulf': 'залив', 'strait': 'пролив',
            'peninsula': 'полуостров', 'archipelago': 'архипелаг', 'atoll': 'атолл',
            'oasis': 'оазис', 'dune': 'дюна', 'savanna': 'саванна', 'prairie': 'прерия',
            'tundra': 'тундра', 'taiga': 'тайга', 'rainforest': 'тропический лес',
            'wetland': 'водно-болотные угодья', 'estuary': 'устье реки', 'delta': 'дельта',
            'coast': 'побережье', 'shore': 'берег', 'beach': 'пляж', 'lagoon': 'лагуна',
            'reef': 'риф', 'coral reef': 'коралловый риф', 'kelp forest': 'водорослевый лес',
            'mangrove': 'мангровые заросли', 'bamboo forest': 'бамбуковый лес',
            'cherry blossom': 'цветение сакуры', 'maple tree': 'клен', 'oak tree': 'дуб',
            'pine tree': 'сосна', 'birch tree': 'береза', 'willow tree': 'ива',
            'palm tree': 'пальма', 'cactus': 'кактус', 'succulent': 'суккулент',
            'fern': 'папоротник', 'moss': 'мох', 'lichen': 'лишайник', 'mushroom': 'гриб',
            'rose': 'роза', 'tulip': 'тюльпан', 'lily': 'лилия', 'orchid': 'орхидея',
            'sunflower': 'подсолнух', 'daisy': 'маргаритка', 'violet': 'фиалка',
            'lavender': 'лаванда', 'jasmine': 'жасмин', 'lotus': 'лотос',
            'cherry blossom': 'цветение сакуры', 'magnolia': 'магнолия',
            'peony': 'пион', 'hydrangea': 'гортензия', 'carnation': 'гвоздика',
            'daffodil': 'нарцисс', 'iris': 'ирис', 'poppy': 'мак',
            'bluebell': 'колокольчик', 'forget-me-not': 'незабудка',
            'buttercup': 'лютик', 'dandelion': 'одуванчик', 'thistle': 'чертополох',
            'clover': 'клевер', 'heather': 'вереск', 'broom': 'ракитник',

            # Люди и деятельность (150+ слов)
            'person': 'человек', 'man': 'мужчина', 'woman': 'женщина', 'child': 'ребенок',
            'baby': 'младенец', 'family': 'семья', 'friend': 'друг', 'couple': 'пара',
            'doctor': 'врач', 'teacher': 'учитель', 'student': 'студент', 'worker': 'рабочий',
            'athlete': 'атлет', 'dancer': 'танцор', 'musician': 'музыкант', 'artist': 'художник',
            'cook': 'повар', 'farmer': 'фермер', 'soldier': 'солдат', 'police': 'полиция',
            'firefighter': 'пожарный', 'pilot': 'пилот', 'driver': 'водитель', 'sailor': 'моряк',
            'engineer': 'инженер', 'scientist': 'ученый', 'programmer': 'программист',
            'designer': 'дизайнер', 'architect': 'архитектор', 'builder': 'строитель',
            'electrician': 'электрик', 'plumber': 'сантехник', 'mechanic': 'механик',
            'driver': 'водитель', 'pilot': 'пилот', 'captain': 'капитан', 'chef': 'шеф-повар',
            'waiter': 'официант', 'manager': 'менеджер', 'director': 'директор',
            'accountant': 'бухгалтер', 'lawyer': 'юрист', 'judge': 'судья',
            'politician': 'политик', 'journalist': 'журналист', 'reporter': 'репортер',
            'writer': 'писатель', 'poet': 'поэт', 'actor': 'актер', 'actress': 'актриса',
            'singer': 'певец', 'dancer': 'танцор', 'painter': 'художник', 'sculptor': 'скульптор',
            'photographer': 'фотограф', 'filmmaker': 'режиссер', 'producer': 'продюсер',
            'composer': 'композитор', 'conductor': 'дирижер', 'musician': 'музыкант',
            'doctor': 'врач', 'nurse': 'медсестра', 'dentist': 'стоматолог',
            'psychologist': 'психолог', 'therapist': 'терапевт', 'surgeon': 'хирург',
            'veterinarian': 'ветеринар', 'pharmacist': 'фармацевт', 'paramedic': 'парамедик',
            'athlete': 'спортсмен', 'coach': 'тренер', 'referee': 'судья',
            'gymnast': 'гимнаст', 'swimmer': 'пловец', 'runner': 'бегун',
            'cyclist': 'велосипедист', 'boxer': 'боксер', 'wrestler': 'борец',
            'martial artist': 'мастер боевых искусств', 'yogi': 'йог',
            'meditator': 'медитирующий', 'student': 'ученик', 'teacher': 'преподаватель',
            'professor': 'профессор', 'researcher': 'исследователь', 'scholar': 'ученый',
            'librarian': 'библиотекарь', 'archivist': 'архивариус', 'curator': 'куратор',
            'farmer': 'фермер', 'gardener': 'садовник', 'beekeeper': 'пчеловод',
            'fisherman': 'рыбак', 'hunter': 'охотник', 'ranger': 'рейнджер',
            'conservationist': 'эколог', 'activist': 'активист', 'volunteer': 'волонтер',
            'traveler': 'путешественник', 'explorer': 'исследователь', 'adventurer': 'авантюрист',
            'tourist': 'турист', 'guide': 'гид', 'translator': 'переводчик',
            'interpreter': 'переводчик', 'diplomat': 'дипломат', 'ambassador': 'посол',
            'entrepreneur': 'предприниматель', 'businessman': 'бизнесмен',
            'investor': 'инвестор', 'banker': 'банкир', 'trader': 'трейдер',
            'analyst': 'аналитик', 'consultant': 'консультант', 'specialist': 'специалист',
            'expert': 'эксперт', 'professional': 'профессионал', 'employee': 'сотрудник',
            'employer': 'работодатель', 'worker': 'работник', 'laborer': 'рабочий',
            'craftsman': 'ремесленник', 'artisan': 'ремесленник', 'blacksmith': 'кузнец',
            'carpenter': 'плотник', 'mason': 'каменщик', 'tailor': 'портной',
            'jeweler': 'ювелир', 'potter': 'гончар', 'weaver': 'ткач',
            'baker': 'пекарь', 'butcher': 'мясник', 'barber': 'парикмахер',
            'hairdresser': 'парикмахер', 'stylist': 'стилист', 'makeup artist': 'визажист',
            'model': 'модель', 'influencer': 'инфлюенсер', 'blogger': 'блоггер',
            'youtuber': 'ютубер', 'streamer': 'стример', 'gamer': 'геймер',

            # Спорт (100+ слов)
            'football': 'футбол', 'basketball': 'баскетбол', 'tennis': 'теннис', 'volleyball': 'волейбол',
            'baseball': 'бейсбол', 'hockey': 'хоккей', 'golf': 'гольф', 'swimming': 'плавание',
            'running': 'бег', 'cycling': 'велоспорт', 'boxing': 'бокс', 'martial arts': 'боевые искусства',
            'skiing': 'лыжи', 'snowboarding': 'сноуборд', 'surfing': 'серфинг', 'skateboarding': 'скейтбординг',
            'gymnastics': 'гимнастика', 'athletics': 'легкая атлетика', 'weightlifting': 'тяжелая атлетика',
            'wrestling': 'борьба', 'judo': 'дзюдо', 'karate': 'каратэ', 'taekwondo': 'тхэквондо',
            'fencing': 'фехтование', 'archery': 'стрельба из лука', 'shooting': 'стрельба',
            'horse racing': 'скачки', 'equestrian': 'конный спорт', 'polo': 'поло',
            'cricket': 'крикет', 'rugby': 'регби', 'handball': 'гандбол', 'badminton': 'бадминтон',
            'table tennis': 'настольный теннис', 'squash': 'сквош', 'racquetball': 'ракетбол',
            'lacrosse': 'лакросс', 'water polo': 'водное поло', 'synchronized swimming': 'синхронное плавание',
            'diving': 'дайвинг', 'sailing': 'парусный спорт', 'rowing': 'гребля', 'canoeing': 'каноэ',
            'kayaking': 'каякинг', 'rafting': 'рафтинг', 'climbing': 'скалолазание', 'mountaineering': 'альпинизм',
            'hiking': 'пеший туризм', 'trekking': 'треккинг', 'orienteering': 'ориентирование',
            'parkour': 'паркур', 'free running': 'фриран', 'breakdancing': 'брейк-данс',
            'dance sport': 'танцевальный спорт', 'figure skating': 'фигурное катание',
            'speed skating': 'конькобежный спорт', 'ice hockey': 'хоккей с шайбой',
            'curling': 'керлинг', 'bobsleigh': 'бобслей', 'luge': 'санный спорт',
            'skeleton': 'скелетон', 'biathlon': 'биатлон', 'cross-country skiing': 'лыжные гонки',
            'ski jumping': 'прыжки с трамплина', 'nordic combined': 'лыжное двоеборье',
            'alpine skiing': 'горнолыжный спорт', 'freestyle skiing': 'фристайл',
            'snowboarding': 'сноубординг', 'motorsport': 'мотоспорт', 'formula 1': 'формула 1',
            'nascar': 'наскар', 'rally': 'ралли', 'motorcycle racing': 'мотогонки',
            'cycling': 'велоспорт', 'tour de france': 'тур де франс', 'triathlon': 'триатлон',
            'ironman': 'айронмен', 'decathlon': 'десятиборье', 'heptathlon': 'семиборье',
            'marathon': 'марафон', 'sprint': 'спринт', 'hurdles': 'барьерный бег',
            'relay': 'эстафета', 'long jump': 'прыжки в длину', 'high jump': 'прыжки в высоту',
            'pole vault': 'прыжки с шестом', 'shot put': 'толкание ядра', 'discus': 'метание диска',
            'javelin': 'метание копья', 'hammer throw': 'метание молота',

            # Технологии (150+ слов)
            'computer': 'компьютер', 'laptop': 'ноутбук', 'phone': 'телефон', 'tablet': 'планшет',
            'camera': 'камера', 'tv': 'телевизор', 'radio': 'радио', 'headphones': 'наушники',
            'microphone': 'микрофон', 'speaker': 'колонка', 'keyboard': 'клавиатура', 'mouse': 'мышь',
            'monitor': 'монитор', 'printer': 'принтер', 'router': 'роутер', 'server': 'сервер',
            'robot': 'робот', 'drone': 'дрон', 'satellite': 'спутник', 'microchip': 'микрочип',
            'processor': 'процессор', 'memory': 'память', 'storage': 'хранилище', 'hard drive': 'жесткий диск',
            'ssd': 'твердотельный накопитель', 'graphics card': 'видеокарта', 'motherboard': 'материнская плата',
            'power supply': 'блок питания', 'cooling system': 'система охлаждения', 'fan': 'вентилятор',
            'webcam': 'веб-камера', 'scanner': 'сканер', 'projector': 'проектор', 'smartwatch': 'умные часы',
            'fitness tracker': 'фитнес-трекер', 'smartphone': 'смартфон', 'tablet': 'планшет',
            'ebook reader': 'электронная книга', 'gps': 'gps', 'navigation system': 'навигационная система',
            'car electronics': 'автоэлектроника', 'home automation': 'умный дом', 'smart home': 'умный дом',
            'iot': 'интернет вещей', 'wearable technology': 'носимая электроника', 'virtual reality': 'виртуальная реальность',
            'augmented reality': 'дополненная реальность', 'mixed reality': 'смешанная реальность',
            'ai': 'искусственный интеллект', 'machine learning': 'машинное обучение', 'neural network': 'нейронная сеть',
            'blockchain': 'блокчейн', 'cryptocurrency': 'криптовалюта', 'bitcoin': 'биткоин',
            'ethereum': 'эфириум', 'nft': 'нфт', 'metaverse': 'метавселенная',
            'cloud computing': 'облачные вычисления', 'big data': 'большие данные', 'data science': 'наука о данных',
            'cybersecurity': 'кибербезопасность', 'encryption': 'шифрование', 'firewall': 'брандмауэр',
            'software': 'программное обеспечение', 'app': 'приложение', 'website': 'веб-сайт',
            'web development': 'веб-разработка', 'programming': 'программирование', 'coding': 'кодирование',
            'algorithm': 'алгоритм', 'data structure': 'структура данных', 'database': 'база данных',
            'sql': 'sql', 'nosql': 'nosql', 'api': 'api', 'framework': 'фреймворк',
            'library': 'библиотека', 'sdk': 'sdk', 'ide': 'ide', 'compiler': 'компилятор',
            'operating system': 'операционная система', 'windows': 'windows', 'linux': 'linux',
            'macos': 'macos', 'android': 'android', 'ios': 'ios', 'chrome os': 'chrome os',
            'browser': 'браузер', 'search engine': 'поисковая система', 'social media': 'социальные сети',
            'streaming': 'стриминг', 'podcast': 'подкаст', 'blog': 'блог', 'forum': 'форум',
            'e-commerce': 'электронная коммерция', 'online shopping': 'онлайн-шоппинг', 'digital payment': 'цифровой платеж',
            'mobile payment': 'мобильный платеж', 'contactless payment': 'бесконтактный платеж',
            'biometrics': 'биометрия', 'facial recognition': 'распознавание лиц', 'fingerprint': 'отпечаток пальца',
            'voice recognition': 'распознавание голоса', 'quantum computing': 'квантовые вычисления',
            'nanotechnology': 'нанотехнология', 'biotechnology': 'биотехнология', 'genetic engineering': 'генная инженерия',
            '3d printing': '3d-печать', 'robotics': 'робототехника', 'automation': 'автоматизация',
            'self-driving car': 'беспилотный автомобиль', 'electric vehicle': 'электромобиль',
            'renewable energy': 'возобновляемая энергия', 'solar power': 'солнечная энергия',
            'wind power': 'ветровая энергия', 'hydroelectric power': 'гидроэнергетика',
            'nuclear power': 'ядерная энергия', 'battery': 'батарея', 'charger': 'зарядное устройство',
            'wireless charging': 'беспроводная зарядка', 'bluetooth': 'bluetooth', 'wifi': 'wifi',
            '5g': '5g', '6g': '6g', 'internet': 'интернет', 'broadband': 'широкополосный доступ',
            'fiber optic': 'оптоволокно', 'satellite internet': 'спутниковый интернет',

            # Одежда и мода (100+ слов)
            'shirt': 'рубашка', 'pants': 'брюки', 'dress': 'платье', 'skirt': 'юбка',
            'jacket': 'куртка', 'coat': 'пальто', 'hat': 'шляпа', 'shoes': 'обувь',
            'sneakers': 'кроссовки', 'boots': 'ботинки', 'sandals': 'сандалии', 'socks': 'носки',
            'underwear': 'нижнее белье', 'gloves': 'перчатки', 'scarf': 'шарф', 'glasses': 'очки',
            'jewelry': 'украшения', 'ring': 'кольцо', 'necklace': 'ожерелье', 'watch': 'часы',
            'bracelet': 'браслет', 'earrings': 'серьги', 'brooch': 'брошь', 'tie': 'галстук',
            'bow tie': 'бабочка', 'belt': 'ремень', 'wallet': 'кошелек', 'bag': 'сумка',
            'backpack': 'рюкзак', 'purse': 'кошелек', 'clutch': 'клатч', 'tote bag': 'сумка-тоут',
            'suit': 'костюм', 'tuxedo': 'смокинг', 'uniform': 'униформа', 'costume': 'костюм',
            'swimsuit': 'купальник', 'bikini': 'бикини', 'trunks': 'плавки', 'robe': 'халат',
            'pajamas': 'пижама', 'nightgown': 'ночная рубашка', 'lingerie': 'белье',
            'stockings': 'чулки', 'tights': 'колготки', 'leggings': 'леггинсы', 'jeans': 'джинсы',
            'shorts': 'шорты', 't-shirt': 'футболка', 'blouse': 'блузка', 'sweater': 'свитер',
            'hoodie': 'толстовка', 'cardigan': 'кардиган', 'vest': 'жилет', 'overalls': 'комбинезон',
            'raincoat': 'дождевик', 'windbreaker': 'ветровка', 'parka': 'парка', 'poncho': 'пончо',
            'kimono': 'кимоно', 'sari': 'сари', 'hanbok': 'ханбок', 'cheongsam': 'ципао',
            'dirndl': 'дирндль', 'lederhosen': 'ледерхозен', 'kilt': 'килт', 'burqa': 'бурка',
            'hijab': 'хиджаб', 'turban': 'тюрбан', 'yarmulke': 'ермолка', 'veil': 'вуаль',
            'crown': 'корона', 'tiara': 'тиара', 'wig': 'парик', 'hair accessory': 'аксессуар для волос',
            'hairpin': 'заколка', 'headband': 'повязка для волос', 'fashion': 'мода',
            'style': 'стиль', 'trend': 'тренд', 'designer': 'дизайнер', 'model': 'модель',
            'runway': 'подиум', 'fashion show': 'показ мод', 'couture': 'от кутюр',
            'haute couture': 'высокая мода', 'ready-to-wear': 'готовая одежда',
            'accessory': 'аксессуар', 'footwear': 'обувь', 'headwear': 'головной убор',
            'eyewear': 'очки', 'jewelry': 'ювелирные изделия', 'perfume': 'парфюм',
            'cosmetics': 'косметика', 'makeup': 'макияж', 'skincare': 'уход за кожей',

            # Дом и интерьер (150+ слов)
            'house': 'дом', 'apartment': 'квартира', 'room': 'комната', 'kitchen': 'кухня',
            'bedroom': 'спальня', 'bathroom': 'ванная', 'living room': 'гостиная', 'office': 'офис',
            'garden': 'сад', 'balcony': 'балкон', 'window': 'окно', 'door': 'дверь',
            'chair': 'стул', 'table': 'стол', 'bed': 'кровать', 'sofa': 'диван',
            'cabinet': 'шкаф', 'shelf': 'полка', 'mirror': 'зеркало', 'lamp': 'лампа',
            'carpet': 'ковер', 'curtain': 'штора', 'painting': 'картина', 'vase': 'ваза',
            'clock': 'часы', 'candle': 'свеча', 'pillow': 'подушка', 'blanket': 'одеяло',
            'rug': 'коврик', 'wallpaper': 'обои', 'tile': 'плитка', 'floor': 'пол',
            'ceiling': 'потолок', 'wall': 'стена', 'staircase': 'лестница', 'fireplace': 'камин',
            'bookshelf': 'книжная полка', 'desk': 'письменный стол', 'dresser': 'комод',
            'wardrobe': 'гардероб', 'closet': 'шкаф', 'cupboard': 'буфет', 'drawer': 'ящик',
            'counter': 'стойка', 'island': 'остров', 'sink': 'раковина', 'faucet': 'кран',
            'refrigerator': 'холодильник', 'oven': 'духовка', 'stove': 'плита', 'microwave': 'микроволновка',
            'dishwasher': 'посудомоечная машина', 'toaster': 'тостер', 'blender': 'блендер',
            'coffee maker': 'кофеварка', 'kettle': 'чайник', 'cutting board': 'разделочная доска',
            'utensil': 'столовый прибор', 'plate': 'тарелка', 'bowl': 'миска', 'cup': 'чашка',
            'glass': 'стакан', 'fork': 'вилка', 'knife': 'нож', 'spoon': 'ложка',
            'napkin': 'салфетка', 'tablecloth': 'скатерть', 'towel': 'полотенце', 'shower': 'душ',
            'bathtub': 'ванна', 'toilet': 'туалет', 'sink': 'умывальник', 'mirror': 'зеркало',
            'cabinet': 'шкафчик', 'shelf': 'полка', 'laundry': 'прачечная', 'washing machine': 'стиральная машина',
            'dryer': 'сушилка', 'iron': 'утюг', 'ironing board': 'гладильная доска',
            'vacuum cleaner': 'пылесос', 'broom': 'метла', 'mop': 'швабра', 'dustpan': 'совок',
            'trash can': 'мусорное ведро', 'recycling bin': 'корзина для переработки',
            'plant': 'растение', 'flower': 'цветок', 'vase': 'ваза', 'pot': 'горшок',
            'planter': 'кашпо', 'herb garden': 'огород с травами', 'indoor garden': 'комнатный сад',
            'aquarium': 'аквариум', 'terrarium': 'террариум', 'birdcage': 'клетка для птиц',
            'pet bed': 'лежанка для питомца', 'dog house': 'собачья будка', 'cat tree': 'когтеточка',
            'home decor': 'домашний декор', 'furniture': 'мебель', 'lighting': 'освещение',
            'textile': 'текстиль', 'art': 'искусство', 'sculpture': 'скульптура',
            'photograph': 'фотография', 'frame': 'рамка', 'display case': 'витрина',
            'mantel': 'каминная полка', 'sconce': 'бра', 'chandelier': 'люстра',
            'floor lamp': 'торшер', 'table lamp': 'настольная лампа', 'desk lamp': 'настольная лампа',
            'night light': 'ночник', 'candle holder': 'подсвечник', 'vase': 'ваза',
            'bowl': 'чаша', 'tray': 'поднос', 'basket': 'корзина', 'box': 'коробка',
            'trinket': 'безделушка', 'ornament': 'украшение', 'figurine': 'фигурка',
            'statuette': 'статуэтка', 'bookend': 'подставка для книг', 'paperweight': 'пресс-папье',
            'globe': 'глобус', 'map': 'карта', 'compass': 'компас', 'telescope': 'телескоп',
            'microscope': 'микроскоп', 'magnifying glass': 'увеличительное стекло',
            'barometer': 'барометр', 'thermometer': 'термометр', 'hygrometer': 'гигрометр',
            'clock': 'часы', 'sundial': 'солнечные часы', 'hourglass': 'песочные часы',
            'calendar': 'календарь', 'planner': 'ежедневник', 'notebook': 'блокнот',
            'pen': 'ручка', 'pencil': 'карандаш', 'marker': 'маркер', 'highlighter': 'маркер',
            'stapler': 'степлер', 'staple remover': 'съемник скоб', 'hole punch': 'дырокол',
            'scissors': 'ножницы', 'ruler': 'линейка', 'tape': 'лента', 'glue': 'клей',
            'paper clip': 'скрепка', 'binder clip': 'зажим для бумаг', 'rubber band': 'резинка',
            'push pin': 'канцелярская кнопка', 'thumbtack': 'канцелярская кнопка',
            'bulletin board': 'пробковая доска', 'whiteboard': 'маркерная доска',
            'chalkboard': 'грифельная доска', 'easel': 'мольберт', 'palette': 'палитра',
            'paintbrush': 'кисть', 'paint': 'краска', 'canvas': 'холст', 'sketchbook': 'скетчбук',
            'charcoal': 'уголь', 'pastel': 'пастель', 'watercolor': 'акварель',
            'oil paint': 'масляная краска', 'acrylic paint': 'акриловая краска',
            'clay': 'глина', 'pottery': 'гончарное изделие', 'ceramic': 'керамика',
            'porcelain': 'фарфор', 'glassware': 'стеклянная посуда', 'crystal': 'хрусталь',
            'silverware': 'серебряная посуда', 'cutlery': 'столовые приборы',
            'china': 'фарфоровая посуда', 'stoneware': 'посуда из камня',
            'woodwork': 'деревянное изделие', 'carving': 'резьба', 'inlay': 'инкрустация',
            'mosaic': 'мозаика', 'stained glass': 'витраж', 'tapestry': 'гобелен',
            'embroidery': 'вышивка', 'needlepoint': 'вышивание', 'cross-stitch': 'вышивка крестом',
            'knitting': 'вязание', 'crochet': 'вязание крючком', 'sewing': 'шитье',
            'quilting': 'лоскутное шитье', 'patchwork': 'пэчворк', 'weaving': 'ткачество',
            'spinning': 'прядение', 'dyeing': 'окрашивание', 'printing': 'печать',
            'bookbinding': 'переплетное дело', 'calligraphy': 'каллиграфия',
            'illumination': 'иллюминирование', 'origami': 'оригами', 'paper craft': 'бумажное ремесло',
            'scrapbooking': 'скрапбукинг', 'card making': 'изготовление открыток',
            'jewelry making': 'изготовление украшений', 'beading': 'бисероплетение',
            'metalworking': 'металлообработка', 'blacksmithing': 'кузнечное дело',
            'welding': 'сварка', 'forging': 'ковка', 'casting': 'литье',
            'engraving': 'гравировка', 'etching': 'травление', 'polishing': 'полировка',
            'lacquering': 'лакирование', 'varnishing': 'лакирование', 'gilding': 'золочение',
            'silvering': 'серебрение', 'bronzing': 'бронзирование', 'patinating': 'патинирование',
            'restoration': 'реставрация', 'conservation': 'консервация', 'preservation': 'сохранение',
            'framing': 'обрамление', 'matting': 'паспарту', 'glazing': 'остекление',
            'mounting': 'монтаж', 'hanging': 'подвешивание', 'displaying': 'экспонирование',
            'arranging': 'аранжировка', 'styling': 'стилизация', 'decorating': 'декорирование',
            'renovation': 'реновация', 'remodeling': 'перепланировка', 'refurbishment': 'реконструкция',
            'upcycling': 'апсайклинг', 'repurposing': 'перепрофилирование', 'recycling': 'переработка',
            'sustainability': 'устойчивость', 'eco-friendly': 'экологичный',
            'green design': 'зеленый дизайн', 'biophilic design': 'биофильный дизайн',
            'minimalism': 'минимализм', 'maximalism': 'максимализм', 'modern': 'модерн',
            'contemporary': 'современный', 'traditional': 'традиционный', 'classical': 'классический',
            'rustic': 'деревенский', 'industrial': 'индустриальный', 'vintage': 'винтажный',
            'retro': 'ретро', 'art deco': 'ар-деко', 'art nouveau': 'ар-нуво',
            'mid-century modern': 'модерн середины века', 'scandinavian': 'скандинавский',
            'japanese': 'японский', 'mediterranean': 'средиземноморский', 'bohemian': 'богемный',
            'coastal': 'прибрежный', 'tropical': 'тропический', 'farmhouse': 'фермерский',
            'cottage': 'коттеджный', 'lodge': 'охотничий', 'cabin': 'домик',
            'chalet': 'шале', 'villa': 'вилла', 'mansion': 'особняк', 'palace': 'дворец',
            'castle': 'замок', 'manor': 'поместье', 'estate': 'имение', 'property': 'собственность',
            'real estate': 'недвижимость', 'architecture': 'архитектура', 'design': 'дизайн',
            'layout': 'планировка', 'floor plan': 'поэтажный план', 'blueprint': 'чертеж',
            'model': 'макет', 'render': 'рендер', 'visualization': 'визуализация',
            'perspective': 'перспектива', 'elevation': 'фасад', 'section': 'разрез',
            'detail': 'деталь', 'specification': 'спецификация', 'material': 'материал',
            'finish': 'отделка', 'texture': 'текстура', 'color': 'цвет', 'pattern': 'узор',
            'motif': 'мотив', 'theme': 'тема', 'style': 'стиль', 'aesthetic': 'эстетика',
            'mood': 'настроение', 'atmosphere': 'атмосфера', 'ambiance': 'атмосфера',
            'vibe': 'вибрация', 'feeling': 'чувство', 'emotion': 'эмоция', 'sensation': 'ощущение',
            'impression': 'впечатление', 'experience': 'опыт', 'memory': 'воспоминание',
            'nostalgia': 'ностальгия', 'sentiment': 'чувство', 'association': 'ассоциация',
            'symbolism': 'символизм', 'meaning': 'значение', 'significance': 'значимость',
            'value': 'ценность', 'worth': 'стоимость', 'price': 'цена', 'cost': 'затраты',
            'budget': 'бюджет', 'investment': 'инвестиция', 'return': 'возврат',
            'profit': 'прибыль', 'loss': 'убыток', 'gain': 'прирост', 'benefit': 'выгода',
            'advantage': 'преимущество', 'disadvantage': 'недостаток', 'strength': 'сила',
            'weakness': 'слабость', 'opportunity': 'возможность', 'threat': 'угроза',
            'challenge': 'вызов', 'solution': 'решение', 'problem': 'проблема',
            'issue': 'вопрос', 'concern': 'обеспокоенность', 'question': 'вопрос',
            'answer': 'ответ', 'response': 'ответ', 'reply': 'ответ', 'feedback': 'обратная связь',
            'comment': 'комментарий', 'opinion': 'мнение', 'view': 'взгляд',
            'perspective': 'перспектива', 'standpoint': 'точка зрения', 'position': 'позиция',
            'attitude': 'отношение', 'belief': 'убеждение', 'principle': 'принцип',
            'value': 'ценность', 'virtue': 'добродетель', 'quality': 'качество',
            'characteristic': 'характеристика', 'feature': 'особенность', 'aspect': 'аспект',
            'element': 'элемент', 'component': 'компонент', 'ingredient': 'ингредиент',
            'factor': 'фактор', 'variable': 'переменная', 'parameter': 'параметр',
            'criterion': 'критерий', 'standard': 'стандарт', 'benchmark': 'ориентир',
            'measure': 'мера', 'metric': 'метрика', 'indicator': 'индикатор',
            'signal': 'сигнал', 'sign': 'знак', 'symbol': 'символ', 'mark': 'метка',
            'token': 'жетон', 'badge': 'значок', 'emblem': 'эмблема', 'logo': 'логотип',
            'brand': 'бренд', 'trademark': 'торговая марка', 'copyright': 'авторское право',
            'patent': 'патент', 'license': 'лицензия', 'permit': 'разрешение',
            'certificate': 'сертификат', 'diploma': 'диплом', 'degree': 'степень',
            'qualification': 'квалификация', 'credential': 'удостоверение', 'document': 'документ',
            'record': 'запись', 'file': 'файл', 'archive': 'архив', 'database': 'база данных',
            'library': 'библиотека', 'collection': 'коллекция', 'set': 'набор',
            'group': 'группа', 'category': 'категория', 'class': 'класс',
            'type': 'тип', 'kind': 'вид', 'sort': 'сорт', 'variety': 'разновидность',
            'species': 'вид', 'genus': 'род', 'family': 'семейство', 'order': 'отряд',
            'class': 'класс', 'phylum': 'тип', 'kingdom': 'царство', 'domain': 'домен',
            'realm': 'царство', 'world': 'мир', 'universe': 'вселенная', 'cosmos': 'космос',
            'galaxy': 'галактика', 'star system': 'звездная система', 'planet': 'планета',
            'moon': 'луна', 'asteroid': 'астероид', 'comet': 'комета', 'meteor': 'метеор',
            'nebula': 'туманность', 'black hole': 'черная дыра', 'wormhole': 'кротовая нора',
            'multiverse': 'мультивселенная', 'dimension': 'измерение', 'reality': 'реальность',
            'existence': 'существование', 'being': 'бытие', 'consciousness': 'сознание',
            'mind': 'разум', 'soul': 'душа', 'spirit': 'дух', 'energy': 'энергия',
            'matter': 'материя', 'antimatter': 'антиматерия', 'dark matter': 'темная материя',
            'dark energy': 'темная энергия', 'quantum': 'квант', 'particle': 'частица',
            'atom': 'атом', 'molecule': 'молекула', 'element': 'элемент', 'compound': 'соединение',
            'mixture': 'смесь', 'solution': 'раствор', 'suspension': 'суспензия',
            'colloid': 'коллоид', 'emulsion': 'эмульсия', 'foam': 'пена',
            'aerosol': 'аэрозоль', 'gel': 'гель', 'solid': 'твердое тело',
            'liquid': 'жидкость', 'gas': 'газ', 'plasma': 'плазма', 'crystal': 'кристалл',
            'mineral': 'минерал', 'rock': 'горная порода', 'stone': 'камень',
            'gem': 'драгоценный камень', 'crystal': 'кристалл', 'metal': 'металл',
            'alloy': 'сплав', 'ceramic': 'керамика', 'polymer': 'полимер',
            'composite': 'композит', 'nanomaterial': 'наноматериал', 'biomaterial': 'биоматериал',
            'smart material': 'умный материал', 'memory material': 'материал с памятью формы',
            'phase change material': 'материал с фазовым переходом', 'superconductor': 'сверхпроводник',
            'semiconductor': 'полупроводник', 'insulator': 'изолятор', 'conductor': 'проводник',
            'magnet': 'магнит', 'electromagnet': 'электромагнит', 'super magnet': 'супермагнит',
            'permanent magnet': 'постоянный магнит', 'temporary magnet': 'временный магнит',
            'ferromagnet': 'ферромагнетик', 'paramagnet': 'парамагнетик', 'diamagnet': 'диамагнетик',
            'magnetic field': 'магнитное поле', 'electric field': 'электрическое поле',
            'gravitational field': 'гравитационное поле', 'quantum field': 'квантовое поле',
            'force': 'сила', 'energy': 'энергия', 'power': 'мощность', 'work': 'работа',
            'heat': 'тепло', 'temperature': 'температура', 'pressure': 'давление',
            'volume': 'объем', 'density': 'плотность', 'mass': 'масса', 'weight': 'вес',
            'gravity': 'гравитация', 'acceleration': 'ускорение', 'velocity': 'скорость',
            'momentum': 'импульс', 'inertia': 'инерция', 'friction': 'трение',
            'viscosity': 'вязкость', 'elasticity': 'упругость', 'plasticity': 'пластичность',
            'ductility': 'пластичность', 'brittleness': 'хрупкость', 'hardness': 'твердость',
            'toughness': 'вязкость', 'strength': 'прочность', 'stiffness': 'жесткость',
            'flexibility': 'гибкость', 'malleability': 'ковкость', 'conductivity': 'проводимость',
            'resistivity': 'удельное сопротивление', 'capacitance': 'емкость',
            'inductance': 'индуктивность', 'impedance': 'импеданс', 'resonance': 'резонанс',
            'frequency': 'частота', 'wavelength': 'длина волны', 'amplitude': 'амплитуда',
            'phase': 'фаза', 'period': 'период', 'cycle': 'цикл', 'oscillation': 'колебание',
            'vibration': 'вибрация', 'wave': 'волна', 'particle': 'частица',
            'quantum': 'квант', 'photon': 'фотон', 'electron': 'электрон',
            'proton': 'протон', 'neutron': 'нейтрон', 'quark': 'кварк', 'lepton': 'лептон',
            'boson': 'бозон', 'fermion': 'фермион', 'hadron': 'адрон', 'meson': 'мезон',
            'baryon': 'барион', 'atom': 'атом', 'molecule': 'молекула', 'ion': 'ион',
            'isotope': 'изотоп', 'element': 'элемент', 'compound': 'соединение',
            'mixture': 'смесь', 'solution': 'раствор', 'suspension': 'суспензия',
            'colloid': 'коллоид', 'emulsion': 'эмульсия', 'foam': 'пена',
            'aerosol': 'аэрозоль', 'gel': 'гель', 'solid': 'твердое тело',
            'liquid': 'жидкость', 'gas': 'газ', 'plasma': 'плазма', 'crystal': 'кристалл',
            'mineral': 'минерал', 'rock': 'горная порода', 'stone': 'камень',
            'gem': 'драгоценный камень', 'crystal': 'кристалл', 'metal': 'металл',
            'alloy': 'сплав', 'ceramic': 'керамика', 'polymer': 'полимер',
            'composite': 'композит', 'nanomaterial': 'наноматериал', 'biomaterial': 'биоматериал',
            'smart material': 'умный материал', 'memory material': 'материал с памятью формы',
            'phase change material': 'материал с фазовым переходом', 'superconductor': 'сверхпроводник',
            'semiconductor': 'полупроводник', 'insulator': 'изолятор', 'conductor': 'проводник',
            'magnet': 'магнит', 'electromagnet': 'электромагнит', 'super magnet': 'супермагнит',
            'permanent magnet': 'постоянный магнит', 'temporary magnet': 'временный магнит',
            'ferromagnet': 'ферромагнетик', 'paramagnet': 'парамагнетик', 'diamagnet': 'диамагнетик',
            'magnetic field': 'магнитное поле', 'electric field': 'электрическое поле',
            'gravitational field': 'гравитационное поле', 'quantum field': 'квантовое поле',
            'force': 'сила', 'energy': 'энергия', 'power': 'мощность', 'work': 'работа',
            'heat': 'тепло', 'temperature': 'температура', 'pressure': 'давление',
            'volume': 'объем', 'density': 'плотность', 'mass': 'масса', 'weight': 'вес',
            'gravity': 'гравитация', 'acceleration': 'ускорение', 'velocity': 'скорость',
            'momentum': 'импульс', 'inertia': 'инерция', 'friction': 'трение',
            'viscosity': 'вязкость', 'elasticity': 'упругость', 'plasticity': 'пластичность',
            'ductility': 'пластичность', 'brittleness': 'хрупкость', 'hardness': 'твердость',
            'toughness': 'вязкость', 'strength': 'прочность', 'stiffness': 'жесткость',
            'flexibility': 'гибкость', 'malleability': 'ковкость', 'conductivity': 'проводимость',
            'resistivity': 'удельное сопротивление', 'capacitance': 'емкость',
            'inductance': 'индуктивность', 'impedance': 'импеданс', 'resonance': 'резонанс',
            'frequency': 'частота', 'wavelength': 'длина волны', 'amplitude': 'амплитуда',
            'phase': 'фаза', 'period': 'период', 'cycle': 'цикл', 'oscillation': 'колебание',
            'vibration': 'вибрация', 'wave': 'волна', 'particle': 'частица'
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

# HTML шаблон (остается без изменений)
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
