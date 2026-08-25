# OCI Log Handler

A buffered Python `logging` handler that sends application logs to Oracle Cloud
Infrastructure Logging by using the OCI Python SDK Logging Ingestion client.

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
handler.flush()
```

By default, failed submissions are kept in a bounded retry buffer and do not
raise exceptions into the application. Pass `raise_exceptions=True` if your
application should fail fast when OCI submission fails.
