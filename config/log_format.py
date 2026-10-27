import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

STANDARD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}

run_id_var: ContextVar[str | None] = ContextVar("run_id", default=None)


class RunIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        run_id = run_id_var.get()
        if run_id and not hasattr(record, "run_id"):
            record.run_id = run_id
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
    