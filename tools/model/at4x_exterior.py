"""Exterior of the factory 2022 GMC Sierra 1500 AT4X, matched to reference photos.

Every visible body panel is a dense curved surface (surf.panel) lifted from an exact outline, so the doors,
fenders and bedside share one continuous side surface with plan-view curvature (at4x_dims.bow), a crisp shoulder
crease and the rear haunch. Trim pieces (lamps, grille bars, bumpers) are lofted solids.

The work is split by region so each can be refined independently:
    ext_front.py  fenders, hood, cowl, fascia, headlamps, grille, front bumper
    ext_cab.py    doors, cab sides, greenhouse, mirrors, running boards
    ext_rear.py   bedsides, bed, tailgate, taillamps, rear bumper
    ext_common.py shared helpers
"""
from ext_cab import build_cab
from ext_common import mirror_side  # noqa: F401  (re-exported for at4x_body)
from ext_front import build_front
from ext_rear import build_rear


def build_exterior(mb):
    build_front(mb)
    build_cab(mb)
    build_rear(mb)
