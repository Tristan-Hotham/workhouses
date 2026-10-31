"""Shared paths and helpers for the workhouses project.

Raw inputs (read in place, never modified; nothing is fetched by these scripts):
  /home/claude/newdata/raw2/workhouse/workhouses_osm.json      Overpass API JSON: 230 OpenStreetMap elements in Great Britain
                                                               and Ireland whose name matches workhouse, union house, poor
                                                               house or house of industry (tags and centre points). ODbL.
  /home/claude/newdata/raw2/workhouse/workhouses_wd_class.tsv  Wikidata (QLever TSV): instances of workhouse (Q628155) and
                                                               poorhouse (Q1929784) worldwide: item, label, coordinates,
                                                               inception, country, class. CC0.
  /home/claude/newdata/raw2/workhouse/workhouses_wp.json       English Wikipedia: pages in the workhouse categories for the UK
                                                               and Ireland, with coordinates (some), Wikidata ID and short
                                                               description. CC BY-SA 4.0.
  /home/claude/newdata/raw2/listed-buildings/data/listed_*.csv.gz
                                                               Every UK list entry (the Listed Kingdom study): Historic England
                                                               NHLE, Historic Environment Scotland, Cadw, NI Department for
                                                               Communities. Open Government Licence.
  /home/claude/newdata/raw/geo/counties_uk.geojson             England ceremonial counties, Welsh preserved counties, Scottish
                                                               council areas, Northern Ireland (ONS / OSNI, OGL).
  /home/claude/newdata/raw/geo/ne_10m_admin_1_states_provinces.geojson, ne_10m_populated_places_simple.geojson,
  ne_50m_land.geojson                                          Natural Earth (public domain): Irish counties, towns, coastline.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("WH_RAW", "/home/claude/newdata/raw2/workhouse")
LISTED = os.environ.get("WH_LISTED", "/home/claude/newdata/raw2/listed-buildings/data")
GEO = os.environ.get("WH_GEO", "/home/claude/newdata/raw/geo")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("WHTMP", "/dev/shm/workhouses"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "workhouses"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "{{DOI}}"            # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/workhouses/"      # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
NATIONS = ["England", "Wales", "Scotland", "Northern Ireland", "Ireland"]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from the sources (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "word":
        w = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    raise ValueError(f)


def fill(text, R, fmtf=fmt, keep=("DOI", "BLOG_URL", "DOI_URL")):
    """Replace {{path|format}} tokens with values from results.json; leave the publisher's placeholders alone."""
    def rep(m):
        if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE_"):
            return m.group(0)
        return fmtf(get(R, m.group(1)), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def hav(lat1, lon1, lat2, lon2):
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))
