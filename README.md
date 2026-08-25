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
    "ocid1.log.oc1..example",
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
    "ocid1.log.oc1..example",
    client=client,
    capacity=100,
)

logger = logging.getLogger("my-app")
logger.addHandler(handler)
```

For signer-based authentication, pass `signer=` when constructing the handler
or create the `LoggingClient` with your signer and pass it as `client=`.

## Handler arguments

`OciLoggingHandler` takes the target OCI log OCID as its first argument:

```python
OciLoggingHandler("ocid1.log.oc1..example", ...)
```

Optional keyword arguments:

- `config`: OCI SDK config dictionary.
- `signer`: OCI signer to use instead of config-file key authentication.
- `capacity`: number of log records to buffer before flushing. Defaults to
  `100`.
- `client`: existing `oci.loggingingestion.LoggingClient`. When provided,
  `config` and `signer` are not used to create a client.
- `source`: OCI log entry batch source. Defaults to `"oci-log-handler"`.
- `log_type`: OCI log entry batch type. Defaults to `"python_application"`.
- `specversion`: OCI logs payload spec version. Defaults to `"1.0"`.
- `raise_exceptions`: re-raise OCI submission errors instead of using
  `logging.Handler.handleError`. Defaults to `False`.

Provide one of `config`, `signer`, or `client`.

## Delivery behavior

This handler is best-effort and keeps its retry buffer in memory. By default,
failed submissions are restored to the handler's bounded buffer and do not raise
exceptions into the application. If the process exits before a later successful
flush, those buffered records are not durable.

Pass `raise_exceptions=True` if your application should fail fast when OCI
submission fails.
