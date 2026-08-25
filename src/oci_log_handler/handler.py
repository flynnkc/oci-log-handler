"""Buffered Python logging handler for OCI Logging."""

from __future__ import annotations

from datetime import UTC, datetime
from logging import LogRecord
from logging.handlers import BufferingHandler
from typing import Any
from uuid import uuid4

from oci import loggingingestion
from oci.signer import Signer


class OciLoggingHandler(BufferingHandler):
    """Send Python log records to Oracle Cloud Infrastructure Logging.

    The handler buffers records and writes them to OCI Logging as a single
    ``put_logs`` request when the buffer reaches ``capacity`` or when
    ``flush()`` is called.
    """

    def __init__(
        self,
        log_ocid: str,
        config: dict[str, Any] | None = None,
        signer: Signer | None = None,
        capacity: int = 100,
        *,
        client: Any | None = None,
        source: str = "oci-log-handler-0.1.0",
        log_type: str = "python_application",
        specversion: str = "1.0",
        raise_exceptions: bool = False,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        if client is None and config is None:
            raise ValueError("config is required when client is not provided")

        super().__init__(capacity)
        self.log_ocid = log_ocid
        self.client = client or loggingingestion.LoggingClient(config, signer=signer)
        self.source = source
        self.log_type = log_type
        self.specversion = specversion
        self.raise_exceptions = raise_exceptions

    def flush(self) -> None:
        """Submit buffered records to OCI Logging."""
        self.acquire()
        try:
            records = self.buffer[:]
            self.buffer.clear()
        finally:
            self.release()

        if not records:
            return

        try:
            entries = [self._record_to_entry(record) for record in records]
            details = loggingingestion.models.PutLogsDetails(
                specversion=self.specversion,
                log_entry_batches=[
                    loggingingestion.models.LogEntryBatch(
                        defaultlogentrytime=datetime.now(UTC),
                        source=self.source,
                        type=self.log_type,
                        entries=entries,
                    )
                ],
            )
            self.client.put_logs(self.log_ocid, details)
        except Exception:
            self._restore_records(records)
            if self.raise_exceptions:
                raise
            self.handleError(records[-1])

    def close(self) -> None:
        """Flush pending records before closing the handler."""
        try:
            self.flush()
        finally:
            super().close()

    def _record_to_entry(self, record: LogRecord) -> Any:
        return loggingingestion.models.LogEntry(
            data=self.format(record),
            id=str(uuid4()),
            time=datetime.fromtimestamp(record.created, UTC),
        )

    def _restore_records(self, records: list[LogRecord]) -> None:
        self.acquire()
        try:
            self.buffer = (records + self.buffer)[-self.capacity :]
        finally:
            self.release()
