# -*- coding: utf-8 -*-
"""
Данные сеттинга для генератора.
В посты не выводятся технические группы вроде "front", "deep_rear".
"""

KURBANIA_ZONES = {
    "southwest_close": {
        "region": "Форская область",
        "depth": "close",
        "direction": "юго-запад",
        "places": ["Гона", "Зурба", "Черный", "Фрода", "Сейла", "Фор", "Шорок", "Велико-Умуртск"],
    },
    "west_close": {
        "region": "Мноройская область",
        "depth": "close",
        "direction": "запад",
        "places": ["Стрекозное", "Ройск", "Чопла", "Эниа", "Решедэн", "Агда", "Наржа"],
    },
    "northwest_close": {
        "region": "Алугданская область",
        "depth": "close",
        "direction": "северо-запад",
        "places": ["Дерево", "Малая Зелень", "Дамир", "Нелель", "Жаднач"],
    },
    "north_close": {
        "region": "Сугданская область",
        "depth": "close",
        "direction": "север",
        "places": ["Сокол", "Велена", "Доковы"],
    },
    "southwest_middle": {
        "region": "Форская область",
        "depth": "middle",
        "direction": "юго-запад",
        "places": ["Вейла", "Ал", "Гоный Ал", "Евгено-Форов", "Малый Фор", "Кужда"],
    },
    "west_middle": {
        "region": "Моноройская область",
        "depth": "middle",
        "direction": "запад",
        "places": ["Моноройск", "Гера", "Наржа", "Зеленостопль"],
    },
    "northwest_middle": {
        "region": "Сугданская область",
        "depth": "middle",
        "direction": "северо-запад",
        "places": ["Озерослав", "Ромашка", "Рекаль"],
    },
    "north_middle": {
        "region": "Ангераская область",
        "depth": "middle",
        "direction": "север",
        "places": ["Ангерас", "Доковы", "Доброгород"],
    },
    "center_rear": {
        "region": "Озерославская область",
        "depth": "rear",
        "direction": "центр",
        "places": ["Озерославск", "Алержа"],
    },
    "kurb_rear": {
        "region": "Курбская область",
        "depth": "rear",
        "direction": "центр",
        "places": ["Курбск", "Дель", "Обищина", "Зелен"],
    },
    "verh_rear": {
        "region": "Верходиямская область",
        "depth": "rear",
        "direction": "центр",
        "places": ["Верходияма", "Дияга"],
    },
    "east_rear": {
        "region": "Ангераская область",
        "depth": "rear",
        "direction": "восток",
        "places": ["Ебаз", "Шенматор", "Кельматор"],
    },
    "diyam_rear": {
        "region": "Диямская область",
        "depth": "rear",
        "direction": "восток",
        "places": ["Великий", "Фердель", "Оробож", "Нелян", "Дияма", "Рейла", "Пуснарь", "Зелемай", "Хладский"],
    },
    "danel_far": {
        "region": "Дамельская область",
        "depth": "far",
        "direction": "восток",
        "places": ["Дамель", "Гамельск", "Гемель", "Душинка", "Смертный", "Нельск", "Дервей"],
    },
    "nel_far": {
        "region": "Курбская область, Нельский округ",
        "depth": "far",
        "direction": "восток",
        "places": ["Нель-Восточный", "Фруктовск", "Краин", "Курбанска"],
    },
}

TURBANIA_PRESSURE_AREAS = [
    "Турбанов-ярское направление",
    "Новотурбанское направление",
    "Лахтинский участок",
    "Рекославский узел",
    "Лесопольская линия",
    "Север Турбанов-Ярской области",
    "Тихоборский северный пояс",
    "Дамирск-Саржинское направление",
]

THREAT_BY_DEPTH = {
    "close": ["artillery", "aviation", "missile", "fpv", "bpla"],
    "middle": ["aviation", "missile", "artillery", "bpla"],
    "rear": ["missile", "aviation", "bpla"],
    "far": ["missile", "aviation", "bpla"],
}

SCENARIO_ALLOWED = {
    "mixed": ["bpla", "fpv", "artillery", "aviation", "missile"],
    "bpla": ["bpla", "fpv"],
    "missile": ["missile"],
    "aviation": ["aviation", "missile"],
    "artillery": ["artillery", "fpv"],
}

MODE_SETTINGS = {
    "calm": {
        "new_weight": 0.55,
        "update_weight": 0.45,
        "clear_chance": 0.45,
        "expand_chance": 0.10,
        "combine_chance": 0.05,
    },
    "normal": {
        "new_weight": 0.50,
        "update_weight": 0.50,
        "clear_chance": 0.28,
        "expand_chance": 0.22,
        "combine_chance": 0.12,
    },
    "hot": {
        "new_weight": 0.45,
        "update_weight": 0.55,
        "clear_chance": 0.16,
        "expand_chance": 0.35,
        "combine_chance": 0.22,
    },
    "chaos": {
        "new_weight": 0.38,
        "update_weight": 0.62,
        "clear_chance": 0.10,
        "expand_chance": 0.42,
        "combine_chance": 0.35,
    },
}

# БПЛА по лору летают редко. Даже в hot/chaos они остаются не основой генерации.
THREAT_WEIGHTS_BY_MODE = {
    "calm": {
        "bpla": 1,
        "fpv": 1,
        "artillery": 4,
        "aviation": 5,
        "missile": 4,
    },
    "normal": {
        "bpla": 1,
        "fpv": 2,
        "artillery": 5,
        "aviation": 6,
        "missile": 5,
    },
    "hot": {
        "bpla": 1,
        "fpv": 3,
        "artillery": 6,
        "aviation": 7,
        "missile": 6,
    },
    "chaos": {
        "bpla": 2,
        "fpv": 4,
        "artillery": 7,
        "aviation": 8,
        "missile": 7,
    },
}

THREAT_LABELS = {
    "bpla": "БПЛА",
    "fpv": "FPV",
    "artillery": "артиллерия",
    "aviation": "авиация",
    "missile": "ракеты",
}

DIRECTIONS_TEXT = {
    "юго-запад": ["с юго-западного направления", "по юго-западной дуге"],
    "запад": ["с западного направления", "по западной дуге"],
    "северо-запад": ["с северо-западного направления", "по северо-западной дуге"],
    "север": ["с северного направления", "по северной дуге"],
    "центр": ["в центральной части", "по центральному поясу"],
    "восток": ["на восточном направлении", "по восточной линии"],
}
