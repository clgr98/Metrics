# Metrics

Private ALLTEST metrics stack for ELCM.

This repository provides a Docker image, `elcm-alltest-source`, plus a Compose stack
that lets ELCM test these collectors:

- `Run.KafkaConsumerToInflux`
- `Run.MqttToInflux`
- `Run.PrometheusToInflux`
- `Run.TelegrafToInflux`

External runtime images and the source-image base are pinned by digest. See
[IMAGE_LOCKS.md](IMAGE_LOCKS.md) for the selected releases and update procedure.

The Python source image publishes synthetic sensor values to Kafka and MQTT, exposes
Windows-like Prometheus metrics, and the stack includes a real Telegraf agent that
sends JSON metrics to ELCM's `Run.TelegrafToInflux` TCP listener.

## Start

Start ELCM-Env first, then start Metrics:

```powershell
docker compose up -d --build
```

Services exposed on the host:

- Kafka: `9092`
- MQTT: `1885`
- Prometheus: `9090`
- Raw exporter debug endpoint: `8000`

Telegraf does not expose a host port. It connects out to ELCM on TCP `8094`.

Prometheus should be available at:

```text
http://localhost:9090
```

## Use With ELCM-Env

Use [samples/ALLTEST_DOCKER.yml](samples/ALLTEST_DOCKER.yml). Metrics attaches Kafka,
MQTT, Prometheus, and Telegraf to Docker network `elcm-env_default`, so ELCM reaches
them by container name:

- Kafka: `alltest-kafka:29092`
- MQTT: `alltest-mqtt:1885`
- Prometheus: `alltest-prometheus:9090`
- Telegraf output: `elcm:8094`

For the OCUDU/OAI virtual-radio path, select the `oai` backend in Portal System
Configuration and upload
[samples/OCUDU_OAI_RADIO_METRICS.yml](samples/OCUDU_OAI_RADIO_METRICS.yml).
The sample uses one OAI UE, runs ping followed by iPerf2, keeps the four Metrics
collectors active, and adds dashboards backed by:

- `virtual_ran_ue_timeseries` for CQI, MCS, scheduler bitrate and HARQ results.
- `radio_channel_timeseries` for SNR, RSRP and timing advance.

The testcase does not declare a legacy RAN type. ELCM uses the backend metadata
returned by Lab-Proxy and writes `ran_backend=oai`,
`ran_type=ocudu_oai_zmq`, `experiment_mode=virtual_oai` and
`agent_type=oai` to InfluxDB.

Panels that compare several fields define explicit `Legend` lists, so Grafana
shows names such as `DL MCS`, `UL MCS`, `PUSCH SNR` and `PUCCH SNR` instead of
an ambiguous `_value` or repeated `ue01`.

For a controlled channel experiment, upload
[samples/OCUDU_OAI_CHANNEL_COMPARISON.yml](samples/OCUDU_OAI_CHANNEL_COMPARISON.yml).
It runs the same ping and iPerf2 workloads twice through the ZeroMQ I/Q relay.
Both conditions use deterministic -40 dBFS noise; the baseline applies 0 dB
attenuation and the second condition applies 6 dB in both directions. The
dashboard pairs timestamped
`radio_channel_ground_truth_timeseries` values with observed RSRP, SNR, CQI,
HARQ error rate, throughput and RTT. Every multi-series panel has explicit
legends and every panel follows the 24-column two-column grid. The iPerf2
client is routed through the UE tunnel and bound to its PDU address, so the
throughput series cannot bypass the radio over Docker `eth0`.

## Dashboard Layout

Grafana uses a 24-column grid. Dashboard geometry in ELCM test cases is defined as:

```yaml
Size: [height, width]
Position: [x, y]
```

For a compact two-column layout with panels sized `[8, 12]`, use:

```text
[0, 0]   [12, 0]
[0, 8]   [12, 8]
[0, 16]  [12, 16]
```

The horizontal coordinate plus the panel width must not exceed 24, and dashboard
panels must not overlap.

## Telegraf Test

The sample contains `Run.TelegrafToInflux` listening on TCP `8094`. Metrics connects
`alltest-telegraf` to Docker network `elcm-env_default` and sends metrics to
`tcp://elcm:8094`.

Until an ELCM execution starts `Run.TelegrafToInflux`, Telegraf may log connection
refused messages for `8094`. Its output buffer is deliberately limited to two
collection intervals, so the next execution receives current samples instead of
replaying minutes of data from a previous closed listener.

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

Telegraf sends JSON metrics with names such as `mem` and `cpu`; ELCM adapts the
`mem.used` field into dashboard field `used_mem`.

## Contracts

Run the repository checks before uploading the sample:

```powershell
./tests/oai-radio-metrics-contract.ps1
./tests/telegraf-freshness-contract.ps1
./tests/oai-channel-comparison-contract.ps1
```
