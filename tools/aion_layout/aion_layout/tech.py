# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               IHP SG13G2 technology description
# ================================================================

"""Technology data extracted from the legacy lclayout SG13G2 setup.

All dimensions are stored in nanometres unless otherwise noted.  The GDSII
physical unit is metres and is exposed via ``Tech.db_unit``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Layer:
    """A physical layer with its GDSII layer/datatype and basic design rules."""

    name: str
    gds_layer: int
    gds_datatype: int
    min_width: Optional[float] = None
    min_spacing: Optional[float] = None
    pin_datatype: Optional[int] = None
    label_datatype: Optional[int] = None

    @property
    def gds_pair(self) -> tuple[int, int]:
        """Return the ``(layer, datatype)`` pair used for normal geometry."""
        return (self.gds_layer, self.gds_datatype)

    @property
    def pin_pair(self) -> Optional[tuple[int, int]]:
        """Return the ``(layer, datatype)`` pair used for pins, if any."""
        if self.pin_datatype is None:
            return None
        return (self.gds_layer, self.pin_datatype)

    @property
    def label_pair(self) -> Optional[tuple[int, int]]:
        """Return the ``(layer, datatype)`` pair used for text labels, if any."""
        if self.label_datatype is None:
            return None
        return (self.gds_layer, self.label_datatype)


@dataclass
class Tech:
    """Container for a PDK: layers, design rules and standard-cell grid defaults."""

    name: str
    db_unit: float
    layers: dict[str, Layer] = field(default_factory=dict)
    design_rules: dict[str, Any] = field(default_factory=dict)
    grid: dict[str, Any] = field(default_factory=dict)
    standard_cell: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, name: str) -> Layer:
        """Return a layer by name."""
        return self.layers[name]

    def get(self, name: str, default: Optional[Layer] = None) -> Optional[Layer]:
        """Return a layer by name, or ``default`` if it does not exist."""
        return self.layers.get(name, default)

    @property
    def layer_list(self) -> list[Layer]:
        """Return all layers as a list."""
        return list(self.layers.values())


def _build_sg13g2_layers() -> dict[str, Layer]:
    """Build the SG13G2 layer table from the legacy lclayout setup."""
    layers = {
        # Active / diffusion
        "Activ": Layer(
            name="Activ",
            gds_layer=1,
            gds_datatype=0,
            min_width=240.0,
            min_spacing=210.0,
        ),
        # Implant layers
        "NSD": Layer(
            name="NSD",
            gds_layer=7,
            gds_datatype=0,
        ),
        "PSD": Layer(
            name="PSD",
            gds_layer=14,
            gds_datatype=0,
        ),
        # Wells
        "NWell": Layer(
            name="NWell",
            gds_layer=31,
            gds_datatype=0,
            min_width=620.0,
            min_spacing=620.0,
        ),
        "PWell": Layer(
            name="PWell",
            gds_layer=46,
            gds_datatype=0,
        ),
        # Gate
        "GatPoly": Layer(
            name="GatPoly",
            gds_layer=5,
            gds_datatype=0,
            min_width=130.0,
            min_spacing=180.0,
        ),
        # Contacts / vias
        "Cont": Layer(
            name="Cont",
            gds_layer=6,
            gds_datatype=0,
        ),
        "Via1": Layer(
            name="Via1",
            gds_layer=19,
            gds_datatype=0,
            min_width=190.0,
            min_spacing=220.0,
        ),
        # Metal1
        "Metal1": Layer(
            name="Metal1",
            gds_layer=8,
            gds_datatype=0,
            min_width=160.0,
            min_spacing=180.0,
            pin_datatype=2,
            label_datatype=25,
        ),
        # Metal2
        "Metal2": Layer(
            name="Metal2",
            gds_layer=10,
            gds_datatype=0,
            min_width=200.0,
            min_spacing=210.0,
            pin_datatype=2,
            label_datatype=25,
        ),
        # Cell boundary
        "prBoundary": Layer(
            name="prBoundary",
            gds_layer=189,
            gds_datatype=4,
        ),
    }
    return layers


def _build_sg13g2_design_rules() -> dict[str, Any]:
    """Build the SG13G2 design-rule table from the legacy lclayout setup."""
    return {
        "min_width_nm": {
            "Activ": 240.0,
            "GatPoly": 130.0,
            "Metal1": 160.0,
            "Metal2": 200.0,
            "NWell": 620.0,
            "Via1": 190.0,
        },
        "min_spacing_nm": {
            "Activ": 210.0,
            "GatPoly": 180.0,
            "Metal1": 180.0,
            "Metal2": 210.0,
            "Via1": 220.0,
            "NWell": 620.0,
        },
        # Pair-wise spacing rules (layer_a, layer_b) in nanometres.
        "min_spacing_nm_pairs": {
            ("GatPoly", "Cont"): 70.0,
            ("GatPoly", "Activ"): 70.0,
        },
        "min_enclosure_nm": {
            # layer -> { enclosed_layer : minimum enclosure }
            "Metal1": {"Cont": 70.0, "Via1": 10.0},
            "Metal2": {"Via1": 10.0},
            "NWell": {"PSD": 310.0},
            "PWell": {"NSD": 310.0},
            "NSD": {"Cont": 90.0},
            "PSD": {"Cont": 90.0},
            "GatPoly": {"Cont": 70.0},
        },
        "via_size_nm": {
            "Cont": 160.0,
            "Via1": 190.0,
        },
        "gate_extension_nm": 185.0,
        "power_rail_width_nm": 440.0,
        "min_gate_width_nm": {
            "nfet": 200.0,
            "pfet": 200.0,
        },
    }


def _build_sg13g2_grid() -> dict[str, Any]:
    """Build the SG13G2 routing grid from the legacy lclayout setup."""
    pitch_x = 240.0
    pitch_y = 420.0
    return {
        "pitch_x_nm": pitch_x,
        "pitch_y_nm": pitch_y,
        "offset_x_nm": pitch_x,
        "offset_y_nm": pitch_y / 2.0,
        "tracks_y_nm": [
            0.0,
            420.0,
            840.0,
            1260.0,
            1470.0,
            1680.0,
            1890.0,
            2100.0,
            2310.0,
            2520.0,
            2940.0,
            3360.0,
            3780.0,
        ],
    }


def _build_sg13g2_standard_cell() -> dict[str, Any]:
    """Build SG13G2 standard-cell layout defaults from the legacy setup."""
    return {
        "site_width_nm": 480.0,
        "cell_height_nm": 3780.0,
        "power_rail_width_nm": 440.0,
        "transistor_offset_y_nm": 450.0,
        "gate_extension_nm": 185.0,
    }


# Global singleton-like technology object for SG13G2.
sg13g2_tech = Tech(
    name="ihp-sg13g2",
    db_unit=1e-9,
    layers=_build_sg13g2_layers(),
    design_rules=_build_sg13g2_design_rules(),
    grid=_build_sg13g2_grid(),
    standard_cell=_build_sg13g2_standard_cell(),
)

__all__ = ["Layer", "Tech", "sg13g2_tech"]
