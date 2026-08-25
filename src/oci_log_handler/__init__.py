"""Python logging handler for Oracle Cloud Infrastructure Logging."""

from importlib.metadata import PackageNotFoundError, version

from .handler import OciLoggingHandler

__all__ = ["OciLoggingHandler"]

try:
    __version__ = version("oci-log-handler")
except PackageNotFoundError:
    __version__ = "0.0.0"
