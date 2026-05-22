from __future__ import annotations

from pathlib import Path

import pytest

from lua_parser import LuaParser, parse_lua_variable
from server import _parse_lua_assignment


@pytest.mark.unit
def test_parse_nested_saved_variable(tmp_path: Path):
    path = tmp_path / "sample.lua"
    path.write_text(
        """
other = {}
iasync_data = {
  ["name"] = "alpha\\n beta",
  ["enabled"] = true,
  ["missing"] = nil,
  ["count"] = -12.5,
  ["items"] = {
    [1] = "first",
    ["two"] = 2,
  },
}
""",
        encoding="utf-8",
    )

    data = parse_lua_variable(str(path), "iasync_data")

    assert data["name"] == "alpha\n beta"
    assert data["enabled"] is True
    assert data["missing"] is None
    assert data["count"] == -12.5
    assert data["items"][1] == "first"
    assert data["items"]["two"] == 2


@pytest.mark.unit
def test_parse_lua_assignment_with_spaces(tmp_path: Path):
    path = tmp_path / "ttc.lua"
    path.write_text('self.PriceTable = { ["TimeStamp"] = 123, ["Data"] = {} }', encoding="utf-8")

    data = _parse_lua_assignment(path, "self.PriceTable")

    assert data["TimeStamp"] == 123
    assert data["Data"] == {}


@pytest.mark.unit
def test_parse_variable_without_space_before_equals(tmp_path: Path):
    path = tmp_path / "sample.lua"
    path.write_text('WizardsWardrobeSV={["Default"]={}}', encoding="utf-8")

    data = parse_lua_variable(str(path), "WizardsWardrobeSV")

    assert data["Default"] == {}


@pytest.mark.unit
def test_parse_missing_variable_raises_value_error(tmp_path: Path):
    path = tmp_path / "sample.lua"
    path.write_text("other = {}", encoding="utf-8")

    with pytest.raises(ValueError, match="not found"):
        parse_lua_variable(str(path), "iasync_data")


@pytest.mark.unit
def test_parse_malformed_table_raises_syntax_error():
    parser = LuaParser('iasync_data = { ["a"] = }')

    with pytest.raises(SyntaxError):
        parser.parse_variable("iasync_data")
