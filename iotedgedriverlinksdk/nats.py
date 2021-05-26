import asyncio
import json
import os
import queue
import random
import signal
import string
import sys
import threading
import time

from nats.aio.client import Client as NATS
from nats.aio.errors import NatsError
from iotedgedriverlinksdk import _driver_id, getLogger

_logger = getLogger()


def exit_handler(signum, frame):
    sys.exit(0)


_nat_publish_queue = queue.Queue()
_nat_client_publish_queue = queue.Queue()
_nat_subscribe_queue = queue.Queue()


class _natsPublish(object):
    def __init__(self):
        self.url = os.environ.get(
            'IOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _publish(self):
        global _nat_client_publish_queue
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            _logger.error(e1)
            sys.exit(1)

        while True:
            try:
                msg = _nat_client_publish_queue.get()
                bty = msg['payload']
                await self.nc.publish(subject=msg['subject'],
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except NatsError as e:
                _logger.error(e)
            except Exception as e:
                _logger.error(e)

    def start(self):
        self.loop.run_until_complete(self._publish())


class _natsClientPub(object):
    def __init__(self):
        self.url = os.environ.get(
            'IOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _publish(self):
        global _nat_publish_queue
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            _logger.error(e1)
            sys.exit(1)

        while True:
            try:
                msg = _nat_publish_queue.get()
                bty = json.dumps(msg['payload'])
                await self.nc.publish(subject=msg['subject'],
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except NatsError as e:
                _logger.error(e)
            except Exception as e:
                _logger.error(e)

    def start(self):
        self.loop.run_until_complete(self._publish())
        # self.loop.run_forever()


class _natsClientSub(object):
    def __init__(self):
        self.url = os.environ.get(
            'IOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _connect(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            _logger.error(e1)
            sys.exit(1)

        async def message_handler(msg):
            global _nat_subscribe_queue
            _nat_subscribe_queue.put(msg)
        await self.nc.subscribe("edge.local."+_driver_id, queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.local.broadcast", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.state.reply", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.flush()

    def start(self):
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()


class _natsSubscribe(object):
    def __init__(self, subject: str, queue: str, cb):
        self.url = os.environ.get(
            'IOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()
        self.cb = cb
        self.subject = subject
        self.queue = queue

    async def _connect(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            _logger.error(e1)
            sys.exit(1)
        await self.nc.subscribe(self.subject, queue=self.queue, cb=self.cb, is_async=True)
        await self.nc.flush()

    def start(self):
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()


def _publish_nats_msg(msg):
    global _nat_publish_queue
    data = {
        'subject': 'edge.router.'+_driver_id,
        'payload': msg
    }
    _nat_publish_queue.put(data)


def natsPublish(subject: str, payload: bytes):
    global _nat_client_publish_queue
    data = {
        'subject': subject,
        'payload': payload
    }
    _nat_client_publish_queue.put(data)


def natsSubscribe(subject, queue, cb):
    def _nats_sub():
        _natsSubscribe(subject, queue, cb).start()
    t = threading.Thread(target=_nats_sub)
    t.setDaemon(True)
    t.start()


def _start_pub():
    _natsClientPub().start()


def _nats_pub():
    _natsPublish().start()


def _start_sub():
    _natsClientSub().start()


_t_pub = threading.Thread(target=_nats_pub)
_t_pub.setDaemon(True)
_t_pub.start()

_t_nats_pub = threading.Thread(target=_start_pub)
_t_nats_pub.setDaemon(True)
_t_nats_pub.start()

_t_nats_sub = threading.Thread(target=_start_sub)
_t_nats_sub.setDaemon(True)
_t_nats_sub.start()
