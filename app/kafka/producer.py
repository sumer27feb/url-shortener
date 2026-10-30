
import asyncio
import logging
import os

from confluent_kafka.aio import AIOProducer

from app.core.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CLICKS_TOPIC,
)
from app.schemas.click_events import LinkClickedEvent


logger = logging.getLogger(__name__)


class ClickEventPublisher:
    def __init__(self):
        self._producer: AIOProducer | None = None

    def start(self) -> None:
        try:
            self._producer = AIOProducer({
                "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                "client.id": f"url-shortener-api-{os.getpid()}",
                "acks": "all",
                "enable.idempotence": True,
                "delivery.timeout.ms": 10000,
                "broker.address.family": "v4",
            })

            logger.warning(
                "[KAFKA] Producer initialized: %s",
                KAFKA_BOOTSTRAP_SERVERS,
            )

        except Exception:
            logger.exception("Kafka producer initialization failed")
            self._producer = None

    async def publish(self, event: LinkClickedEvent) -> None:
        logger.warning(
            "[KAFKA] publish() called for event %s",
            event.event_id,
        )
        if self._producer is None:
            logger.warning(
                "Kafka producer unavailable; dropping event %s",
                event.event_id,
            )
            return

        try:
            delivery_future = await self._producer.produce(
                topic=KAFKA_CLICKS_TOPIC,
                key=event.link.short_code.encode("utf-8"),
                value=event.model_dump_json().encode("utf-8"),
            )

            logger.warning(
                "[KAFKA] Event enqueued: %s",
                event.event_id,
            )

            delivery_future.add_done_callback(
                lambda future: self._on_delivery(
                    future,
                    str(event.event_id),
                )
            )

        except Exception:
            logger.exception(
                "Failed to enqueue Kafka event %s",
                event.event_id,
            )

    @staticmethod
    def _on_delivery(
        future: asyncio.Future,
        event_id: str,
    ) -> None:
        if future.cancelled():
            logger.warning(
                "Kafka delivery cancelled for event %s",
                event_id,
            )
            return

        try:
            message = future.result()

        except Exception:
            logger.exception(
                "Kafka delivery failed for event %s",
                event_id,
            )
            return

        logger.warning(
            "Kafka event %s delivered to partition %s, offset %s",
            event_id,
            message.partition(),
            message.offset(),
        )

    async def close(self) -> None:
        if self._producer is None:
            return

        try:
            await self._producer.close()

        except Exception:
            logger.exception("Error closing Kafka producer")

        finally:
            self._producer = None
