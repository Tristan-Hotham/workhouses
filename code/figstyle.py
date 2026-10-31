"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the whitewash and brick palette, kind and reuse colours, and the outline of Britain and Ireland
(UK counties and Irish counties from data/counties.json) in the LAEA Europe projection (EPSG:3035)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FONTS = os.environ.get("WH_FONTS", "/home/claude/ref/fonts")
FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6B645C", "axes.labelcolor": "#24201D",
                     "xtick.color": "#6B645C", "ytick.color": "#6B645C"})
BG, FG, MUT, LAND, RULE, HOT, COOL, MOSS = "#F6F2EA", "#24201D", "#6B645C", "#E4DCCD", "#D8CFBE", "#9C3B26", "#3F5E73", "#2F5D50"
KC = {"building": "#9C3B26", "site": "#C98A2B", "burial": "#2F5D50", "name": "#4F6D8A", "business": "#9A8FA3"}
KL = {"building": "Surviving building", "site": "Site or memorial", "burial": "Burial ground", "name": "Street or place name", "business": "Business using the name"}
RC = {"hospital": "#3F6FA0", "homes": "#C2643A", "museum": "#7A4E9A", "offices": "#6B7F3A", "business": "#B8962E", "education": "#2E8C8C", "ruin": "#7D7268", "unknown": "#B9B0A2"}
RL = {"hospital": "Hospital or health", "homes": "Homes, flats or a house name", "museum": "Museum or heritage site", "offices": "Offices, council or community",
      "business": "Business, workshop or studio", "education": "School, college or university", "ruin": "Ruin", "unknown": "Not stated"}
PJ = Transformer.from_crs(4326, 3035, always_xy=True)
CT = jload(f"{DATA}/counties.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in CT["features"]:
    ps = []
    for ring in rings(f["geometry"]):
        x, y = PJ.transform(ring[:, 0], ring[:, 1])
        ps.append(np.column_stack([x, y]))
    SHAPES.append((f["properties"]["n"], f["properties"]["c"], ps))
X0, Y0 = PJ.transform(-10.7, 51.3)
EXT = (2.86e6, 3.83e6, 3.04e6, 4.36e6)        # Britain and Ireland in EPSG:3035 (x0, x1, y0, y1)


def isles(ax, fc=LAND, ec="#FFFFFF", lw=.35, colour_of=None, ext=EXT):
    for n, c, ps in SHAPES:
        col = colour_of(n, c) if colour_of else None
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=col or fc, ec=ec, lw=lw, zorder=1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def proj(lon, lat):
    return PJ.transform(np.asarray(lon), np.asarray(lat))


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
