# -*- coding: utf-8 -*-
import copy, random, time, uuid
from typing import Dict, List, Any, Tuple
from data import (
    KURBANIA_ZONES,
    THREAT_BY_DEPTH,
    SCENARIO_ALLOWED,
    MODE_SETTINGS,
    THREAT_WEIGHTS_BY_MODE,
    DIRECTIONS_TEXT,
    MISSILE_TYPES,
    AVIATION_TYPES,
    TURBANIA_LAUNCH_REGIONS_BY_THREAT,
    COMBINED_ATTACK_TYPES,
)

DANGERS_WITH_SIREN = {"artillery", "missile", "ballistic", "aviation", "combined"}

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

def _first_city(places_text: str) -> str:
    city = places_text.split(",", 1)[0].strip()
    city = city.replace(" и близлежащие", "").replace(" и район", "").strip()
    return city or "Дияма"

def _direction_phrase(zone: Dict[str, Any]) -> str:
    return random.choice(DIRECTIONS_TEXT.get(zone["direction"], ["по направлению"]))

def _direction_target(zone: Dict[str, Any]) -> str:
    # Важно: названия субъектов НЕ склоняем.
    # Канальный стиль использует только именительный падеж:
    # "В направлении: Диямская агломерация", а не "Диямскую агломерацию".
    return zone.get("region", "")

def _origin_for_threat(threat: str) -> str:
    if threat == "ballistic":
        return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["ballistic"])
    if threat == "aviation":
        return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["aviation"])
    return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["missile"])

def _origin_for_component(component: str) -> str:
    if component == "ballistic":
        return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["ballistic"])
    if component == "aviation":
        return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["aviation"])
    return random.choice(TURBANIA_LAUNCH_REGIONS_BY_THREAT["missile"])


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
    if threat == "combined":
        return random.choice(["Немедленно в укрытия", "Не игнорируйте сигнал тревоги", "Укрытия и подвальные помещения", "Сохранять укрытия до отбоя"])
    return ""

def _set_air_alert_next(data: Dict[str, Any], city: str) -> None:
    data["pending_air_alert"] = {"city": city, "ts": int(time.time())}
    data["urgent_next"] = True

def _set_reaction_posts(data: Dict[str, Any], city: str) -> None:
    # Иногда перед сиреной идет отдельный пост о работе ПВО.
    if random.random() < 0.38:
        _set_pvo_next(data, city)
        data["pending_air_alert"] = {"city": city, "ts": int(time.time())}
    else:
        _set_air_alert_next(data, city)


def _set_clear_air_alert_next(data: Dict[str, Any], city: str) -> None:
    data["pending_clear_air_alert"] = {"city": city, "ts": int(time.time())}
    data["urgent_next"] = True

def _air_alert_message(pending: Dict[str, Any], data: Dict[str, Any]) -> str:
    city = pending.get("city", "Дияма")
    data["last_event_kind"] = "air_alert"
    return f"{city}\n⚠️ВОЗДУШНАЯ ТРЕВОГА⚠️"

def _clear_air_alert_message(pending: Dict[str, Any], data: Dict[str, Any]) -> str:
    city = pending.get("city", "Дияма")
    data["last_event_kind"] = "clear_air_alert"
    return f"{city}\n✅ОТБОЙ ВОЗДУШНОЙ ТРЕВОГИ✅"

def _set_pvo_next(data: Dict[str, Any], place: str) -> None:
    data["pending_pvo"] = {"place": place, "ts": int(time.time())}
    data["urgent_next"] = True

def _pvo_message(pending: Dict[str, Any], data: Dict[str, Any]) -> str:
    place = pending.get("place", "Дияма")
    data["last_event_kind"] = "pvo"
    return f"{place}\nРабота ПВО"


def _new_message(threat: str, zone: Dict[str, Any], places: str) -> str:
    region = zone["region"]
    att = _attention(threat)
    templates = {
        "bpla": ["{places}\n{region}\nРедкая фиксация БПЛА", "{places}\n{region}\nВнимание по БПЛА\n{att}"],
        "fpv": ["{places}\n{region}\nЛокальная опасность FPV", "{places}\n{region}\nВнимание по FPV\n{att}"],
        "artillery": ["{places}\n{region}\nАртиллерийская тревога\n{att}", "{places}\n{region}\nОпасность артиллерийского обстрела\n{att}", "{places}\n{region}\nВнимание по артиллерии\n{att}"],
        "missile": ["{region}\nРакетная опасность", "{places}\n{region}\nРАКЕТНАЯ ОПАСНОСТЬ\n{att}", "{region}\nУгроза ракетного удара\n{att}", "{places}\n{region}\nТревога по ракетной угрозе"],
        "ballistic": ["{region}\nБаллистическая опасность\n{att}", "{places}\n{region}\nБАЛЛИСТИЧЕСКАЯ УГРОЗА\n{att}", "{region}\nУгроза баллистики\n{att}", "{places}\n{region}\nТревога по баллистике"],
        "combined": ["{places}\n{region}\nКомбинированная атака\n{combo}\n{att}", "{region}\nКОМБИНИРОВАННАЯ ОПАСНОСТЬ\n{combo}\n{att}", "{places}\n{region}\nТревога по комбинированной атаке\n{combo}"],
        "aviation": ["{places}\n{region}\nАвиационно-ракетно-бомбовая опасность", "{region}\nАвиационная опасность\n{places}", "{places}\n{region}\nТревога по авиации\n{att}", "{places}\n{region}\nАвиационная и ракетная опасность"],
    }
    return _clean(random.choice(templates[threat]).format(places=places, region=region, att=att, combo=random.choice(COMBINED_ATTACK_TYPES)))

def _zone_key_by_obj(zone: Dict[str, Any]) -> str:
    for key, value in KURBANIA_ZONES.items():
        if value is zone:
            return key
    for key, value in KURBANIA_ZONES.items():
        if value.get("region") == zone.get("region") and value.get("places") == zone.get("places"):
            return key
    return random.choice(list(KURBANIA_ZONES.keys()))

def _prealert_message(threat: str, zone: Dict[str, Any]) -> Dict[str, Any]:
    target = _direction_target(zone)
    places = _places_line(zone)

    if threat in ("missile", "ballistic"):
        origin = _origin_for_threat(threat)
        rocket = random.choice(MISSILE_TYPES.get(threat, MISSILE_TYPES["missile"]))
        if random.choice(["fixation", "launch"]) == "launch":
            text = f"Пуски ракет ({rocket})\nРайон пуска: {origin}\nВ направлении: {target}"
        else:
            text = f"Фиксация ракет ({rocket})\nРайон пуска: {origin}\nВ направлении: {target}"

    elif threat == "combined":
        combo = random.choice(COMBINED_ATTACK_TYPES)

        if "баллистика" in combo:
            missile_component = "ballistic"
        else:
            missile_component = "missile"

        rocket = random.choice(MISSILE_TYPES.get(missile_component, MISSILE_TYPES["missile"]))
        aircraft = random.choice(AVIATION_TYPES)
        launch_origin = _origin_for_component(missile_component)
        aviation_origin = _origin_for_component("aviation")

        text = (
            f"Фиксация комбинированной атаки ({combo})\n"
            f"Ракетный компонент: {rocket}\n"
            f"Авиационный компонент: {aircraft}\n"
            f"Район пуска: {launch_origin}\n"
            f"Район вылета: {aviation_origin}\n"
            f"В направлении: {target}"
        )

    else:
        origin = _origin_for_threat("aviation")
        aircraft = random.choice(AVIATION_TYPES)
        if random.choice(["flight", "fixation"]) == "flight":
            text = f"Пролёт авиации ({aircraft})\nРайон вылета: {origin}\nВ направлении: {target}"
        else:
            text = f"Фиксация авиации ({aircraft})\nРайон вылета: {origin}\nВ направлении: {target}"

    return {
        "text": _clean(text),
        "threat": threat,
        "zone_key": _zone_key_by_obj(zone),
        "region": zone["region"],
        "places_text": places,
        "air_city": _first_city(places),
        "ts": int(time.time()),
    }

def _danger_after_prealert(pending: Dict[str, Any], data: Dict[str, Any]) -> str:
    threat = pending["threat"]
    region = pending["region"]
    places = pending["places_text"]
    zone_key = pending["zone_key"]
    city = pending.get("air_city") or _first_city(places)

    if threat == "ballistic":
        text = random.choice([
            f"{places}\n{region}\nБАЛЛИСТИЧЕСКАЯ УГРОЗА\n{_attention('ballistic')}",
            f"{region}\nБаллистическая опасность\n{_attention('ballistic')}",
            f"{places}\n{region}\nТревога по баллистике",
        ])
    elif threat == "missile":
        text = random.choice([
            f"{places}\n{region}\nРАКЕТНАЯ ОПАСНОСТЬ\n{_attention('missile')}",
            f"{region}\nРакетная опасность",
            f"{places}\n{region}\nТревога по ракетной угрозе",
        ])
    elif threat == "combined":
        combo = random.choice(COMBINED_ATTACK_TYPES)
        text = random.choice([
            f"{places}\n{region}\nКОМБИНИРОВАННАЯ ОПАСНОСТЬ\n{combo}\n{_attention('combined')}",
            f"{places}\n{region}\nКомбинированная атака\n{combo}",
            f"{region}\nТревога по комбинированной атаке\n{combo}\n{_attention('combined')}",
        ])
    else:
        text = random.choice([
            f"{places}\n{region}\nАвиационная опасность",
            f"{places}\n{region}\nАвиационно-ракетно-бомбовая опасность",
            f"{places}\n{region}\nТревога по авиации\n{_attention('aviation')}",
        ])

    data.setdefault("active_incidents", []).append({
        "id": uuid.uuid4().hex[:8],
        "ts": int(time.time()),
        "age": 0,
        "zone_key": zone_key,
        "region": region,
        "places_text": places,
        "threat": threat,
    })
    data["active_incidents"] = data["active_incidents"][-30:]
    _set_reaction_posts(data, city)
    data["last_event_kind"] = "danger"
    return _clean(text)

def _should_make_prealert(threat: str, state: Dict[str, Any]) -> bool:
    if threat not in ("missile", "ballistic", "aviation", "combined"):
        return False
    scenario = state.get("scenario", "mixed")
    mode = state.get("mode", "normal")
    base = {"calm": 0.18, "normal": 0.30, "hot": 0.38, "chaos": 0.45}.get(mode, 0.30)
    if scenario in ("missile", "ballistic", "aviation"):
        base += 0.10
    return random.random() < min(base, 0.60)

def _clear_message(i: Dict[str, Any]) -> str:
    p, r, t = i["places_text"], i["region"], i["threat"]
    templates = {
        "bpla": ["{p}\n{r}\nОтбой беспилотной опасности", "{r}\nОтбой тревоги по БПЛА"],
        "fpv": ["{p}\n{r}\nОтбой опасности по FPV"],
        "artillery": ["{p}\n{r}\nОтбой артиллерийской тревоги", "{r}\nОтбой артиллерийской опасности"],
        "missile": ["{r}\nОтбой ракетной опасности", "{p}\n{r}\nОТБОЙ РАКЕТНОЙ ОПАСНОСТИ"],
        "ballistic": ["{r}\nОтбой баллистической опасности", "{p}\n{r}\nОТБОЙ БАЛЛИСТИЧЕСКОЙ УГРОЗЫ"],
        "combined": ["{r}\nОтбой комбинированной опасности", "{p}\n{r}\nОТБОЙ КОМБИНИРОВАННОЙ УГРОЗЫ"],
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
        "combined": ["{p}\n{r}\nКомбинированная опасность сохраняется", "{p}\n{r}\nКОМБИНИРОВАННАЯ УГРОЗА\nПовторно"],
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
        text = f"{places}\n{zone['region']}\nРасширение артиллерийской тревоги\n{_attention(t)}"
    elif t == "missile":
        text = f"{zone['region']}\nРасширение ракетной опасности\n{places}"
    elif t == "ballistic":
        text = f"{zone['region']}\nРасширение баллистической опасности\n{places}\n{_attention(t)}"
    elif t == "aviation":
        text = f"{places}\n{zone['region']}\nРасширение авиационно-ракетно-бомбовой опасности"
    elif t == "combined":
        text = f"{places}\n{zone['region']}\nРасширение комбинированной опасности\n{random.choice(COMBINED_ATTACK_TYPES)}"
    elif t == "fpv":
        text = f"{places}\n{zone['region']}\nЛокальное расширение опасности FPV"
    else:
        text = f"{places}\n{zone['region']}\nОпасность по БПЛА\nВероятное смещение {_direction_phrase(zone)}"
    if t in DANGERS_WITH_SIREN:
        _set_reaction_posts(state, _first_city(places))
    return _clean(text)

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
    if t == "combined":
        return _clean(f"{p}\n{r}\nКомбинированная опасность сохраняется\n{random.choice(COMBINED_ATTACK_TYPES)}")
    return _repeat_message(i)

def _clean(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line.strip()]).strip()

def generate_event(state_data: Dict[str, Any], commit: bool = True) -> str:
    data = state_data if commit else copy.deepcopy(state_data)
    data.setdefault("active_incidents", [])
    data["last_event_kind"] = "text"

    # Приоритет: фиксация -> опасность -> сирена -> отбой сирены
    pending = data.pop("pending_alert", None)
    if pending:
        return _danger_after_prealert(pending, data)

    pending_air = data.pop("pending_air_alert", None)
    if pending_air:
        return _air_alert_message(pending_air, data)

    pending_clear_air = data.pop("pending_clear_air_alert", None)
    if pending_clear_air:
        return _clear_air_alert_message(pending_clear_air, data)

    pending_pvo = data.pop("pending_pvo", None)
    if pending_pvo:
        return _pvo_message(pending_pvo, data)

    settings = MODE_SETTINGS.get(data.get("mode", "normal"), MODE_SETTINGS["normal"])
    active: List[Dict[str, Any]] = data["active_incidents"]

    if active and random.random() < settings["update_weight"]:
        incident = random.choice(active)
        roll = random.random()
        if roll < settings["clear_chance"]:
            text = _clear_message(incident)
            cleared_threat = incident["threat"]
            city = _first_city(incident["places_text"])
            active.remove(incident)
            if cleared_threat in DANGERS_WITH_SIREN:
                _set_clear_air_alert_next(data, city)
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

    if _should_make_prealert(threat, data):
        pre = _prealert_message(threat, zone)
        data["pending_alert"] = {
            "threat": pre["threat"],
            "zone_key": pre["zone_key"],
            "region": pre["region"],
            "places_text": pre["places_text"],
            "air_city": pre["air_city"],
            "ts": pre["ts"],
        }
        data["urgent_next"] = True
        data["last_event_kind"] = "prealert"
        return pre["text"]

    places = _places_line(zone)
    text = _new_message(threat, zone, places)
    active.append({"id": uuid.uuid4().hex[:8], "ts": int(time.time()), "age": 0, "zone_key": zone_key, "region": zone["region"], "places_text": places, "threat": threat})
    if threat in DANGERS_WITH_SIREN:
        _set_reaction_posts(data, _first_city(places))
    if commit:
        data["active_incidents"] = active[-30:]
    data["last_event_kind"] = "danger" if threat in DANGERS_WITH_SIREN else "text"
    return text

def format_active(state_data: Dict[str, Any]) -> str:
    active = state_data.get("active_incidents", [])
    pending = state_data.get("pending_alert")
    pending_air = state_data.get("pending_air_alert")
    pending_clear_air = state_data.get("pending_clear_air_alert")
    lines = []
    if pending:
        lines.append(f"Следующий пост: опасность после фиксации / {pending.get('threat')} / {pending.get('region')} / {pending.get('places_text')}")
    if pending_air:
        lines.append(f"Следующий пост: воздушная тревога / {pending_air.get('city')}")
    if pending_clear_air:
        lines.append(f"Следующий пост: отбой воздушной тревоги / {pending_clear_air.get('city')}")
    if not active and not lines:
        return "Активных веток нет."
    lines.extend([f"{x.get('id','????')} — {x.get('places_text')} / {x.get('region')} / {x.get('threat')} / возраст: {x.get('age',0)}" for x in active[-20:]])
    return "\n".join(lines)
