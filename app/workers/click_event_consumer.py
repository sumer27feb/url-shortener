
import asyncio
import logging
import sys

from confluent_kafka import Consumer, KafkaException
from pydantic import ValidationError

from app.core.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CLICKS_TOPIC,
    KAFKA_CLICK_CONSUMER_GROUP,
)
from app.db.repositories.click_event_repository import (
    insert_click_event,
)
from app.db.session import AsyncLocalSession, engine
from app.schemas.click_events import LinkClickedEvent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


def create_consumer() -> Consumer:
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_CLICK_CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "enable.auto.offset.store": False,
        "broker.address.family": "v4",
    })


async def persist_event(event: LinkClickedEvent) -> bool:
    async with AsyncLocalSession() as db:
        async with db.begin():
            inserted = await insert_click_event(
                db=db,
                event=event,
            )

    # Leaving db.begin() successfully commits the transaction.
    return inserted


def commit_message(consumer: Consumer, message) -> None:
    partitions = consumer.commit(
        message=message,
        asynchronous=False,
    )

    if not partitions:
        raise RuntimeError("Kafka offset commit returned no result")

    for partition in partitions:
        if partition.error is not None:
            raise KafkaException(partition.error)


async def run_consumer() -> None:
    consumer = create_consumer()
    consumer.subscribe([KAFKA_CLICKS_TOPIC])

    logger.info(
        "Consumer started: topic=%s group=%s",
        KAFKA_CLICKS_TOPIC,
        KAFKA_CLICK_CONSUMER_GROUP,
    )

    try:
        while True:
            message = consumer.poll(timeout=1.0)

            if message is None:
                continue

            if message.error():
                raise KafkaException(message.error())

            try:
                event = LinkClickedEvent.model_validate_json(
                    message.value()
                )

            except ValidationError as exc:
                logger.warning(
                    "Skipping invalid event at partition=%s "
                    "offset=%s: %s",
                    message.partition(),
                    message.offset(),
                    exc,
                )

                # Explicitly acknowledge malformed records.
                commit_message(consumer, message)
                continue

            # PostgreSQL failures propagate and stop the worker.
            # The Kafka offset is not committed in that case.
            try:
                inserted = await persist_event(event)

            except Exception:
                logger.exception(
                    "Database persistence failed for event %s",
                    event.event_id,
                )
                raise

            # This happens only after the DB transaction commits.
            commit_message(consumer, message)

            if inserted:
                logger.info(
                    "Stored click event %s for %s",
                    event.event_id,
                    event.link.short_code,
                )
            else:
                logger.info(
                    "Duplicate event %s ignored",
                    event.event_id,
                )

    finally:
        consumer.close()
        await engine.dispose()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )

    try:
        asyncio.run(run_consumer())

    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
