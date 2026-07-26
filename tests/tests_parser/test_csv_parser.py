import builtins

import pandas as pd
import pytest

from ehubx.core import logging
from ehubx.parser import csv_parser, exceptions
from ehubx.parser.csv_parser import HeaderId


def _write_csv(tmp_path, name, lines):
    path = tmp_path / name
    path.write_text("\n".join(lines))
    return path


def test_parse_missing_file_raises_missingfileexception(tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"
    with pytest.raises(exceptions.MissingFileException) as exc_info:
        csv_parser.parse(str(missing_path), header_ids=[HeaderId.STAGEID])
    assert "CSV file does not exist" in str(exc_info.value)
    assert exc_info.value._file_type == csv_parser.FILETYPE_CSV


def test_parse_raises_when_header_ids_missing(tmp_path):
    lines = [
        "stage_id,stageA",
        "wrong_header,techX",
        "0,1",
    ]
    csv_path = _write_csv(tmp_path, "missing_header.csv", lines)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.TECHID])

    assert HeaderId.TECHID.value in str(exc_info.value)
    assert isinstance(exc_info.value, exceptions.ParsingException)


def test_parse_raises_on_duplicate_headers(tmp_path):
    lines = [
        "stage_id,stageA,stageA",
        "tech_id,techX,techX",
        "0,1,2",
    ]
    csv_path = _write_csv(tmp_path, "duplicate_header.csv", lines)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.TECHID])

    assert "duplicate headers" in str(exc_info.value)
    assert isinstance(exc_info.value, exceptions.ParsingException)


def test_parse_parses_units_and_coerces_numeric(tmp_path, monkeypatch):
    lines = [
        "stage_id,stageA",
        "hub_id,hub1",
        "unit,kW",
        "0,5",
        "1,not_a_number",
    ]
    csv_path = _write_csv(tmp_path, "with_units.csv", lines)

    warnings = []
    monkeypatch.setattr(logging, "log_warning", lambda msg, module="": warnings.append(msg))

    df = csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.HUBID])

    assert df.attrs[csv_parser.ATTR_UNIT] == {("stageA", "hub1"): "kW"}
    assert list(df.index) == ["0", "1"]
    assert df.loc["0", ("stageA", "hub1")] == 5
    assert df.loc["1", ("stageA", "hub1")] == 0
    assert any("NaN values" in msg for msg in warnings)


def test_parse_assigns_empty_unit_when_absent(tmp_path):
    lines = [
        "stage_id,stageA",
        "hub_id,hub1",
        "0,3",
        "1,4",
    ]
    csv_path = _write_csv(tmp_path, "without_units.csv", lines)

    df = csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.HUBID])

    assert df.attrs[csv_parser.ATTR_UNIT] == {("stageA", "hub1"): ""}
    assert df.loc[0, ("stageA", "hub1")] == 3
    assert df.loc[1, ("stageA", "hub1")] == 4


def test_parse_retries_after_permission_error(tmp_path, monkeypatch):
    lines = [
        "stage_id,stageA",
        "hub_id,hub1",
        "0,3",
    ]
    csv_path = _write_csv(tmp_path, "permission_retry.csv", lines)

    read_calls = {"count": 0}
    real_read_csv = pd.read_csv

    def fake_read_csv(path, *args, **kwargs):
        # Let the header preview read succeed, but simulate a transient lock on the first full read.
        if kwargs.get("nrows") is not None:
            return real_read_csv(path, *args, **kwargs)
        if read_calls["count"] == 0:
            read_calls["count"] += 1
            raise PermissionError("locked")
        return real_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(csv_parser.pd, "read_csv", fake_read_csv)
    monkeypatch.setattr(logging, "pause_console_log", lambda write_console_entry=True: None)
    monkeypatch.setattr(logging, "resume_console_log", lambda write_console_entry=True: None)
    monkeypatch.setattr(builtins, "input", lambda *_, **__: None)

    df = csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.HUBID])

    assert read_calls["count"] == 1
    assert df.loc[0, ("stageA", "hub1")] == 3


def test_parse_handles_empty_file(tmp_path):
    csv_path = _write_csv(tmp_path, "empty.csv", [])

    with pytest.raises(exceptions.ParsingException) as exc_info:
        csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID])

    assert "File is empty" in str(exc_info.value)


def test_parse_retries_on_parser_error(tmp_path, monkeypatch):
    lines = [
        "stage_id,stageA",
        "hub_id,hub1",
        "0,3",
    ]
    csv_path = _write_csv(tmp_path, "parser_retry.csv", lines)

    read_calls = {"count": 0}
    real_read_csv = pd.read_csv

    def fake_read_csv(path, *args, **kwargs):
        if kwargs.get("nrows") is not None:
            return real_read_csv(path, *args, **kwargs)
        if read_calls["count"] == 0:
            read_calls["count"] += 1
            raise pd.errors.ParserError("bad")
        return real_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(csv_parser.pd, "read_csv", fake_read_csv)
    monkeypatch.setattr(logging, "pause_console_log", lambda write_console_entry=True: None)
    monkeypatch.setattr(logging, "resume_console_log", lambda write_console_entry=True: None)
    monkeypatch.setattr(builtins, "input", lambda *_, **__: None)

    df = csv_parser.parse(str(csv_path), header_ids=[HeaderId.STAGEID, HeaderId.HUBID])

    assert read_calls["count"] == 1
    assert df.loc[0, ("stageA", "hub1")] == 3
