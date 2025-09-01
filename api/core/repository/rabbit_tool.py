import pika
import json
from typing import Callable, Optional, Dict, Any
import config 
from api.core.middleware.logging import logger
from typing import List
class RabbitTool:
    def __init__(
        self,
        host: str = config.RABBIT_HOST,
        port: int = config.RABBIT_PORT,
        username: str = config.RABBIT_USERNAME,
        password: str = config.RABBIT_PASSWORD,
        virtual_host: str = "/"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.connection = None
        self.channel = None

    def __enter__(self) -> "RabbitTool":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def is_connected(self) -> bool:
        """Check if the connection to RabbitMQ is established."""
        return self.connection is not None and not self.connection.is_closed

    def connect(self) -> None:
        """Establish connection to RabbitMQ server."""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.debug("Successfully connected to RabbitMQ")

    def close(self) -> None:
        """Close the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.debug("RabbitMQ connection closed")

    def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any]
                ) -> None:
        """
        Publish a message to RabbitMQ.
        
        Args:
            exchange: Name of the exchange
            routing_key: Routing key for the message
            message: Message to be published (will be converted to JSON)
            exchange_type: Type of exchange (default: direct)
            durable: Whether the exchange should be durable
        """
        if not self.connection or self.connection.is_closed:
            self.connect()
        #logger.info(f"Publishing message to exchange '{exchange}' with routing key '{routing_key}' {message}")
        # Convert message to JSON
        message_body = json.dumps(message)

        # Publish message
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json',
                type=routing_key
            )
        )
        #logger.info(f"Message published to exchange '{exchange}' with routing key '{routing_key}'")

    def consume(
        self,
        queue_name: str,
        callback: Callable,
        exchange: Optional[str] = None,
        routing_key: Optional[str] = None,
        auto_ack: bool = False
    ) -> None:
        """
        Start consuming messages from a queue.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Function to be called when a message is received
            exchange: Name of the exchange to bind to (optional)
            routing_key: Routing key for binding (optional)
            exchange_type: Type of exchange (default: direct)
            durable: Whether the queue should be durable
            auto_ack: Whether to automatically acknowledge messages
        """
        if not self.connection or self.connection.is_closed:
            self.connect()

        if exchange:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue_name,
                routing_key=routing_key or queue_name
            )

        def message_handler(ch, method, properties, body):
            try:
                logger.debug(f"Received message from queue '{queue_name}': {body}")
                message = json.loads(body)
                callback(message,properties=properties)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode message: {body}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag,requeue=auto_ack)

            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}", exc_info=True)
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag,requeue=auto_ack)

        # Start consuming
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=message_handler,
            auto_ack=auto_ack
        )
        
        logger.info(f"Started consuming messages from queue '{queue_name}'")
        self.channel.start_consuming()

    def create(
        self,
        exchange: str,
        queue_name: str,
        routing_key: Optional[List] = None,
        exchange_type: str = "direct",
        durable: bool = True
    ) -> None:
        """
        Create exchange and queue if they don't exist.
        
        Args:
            exchange: Name of the exchange
            queue_name: Name of the queue
            routing_key: Routing key for binding (defaults to queue_name if not provided)
            exchange_type: Type of exchange (default: direct)
            durable: Whether the exchange and queue should be durable
        """
        if not self.connection or self.connection.is_closed:
            self.connect()

        # Declare exchange
        self.channel.exchange_declare(
            exchange=exchange,
            exchange_type=exchange_type,
            durable=durable
        )
        self.channel.exchange_declare(
            exchange=f"{exchange}.dlx",
            exchange_type=exchange_type,
            durable=durable
        )
        args = {
            'x-dead-letter-exchange': f"{exchange}.dlx",
            'x-dead-letter-routing-key': f"{queue_name}.dlq"
        }
        # Declare queue
        self.channel.queue_declare(
            queue=queue_name,
            durable=durable,
            arguments=args
        )
        self.channel.queue_declare(
            queue=f"{queue_name}.dlq",
            durable=durable
        )
        self.channel.queue_bind(
                exchange=f"{exchange}.dlx",
                queue=f"{queue_name}.dlq",
                routing_key=f"{queue_name}.dlq"
            )
        for rk in routing_key:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue_name,
                routing_key=rk
            )

        logger.info(f"Created exchange '{exchange}' and queue '{queue_name}' with routing key '{routing_key}'")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
