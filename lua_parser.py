"""Recursive-descent Lua table parser for ESO SavedVariables files."""

import re

_SKIP_RE = re.compile(r'(?:[ \t\n\r]+|--[^\n]*)+')
_VAR_ASSIGN_TEMPLATE = r'(?:(?<=^)|(?<=\n)){name}\s*='


class LuaParser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.n = len(text)

    def _skip(self):
        m = _SKIP_RE.match(self.text, self.pos)
        if m:
            self.pos = m.end()

    def _peek(self) -> str | None:
        self._skip()
        return self.text[self.pos] if self.pos < self.n else None

    def _expect(self, ch: str):
        self._skip()
        if self.pos >= self.n or self.text[self.pos] != ch:
            got = repr(self.text[self.pos]) if self.pos < self.n else 'EOF'
            raise SyntaxError(f"Expected {ch!r}, got {got} at pos {self.pos}")
        self.pos += 1

    def _parse_string(self) -> str:
        self.pos += 1  # skip opening "
        parts = []
        while self.pos < self.n:
            ch = self.text[self.pos]
            if ch == '\\':
                self.pos += 1
                if self.pos < self.n:
                    esc = self.text[self.pos]
                    if esc == '"':   parts.append('"')
                    elif esc == 'n': parts.append('\n')
                    elif esc == 't': parts.append('\t')
                    elif esc == 'r': parts.append('\r')
                    elif esc == '\\': parts.append('\\')
                    else:            parts.append('\\' + esc)
                    self.pos += 1
            elif ch == '"':
                self.pos += 1
                return ''.join(parts)
            else:
                parts.append(ch)
                self.pos += 1
        raise SyntaxError("Unterminated string")

    def _parse_number(self) -> int | float:
        start = self.pos
        if self.pos < self.n and self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < self.n and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < self.n and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < self.n and self.text[self.pos].isdigit():
                self.pos += 1
        if self.pos < self.n and self.text[self.pos] in ('e', 'E'):
            self.pos += 1
            if self.pos < self.n and self.text[self.pos] in ('+', '-'):
                self.pos += 1
            while self.pos < self.n and self.text[self.pos].isdigit():
                self.pos += 1
        s = self.text[start:self.pos]
        return float(s) if ('.' in s or 'e' in s.lower()) else int(s)

    def _parse_value(self):
        c = self._peek()
        if c == '"':
            return self._parse_string()
        if c == '{':
            return self._parse_table()
        if c == '-' or (c and c.isdigit()):
            return self._parse_number()
        if self.text[self.pos:self.pos + 4] == 'true':
            self.pos += 4
            return True
        if self.text[self.pos:self.pos + 5] == 'false':
            self.pos += 5
            return False
        if self.text[self.pos:self.pos + 3] == 'nil':
            self.pos += 3
            return None
        raise SyntaxError(f"Unexpected {c!r} at pos {self.pos}")

    def _parse_key(self):
        self._expect('[')
        kc = self._peek()
        key = self._parse_string() if kc == '"' else self._parse_number()
        self._expect(']')
        self._expect('=')
        return key

    def _skip_value(self):
        c = self._peek()
        if c == '"':
            self._parse_string()
            return
        if c == '{':
            self._skip_table()
            return
        if c == '-' or (c and c.isdigit()):
            self._parse_number()
            return
        if self.text[self.pos:self.pos + 4] == 'true':
            self.pos += 4
            return
        if self.text[self.pos:self.pos + 5] == 'false':
            self.pos += 5
            return
        if self.text[self.pos:self.pos + 3] == 'nil':
            self.pos += 3
            return
        raise SyntaxError(f"Unexpected {c!r} at pos {self.pos}")

    def _skip_table(self):
        self._expect('{')
        while True:
            c = self._peek()
            if c == '}':
                self.pos += 1
                break
            if c == '[':
                self._parse_key()
                self._skip_value()
            else:
                self._skip_value()
            self._skip()
            if self._peek() == ',':
                self.pos += 1

    def _parse_table_excluding_keys(self, excluded_keys: set[str] | None = None):
        self._expect('{')
        result = {}
        arr_idx = 1
        excluded_keys = excluded_keys or set()
        while True:
            c = self._peek()
            if c == '}':
                self.pos += 1
                break
            if c == '[':
                key = self._parse_key()
                if key in excluded_keys:
                    self._skip_value()
                else:
                    result[key] = self._parse_value()
            else:
                result[arr_idx] = self._parse_value()
                arr_idx += 1
            self._skip()
            if self._peek() == ',':
                self.pos += 1
        return result

    def _parse_table(self) -> dict:
        self._expect('{')
        result = {}
        arr_idx = 1
        while True:
            c = self._peek()
            if c == '}':
                self.pos += 1
                break
            if c == '[':
                key = self._parse_key()
                result[key] = self._parse_value()
            else:
                result[arr_idx] = self._parse_value()
                arr_idx += 1
            self._skip()
            if self._peek() == ',':
                self.pos += 1
        return result

    def parse_variable(self, name: str):
        """Find and parse a top-level Lua variable assignment by name."""
        pattern = re.compile(_VAR_ASSIGN_TEMPLATE.format(name=re.escape(name)))
        match = pattern.search(self.text)
        if not match:
            raise ValueError(f"Variable {name!r} not found in file")
        self.pos = match.end()
        return self._parse_value()


def parse_lua_variable(file_path: str, variable_name: str) -> dict:
    """Parse any named top-level variable from a Lua SavedVariables file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_lua_text_variable(content, variable_name)


def parse_lua_text_variable(content: str, variable_name: str) -> dict:
    """Parse any named top-level variable from a Lua SavedVariables string."""
    parser = LuaParser(content)
    return parser.parse_variable(variable_name)


def parse_iasync_core(file_path: str) -> dict:
    """Parse only the iasync fields needed for /api/data and /api/builds."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_iasync_core_text(content)


def parse_iasync_core_text(content: str) -> dict:
    """Parse only the iasync fields needed for /api/data and /api/builds from a string."""
    parser = LuaParser(content)
    pattern = re.compile(_VAR_ASSIGN_TEMPLATE.format(name=re.escape("iasync_data")))
    match = pattern.search(content)
    if not match:
        raise ValueError("Variable 'iasync_data' not found in file")
    parser.pos = match.end()
    parser._expect('{')

    result = {}
    wanted_top_level = {"lastUpdate", "accountName", "abilityNames", "cpNames", "chars", "bank", "houses", "guildBanks"}
    while True:
        c = parser._peek()
        if c == '}':
            parser.pos += 1
            break
        if c == '[':
            key = parser._parse_key()
            if key not in wanted_top_level:
                parser._skip_value()
            elif key == "chars":
                result[key] = _parse_chars_without_achievements(parser)
            else:
                result[key] = parser._parse_value()
        else:
            parser._skip_value()
        parser._skip()
        if parser._peek() == ',':
            parser.pos += 1
    return result


def _parse_chars_without_achievements(parser: LuaParser) -> dict:
    parser._expect('{')
    result = {}
    arr_idx = 1
    while True:
        c = parser._peek()
        if c == '}':
            parser.pos += 1
            break
        if c == '[':
            key = parser._parse_key()
            if parser._peek() == '{':
                result[key] = parser._parse_table_excluding_keys({"achievements"})
            else:
                result[key] = parser._parse_value()
        else:
            result[arr_idx] = parser._parse_value()
            arr_idx += 1
        parser._skip()
        if parser._peek() == ',':
            parser.pos += 1
    return result
