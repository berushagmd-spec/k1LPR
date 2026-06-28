# -*- coding: utf-8 -*-
import copy, random, time, uuid
from typing import Dict, List, Any, Tuple
from data import KURBANIA_ZONES, THREAT_BY_DEPTH, SCENARIO_ALLOWED, MODE_SETTINGS, THREAT_WEIGHTS_BY_MODE, DIRECTIONS_TEXT

def _pick_zone(state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    zones = list(KURBANIA_ZONES.items())
    mode = state.get("mode", "normal")
    weighted = []
    for key, zone in zones:
        depth = zone["depth"]
        if mode in ("hot", "chaos"):
            weight = {"close": 5, "middle": 4, "rear": 3, "far": 2}.get(depth, 2)
        elif mode == "calm":
            weight = {"close": 2, "middle": 2, "rear": 3, "far": 2}.get(depth, 2)
        else:
            weight = {"close": 3, "middle": 3, "rear": 3, "far": 2}.get(depth, 2)
        weighted.extend([(key, zone)] * weight)
    return random.choice(weighted)

def _pick_threat(zone: Dict[str, Any], state: Dict[str, Any]) -> str:
    scenario = state.get("scenario", "mixed")
    mode = state.get("mode", "normal")
    a = set(SCENARIO_ALLOWED.get(scenario, SCENARIO_ALLOWED["mixed"]))
    b = set(THREAT_BY_DEPTH.get(zone["depth"], THREAT_BY_DEPTH["middle"]))
    allowed = list(a & b) or list(b)
    weights = THREAT_WEIGHTS_BY_MODE.get(mode, THREAT_WEIGHTS_BY_MODE["normal"])
    pool = []
    for t in allowed:
        pool.extend([t] * max(1, int(weights.get(t, 1))))
    return random.choice(pool)

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
    return random.choice(DIRECTIONS_TEXT.get(zone["direction"], ["по направлению"]))

def _attention(threat: str) -> str:
    if threat == "artillery":
        return random.choice(["Принять меры безопасности", "Работают укрытия", "Не находиться на открытых участках", "Без необходимости не перемещаться"])
    if threat == "fpv":
        return random.choice(["Особое внимание дорогам", "Не перемещаться без необходимости"])
    if threat == "bpla":
        return random.choice(["Сохранять внимание", "Возможен проход к соседним населенным пунктам", ""])
    if threat == "missile":
        return random.choice(["Займите безопасные места", "Не игнорируйте сигнал тревоги", "Укрытия и подвальные помещения"])
    if threat == "ballistic":
        return random.choice(["Немедленно в укрытия", "Время реакции минимальное", "Не находиться у окон", "Укрытия и подвальные помещения"])
    if threat == "aviation":
        return random.choice(["Внимание по небу", "Возможна работа авиации", "Сохранять укрытия до отбоя"])
    return ""

def _new_message(threat: str, zone: Dict[str, Any], places: str) -> str:
    region = zone["region"]
    att = _attention(threat)
    templates = {
        "bpla": ["{places}\n{region}\nРедкая фиксация БПЛА", "{places}\n{region}\nВнимание по БПЛА\n{att}"],
        "fpv": ["{places}\n{region}\nЛокальная опасность FPV", "{places}\n{region}\nВнимание по FPV\n{att}"],
        "artillery": ["{places}\n{region}\nАртиллерийская тревога\n{att}", "{places}\n{region}\nОпасность артиллерийского обстрела\n{att}", "{places}\n{region}\nВнимание по артиллерии\n{att}"],
        "missile": ["{region}\nРакетная опасность", "{places}\n{region}\nРАКЕТНАЯ ОПАСНОСТЬ\n{att}", "{region}\nУгроза ракетного удара\n{att}", "{places}\n{region}\nТревога по ракетной угрозе"],
        "ballistic": ["{region}\nБаллистическая опасность\n{att}", "{places}\n{region}\nБАЛЛИСТИЧЕСКАЯ УГРОЗА\n{att}", "{region}\nУгроза баллистики\n{att}", "{places}\n{region}\nТревога по баллистике"],
        "aviation": ["{places}\n{region}\nАвиационно-ракетно-бомбовая опасность", "{region}\nАвиационная опасность\n{places}", "{places}\n{region}\nТревога по авиации\n{att}", "{places}\n{region}\nАвиационная и ракетная опасность"],
    }
    return _clean(random.choice(templates[threat]).format(places=places, region=region, att=att))

def _clear_message(i: Dict[str, Any]) -> str:
    p, r, t = i["places_text"], i["region"], i["threat"]
    templates = {
        "bpla": ["{p}\n{r}\nОтбой беспилотной опасности", "{r}\nОтбой тревоги по БПЛА"],
        "fpv": ["{p}\n{r}\nОтбой опасности по FPV"],
        "artillery": ["{p}\n{r}\nОтбой артиллерийской тревоги", "{r}\nОтбой артиллерийской опасности"],
        "missile": ["{r}\nОтбой ракетной опасности", "{p}\n{r}\nОТБОЙ РАКЕТНОЙ ОПАСНОСТИ"],
        "ballistic": ["{r}\nОтбой баллистической опасности", "{p}\n{r}\nОТБОЙ БАЛЛИСТИЧЕСКОЙ УГРОЗЫ"],
        "aviation": ["{p}\n{r}\nОтбой авиационно-ракетно-бомбовой опасности", "{r}\nОтбой авиационной опасности"],
    }
    return _clean(random.choice(templates[t]).format(p=p, r=r))

def _repeat_message(i: Dict[str, Any]) -> str:
    p, r, t = i["places_text"], i["region"], i["threat"]
    templates = {
        "bpla": ["{p}\n{r}\nРедкая фиксация БПЛА сохраняется"],
        "fpv": ["{p}\n{r}\nЛокальная опасность FPV сохраняется"],
        "artillery": ["{p}\n{r}\nАртиллерийская тревога сохраняется", "{p}\n{r}\nПовторно внимание по артиллерии"],
        "missile": ["{r}\nРакетная опасность сохраняется", "{p}\n{r}\nРАКЕТНАЯ ОПАСНОСТЬ\nПовторно"],
        "ballistic": ["{r}\nБаллистическая опасность сохраняется", "{p}\n{r}\nБАЛЛИСТИЧЕСКАЯ УГРОЗА\nПовторно"],
        "aviation": ["{p}\n{r}\nАвиационная опасность сохраняется", "{p}\n{r}\nАвиационно-ракетно-бомбовая опасность\nПовторно"],
    }
    return _clean(random.choice(templates[t]).format(p=p, r=r))

def _expand_message(i: Dict[str, Any], state: Dict[str, Any]) -> str:
    old_zone = KURBANIA_ZONES.get(i.get("zone_key"))
    if not old_zone:
        return _repeat_message(i)
    candidates = [(k, z) for k, z in KURBANIA_ZONES.items() if z["direction"] == old_zone["direction"] and k != i.get("zone_key")]
    if not candidates:
        candidates = list(KURBANIA_ZONES.items())
    key, zone = random.choice(candidates)
    places = _places_line(zone, 1, 3)
    i.update({"zone_key": key, "region": zone["region"], "places_text": places, "age": i.get("age", 0) + 1})
    t = i["threat"]
    if t == "artillery":
        return _clean(f"{places}\n{zone['region']}\nРасширение артиллерийской тревоги\n{_attention(t)}")
    if t == "missile":
        return _clean(f"{zone['region']}\nРасширение ракетной опасности\n{places}")
    if t == "ballistic":
        return _clean(f"{zone['region']}\nРасширение баллистической опасности\n{places}\n{_attention(t)}")
    if t == "aviation":
        return _clean(f"{places}\n{zone['region']}\nРасширение авиационно-ракетно-бомбовой опасности")
    if t == "fpv":
        return _clean(f"{places}\n{zone['region']}\nЛокальное расширение опасности FPV")
    return _clean(f"{places}\n{zone['region']}\nОпасность по БПЛА\nВероятное смещение {_direction_phrase(zone)}")

def _combine_message(i: Dict[str, Any]) -> str:
    p, r, t = i["places_text"], i["region"], i["threat"]
    if t == "aviation":
        return _clean(f"{p}\n{r}\nАвиационная и ракетная опасность\nПовторно")
    if t == "missile":
        return _clean(f"{p}\n{r}\nРакетная опасность сохраняется\nВозможна баллистика")
    if t == "ballistic":
        return _clean(f"{p}\n{r}\nБаллистическая и ракетная опасность\nПовторно")
    if t == "artillery":
        return _clean(f"{p}\n{r}\nАртиллерийская тревога сохраняется\nПовторно")
    return _repeat_message(i)

def _clean(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line.strip()]).strip()

def generate_event(state_data: Dict[str, Any], commit: bool = True) -> str:
    data = state_data if commit else copy.deepcopy(state_data)
    data.setdefault("active_incidents", [])
    settings = MODE_SETTINGS.get(data.get("mode", "normal"), MODE_SETTINGS["normal"])
    active: List[Dict[str, Any]] = data["active_incidents"]

    if active and random.random() < settings["update_weight"]:
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
    active.append({"id": uuid.uuid4().hex[:8], "ts": int(time.time()), "age": 0, "zone_key": zone_key, "region": zone["region"], "places_text": places, "threat": threat})
    if commit:
        data["active_incidents"] = active[-30:]
    return text

def format_active(state_data: Dict[str, Any]) -> str:
    active = state_data.get("active_incidents", [])
    if not active:
        return "Активных веток нет."
    return "\n".join([f"{x.get('id','????')} — {x.get('places_text')} / {x.get('region')} / {x.get('threat')} / возраст: {x.get('age',0)}" for x in active[-20:]])
