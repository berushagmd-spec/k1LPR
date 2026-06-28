# -*- coding: utf-8 -*-
import asyncio, logging, os, random, time
from dataclasses import dataclass
from typing import Set, List, Tuple
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from generator import generate_event, format_active
from state import BotState

@dataclass
class Config:
    bot_token: str
    target_chat_id: int
    admin_ids: Set[int]
    min_interval: int
    max_interval: int
    mode: str
    scenario: str
    state_file: str
    log_level: str

def parse_admin_ids(value: str) -> Set[int]:
    result = set()
    for raw in value.split(","):
        raw = raw.strip()
        if raw:
            result.add(int(raw))
    return result

def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Заполните .env.")
    mn = max(1, int(os.getenv("MIN_INTERVAL_MINUTES", "3")))
    mx = max(mn, int(os.getenv("MAX_INTERVAL_MINUTES", "10")))
    return Config(
        bot_token=token,
        target_chat_id=int(os.getenv("TARGET_CHAT_ID", "-1004449922425")),
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "7787565361")),
        min_interval=mn,
        max_interval=mx,
        mode=os.getenv("MODE", "normal").strip() or "normal",
        scenario=os.getenv("SCENARIO", "mixed").strip() or "mixed",
        state_file=os.getenv("STATE_FILE", "state.json").strip() or "state.json",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )

def get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    return context.application.bot_data["state"]

def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    config: Config = context.application.bot_data["config"]
    user = update.effective_user
    return bool(user and user.id in config.admin_ids)

def parse_command(text: str) -> Tuple[str, List[str], str]:
    text = text.strip()
    if not text.startswith("/"):
        return "", [], ""
    parts = text.split(maxsplit=1)
    cmd = parts[0][1:].split("@", 1)[0].lower().strip()
    rest = parts[1] if len(parts) > 1 else ""
    return cmd, rest.split() if rest else [], rest

def schedule_next_post(state: BotState, soon: bool = False) -> None:
    if soon:
        state.data["next_post_at"] = int(time.time()) + 5
    else:
        mn = int(state.data.get("min_interval", 3))
        mx = int(state.data.get("max_interval", 10))
        state.data["next_post_at"] = int(time.time()) + random.randint(mn * 60, mx * 60)
    state.save()

async def send_to_channel(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    state = get_state(context)
    await context.bot.send_message(chat_id=int(state.data["channel_id"]), text=text)
    state.append_post(text)

async def poster_loop(application: Application) -> None:
    logger = logging.getLogger("poster")
    state: BotState = application.bot_data["state"]
    if not state.data.get("next_post_at"):
        schedule_next_post(state, soon=True)
    while True:
        try:
            now = int(time.time())
            if state.data.get("enabled", True) and now >= int(state.data.get("next_post_at", 0)):
                text = generate_event(state.data, commit=True)
                state.save()
                await application.bot.send_message(chat_id=int(state.data["channel_id"]), text=text)
                state.append_post(text)
                logger.info("Posted generated event to %s", state.data["channel_id"])
                schedule_next_post(state, soon=False)
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Autoposting error")
            await asyncio.sleep(15)

async def on_startup(application: Application) -> None:
    application.create_task(poster_loop(application))

async def help_text(update: Update) -> None:
    await update.message.reply_text(
        "Бот Курбании активен. Команды лучше писать в личку боту.\n\n"
        "/id — показать ваш Telegram ID\n"
        "/status — статус\n"
        "/preview — пример без публикации\n"
        "/sample 5 — несколько примеров\n"
        "/post_now — сразу пост в канал\n"
        "/custom текст — свой пост в канал\n"
        "/pause — пауза\n"
        "/resume — продолжить\n"
        "/set_interval 1 3 — интервал в минутах\n"
        "/set_channel -1004449922425 — канал\n"
        "/mode calm|normal|hot|chaos — интенсивность\n"
        "/scenario mixed|bpla|missile|ballistic|aviation|artillery — сценарий\n"
        "/active — активные ветки\n"
        "/clear_active — очистить ветки"
    )

async def command_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    cmd, args, rest = parse_command(update.message.text)
    if not cmd:
        return

    state = get_state(context)
    user = update.effective_user

    if cmd == "id":
        await update.message.reply_text(f"Ваш Telegram ID: {user.id if user else 'не виден'}")
        return

    if cmd in ("start", "help"):
        if not is_admin(update, context):
            await update.message.reply_text(f"Нет доступа. Ваш ID: {user.id if user else 'не виден'}")
            return
        await help_text(update)
        return

    if not is_admin(update, context):
        await update.message.reply_text(
            f"Нет доступа. Ваш ID: {user.id if user else 'не виден'}\n"
            "Если ID правильный — добавь его в ADMIN_IDS в .env и перезапусти бота."
        )
        return

    if cmd == "status":
        data = state.data
        left = max(0, int(data.get("next_post_at", 0)) - int(time.time()))
        await update.message.reply_text(
            f"Статус: {'включен' if data.get('enabled', True) else 'пауза'}\n"
            f"Канал: {data.get('channel_id')}\n"
            f"Интервал: {data.get('min_interval')}–{data.get('max_interval')} мин.\n"
            f"Следующий пост примерно через: {left} сек.\n"
            f"Режим: {data.get('mode')}\n"
            f"Сценарий: {data.get('scenario')}\n"
            f"Активных веток: {len(data.get('active_incidents', []))}"
        )
        return

    if cmd == "preview":
        await update.message.reply_text("Предпросмотр:\n\n" + generate_event(state.data, commit=False))
        return

    if cmd == "sample":
        try:
            count = int(args[0]) if args else 5
        except ValueError:
            count = 5
        count = max(1, min(count, 10))
        samples = [f"{i+1})\n{generate_event(state.data, commit=False)}" for i in range(count)]
        await update.message.reply_text("\n\n———\n\n".join(samples))
        return

    if cmd == "post_now":
        text = generate_event(state.data, commit=True)
        state.save()
        await send_to_channel(context, text)
        schedule_next_post(state, soon=False)
        await update.message.reply_text("Опубликовано:\n\n" + text)
        return

    if cmd == "custom":
        text = rest.strip()
        if not text:
            await update.message.reply_text("Использование: /custom текст поста")
            return
        await send_to_channel(context, text)
        schedule_next_post(state, soon=False)
        await update.message.reply_text("Свое сообщение отправлено в канал.")
        return

    if cmd == "pause":
        state.data["enabled"] = False
        state.save()
        await update.message.reply_text("Автопостинг остановлен.")
        return

    if cmd == "resume":
        state.data["enabled"] = True
        schedule_next_post(state, soon=True)
        await update.message.reply_text("Автопостинг включен. Следующий пост будет скоро.")
        return

    if cmd == "set_interval":
        if len(args) != 2:
            await update.message.reply_text("Использование: /set_interval 1 3")
            return
        try:
            mn, mx = int(args[0]), int(args[1])
        except ValueError:
            await update.message.reply_text("Интервал должен быть числами.")
            return
        mn, mx = max(1, mn), max(max(1, mn), mx)
        state.data["min_interval"] = mn
        state.data["max_interval"] = mx
        schedule_next_post(state, soon=True)
        await update.message.reply_text(f"Интервал изменен: {mn}–{mx} мин. Следующий пост будет скоро.")
        return

    if cmd == "set_channel":
        if len(args) != 1:
            await update.message.reply_text("Использование: /set_channel -1004449922425")
            return
        try:
            state.data["channel_id"] = int(args[0])
        except ValueError:
            await update.message.reply_text("ID канала должен быть числом.")
            return
        state.save()
        await update.message.reply_text(f"Канал изменен: {state.data['channel_id']}")
        return

    if cmd == "mode":
        allowed = {"calm", "normal", "hot", "chaos"}
        if len(args) != 1 or args[0] not in allowed:
            await update.message.reply_text("Использование: /mode calm|normal|hot|chaos")
            return
        state.data["mode"] = args[0]
        state.save()
        await update.message.reply_text(f"Режим изменен: {args[0]}")
        return

    if cmd == "scenario":
        allowed = {"mixed", "bpla", "missile", "ballistic", "aviation", "artillery"}
        if len(args) != 1 or args[0] not in allowed:
            await update.message.reply_text("Использование: /scenario mixed|bpla|missile|ballistic|aviation|artillery")
            return
        state.data["scenario"] = args[0]
        state.save()
        await update.message.reply_text(f"Сценарий изменен: {args[0]}")
        return

    if cmd == "active":
        await update.message.reply_text(format_active(state.data))
        return

    if cmd == "clear_active":
        state.clear_active()
        await update.message.reply_text("Активные ветки очищены.")
        return

    await update.message.reply_text("Неизвестная команда. /help")

def build_application() -> Application:
    config = load_config()
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO), format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    defaults = {
        "enabled": True,
        "channel_id": config.target_chat_id,
        "min_interval": config.min_interval,
        "max_interval": config.max_interval,
        "mode": config.mode,
        "scenario": config.scenario,
        "active_incidents": [],
        "last_posts": [],
        "next_post_at": int(time.time()) + 5,
    }
    state = BotState(config.state_file, defaults)
    app = Application.builder().token(config.bot_token).post_init(on_startup).build()
    app.bot_data["config"] = config
    app.bot_data["state"] = state
    app.add_handler(MessageHandler(filters.TEXT, command_router))
    return app

def main() -> None:
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
