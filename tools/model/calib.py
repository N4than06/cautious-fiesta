"""Camera calibration of the reference photos from hand-picked keypoints.

Each photo lists (pixel u, v in the 1024x768 image) <-> 3D point on the real truck, written in model space
(at4x_dims constants). A pinhole camera (location, target, roll, focal length) is solved by Nelder-Mead on
reprojection error. Residuals are printed per point: a consistent residual on one feature means the model's
dimension there differs from the real truck.

    python tools/model/calib.py OUT.json
"""
import json
import math
import sys

import bpy  # noqa: F401  (provides mathutils)
from mathutils import Matrix, Vector

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from at4x_dims import *  # noqa: F401,F403
from fitcam import nelder_mead

W, H = 1024, 768
XW = 0.97   # outer face of the tyres/flares

POINTS = {
    "02": [  # passenger side, nearly in profile, slight front
        ("front wheel centre", (808, 532), (XW, FAX, WZ)),
        ("rear wheel centre", (195, 488), (XW, RAX, WZ)),
        ("front tyre contact", (808, 607), (XW, FAX, GROUND)),
        ("rear tyre contact", (195, 545), (XW, RAX, GROUND)),
        ("cab roof rear corner", (316, 247), (0.84, Y_CAB_R, G(ZG_ROOF))),
        ("roof front corner", (598, 241), (0.80, Y_ROOF_F, G(1.955))),
        ("bed rear top corner", (60, 326), (1.0, Y_BED_R, G(ZG_RAIL))),
        ("bed front top corner", (298, 322), (1.0, Y_BED_F, G(ZG_RAIL))),
        ("B-pillar at belt", (478, 338), (0.96, 0.174, G(ZG_BELT))),
        ("headlamp top outer", (912, 366), (0.99, 2.79, G(1.30))),
        ("front tyre top", (808, 455), (XW, FAX, G(2 * TIRE_R))),
        ("rear tyre top", (195, 428), (XW, RAX, G(2 * TIRE_R))),
    ],
    "06": [  # front three-quarter, driver side
        ("front wheel centre", (485, 545), (-XW, FAX, WZ)),
        ("front tyre contact", (480, 640), (-XW, FAX, GROUND)),
        ("rear wheel centre", (848, 395), (-XW, RAX, WZ)),
        ("rear tyre contact", (845, 446), (-XW, RAX, GROUND)),
        ("headlamp top outer", (402, 314), (-0.99, 2.79, G(1.30))),
        ("headlamp top inner", (256, 318), (-0.665, 2.81, G(1.30))),
        ("GMC emblem centre", (104, 336), (0.0, 2.86, G(1.12))),
        ("roof front corner", (432, 150), (-0.80, Y_ROOF_F, G(1.955))),
        ("cab roof rear corner", (700, 142), (-0.84, Y_CAB_R, G(ZG_ROOF))),
        ("bed rear top corner", (912, 237), (-1.0, Y_BED_R, G(ZG_RAIL))),
    ],
    "03": [  # rear three-quarter, passenger side
        ("rear wheel centre", (565, 535), (XW, RAX, WZ)),
        ("rear tyre contact", (560, 633), (XW, RAX, GROUND)),
        ("front wheel centre", (910, 396), (XW, FAX, WZ)),
        ("front tyre contact", (906, 450), (XW, FAX, GROUND)),
        ("tailgate top driver corner", (75, 243), (-0.82, Y_BED_R, G(ZG_RAIL - 0.01))),
        ("bed rear top corner", (312, 262), (1.0, Y_BED_R, G(ZG_RAIL))),
        ("cab roof rear corner driver", (440, 155), (-0.84, Y_CAB_R, G(ZG_ROOF))),
        ("cab roof rear corner pass", (660, 150), (0.84, Y_CAB_R, G(ZG_ROOF))),
        ("hitch receiver", (155, 520), (0.0, REAR - 0.04, G(0.47))),
        ("taillamp bottom", (335, 438), (0.93, Y_BED_R - 0.01, G(0.99))),
    ],
}


def project(params, p):
    lx, ly, lz, tx, ty, tz, roll, lens = params
    loc, tgt = Vector((lx, ly, lz)), Vector((tx, ty, tz))
    rot = (tgt - loc).to_track_quat("-Z", "Y").to_matrix() @ Matrix.Rotation(roll, 3, "Z")
    c = rot.transposed() @ (Vector(p) - loc)
    if c.z >= -1e-6:
        return None
    f = lens / 36.0 * W
    return (W / 2 + f * c.x / -c.z, H / 2 - f * c.y / -c.z)


def solve(pts, x0):
    def err(params):
        lens = params[7]
        e = 0.0 if 18 <= lens <= 60 else 1e5 * (min(abs(lens - 18), abs(lens - 60)) + 1)
        if abs(params[6]) > 0.08:
            e += 1e5
        for _, uv, p in pts:
            q = project(params, p)
            if q is None:
                return 1e9
            e += (q[0] - uv[0]) ** 2 + (q[1] - uv[1]) ** 2
        return e
    import random
    rnd = random.Random(1)
    best, val = x0, err(x0)
    for trial in range(12):
        x = list(x0) if trial == 0 else [v + rnd.uniform(-1, 1) * d for v, d in
                                         zip(x0, [1.5, 1.5, 0.6, 0.3, 0.3, 0.2, 0.03, 8])]
        cand, cv = nelder_mead(err, x, [1.0, 1.0, 0.5, 0.3, 0.3, 0.2, 0.03, 5.0], iters=300)
        if cv < val:
            best, val = cand, cv
    for steps in ([1.0, 1.0, 0.5, 0.3, 0.3, 0.2, 0.05, 5.0], [0.3, 0.3, 0.15, 0.1, 0.1, 0.05, 0.02, 1.5],
                  [0.1, 0.1, 0.05, 0.03, 0.03, 0.02, 0.005, 0.5]):
        best, val = nelder_mead(err, best, steps, iters=400)
    return best, math.sqrt(val / len(pts))


GUESS = {
    "02": [6.2, 1.4, 2.1, 0, 0.0, 0.33, 0, 32],
    "06": [-3.2, 5.2, 0.7, 0, 0.0, 0.1, 0, 38],
    "03": [1.4, -7.0, 1.2, 0, 0.0, -0.06, 0, 47],
}

if __name__ == "__main__":
    out = {}
    for k, pts in POINTS.items():
        params, rms = solve(pts, GUESS[k])
        print(f"photo {k}: rms {rms:.1f}px  lens {params[7]:.1f}mm  cam ({params[0]:.2f},{params[1]:.2f},{params[2]:.2f})")
        for name, uv, p in pts:
            q = project(params, p)
            print(f"   {name:28s} du {q[0] - uv[0]:+6.1f}  dv {q[1] - uv[1]:+6.1f}")
        out[k] = dict(params=params, rms=rms)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    sys.stdout.flush()
    os._exit(0)
