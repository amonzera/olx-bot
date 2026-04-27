from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.bot.commands import (
    HELP_TEXT,
    command_payload,
    format_alert,
    parse_alert_id,
    parse_alert_payload,
    parse_edit_payload,
)
from src.core.config import settings
from src.notifiers.telegram import TelegramNotifier
from src.scraper.client import OLXClient
from src.services.analyzer import OpportunityAnalyzer
from src.services.monitor import LocalMonitor, MonitorResult
from src.storage.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)


class ScanService:
    def __init__(self, monitor: LocalMonitor, repository: SQLiteRepository):
        self.monitor = monitor
        self.repository = repository
        self._lock = asyncio.Lock()

    async def scan_alert(self, alert_id: int) -> MonitorResult | None:
        alert = self.repository.get_alert(alert_id)
        if alert is None or not alert.active:
            return None

        async with self._lock:
            result = await asyncio.to_thread(self.monitor.scan_once, alert.to_config())
            self.repository.mark_alert_scanned(alert.id)
            return result


class AlertScheduler:
    def __init__(
        self,
        repository: SQLiteRepository,
        scanner: ScanService,
        *,
        interval_seconds: int,
        delay_between_alerts_seconds: int,
    ):
        self.repository = repository
        self.scanner = scanner
        self.interval_seconds = interval_seconds
        self.delay_between_alerts_seconds = delay_between_alerts_seconds

    async def run_forever(self) -> None:
        await asyncio.sleep(5)
        while True:
            alerts = self.repository.list_active_alerts()
            for alert in alerts:
                try:
                    result = await self.scanner.scan_alert(alert.id)
                    if result is not None:
                        logger.info(
                            "Alert scan completed",
                            extra={
                                "alert_id": alert.id,
                                "fetched": result.fetched_count,
                                "notified": result.notified_count,
                            },
                        )
                except Exception:
                    logger.exception("Alert scan failed", extra={"alert_id": alert.id})

                await asyncio.sleep(self.delay_between_alerts_seconds)

            await asyncio.sleep(self.interval_seconds)


def build_router(repository: SQLiteRepository, scanner: ScanService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            "Monitor local da OLX iniciado.\n\n"
            "Use /add para criar um alerta. A busca inicial acontece assim que o alerta é salvo.\n\n"
            f"{HELP_TEXT}"
        )

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(HELP_TEXT)

    @router.message(Command("add"))
    async def add_alert(message: Message) -> None:
        try:
            draft = parse_alert_payload(command_payload(message.text))
        except ValueError as exc:
            await message.answer(str(exc))
            return

        alert = repository.create_alert(
            chat_id=str(message.chat.id),
            search_term=draft.search_term,
            location=draft.location,
            min_price_cents=draft.min_price_cents,
            max_price_cents=draft.max_price_cents,
            max_age_days=settings.MAX_LISTING_AGE_DAYS,
        )
        await message.answer(
            f"Alerta criado:\n\n{format_alert(alert)}\n\nVou buscar as ofertas iniciais agora."
        )
        await scan_and_report(message, scanner, alert.id)

    @router.message(Command("list"))
    async def list_alerts(message: Message) -> None:
        alerts = repository.list_alerts(str(message.chat.id))
        if not alerts:
            await message.answer("Você ainda não tem alertas. Use /add para criar o primeiro.")
            return

        await message.answer("\n\n".join(format_alert(alert) for alert in alerts))

    @router.message(Command("edit"))
    async def edit_alert(message: Message) -> None:
        try:
            alert_id, draft = parse_edit_payload(command_payload(message.text))
        except ValueError as exc:
            await message.answer(str(exc))
            return

        alert = repository.update_alert(
            alert_id=alert_id,
            chat_id=str(message.chat.id),
            search_term=draft.search_term,
            location=draft.location,
            min_price_cents=draft.min_price_cents,
            max_price_cents=draft.max_price_cents,
            max_age_days=settings.MAX_LISTING_AGE_DAYS,
        )
        if alert is None:
            await message.answer("Não encontrei esse alerta para o seu chat.")
            return

        await message.answer(
            f"Alerta atualizado:\n\n{format_alert(alert)}\n\nVou buscar com os novos filtros."
        )
        if alert.active:
            await scan_and_report(message, scanner, alert.id)

    @router.message(Command("delete"))
    async def delete_alert(message: Message) -> None:
        try:
            alert_id = parse_alert_id(command_payload(message.text))
        except ValueError as exc:
            await message.answer(str(exc))
            return

        deleted = repository.delete_alert(alert_id=alert_id, chat_id=str(message.chat.id))
        if deleted:
            await message.answer(f"Alerta #{alert_id} excluído.")
        else:
            await message.answer("Não encontrei esse alerta para o seu chat.")

    @router.message(Command("pause"))
    async def pause_alert(message: Message) -> None:
        await set_alert_active(message, repository, active=False)

    @router.message(Command("resume"))
    async def resume_alert(message: Message) -> None:
        await set_alert_active(message, repository, active=True)

    return router


async def scan_and_report(message: Message, scanner: ScanService, alert_id: int) -> None:
    result = await scanner.scan_alert(alert_id)
    if result is None:
        await message.answer("O alerta não está ativo ou não existe mais.")
        return

    await message.answer(
        "Busca concluída: "
        f"{result.fetched_count} anúncios lidos, "
        f"{result.analyzed_count} analisados, "
        f"{result.notified_count} notificações enviadas."
    )


async def set_alert_active(message: Message, repository: SQLiteRepository, *, active: bool) -> None:
    try:
        alert_id = parse_alert_id(command_payload(message.text))
    except ValueError as exc:
        await message.answer(str(exc))
        return

    updated = repository.set_alert_active(
        alert_id=alert_id,
        chat_id=str(message.chat.id),
        active=active,
    )
    if not updated:
        await message.answer("Não encontrei esse alerta para o seu chat.")
        return

    status = "reativado" if active else "pausado"
    await message.answer(f"Alerta #{alert_id} {status}.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if not settings.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Configure TELEGRAM_BOT_TOKEN no .env antes de iniciar o bot.")

    repository = SQLiteRepository(settings.sqlite_path)
    client = OLXClient()
    scanner = ScanService(
        monitor=LocalMonitor(
            client=client,
            analyzer=OpportunityAnalyzer(),
            repository=repository,
            notifier=TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID or None),
        ),
        repository=repository,
    )
    scheduler = AlertScheduler(
        repository=repository,
        scanner=scanner,
        interval_seconds=settings.SCAN_INTERVAL_SECONDS,
        delay_between_alerts_seconds=settings.DELAY_BETWEEN_ALERT_REQUESTS_SECONDS,
    )

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(repository, scanner))

    scheduler_task = asyncio.create_task(scheduler.run_forever())
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
        await bot.session.close()
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
