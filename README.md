# OCI Log Handler

A buffered Python `logging` handler that sends application logs to Oracle Cloud
Infrastructure Logging by using the OCI Python SDK Logging Ingestion client.

Requires Python 3.11 or later.

## Installation

```bash
pip install oci-log-handler
```

## Usage

```python
import logging

import oci
from oci_log_handler import OciLoggingHandler

config = oci.config.from_file()

handler = OciLoggingHandler(
    log_ocid="ocid1.log.oc1..example",
    config=config,
    capacity=100,
)
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

logger = logging.getLogger("my-app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger.info("Application started")
```

You can also pass an existing OCI Logging Ingestion client:

```python
import logging

import oci
from oci import loggingingestion
from oci_log_handler import OciLoggingHandler

config = oci.config.from_file()
client = loggingingestion.LoggingClient(config)

handler = OciLoggingHandler(
    log_ocid="ocid1.log.oc1..example",
    client=client,
    capacity=100,
)

logger = logging.getLogger("my-app")
logger.addHandler(handler)
```

For signer-based authentication, pass `signer=` when constructing the handler
or create the `LoggingClient` with your signer and pass it as `client=`.

## Delivery behavior

This handler is best-effort and keeps its retry buffer in memory. By default,
failed submissions are restored to the handler's bounded buffer and do not raise
exceptions into the application. If the process exits before a later successful
flush, those buffered records are not durable.

Pass `raise_exceptions=True` if your application should fail fast when OCI
submission fails.
