import json
import logging
import math
import os
import random
import signal
import socket
import threading
import time
from typing import Callable

import paho.mqtt.client as mqtt
from kafka import KafkaProducer
from prometheus_client import Gauge, start_http_server


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
)
LOG = logging.getLogger("alltest-source")
STOP = threading.Event()


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


INTERVAL = max(0.2, env_float("PUBLISH_INTERVAL_SECONDS", 1.0))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor_data_morse")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = env_int("MQTT_PORT", 1885)
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "mi/topic/elcm")
PROMETHEUS_EXPORTER_PORT = env_int("PROMETHEUS_EXPORTER_PORT", 8000)
TELEGRAF_ENABLED = env_bool("TELEGRAF_ENABLED", False)
TELEGRAF_HOST = os.getenv("TELEGRAF_HOST", "localhost")
TELEGRAF_PORT = env_int("TELEGRAF_PORT", 8094)


PROM_WINDOWS_NET_RX = Gauge("windows_net_bytes_received_total", "Synthetic received bytes.")
PROM_WINDOWS_NET_TX = Gauge("windows_net_bytes_sent_total", "Synthetic sent bytes.")
PROM_WINDOWS_DISK_WRITE = Gauge("windows_logical_disk_write_bytes_total", "Synthetic disk write bytes.")
PROM_WINDOWS_DISK_READ = Gauge("windows_logical_disk_read_bytes_total", "Synthetic disk read bytes.")
PROM_PROCESS_CPU = Gauge("alltest_process_cpu_seconds_total", "Synthetic CPU seconds with a distinct name.")


def install_signal_handlers():
    def _stop(_signum, _frame):
        STOP.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)


def wait_retry(name: str, connect: Callable[[], object], delay: float = 2.0):
    attempt = 0
    while not STOP.is_set():
        attempt += 1
        try:
            return connect()
        except Exception as exc:
            LOG.warning("%s not ready on attempt %s: %s", name, attempt, exc)
            STOP.wait(delay)
    return None


def metric_snapshot(i: int) -> dict:
    now = int(time.time())
    wave = math.sin(i / 8.0)
    temperature = round(23.0 + wave * 4.5 + random.uniform(-0.2, 0.2), 2)
    humidity = round(48.0 + math.cos(i / 10.0) * 8.0 + random.uniform(-0.4, 0.4), 2)
    rx = 1_000_000 + i * 45_000 + int(abs(wave) * 8_000)
    tx = 800_000 + i * 37_000 + int(abs(math.cos(i / 9.0)) * 7_000)
    disk_write = 500_000 + i * 21_000
    disk_read = 650_000 + i * 25_000
    cpu = round(100.0 + i * 0.7 + abs(wave), 3)
    used_mem = 2_000_000_000 + int((0.5 + wave / 2) * 400_000_000)
    return {
        "timestamp": now,
        "temperature": temperature,
        "humidity": humidity,
        "temperatura": temperature,
        "humedad": humidity,
        "rx": rx,
        "tx": tx,
        "disk_write": disk_write,
        "disk_read": disk_read,
        "cpu": cpu,
        "used_mem": used_mem,
    }


def kafka_loop():
    def connect():
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            linger_ms=50,
            retries=5,
        )

    producer = wait_retry("Kafka", connect)
    if producer is None:
        return
    LOG.info("Kafka producer connected to %s topic=%s", KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC)

    i = 0
    while not STOP.is_set():
        sample = metric_snapshot(i)
        payload = {
            "timestamp": sample["timestamp"],
            "temperature": sample["temperature"],
            "humidity": sample["humidity"],
            "sensor": "kafka_sensor_01",
        }
        try:
            producer.send(KAFKA_TOPIC, payload)
            producer.flush(timeout=5)
        except Exception as exc:
            LOG.warning("Kafka publish failed: %s", exc)
        i += 1
        STOP.wait(INTERVAL)

    producer.close(timeout=5)


def mqtt_loop():
    client = mqtt.Client(client_id=f"alltest-source-{random.randint(1000, 9999)}")

    def connect():
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
        client.loop_start()
        return client

    connected = wait_retry("MQTT", connect)
    if connected is None:
        return
    LOG.info("MQTT publisher connected to %s:%s topic=%s", MQTT_HOST, MQTT_PORT, MQTT_TOPIC)

    i = 0
    while not STOP.is_set():
        sample = metric_snapshot(i)
        payload = {
            "timestamp": sample["timestamp"],
            "temperatura": sample["temperatura"],
            "humedad": sample["humedad"],
            "sensor": "mqtt_sensor_01",
        }
        result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=0)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOG.warning("MQTT publish returned rc=%s", result.rc)
        i += 1
        STOP.wait(INTERVAL)

    client.loop_stop()
    client.disconnect()


def prometheus_loop():
    start_http_server(PROMETHEUS_EXPORTER_PORT, addr="0.0.0.0")
    LOG.info("Prometheus exporter listening on :%s", PROMETHEUS_EXPORTER_PORT)
    i = 0
    while not STOP.is_set():
        sample = metric_snapshot(i)
        PROM_WINDOWS_NET_RX.set(sample["rx"])
        PROM_WINDOWS_NET_TX.set(sample["tx"])
        PROM_WINDOWS_DISK_WRITE.set(sample["disk_write"])
        PROM_WINDOWS_DISK_READ.set(sample["disk_read"])
        PROM_PROCESS_CPU.set(sample["cpu"])
        i += 1
        STOP.wait(INTERVAL)


def telegraf_loop():
    if not TELEGRAF_ENABLED:
        LOG.info("Telegraf sender disabled")
        return

    i = 0
    sock = None
    while not STOP.is_set():
        if sock is None:
            try:
                sock = socket.create_connection((TELEGRAF_HOST, TELEGRAF_PORT), timeout=5)
                LOG.info("Telegraf sender connected to %s:%s", TELEGRAF_HOST, TELEGRAF_PORT)
            except Exception as exc:
                LOG.warning("Telegraf endpoint not ready: %s", exc)
                STOP.wait(3)
                continue

        sample = metric_snapshot(i)
        payload = {
            "timestamp": sample["timestamp"],
            "used_mem": sample["used_mem"],
            "available_mem": 4_000_000_000 - sample["used_mem"],
            "source": "alltest-source",
        }
        try:
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        except Exception as exc:
            LOG.warning("Telegraf send failed: %s", exc)
            try:
                sock.close()
            except Exception:
                pass
            sock = None
        i += 1
        STOP.wait(INTERVAL)

    if sock is not None:
        try:
            sock.close()
        except Exception:
            pass


def main():
    install_signal_handlers()
    LOG.info("Starting ALLTEST metrics source")
    threads = [
        threading.Thread(target=prometheus_loop, name="prometheus", daemon=True),
        threading.Thread(target=kafka_loop, name="kafka", daemon=True),
        threading.Thread(target=mqtt_loop, name="mqtt", daemon=True),
        threading.Thread(target=telegraf_loop, name="telegraf", daemon=True),
    ]
    for thread in threads:
        thread.start()
    while not STOP.is_set():
        STOP.wait(1)
    for thread in threads:
        thread.join(timeout=8)
    LOG.info("ALLTEST metrics source stopped")


if __name__ == "__main__":
    main()
