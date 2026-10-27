import logging

from config.log_format import RunIdFilter, run_id_var


def make_record() -> logging.LogRecord:
    return logging.LogRecord("jobs.sources.base", logging.INFO, "", 0, "source request finished", (), None)


def test_adds_run_id_during_a_run():
    token = run_id_var.set("abc123def456")
    try:
        record = make_record()
        assert RunIdFilter().filter(record) is True
        assert record.run_id == "abc123def456"
    finally:
        run_id_var.reset(token)


def test_adds_nothing_outside_a_run():
    record = make_record()
    assert RunIdFilter().filter(record) is True
    assert not hasattr(record, "run_id")


def test_keeps_run_id_already_on_record():
    token = run_id_var.set("abc123def456")
    try:
        record = make_record()
        record.run_id = "given000000"
        RunIdFilter().filter(record)
        assert record.run_id == "given000000"
    finally:
        run_id_var.reset(token)