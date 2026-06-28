# -*- coding: utf-8 -*-
import copy
import random
import time
import uuid
from typing import Dict, List, Any, Tuple

from data import (
    KURBANIA_ZONES,
    THREAT_BY_DEPTH,
    SCENARIO_ALLOWED,
    MODE_SETTINGS,
    TURBANIA_PRESSURE_AREAS,
    DIRECTIONS_TEXT,
)


def _pick_zone(state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    zones = list(KURBANIA_ZONES.items())
    mode = state.get("mode", "normal")

    # В горячих режимах чаще выбираются ближние и средние районы.
    if mode in ("hot", "chaos"):
        weighted = []
        for key, zone in zones:
            depth = zone["depth"]
            weight = {"close": 6, "middle": 4, "rear": 2, "far": 1}.get(depth, 2)
            weighted.extend([(key, zone)] * weight)
        return random.choice(weighted)

    if mode == "calm":
        weighted = []
        for key, zone in zones:
            depth = zone["depth"]
            weight = {"close": 2, "middle": 2, "rear": 3, "far": 2}.get(depth, 2)
            weighted.extend([(key, zone)] * weight)
        return random.choice(weighted)

    return random.choice(zones)


def _pick_threat(zone: Dict[str, Any], state: Dict[str, Any]) -> str:
    scenario = state.get("scenario", "mixed")
    allowed_by_scenario = set(SCENARIO_ALLOWED.get(scenario, SCENARIO_ALLOWED["mixed"]))
    allowed_by_depth = set(THREAT_BY_DEPTH.get(zone["depth"], THREAT_BY_DEPTH["middle"]))
    allowed = list(allowed_by_scenario & allowed_by_depth) or list(allowed_by_depth)
    return random.choice(allowed)


def _places_line(zone: Dict[str, Any], count_min: int = 1, count_max: int = 4) -> str:
    places = zone["places"]
    count = random.randint(count_min, min(count_max, len(places)))
    chosen = random.sample(places, count)

    if len(chosen) == 1:
        suffix = random.choice(["и близлежащие", "и район", ""])
        return f"{chosen[0]} {suffix}".strip()

    if len(chosen) == 2:
        return f"{chosen[0]}, {chosen[1]} и близлежащие"

    return ", ".join(chosen[:-1]) + f", {chosen[-1]} и близлежащие"


def _direction_phrase(zone: Dict[str, Any]) -> str:
    options = DIRECTIONS_TEXT.get(zone["direction"], ["по направлению"])
    return random.choice(options)


def _maybe_attention_line(threat: str, zone: Dict[str, Any]) -> str:
    if threat == "artillery":
        return random.choice([
            "Принять меры безопасности",
            "Работают укрытия",
            "Не находиться на открытых участках",
        ])

    if threat == "fpv":
        return random.choice([
            "Особое внимание дорогам и открытым участкам",
            "Не перемещаться без необходимости",
            "Возможна работа малых групп",
        ])

    if threat == "bpla":
        return random.choice([
            "Возможен проход к соседним населенным пунктам",
            "Сохранять внимание",
            "Вероятно смещение по направлению населенных пунктов рядом",
            "",
        ])

    if threat == "missile":
        return random.choice([
            "Займите безопасные места",
            "Не игнорируйте сигнал тревоги",
            "Укрытия и подвальные помещения",
        ])

    if threat == "aviation":
        return random.choice([
            "Внимание по небу",
            "Возможна работа авиации",
            "Сохранять укрытия до отбоя",
        ])

    return ""


def _new_message(threat: str, zone: Dict[str, Any], places_line: str) -> str:
    region = zone["region"]
    direction = _direction_phrase(zone)
    pressure = random.choice(TURBANIA_PRESSURE_AREAS)
    attention = _maybe_attention_line(threat, zone)

    templates = {
        "bpla": [
            "{places}\n{region}\nОпасность по БПЛА",
            "{places}\n{region}\nТревога по БПЛА",
            "{places}\n{region}\nФиксация БПЛА {direction}",
            "{places}\n{region}\nОпасность по БПЛА\n{attention}",
            "{places}\n{region}\nВнимание по БПЛА\nВероятное смещение {direction}",
            "{places}\n{region}\nГруппа БПЛА\n{attention}",
        ],
        "fpv": [
            "{places}\n{region}\nОпасность по FPV",
            "{places}\n{region}\nТревога по малым БПЛА и FPV",
            "{places}\n{region}\nПовышенная опасность FPV\n{attention}",
        ],
        "artillery": [
            "{places}\n{region}\nАртиллерийская тревога\n{attention}",
            "{places}\n{region}\nОпасность артиллерийского обстрела\n{attention}",
            "{places}\n{region}\nВнимание по артиллерии\n{attention}",
        ],
        "missile": [
            "{region}\nРакетная опасность",
            "{places}\n{region}\nРАКЕТНАЯ ОПАСНОСТЬ\n{attention}",
            "{region}\nУгроза ракетного удара\n{attention}",
            "{places}\n{region}\nТревога по ракетной угрозе",
        ],
        "aviation": [
            "{places}\n{region}\nАвиационно-ракетно-бомбовая опасность",
            "{region}\nАвиационная опасность\n{places}",
            "{places}\n{region}\nТревога по авиации\n{attention}",
            "{places}\n{region}\nАвиационная и ракетная опасность",
        ],
    }

    text = random.choice(templates[threat]).format(
        places=places_line,
        region=region,
        direction=direction,
        pressure=pressure,
        attention=attention,
    )
    return _clean(text)


def _clear_message(incident: Dict[str, Any]) -> str:
    threat = incident["threat"]
    region = incident["region"]
    places = incident["places_text"]

    templates = {
        "bpla": [
            "{places}\n{region}\nОтбой беспилотной опасности",
            "{region}\nОтбой тревоги по БПЛА",
            "{places}\n{region}\nОтбой по БПЛА",
        ],
        "fpv": [
            "{places}\n{region}\nОтбой опасности по FPV",
            "{region}\nОтбой тревоги по малым БПЛА",
        ],
        "artillery": [
            "{places}\n{region}\nОтбой артиллерийской тревоги",
            "{region}\nОтбой артиллерийской опасности",
        ],
        "missile": [
            "{region}\nОтбой ракетной опасности",
            "{places}\n{region}\nОТБОЙ РАКЕТНОЙ ОПАСНОСТИ",
        ],
        "aviation": [
            "{places}\n{region}\nОтбой авиационно-ракетно-бомбовой опасности",
            "{region}\nОтбой авиационной опасности",
        ],
    }

    return _clean(random.choice(templates[threat]).format(places=places, region=region))


def _repeat_message(incident: Dict[str, Any]) -> str:
    threat = incident["threat"]
    region = incident["region"]
    places = incident["places_text"]

    templates = {
        "bpla": [
            "{places}\n{region}\nОпасность по БПЛА сохраняется\nПовторно",
            "{region}\nОпасность по БПЛА\nПовторно",
            "{places}\n{region}\nТревога по БПЛА сохраняется",
        ],
        "fpv": [
            "{places}\n{region}\nОпасность по FPV сохраняется",
            "{places}\n{region}\nПовторно FPV",
        ],
        "artillery": [
            "{places}\n{region}\nАртиллерийская тревога сохраняется",
            "{places}\n{region}\nПовторно внимание по артиллерии",
        ],
        "missile": [
            "{region}\nРакетная опасность сохраняется",
            "{places}\n{region}\nРАКЕТНАЯ ОПАСНОСТЬ\nПовторно",
        ],
        "aviation": [
            "{places}\n{region}\nАвиационная опасность сохраняется",
            "{places}\n{region}\nАвиационно-ракетно-бомбовая опасность\nПовторно",
        ],
    }

    return _clean(random.choice(templates[threat]).format(places=places, region=region))


def _expand_message(incident: Dict[str, Any], state: Dict[str, Any]) -> str:
    old_zone_key = incident.get("zone_key")
    old_zone = KURBANIA_ZONES.get(old_zone_key)
    threat = incident["threat"]

    if not old_zone:
        return _repeat_message(incident)

    same_direction = [
        (key, zone)
        for key, zone in KURBANIA_ZONES.items()
        if zone["direction"] == old_zone["direction"] and key != old_zone_key
    ]
    candidates = same_direction or list(KURBANIA_ZONES.items())
    new_key, new_zone = random.choice(candidates)
    new_places = _places_line(new_zone, 1, 3)

    incident["zone_key"] = new_key
    incident["region"] = new_zone["region"]
    incident["places_text"] = new_places
    incident["age"] = incident.get("age", 0) + 1

    if threat == "artillery":
        # Для артиллерии не указываем, откуда летит.
        return _clean(
            f"{new_places}\n{new_zone['region']}\nРасширение артиллерийской тревоги\n{_maybe_attention_line(threat, new_zone)}"
        )

    if threat == "missile":
        return _clean(
            f"{new_zone['region']}\nРасширение ракетной опасности\n{new_places}"
        )

    if threat == "aviation":
        return _clean(
            f"{new_places}\n{new_zone['region']}\nРасширение авиационно-ракетно-бомбовой опасности"
        )

    return _clean(
        f"{new_places}\n{new_zone['region']}\nОпасность по БПЛА\nВероятное смещение {_direction_phrase(new_zone)}"
    )


def _combine_message(incident: Dict[str, Any]) -> str:
    region = incident["region"]
    places = incident["places_text"]
    threat = incident["threat"]

    if threat in ("bpla", "fpv"):
        return _clean(
            random.choice([
                f"{places}\n{region}\nОпасность по БПЛА сохраняется\nДополнительно внимание по FPV",
                f"{places}\n{region}\nБПЛА и FPV\nПовышенное внимание",
                f"{places}\n{region}\nТревога по БПЛА\nВозможна работа малых групп",
            ])
        )

    if threat == "aviation":
        return _clean(
            f"{places}\n{region}\nАвиационная и ракетная опасность\nПовторно"
        )

    if threat == "missile":
        return _clean(
            f"{places}\n{region}\nРакетная опасность\nДополнительно внимание по БПЛА"
        )

    return _repeat_message(incident)


def _clean(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    lines = [line for line in lines if line.strip()]
    return "\n".join(lines).strip()


def generate_event(state_data: Dict[str, Any], commit: bool = True) -> str:
    """
    Генерирует одно сообщение. Если commit=False, state_data не меняется.
    """
    data = state_data if commit else copy.deepcopy(state_data)
    data.setdefault("active_incidents", [])

    mode = data.get("mode", "normal")
    settings = MODE_SETTINGS.get(mode, MODE_SETTINGS["normal"])
    active: List[Dict[str, Any]] = data["active_incidents"]

    should_update = bool(active) and random.random() < settings["update_weight"]

    if should_update:
        incident = random.choice(active)
        roll = random.random()

        if roll < settings["clear_chance"]:
            text = _clear_message(incident)
            active.remove(incident)
        elif roll < settings["clear_chance"] + settings["expand_chance"]:
            text = _expand_message(incident, data)
        elif roll < settings["clear_chance"] + settings["expand_chance"] + settings["combine_chance"]:
            incident["age"] = incident.get("age", 0) + 1
            text = _combine_message(incident)
        else:
            incident["age"] = incident.get("age", 0) + 1
            text = _repeat_message(incident)

        if commit:
            data["active_incidents"] = active[-30:]
        return text

    zone_key, zone = _pick_zone(data)
    threat = _pick_threat(zone, data)
    places = _places_line(zone)
    text = _new_message(threat, zone, places)

    incident = {
        "id": uuid.uuid4().hex[:8],
        "ts": int(time.time()),
        "age": 0,
        "zone_key": zone_key,
        "region": zone["region"],
        "places_text": places,
        "threat": threat,
    }
    active.append(incident)

    if commit:
        data["active_incidents"] = active[-30:]

    return text


def format_active(state_data: Dict[str, Any]) -> str:
    active = state_data.get("active_incidents", [])
    if not active:
        return "Активных веток нет."

    lines = []
    for item in active[-20:]:
        age = item.get("age", 0)
        lines.append(
            f"{item.get('id', '????')} — {item.get('places_text')} / {item.get('region')} / {item.get('threat')} / возраст: {age}"
        )
    return "\n".join(lines)
