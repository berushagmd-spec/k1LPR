# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import random
from dataclasses import dataclass
from typing import Set

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

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
        if not raw:
            continue
        result.add(int(raw))
    return result


def load_config() -> Config:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Заполните .env.")

    min_interval = int(os.getenv("MIN_INTERVAL_MINUTES", "20"))
    max_interval = int(os.getenv("MAX_INTERVAL_MINUTES", "70"))

    if min_interval < 1:
        min_interval = 1
    if max_interval < min_interval:
        max_interval = min_interval

    return Config(
        bot_token=token,
        target_chat_id=int(os.getenv("TARGET_CHAT_ID", "-1004449922425")),
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "7787565361")),
        min_interval=min_interval,
        max_interval=max_interval,
        mode=os.getenv("MODE", "normal").strip() or "normal",
        scenario=os.getenv("SCENARIO", "mixed").strip() or "mixed",
        state_file=os.getenv("STATE_FILE", "state.json").strip() or "state.json",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        config: Config = context.application.bot_data["config"]
        user = update.effective_user
        if not user or user.id not in config.admin_ids:
            if update.message:
                await update.message.reply_text("Нет доступа.")
            return
        return await func(update, context)

    return wrapper


def get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    return context.application.bot_data["state"]


def html_quote(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


async def send_to_channel(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    state = get_state(context)
    channel_id = int(state.data["channel_id"])
    await context.bot.send_message(chat_id=channel_id, text=text)
    state.append_post(text)


async def poster_loop(application: Application) -> None:
    logger = logging.getLogger("poster")
    state: BotState = application.bot_data["state"]

    await asyncio.sleep(3)

    while True:
        try:
            if state.data.get("enabled", True):
                text = generate_event(state.data, commit=True)
                state.save()
                await application.bot.send_message(
                    chat_id=int(state.data["channel_id"]),
                    text=text,
                )
                state.append_post(text)
                logger.info("Posted generated event to %s", state.data["channel_id"])

                delay_min = random.randint(
                    int(state.data["min_interval"]),
                    int(state.data["max_interval"]),
                )
                await asyncio.sleep(delay_min * 60)
            else:
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Autoposting error")
            await asyncio.sleep(60)


async def on_startup(application: Application) -> None:
    application.create_task(poster_loop(application))


@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Бот Курбании активен.\n\n"
        "Команды:\n"
        "/status — статус\n"
        "/preview — пример без публикации\n"
        "/sample 5 — несколько примеров\n"
        "/post_now — опубликовать сгенерированный пост\n"
        "/custom текст — отправить свой текст в канал\n"
        "/pause — пауза\n"
        "/resume — продолжить\n"
        "/set_interval 15 45 — интервал в минутах\n"
        "/set_channel -1004449922425 — канал\n"
        "/mode calm|normal|hot|chaos — режим\n"
        "/scenario mixed|bpla|missile|aviation|artillery — сценарий\n"
        "/active — активные ветки\n"
        "/clear_active — очистить активные ветки"
    )


@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    data = state.data
    enabled = "включен" if data.get("enabled", True) else "пауза"
    active_count = len(data.get("active_incidents", []))

    await update.message.reply_text(
        f"Статус: {enabled}\n"
        f"Канал: {data.get('channel_id')}\n"
        f"Интервал: {data.get('min_interval')}–{data.get('max_interval')} мин.\n"
        f"Режим: {data.get('mode')}\n"
        f"Сценарий: {data.get('scenario')}\n"
        f"Активных веток: {active_count}"
    )


@admin_only
async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    text = generate_event(state.data, commit=False)
    await update.message.reply_text(f"Предпросмотр:\n\n{text}")


@admin_only
async def cmd_sample(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)

    try:
        count = int(context.args[0]) if context.args else 5
    except ValueError:
        count = 5

    count = max(1, min(count, 10))
    samples = []
    for i in range(count):
        samples.append(f"{i + 1})\n{generate_event(state.data, commit=False)}")

    await update.message.reply_text("\n\n———\n\n".join(samples))


@admin_only
async def cmd_post_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    text = generate_event(state.data, commit=True)
    state.save()
    await send_to_channel(context, text)
    await update.message.reply_text(f"Опубликовано:\n\n{text}")


@admin_only
async def cmd_custom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Использование: /custom текст поста")
        return

    await send_to_channel(context, text)
    await update.message.reply_text("Свое сообщение отправлено в канал.")


@admin_only
async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    state.set("enabled", False)
    await update.message.reply_text("Автопостинг остановлен.")


@admin_only
async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    state.set("enabled", True)
    await update.message.reply_text("Автопостинг включен.")


@admin_only
async def cmd_set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Использование: /set_interval 15 45")
        return

    try:
        mn = int(context.args[0])
        mx = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Интервал должен быть числами.")
        return

    mn = max(1, mn)
    mx = max(mn, mx)

    state = get_state(context)
    state.data["min_interval"] = mn
    state.data["max_interval"] = mx
    state.save()

    await update.message.reply_text(f"Интервал изменен: {mn}–{mx} мин.")


@admin_only
async def cmd_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /set_channel -1004449922425")
        return

    try:
        channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID канала должен быть числом.")
        return

    state = get_state(context)
    state.set("channel_id", channel_id)
    await update.message.reply_text(f"Канал изменен: {channel_id}")


@admin_only
async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = {"calm", "normal", "hot", "chaos"}
    if len(context.args) != 1 or context.args[0] not in allowed:
        await update.message.reply_text("Использование: /mode calm|normal|hot|chaos")
        return

    state = get_state(context)
    state.set("mode", context.args[0])
    await update.message.reply_text(f"Режим изменен: {context.args[0]}")


@admin_only
async def cmd_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = {"mixed", "bpla", "missile", "aviation", "artillery"}
    if len(context.args) != 1 or context.args[0] not in allowed:
        await update.message.reply_text("Использование: /scenario mixed|bpla|missile|aviation|artillery")
        return

    state = get_state(context)
    state.set("scenario", context.args[0])
    await update.message.reply_text(f"Сценарий изменен: {context.args[0]}")


@admin_only
async def cmd_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    await update.message.reply_text(format_active(state.data))


@admin_only
async def cmd_clear_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    state.clear_active()
    await update.message.reply_text("Активные ветки очищены.")


def build_application() -> Application:
    config = load_config()

    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    defaults = {
        "enabled": True,
        "channel_id": config.target_chat_id,
        "min_interval": config.min_interval,
        "max_interval": config.max_interval,
        "mode": config.mode,
        "scenario": config.scenario,
        "active_incidents": [],
        "last_posts": [],
    }

    state = BotState(config.state_file, defaults)

    app = Application.builder().token(config.bot_token).post_init(on_startup).build()
    app.bot_data["config"] = config
    app.bot_data["state"] = state

    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("preview", cmd_preview))
    app.add_handler(CommandHandler("sample", cmd_sample))
    app.add_handler(CommandHandler("post_now", cmd_post_now))
    app.add_handler(CommandHandler("custom", cmd_custom))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("set_interval", cmd_set_interval))
    app.add_handler(CommandHandler("set_channel", cmd_set_channel))
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(CommandHandler("scenario", cmd_scenario))
    app.add_handler(CommandHandler("active", cmd_active))
    app.add_handler(CommandHandler("clear_active", cmd_clear_active))

    return app


def main() -> None:
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
