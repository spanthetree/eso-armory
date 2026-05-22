#!/usr/bin/env python3
"""Run mutmut against the deterministic core modules only."""

from pathlib import Path

import mutmut
from mutmut.__main__ import Config, _run


mutmut.config = Config(
    do_not_mutate=[],
    also_copy=[
        Path("tests/"),
        Path("server.py"),
        Path("static/"),
        Path("assets/"),
        Path("pyproject.toml"),
        Path(".gitignore"),
    ],
    max_stack_depth=-1,
    debug=False,
    paths_to_mutate=[
        Path("lua_parser.py"),
        Path("item_link_decoder.py"),
        Path("data_processor.py"),
    ],
    pytest_add_cli_args=[],
    pytest_add_cli_args_test_selection=[
        "tests/unit",
        "tests/api",
    ],
    tests_dir=[],
    mutate_only_covered_lines=False,
    type_check_command=[],
)

_run((), None)
