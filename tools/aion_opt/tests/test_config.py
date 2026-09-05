"""YAML configuration: coverage of every knob, and CLI precedence."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aion_opt.cli import _CONFIG_TO_ARG, _load_config, build_parser
from aion_opt.config import AionOptConfig


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _parse(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    from aion_opt.cli import _subcommand_defaults

    args._defaults = _subcommand_defaults(parser, args.command)
    return args


def test_defaults_are_validated():
    with pytest.raises(ValueError):
        AionOptConfig(Path("a.v"), Path("b.json"), max_pattern_size=1)
    with pytest.raises(ValueError):
        AionOptConfig(Path("a.v"), Path("b.json"), area_factor=1.5)
    with pytest.raises(ValueError):
        AionOptConfig(Path("a.v"), Path("b.json"), max_outputs=0)


def test_min_selected_defaults_to_min_occurrences():
    cfg = AionOptConfig(Path("a.v"), Path("b.json"), min_occurrences=5)
    assert cfg.min_selected_occurrences == 5


def test_unknown_keys_are_rejected():
    with pytest.raises(ValueError, match="unknown configuration key"):
        AionOptConfig.from_dict(
            {"input_netlist": "a.v", "cell_lib": "b.json", "max_patern_size": 4}
        )


def test_config_fills_unset_arguments(tmp_path):
    cfg = _write(
        tmp_path,
        {
            "input_netlist": "design.v",
            "cell_lib": "tech.json",
            "top_module": "top",
            "max_pattern_size": 5,
            "min_occurrences": 7,
            "max_outputs": 2,
            "cell_prefix": "MYLIB_",
            "elite_count": 12,
            "jobs": 3,
        },
    )
    args = _parse(
        ["generate-cells", "--config", str(cfg), "--output-cells", "c.v",
         "--output-report", "r.json"]
    )
    _load_config(args)

    assert args.input == Path("design.v")
    assert args.top == "top"
    assert args.max_size == 5
    assert args.min_occurrences == 7
    assert args.max_outputs == 2
    assert args.cell_prefix == "MYLIB_"
    assert args.elite_count == 12
    assert args.jobs == 3


def test_command_line_wins_over_config(tmp_path):
    cfg = _write(
        tmp_path,
        {"input_netlist": "design.v", "cell_lib": "tech.json", "max_pattern_size": 5},
    )
    args = _parse(
        ["generate-cells", "--config", str(cfg), "--max-size", "2",
         "--output-cells", "c.v", "--output-report", "r.json"]
    )
    _load_config(args)
    assert args.max_size == 2


def test_every_mapped_config_key_exists():
    known = {f.name for f in AionOptConfig.__dataclass_fields__.values()}
    assert set(_CONFIG_TO_ARG) <= known


def test_repository_example_config_loads():
    example = Path(__file__).resolve().parents[3] / "examples" / "aion_opt" / "aion_opt.yaml"
    if not example.exists():
        pytest.skip("example config not present")
    cfg = AionOptConfig.from_yaml(example)
    assert cfg.top_module == "pm32"
    assert cfg.to_dict()["max_pattern_size"] == cfg.max_pattern_size
