# Metrics

Private ALLTEST metrics stack for ELCM.

This repository provides a Docker image, `elcm-alltest-source`, plus a Compose stack
that lets ELCM test these collectors:

- `Run.KafkaConsumerToInflux`
- `Run.MqttToInflux`
- `Run.PrometheusToInflux`

The Python source image publishes synthetic sensor values to Kafka and MQTT, exposes
Windows-like Prometheus metrics, and can optionally send Telegraf-style JSON to ELCM.

## Start

```powershell
docker compose up -d --build
```

Services exposed on the host:

- Kafka: `9092`
- MQTT: `1885`
- Prometheus: `9090`
- Raw exporter debug endpoint: `8000`

Prometheus should be available at:

```text
http://localhost:9090
```

## Use With ELCM In Docker Desktop

Use [samples/ALLTEST_DOCKER.yml](samples/ALLTEST_DOCKER.yml). It points Kafka, MQTT
and Prometheus to `host.docker.internal`, which ELCM containers can resolve on Docker
Desktop.

For Kafka, the broker advertises `host.docker.internal:9092` by default. If ELCM runs
outside Docker or from another VM, start the stack with an address that the ELCM process
can reach:

```powershell
$env:ALLTEST_KAFKA_ADVERTISED_HOST="192.168.239.131"
docker compose up -d --build
```

Then use that same host/IP in the testcase for Kafka `Ip`, MQTT `Broker`, and
Prometheus `Url`.

## Optional Telegraf Test

The sample contains `Run.TelegrafToInflux`, but the metrics stack keeps its Telegraf
sender disabled by default because ELCM must be listening on TCP `8094`.

Enable it only when the ELCM task is running and reachable:

```powershell
$env:ALLTEST_TELEGRAF_ENABLED="true"
$env:ALLTEST_TELEGRAF_HOST="host.docker.internal"
$env:ALLTEST_TELEGRAF_PORT="8094"
docker compose up -d --build
```

If ELCM is running inside Docker, expose port `8094` from the ELCM container before
enabling this sender.

## Stop

```powershell
docker compose down
```

## Payloads

Kafka topic `sensor_data_morse` receives JSON like:

```json
{"timestamp": 1770000000, "temperature": 24.3, "humidity": 55.1, "sensor": "kafka_sensor_01"}
```

MQTT topic `mi/topic/elcm` receives JSON like:

```json
{"timestamp": 1770000000, "temperatura": 24.3, "humedad": 55.1, "sensor": "mqtt_sensor_01"}
```

Prometheus exposes:

- `windows_net_bytes_received_total`
- `windows_net_bytes_sent_total`
- `windows_logical_disk_write_bytes_total`
- `windows_logical_disk_read_bytes_total`
- `process_cpu_seconds_total`
