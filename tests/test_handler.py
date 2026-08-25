from __future__ import annotations

import logging
import unittest
from datetime import UTC, datetime

from oci_log_handler import OciLoggingHandler


class FakeClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = []

    def put_logs(self, log_ocid, details):
        self.calls.append((log_ocid, details))
        if self.fail:
            raise RuntimeError("submission failed")


class OciLoggingHandlerTests(unittest.TestCase):
    def test_flush_sends_buffered_records(self) -> None:
        client = FakeClient()
        handler = OciLoggingHandler(
            "ocid1.log.oc1..example",
            capacity=2,
            client=client,
            source="unit-test",
            log_type="test_log",
        )
        handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

        record = logging.LogRecord(
            "test",
            logging.INFO,
            __file__,
            10,
            "hello %s",
            ("world",),
            None,
        )
        record.created = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC).timestamp()

        handler.emit(record)
        handler.flush()

        self.assertEqual(handler.buffer, [])
        self.assertEqual(len(client.calls), 1)

        log_ocid, details = client.calls[0]
        self.assertEqual(log_ocid, "ocid1.log.oc1..example")
        self.assertEqual(details.specversion, "1.0")

        batch = details.log_entry_batches[0]
        self.assertEqual(batch.source, "unit-test")
        self.assertEqual(batch.type, "test_log")
        self.assertEqual(len(batch.entries), 1)

        entry = batch.entries[0]
        self.assertEqual(entry.data, "INFO:hello world")
        self.assertEqual(entry.time, datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC))
        self.assertTrue(entry.id)

    def test_emit_flushes_when_capacity_is_reached(self) -> None:
        client = FakeClient()
        handler = OciLoggingHandler(
            "ocid1.log.oc1..example",
            capacity=1,
            client=client,
        )

        handler.emit(logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None))

        self.assertEqual(handler.buffer, [])
        self.assertEqual(len(client.calls), 1)

    def test_failed_flush_restores_bounded_buffer_without_raising(self) -> None:
        original_raise_exceptions = logging.raiseExceptions
        logging.raiseExceptions = False
        self.addCleanup(setattr, logging, "raiseExceptions", original_raise_exceptions)

        client = FakeClient(fail=True)
        handler = OciLoggingHandler(
            "ocid1.log.oc1..example",
            capacity=2,
            client=client,
        )

        first = logging.LogRecord("test", logging.INFO, __file__, 1, "first", (), None)
        second = logging.LogRecord("test", logging.INFO, __file__, 2, "second", (), None)
        handler.emit(first)
        handler.emit(second)

        self.assertEqual(handler.buffer, [first, second])
        self.assertEqual(len(client.calls), 1)

    def test_failed_flush_can_raise(self) -> None:
        handler = OciLoggingHandler(
            "ocid1.log.oc1..example",
            capacity=1,
            client=FakeClient(fail=True),
            raise_exceptions=True,
        )

        with self.assertRaises(RuntimeError):
            handler.emit(logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None))

    def test_requires_config_or_client(self) -> None:
        with self.assertRaisesRegex(ValueError, "config is required"):
            OciLoggingHandler("ocid1.log.oc1..example")

    def test_requires_positive_capacity(self) -> None:
        with self.assertRaisesRegex(ValueError, "capacity"):
            OciLoggingHandler("ocid1.log.oc1..example", client=FakeClient(), capacity=0)


if __name__ == "__main__":
    unittest.main()
