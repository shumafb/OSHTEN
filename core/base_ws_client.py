import asyncio
import json
import logging

import websockets


class BaseWSClient:
    """
    Базовый класс для работы с WebSocket соединениями.
    Обеспечивает подключение, переподключение, подписку и обработку сообщений.

    Attributes:
        url (str): URL для WebSocket подключения
        subscribe_payload (dict): Данные для отправки при подписке
        name (str): Имя клиента для логирования
        message_handler (callable): Функция обработки входящих сообщений
        ws (websockets.WebSocketClientProtocol): Объект WebSocket соединения
        reconnect_delay (int): Задержка в секундах перед повторным подключением
    """

    def __init__(self, url: str, subscribe_payload: dict, name: str, message_handler):
        """
        Инициализация WebSocket клиента.

        Args:
            url (str): URL для подключения к WebSocket серверу
            subscribe_payload (dict): Данные для отправки при подписке
            name (str): Имя клиента для идентификации в логах
            message_handler (callable): Функция обработки входящих сообщений
        """
        self.url = url
        self.subscribe_payload = subscribe_payload
        self.name = name
        self.message_handler = message_handler
        self.ws = None
        self.reconnect_delay = 5  # seconds

    async def connect(self):
        """
        Устанавливает и поддерживает WebSocket соединение.
        
        Автоматически переподключается при обрыве связи с заданной задержкой.
        Настраивает ping/pong для проверки активности соединения.
        """
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=10) as ws:
                    self.ws = ws
                    logging.info(f"[{self.name}] Подключено к {self.url}")
                    await self.subscribe()
                    await self.listen()
            except Exception as e:
                logging.warning(f"[{self.name}] Ошибка подключения: {e}")
                logging.info(f"[{self.name}] Повторное подключение через {self.reconnect_delay} секунд...")
                await asyncio.sleep(self.reconnect_delay)

    async def subscribe(self):
        """
        Отправляет данные подписки на сервер.
        
        Сериализует payload в JSON и отправляет через WebSocket соединение.
        Логирует отправленные данные.
        """
        msg = json.dumps(self.subscribe_payload)
        await self.ws.send(msg)
        logging.info(f"[{self.name}] Подписка с payload: {msg}")

    async def listen(self):
        """
        Прослушивает входящие сообщения.
        
        Асинхронно читает сообщения из WebSocket соединения,
        десериализует их из JSON и передает в handler.
        Обрабатывает ошибки при получении и обработке сообщений.
        """
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self.message_handler(data)
            except Exception as e:
                logging.error(f"[{self.name}] Ошибка обработки сообщения: {e}")
