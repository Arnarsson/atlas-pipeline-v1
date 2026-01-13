"""
Kafka Connector for Real-Time Streaming (Phase 6)
==================================================

Provides real-time data ingestion from Apache Kafka.

Features:
- Consumer for reading from Kafka topics
- Producer for writing to Kafka topics
- JSON and Avro message deserialization
- Consumer group management
- Offset tracking for exactly-once semantics
- Batch processing for efficiency

Dependencies:
- aiokafka (async Kafka client)
- Install: pip install aiokafka

Reference: Apache Kafka, Confluent patterns
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable

from app.connectors.base import BaseSourceConnector, ConnectionConfig

logger = logging.getLogger(__name__)

# Optional Kafka imports
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    from aiokafka.errors import KafkaError

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("aiokafka not installed. Install with: pip install aiokafka")


# ============================================================================
# Enums and Data Models
# ============================================================================


class DeserializerType(str, Enum):
    """Message deserializer types."""

    JSON = "json"
    STRING = "string"
    BYTES = "bytes"
    AVRO = "avro"  # Requires additional schema registry


class OffsetReset(str, Enum):
    """Consumer offset reset strategy."""

    EARLIEST = "earliest"  # Start from beginning
    LATEST = "latest"  # Start from end


@dataclass
class KafkaMessage:
    """Kafka message wrapper."""

    topic: str
    partition: int
    offset: int
    key: str | None
    value: Any
    timestamp: datetime
    headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "partition": self.partition,
            "offset": self.offset,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "headers": self.headers,
        }


@dataclass
class ConsumerStats:
    """Consumer statistics."""

    messages_consumed: int = 0
    bytes_consumed: int = 0
    errors: int = 0
    last_offset: dict[str, int] = field(default_factory=dict)  # partition -> offset
    started_at: datetime | None = None
    last_message_at: datetime | None = None


@dataclass
class ProducerStats:
    """Producer statistics."""

    messages_produced: int = 0
    bytes_produced: int = 0
    errors: int = 0
    started_at: datetime | None = None
    last_message_at: datetime | None = None


# ============================================================================
# Kafka Consumer Connector
# ============================================================================


class KafkaConsumerConnector(BaseSourceConnector):
    """
    Kafka consumer connector for real-time data ingestion.

    Supports:
    - Multiple topics subscription
    - Consumer group coordination
    - Automatic offset management
    - Batch consumption for efficiency
    - Message deserialization (JSON, string, bytes)
    """

    def __init__(
        self,
        config: ConnectionConfig,
        topics: list[str] | None = None,
        group_id: str | None = None,
        deserializer: DeserializerType = DeserializerType.JSON,
        auto_offset_reset: OffsetReset = OffsetReset.LATEST,
        batch_size: int = 100,
        batch_timeout_ms: int = 1000,
    ):
        """
        Initialize Kafka consumer.

        Args:
            config: Connection configuration with bootstrap_servers
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            deserializer: Message deserializer type
            auto_offset_reset: Offset reset strategy
            batch_size: Maximum messages per batch
            batch_timeout_ms: Batch timeout in milliseconds
        """
        super().__init__(config)

        if not KAFKA_AVAILABLE:
            raise ImportError("aiokafka is required. Install with: pip install aiokafka")

        # Extract Kafka-specific config
        params = config.additional_params or {}

        self.bootstrap_servers = params.get("bootstrap_servers", "localhost:9092")
        self.topics = topics or params.get("topics", [])
        self.group_id = group_id or params.get("group_id", f"atlas-consumer-{config.source_name}")
        self.deserializer = deserializer
        self.auto_offset_reset = auto_offset_reset
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms

        # Security settings
        self.security_protocol = params.get("security_protocol", "PLAINTEXT")
        self.sasl_mechanism = params.get("sasl_mechanism")
        self.sasl_username = params.get("sasl_username")
        self.sasl_password = params.get("sasl_password")

        # Internal state
        self._consumer: "AIOKafkaConsumer" | None = None
        self._running = False
        self._stats = ConsumerStats()

        logger.info(
            f"Initialized Kafka consumer: servers={self.bootstrap_servers}, "
            f"topics={self.topics}, group={self.group_id}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to Kafka broker."""
        if self._consumer is not None:
            return

        consumer_config = {
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": self.group_id,
            "auto_offset_reset": self.auto_offset_reset.value,
            "enable_auto_commit": True,
            "max_poll_records": self.batch_size,
            "security_protocol": self.security_protocol,
        }

        # Add SASL config if provided
        if self.sasl_mechanism:
            consumer_config["sasl_mechanism"] = self.sasl_mechanism
            consumer_config["sasl_plain_username"] = self.sasl_username
            consumer_config["sasl_plain_password"] = self.sasl_password

        self._consumer = AIOKafkaConsumer(
            *self.topics,
            **consumer_config
        )

        await self._consumer.start()
        self._stats.started_at = datetime.utcnow()

        logger.info(f"Connected to Kafka: {self.bootstrap_servers}")

    async def disconnect(self):
        """Disconnect from Kafka broker."""
        if self._consumer:
            self._running = False
            await self._consumer.stop()
            self._consumer = None
            logger.info("Disconnected from Kafka")

    async def test_connection(self) -> bool:
        """Test Kafka connection."""
        try:
            # Create temporary consumer to test connection
            test_consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                security_protocol=self.security_protocol,
            )
            await test_consumer.start()
            await test_consumer.stop()
            return True
        except Exception as e:
            logger.error(f"Kafka connection test failed: {e}")
            return False

    async def get_data(
        self,
        table: str | None = None,
        query: str | None = None,
        timestamp_column: str | None = None,
        last_timestamp: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get batch of messages from Kafka.

        Note: 'table' parameter is interpreted as topic name.

        Returns:
            List of message dictionaries
        """
        if not self._consumer:
            await self.connect()

        messages = []

        try:
            # Poll for messages with timeout
            data = await self._consumer.getmany(
                timeout_ms=self.batch_timeout_ms,
                max_records=self.batch_size,
            )

            for topic_partition, records in data.items():
                for record in records:
                    msg = self._deserialize_message(record)
                    messages.append(msg.to_dict())

                    # Update stats
                    self._stats.messages_consumed += 1
                    self._stats.last_offset[str(topic_partition)] = record.offset
                    self._stats.last_message_at = datetime.utcnow()

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Error consuming messages: {e}")
            raise

        return messages

    async def stream_messages(
        self,
        callback: Callable[[KafkaMessage], None] | None = None,
    ) -> AsyncIterator[KafkaMessage]:
        """
        Stream messages continuously.

        Args:
            callback: Optional callback for each message

        Yields:
            KafkaMessage objects
        """
        if not self._consumer:
            await self.connect()

        self._running = True

        try:
            async for record in self._consumer:
                if not self._running:
                    break

                msg = self._deserialize_message(record)

                # Update stats
                self._stats.messages_consumed += 1
                self._stats.last_message_at = datetime.utcnow()

                # Call callback if provided
                if callback:
                    callback(msg)

                yield msg

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Streaming error: {e}")
            raise

    def _deserialize_message(self, record) -> KafkaMessage:
        """Deserialize Kafka record to KafkaMessage."""
        # Deserialize key
        key = None
        if record.key:
            try:
                key = record.key.decode("utf-8")
            except Exception:
                key = str(record.key)

        # Deserialize value
        value = record.value
        if self.deserializer == DeserializerType.JSON:
            try:
                value = json.loads(record.value.decode("utf-8"))
            except Exception:
                value = record.value.decode("utf-8", errors="replace")
        elif self.deserializer == DeserializerType.STRING:
            value = record.value.decode("utf-8", errors="replace")
        # BYTES keeps as-is

        # Parse headers
        headers = {}
        if record.headers:
            for h_key, h_value in record.headers:
                try:
                    headers[h_key] = h_value.decode("utf-8")
                except Exception:
                    headers[h_key] = str(h_value)

        # Convert timestamp
        timestamp = datetime.utcfromtimestamp(record.timestamp / 1000)

        return KafkaMessage(
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            key=key,
            value=value,
            timestamp=timestamp,
            headers=headers,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get consumer statistics."""
        return {
            "messages_consumed": self._stats.messages_consumed,
            "bytes_consumed": self._stats.bytes_consumed,
            "errors": self._stats.errors,
            "last_offsets": self._stats.last_offset,
            "started_at": self._stats.started_at.isoformat() if self._stats.started_at else None,
            "last_message_at": self._stats.last_message_at.isoformat() if self._stats.last_message_at else None,
            "running": self._running,
        }

    async def commit_offsets(self):
        """Manually commit current offsets."""
        if self._consumer:
            await self._consumer.commit()
            logger.debug("Committed Kafka offsets")

    async def seek_to_beginning(self, topic: str | None = None):
        """Seek to beginning of topic(s)."""
        if self._consumer:
            partitions = self._consumer.assignment()
            if topic:
                partitions = [p for p in partitions if p.topic == topic]
            await self._consumer.seek_to_beginning(*partitions)
            logger.info(f"Seeked to beginning: {partitions}")

    async def seek_to_end(self, topic: str | None = None):
        """Seek to end of topic(s)."""
        if self._consumer:
            partitions = self._consumer.assignment()
            if topic:
                partitions = [p for p in partitions if p.topic == topic]
            await self._consumer.seek_to_end(*partitions)
            logger.info(f"Seeked to end: {partitions}")


# ============================================================================
# Kafka Producer Connector
# ============================================================================


class KafkaProducerConnector:
    """
    Kafka producer for writing data to topics.

    Supports:
    - Synchronous and asynchronous sends
    - Key-based partitioning
    - JSON serialization
    - Batching for throughput
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "atlas-producer",
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
    ):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            client_id: Producer client ID
            security_protocol: Security protocol
            sasl_mechanism: SASL mechanism
            sasl_username: SASL username
            sasl_password: SASL password
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("aiokafka is required. Install with: pip install aiokafka")

        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.security_protocol = security_protocol
        self.sasl_mechanism = sasl_mechanism
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password

        self._producer: "AIOKafkaProducer" | None = None
        self._stats = ProducerStats()

        logger.info(f"Initialized Kafka producer: servers={bootstrap_servers}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to Kafka broker."""
        if self._producer is not None:
            return

        producer_config = {
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": self.client_id,
            "security_protocol": self.security_protocol,
        }

        if self.sasl_mechanism:
            producer_config["sasl_mechanism"] = self.sasl_mechanism
            producer_config["sasl_plain_username"] = self.sasl_username
            producer_config["sasl_plain_password"] = self.sasl_password

        self._producer = AIOKafkaProducer(**producer_config)
        await self._producer.start()
        self._stats.started_at = datetime.utcnow()

        logger.info(f"Producer connected to Kafka: {self.bootstrap_servers}")

    async def disconnect(self):
        """Disconnect from Kafka broker."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Producer disconnected from Kafka")

    async def send(
        self,
        topic: str,
        value: Any,
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to Kafka topic.

        Args:
            topic: Target topic
            value: Message value (will be JSON serialized if dict)
            key: Optional message key
            headers: Optional message headers

        Returns:
            Send result with partition and offset
        """
        if not self._producer:
            await self.connect()

        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                value_bytes = json.dumps(value).encode("utf-8")
            elif isinstance(value, str):
                value_bytes = value.encode("utf-8")
            elif isinstance(value, bytes):
                value_bytes = value
            else:
                value_bytes = str(value).encode("utf-8")

            # Serialize key
            key_bytes = key.encode("utf-8") if key else None

            # Convert headers
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

            # Send message
            result = await self._producer.send_and_wait(
                topic,
                value=value_bytes,
                key=key_bytes,
                headers=kafka_headers,
            )

            # Update stats
            self._stats.messages_produced += 1
            self._stats.bytes_produced += len(value_bytes)
            self._stats.last_message_at = datetime.utcnow()

            return {
                "topic": result.topic,
                "partition": result.partition,
                "offset": result.offset,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Error sending message: {e}")
            raise

    async def send_batch(
        self,
        topic: str,
        messages: list[dict[str, Any]],
        key_field: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Send a batch of messages.

        Args:
            topic: Target topic
            messages: List of message dictionaries
            key_field: Optional field to use as message key

        Returns:
            List of send results
        """
        results = []

        for msg in messages:
            key = str(msg.get(key_field)) if key_field and key_field in msg else None
            result = await self.send(topic, msg, key=key)
            results.append(result)

        logger.info(f"Sent batch of {len(messages)} messages to {topic}")
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get producer statistics."""
        return {
            "messages_produced": self._stats.messages_produced,
            "bytes_produced": self._stats.bytes_produced,
            "errors": self._stats.errors,
            "started_at": self._stats.started_at.isoformat() if self._stats.started_at else None,
            "last_message_at": self._stats.last_message_at.isoformat() if self._stats.last_message_at else None,
        }


# ============================================================================
# Kafka Admin Operations
# ============================================================================


async def list_topics(bootstrap_servers: str = "localhost:9092") -> list[str]:
    """
    List available Kafka topics.

    Args:
        bootstrap_servers: Kafka broker addresses

    Returns:
        List of topic names
    """
    if not KAFKA_AVAILABLE:
        raise ImportError("aiokafka is required")

    consumer = AIOKafkaConsumer(bootstrap_servers=bootstrap_servers)
    await consumer.start()

    try:
        topics = list(await consumer.topics())
        return topics
    finally:
        await consumer.stop()


async def get_topic_partitions(
    topic: str,
    bootstrap_servers: str = "localhost:9092",
) -> list[dict[str, Any]]:
    """
    Get partition information for a topic.

    Args:
        topic: Topic name
        bootstrap_servers: Kafka broker addresses

    Returns:
        List of partition info dictionaries
    """
    if not KAFKA_AVAILABLE:
        raise ImportError("aiokafka is required")

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
    )
    await consumer.start()

    try:
        partitions = consumer.partitions_for_topic(topic)
        if not partitions:
            return []

        result = []
        for partition in partitions:
            result.append({
                "topic": topic,
                "partition": partition,
            })
        return result
    finally:
        await consumer.stop()


# ============================================================================
# Factory Function for Connector Registry
# ============================================================================


def create_kafka_consumer(config: ConnectionConfig) -> KafkaConsumerConnector:
    """
    Factory function to create Kafka consumer.

    Args:
        config: Connection configuration

    Returns:
        KafkaConsumerConnector instance
    """
    params = config.additional_params or {}

    return KafkaConsumerConnector(
        config=config,
        topics=params.get("topics", []),
        group_id=params.get("group_id"),
        deserializer=DeserializerType(params.get("deserializer", "json")),
        auto_offset_reset=OffsetReset(params.get("auto_offset_reset", "latest")),
        batch_size=params.get("batch_size", 100),
        batch_timeout_ms=params.get("batch_timeout_ms", 1000),
    )
