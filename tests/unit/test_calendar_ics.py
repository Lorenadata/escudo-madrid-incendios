"""M16: el .ics es RFC 5545 válido y un texto aportado por usuarios no puede inyectar propiedades (CRLF injection)."""

from __future__ import annotations

from escudo_api.routers.calendar import _ics_escape, danger_periods, to_ics

CRLF = "\r\n"


def _event(**kw):
    base = {"id": "t1", "start": "2027-01-01", "end": "2027-01-01", "title": "Vence: algo", "area_name": None,
            "detail": "d", "source": "s"}
    return {**base, **kw}


def test_escape_neutralizes_line_breaks_and_controls():
    out = _ics_escape("Ana" + CRLF + "END:VEVENT" + "\r" + "X;y,z" + "\x07")
    assert "\r" not in out and "\n" not in out and "\x07" not in out
    assert out == "Ana\\nEND:VEVENT\\nX\\;y\\,z"


def test_user_text_cannot_inject_properties():
    ics = to_ics([_event(area_name="Zona" + CRLF + "X-INJ:1", detail="r" + "\r" + "ATTACH:http://evil")])
    names = [line.split(":", 1)[0].split(";", 1)[0] for line in ics.split(CRLF) if line and not line.startswith(" ")]
    assert "X-INJ" not in names and "ATTACH" not in names
    assert names.count("BEGIN") == 2 and names.count("END") == 2  # VCALENDAR + un VEVENT


def test_ics_structure_folding_and_all_day_dates():
    ics = to_ics([_event(title="Vence: " + "actuación muy larga " * 10)])
    lines = ics.split(CRLF)
    assert lines[0] == "BEGIN:VCALENDAR" and ics.endswith("END:VCALENDAR" + CRLF)
    assert all(len(line.encode("utf-8")) <= 75 for line in lines)
    assert "DTSTART;VALUE=DATE:20270101" in lines and "DTEND;VALUE=DATE:20270102" in lines


def test_official_danger_periods_literal():
    by = {(e["level"], e["start"]): e["end"] for e in danger_periods(2027)}
    assert by[("alto", "2027-06-15")] == "2027-09-30"
    assert by[("medio", "2027-05-16")] == "2027-06-14" and by[("medio", "2027-10-01")] == "2027-10-31"
    assert by[("bajo", "2027-11-01")] == "2027-12-31" and by[("bajo", "2027-01-01")] == "2027-05-15"
