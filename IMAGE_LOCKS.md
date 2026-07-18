# Docker Image Locks

External images are pinned as `tag@digest`. The tag keeps the selected release
readable, while the digest prevents a later tag update from changing a clean
installation unexpectedly.

| Component | Locked image |
| --- | --- |
| Kafka | `apache/kafka:4.1.1@sha256:0bc1bb2478f45b6cea78864df86acdc11e8df2c5172477819a4d12942cbe5d40` |
| Mosquitto | `eclipse-mosquitto:2.0@sha256:212f89e1eaeb2c322d6441b64396e3346026674db8fa9c27beac293405c32b3c` |
| Telegraf | `telegraf:1.34@sha256:2173764352db5591bebe02d3f965cc64cdd357ff8439f57e45b6a1885eb50333` |
| Prometheus | `prom/prometheus:v2.55.1@sha256:2659f4c2ebb718e7695cb9b25ffa7d6be64db013daba13e05c875451cf51b0d3` |
| Ubuntu source-image base | `ubuntu:24.04@sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90` |

`elcm-alltest-source:latest` is intentionally a local image built from this
repository. Its external Ubuntu base is locked above.

To update a lock, resolve and review the new digest, update every matching
reference, rebuild the stack and run the complete Kafka, MQTT, Prometheus and
Telegraf integration sample before committing the change.
