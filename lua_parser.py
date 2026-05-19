"""Recursive-descent Lua table parser for ESO SavedVariables files."""

import re

_SKIP_RE = re.compile(r'(?:[ \t\n\r]+|--[^\n]*)+')


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
        s = self.text[start:self.pos]
        return float(s) if '.' in s else int(s)

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
                self.pos += 1  # consume '['
                kc = self._peek()
                key = self._parse_string() if kc == '"' else self._parse_number()
                self._expect(']')
                self._expect('=')
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
        marker = f'\n{name} ='
        idx = self.text.find(marker)
        if idx == -1:
            # Try without leading newline (start of file)
            marker = f'{name} ='
            idx = self.text.find(marker)
        if idx == -1:
            raise ValueError(f"Variable {name!r} not found in file")
        self.pos = idx + len(marker)
        return self._parse_value()


def parse_lua_variable(file_path: str, variable_name: str) -> dict:
    """Parse any named top-level variable from a Lua SavedVariables file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = LuaParser(content)
    return parser.parse_variable(variable_name)
