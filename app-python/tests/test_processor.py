import json
from unittest.mock import MagicMock

import processor


def msg(payload, wrap=False):
    body = {"payload": payload} if wrap else payload
    return json.dumps(body).encode()


def test_extract_payload_insert():
    assert processor.extract_payload(msg({"op": "c", "after": {"icao24": "abc"}})) == {"icao24": "abc"}


def test_extract_payload_update_with_schema_wrapper():
    m = msg({"op": "u", "after": {"icao24": "abc"}}, wrap=True)
    assert processor.extract_payload(m) == {"icao24": "abc"}


def test_extract_payload_delete_and_tombstone():
    assert processor.extract_payload(msg({"op": "d", "before": {"icao24": "a"}, "after": None})) is None
    assert processor.extract_payload(None) is None
    assert processor.extract_payload(b"") is None


def test_extract_payload_invalid_json():
    assert processor.extract_payload(b"not json") is None


def test_process_batch_empty():
    assert processor.process_batch([]) == []


def test_process_batch_partitions_by_event_date(monkeypatch):
    s3 = MagicMock()
    monkeypatch.setattr(processor, "_s3_client", s3)
    # 2024-01-01 12:00 UTC e 2024-01-02 12:00 UTC
    batch = [
        {"icao24": "a", "last_contact": 1704110400},
        {"icao24": "b", "last_contact": 1704196800},
        {"icao24": "c", "last_contact": 1704110400},
    ]
    keys = processor.process_batch(batch)
    assert len(keys) == 2
    assert any("year=2024/month=01/day=01" in k for k in keys)
    assert any("year=2024/month=01/day=02" in k for k in keys)
    assert s3.upload_file.call_count == 2


def test_process_batch_propagates_upload_error(monkeypatch):
    s3 = MagicMock()
    s3.upload_file.side_effect = RuntimeError("boom")
    monkeypatch.setattr(processor, "_s3_client", s3)
    try:
        processor.process_batch([{"icao24": "a", "last_contact": 1704110400}])
        assert False, "deveria levantar"
    except RuntimeError:
        pass
