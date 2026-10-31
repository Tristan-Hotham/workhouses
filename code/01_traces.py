"""Read the four sources, keep the traces of workhouses and poorhouses in Great Britain and Ireland, classify each one
(surviving building; site or memorial; burial ground; street or place name; business using the name), say what a
surviving building became where the evidence says, place every trace in a nation and county, remove duplicates and
group building, site and burial traces into workhouse sites. Writes data/traces.csv, data/sites.csv,
data/excluded.csv and WORK/traces.json."""
import csv, glob, math, re
from collections import defaultdict, Counter
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
from common import *

# ---------------------------------------------------------------- geography: nations and counties
UKC = jload(f"{GEO}/counties_uk.geojson")
ADM1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
IEMAP = {"Dún Laoghaire–Rathdown": "Dublin", "Fingal": "Dublin", "South Dublin": "Dublin", "North Tipperary": "Tipperary",
         "South Tipperary": "Tipperary", "Laoighis": "Laois"}
polys = []
for f in UKC["features"]:
    polys.append((f["properties"]["nation"], f["properties"]["county"], shape(f["geometry"]).buffer(0)))
iep = defaultdict(list)
for f in ADM1["features"]:
    if f["properties"]["adm0_a3"] == "IRL":
        iep[IEMAP.get(f["properties"]["name"], f["properties"]["name"])].append(shape(f["geometry"]).buffer(0))
for k, v in iep.items():
    polys.append(("Ireland", k, unary_union(v)))
TREE = STRtree([p[2] for p in polys])


def locate(lat, lon):
    pt = Point(lon, lat)
    for i in TREE.query(pt):
        if polys[i][2].contains(pt):
            return polys[i][0], polys[i][1]
    i = TREE.nearest(pt)          # on the coast: nearest county
    if polys[i][2].distance(pt) < .05:
        return polys[i][0], polys[i][1]
    return None, None


# ---------------------------------------------------------------- reuse: what a surviving building became
REUSE = [  # key, label, pattern (tested in this order)
    ("museum", "Museum or heritage site", r"museum|heritage centre|national trust|\bvisitor"),
    ("hospital", "Hospital or health", r"hospital|infirmary|nurses|medical"),
    ("education", "School, college or university", r"college|school|universit"),
    ("offices", "Offices, council or community", r"offices?\b|council|headquarters|health board|village hall|community"),
    ("business", "Business, workshop or studio", r"premises|factory|studios?\b|crafts|\bshop\b|\bcafe\b|camp ?site|sports|fitness|\bgym\b|training|garage"),
    ("homes", "Homes, flats or a house name", r"flats|apartments|cottages?\b|\bgrange\b|\bthe close\b|\bcourt\b|\bhouse\b|\bhall\b|\boast\b|cuttings|residential|homes?\b"),
    ("ruin", "Ruin", r"\bruins?\b"),
]
REUSE_LABEL = {k: l for k, l, p in REUSE}
REUSE_LABEL["unknown"] = "Not stated"


def reuse_of(text):
    t = text.lower()
    t = re.sub(r"\b(south|north|east|west) of .*$|\bat rear of .*$|\b[\w']+ (road|street|lane|avenue|drive|rd)\b", " ", t)
    t = re.sub(r"work ?house|poor ?house|poors? house|union house|house of industry|keeper's house|school house at|poor law (hospital|offices)|parish hospital|"
               r"board of guardians offices|administrative block|administration block|entrance block|admissions building|casual wards?|chapel|laundry|"
               r"water tower|gate lodges?|was:amenity=hospital", " ", t)
    for k, l, p in REUSE:
        if re.search(p, t):
            return k
    return "unknown"


KINDS = [("building", "Surviving building"), ("site", "Site or memorial"), ("burial", "Burial ground"),
         ("name", "Street or place name"), ("business", "Business using the name")]
traces, excluded = [], []


def add(**k):
    k.setdefault("grade", ""); k.setdefault("reuse", ""); k.setdefault("qid", ""); k.setdefault("wp", ""); k.setdefault("note", "")
    k.setdefault("confidence", "named"); k.setdefault("listed_id", ""); k.setdefault("desc", "")
    traces.append(k)


def drop(src, ref, name, why):
    excluded.append({"source": src, "ref": ref, "name": name, "reason": why})


# ---------------------------------------------------------------- 1. listed buildings (the four UK lists)
LB = pd.concat([pd.read_csv(f, dtype={"id": str}).assign(list=re.sub(r"listed_|_part\d|\.csv\.gz", "", os.path.basename(f)))
                for f in sorted(glob.glob(f"{LISTED}/listed_*.csv.gz"))], ignore_index=True)
LB["name"] = LB["name"].fillna("")
HIT = re.compile(r"work ?house|poor ?house|poors house|house of industry|union house|poor law|casual ward|board of guardians|vagrants", re.I)
NOT = re.compile(r"grand union|norwich union|royal burgess|modern workhouse|pauper", re.I)
NAMEY = re.compile(r"workhouse (bridge|farm|green|yard)|lock up at workhouse farm|poorhouse barn|^\d+, workhouse", re.I)
LISTNAME = {"england": "Historic England (NHLE)", "scotland": "Historic Environment Scotland", "wales": "Cadw",
            "northern_ireland": "NI Department for Communities"}
for r in LB[LB["name"].str.contains(HIT)].itertuples():
    nm = r.name.strip()
    if NOT.search(nm):
        drop("listed", r.id, nm, "not a workhouse (insurance office, canal, golf club, asylum or ambiguous)"); continue
    kind = "name" if NAMEY.search(nm) else "site" if re.search(r"now demolished", nm, re.I) else "building"
    conf = "probable" if re.fullmatch(r"(the chamber |steading, old )?union house.*", nm.lower()) else "named"
    if nm.lower().startswith("the chamber union house"):
        drop("listed", r.id, nm, "house name, no evidence it was a workhouse"); continue
    pretty = nm.title() if nm.isupper() else nm
    pretty = re.sub(r"'S\b", "'s", pretty)
    pretty = re.sub(r"(?<=\S )(And|At|Of|To|The|On|In|For|By|Now|Formerly|Former|Including|Inclusive|Numbers|Number)\b", lambda m: m.group(1).lower() if m.group(1) not in ("Former", "Formerly", "Number", "Numbers", "Inclusive", "Including") else m.group(1).lower(), pretty)
    add(src="listed", ref=r.id, name=pretty, kind=kind, lat=r.lat, lon=r.lon, grade=str(r.grade), listed_id=r.id,
        reuse=reuse_of(nm) if kind == "building" else "", confidence=conf, desc=f"Listed Grade {r.grade}, {LISTNAME[r.list]}")

# ---------------------------------------------------------------- 2. Wikidata (instances of workhouse and poorhouse)
rows = list(csv.reader(open(f"{RAW}/workhouses_wd_class.tsv", encoding="utf-8"), delimiter="\t"))[1:]
q = lambda v: v.rsplit("/", 1)[-1].rstrip(">")
lab = lambda v: re.sub(r'^"?(.*?)"?(@\w+)?$', r"\1", v.strip())
WD = {}
for w, l, c, inc, ctry, typ in rows:
    qid = q(w)
    m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", c)
    e = WD.setdefault(qid, {"qid": qid, "label": lab(l), "lat": None, "lon": None, "inc": inc[:4], "country": q(ctry), "types": set()})
    e["types"].add(q(typ))
    if m: e["lon"], e["lat"] = float(m.group(1)), float(m.group(2))
WD_ABROAD = Counter()
for e in WD.values():
    if e["country"] not in ("Q145", "Q27", "Q174193"):
        WD_ABROAD[e["country"] or "none"] += 1
        continue
    add(src="wikidata", ref=e["qid"], qid=e["qid"], name=e["label"], kind="building", lat=e["lat"], lon=e["lon"],
        desc="Wikidata: " + " and ".join(sorted({"Q628155": "workhouse", "Q1929784": "poorhouse"}[t] for t in e["types"])) + (f", inception {e['inc']}" if e["inc"] else ""))

# ---------------------------------------------------------------- 3. English Wikipedia category pages
WP = jload(f"{RAW}/workhouses_wp.json")
NOTPLACE = {"Christmas Day in the Workhouse": "a poem", "Thomas Penson": "a person (architect)", "Huddersfield workhouse scandal": "an event",
            "Workhouse Visiting Society": "a society", "List of London workhouses": "a list", "Scottish poorhouse": "a general article",
            "Emma Sheppard": "a person (reformer)", "Glasgow Industrial School for Girls": "an industrial school, not a poorhouse"}
for p in WP["pages"]:
    t = p["t"]
    if t in NOTPLACE:
        drop("wikipedia", t, t, "not a place: " + NOTPLACE[t]); continue
    hit = [x for x in traces if x["qid"] and x["qid"] == p.get("q")]
    if hit:   # same item as Wikidata: add the article and its description
        for x in hit:
            x["wp"] = t; x["desc"] += f"; Wikipedia: {p.get('d') or ''}".rstrip(": ")
            if x["lat"] is None and p.get("lat"): x["lat"], x["lon"] = p["lat"], p["lon"]
        continue
    add(src="wikipedia", ref=t, qid=p.get("q") or "", wp=t, name=t, kind="building", lat=p.get("lat"), lon=p.get("lon"),
        desc="Wikipedia: " + (p.get("d") or p["cat"].replace("Category:", "")))

# ---------------------------------------------------------------- 4. OpenStreetMap
OSM = jload(f"{RAW}/workhouses_osm.json")["elements"]
for e in OSM:
    t = e.get("tags", {}); nm = t.get("name", "").strip(); c = e.get("center", {})
    lat, lon = e.get("lat", c.get("lat")), e.get("lon", c.get("lon")); ref = f"{e['type']}/{e['id']}"
    low = nm.lower()
    if re.search(r"grand union|norwich union|credit union|european union", low):
        drop("osm", ref, nm, "named after something else (canal, insurer, credit union)"); continue
    if re.search(r"transformer|substation", low):
        drop("osm", ref, nm, "electricity asset named after a local place"); continue
    if nm == "Castleworkhouse":
        drop("osm", ref, nm, "townland name (Caisleán Mhurchú), not from a workhouse"); continue
    if low.startswith("union house") and t.get("building") != "apartments":
        drop("osm", ref, nm, "'Union House' with no evidence it was a workhouse (student union, farm, café)"); continue
    tagtxt = " ".join(f"{k}={v}" for k, v in t.items() if k in ("amenity", "building", "historic", "tourism", "leisure", "shop", "landuse", "memorial", "highway", "place", "description", "was:amenity"))
    if re.search(r"amenity=(cafe|internet_cafe|training)|leisure=(sports_centre|fitness_centre)|shop=|tourism=camp_site", tagtxt):
        kind = "business"
    elif re.search(r"grave_yard|cemetery|memorial=grave", tagtxt) or re.search(r"burial|cemetery|graveyard|cillín|paupers' remains", low):
        kind = "burial"
    elif re.search(r"site of|, site of", low) or re.search(r"historic=(memorial|archaeological_site)|tourism=information", tagtxt) or re.search(r"\bwalk\b|memorial", low):
        kind = "site"
    elif "tourism=museum" in tagtxt:
        kind = "building"
    elif re.search(r"highway=|place=|landuse=(farmyard|meadow|forest)|leisure=garden", tagtxt) or re.search(r"\b(lane|road|hill|green|end|corner|farm|wood|brook|lake|bridge|cottage|bank|coppice|field|mead|piece|close|cycleway|square|loke)\b", low):
        kind = "name"
    elif re.search(r"building=|historic=|tourism=museum|amenity=(place_of_worship|mortuary)", tagtxt):
        kind = "building"
    elif e["type"] == "relation":
        kind = "site"
    else:
        kind = "name"
    if kind == "name" and "Workhouse Garden" in nm:
        kind = "site"
    reuse = reuse_of(nm + " " + tagtxt.replace("building=yes", "")) if kind == "building" else ""
    if kind == "building" and t.get("building") == "apartments": reuse = "homes"
    add(src="osm", ref=ref, qid=t.get("wikidata", "") if t.get("wikidata") != "Q628155" else "", name=nm, kind=kind, lat=lat, lon=lon,
        reuse=reuse, confidence="probable" if low.startswith("union house") else "named",
        desc="OpenStreetMap: " + tagtxt + (f"; inscription: {t['inscription']}" if t.get("inscription") else "") + (f"; note: {t['note']}" if t.get("note") else ""),
        note=t.get("inscription", ""))

# Wikidata items that are not poor law workhouses
for x in list(traces):
    if x["src"] == "wikidata" and re.search(r"asylum|alms house", x["name"], re.I):
        traces.remove(x); drop("wikidata", x["ref"], x["name"], "almshouse or charitable asylum, not a poor law workhouse")

# ---------------------------------------------------------------- reuse for Wikidata and Wikipedia buildings
for x in traces:
    if x["kind"] == "building" and x["src"] in ("wikidata", "wikipedia"):
        x["reuse"] = reuse_of(x["name"] + " " + x["desc"].replace("Workhouse in", "").replace("Former workhouse", "").replace("Building in", "").replace("Historic building", "").replace("Grade II listed building", "").replace("listed building", ""))
    if x["kind"] == "building" and re.search(r"\bsite of\b", x["name"], re.I):
        x["kind"] = "site"; x["reuse"] = ""

# hand corrections where the words mislead (checked against the item's own description or article)
OVR = {"Windsor House": ("unknown", "hospital campus building; use not stated"), "Clifton House, Belfast": ("unknown", "Belfast Charitable Society poorhouse; use not stated in the data"),
       "Spinning House": ("unknown", "demolished; 'house' is the original name"), "Sayes Court": ("unknown", "'court' is the original manor name"),
       "Wexford Union Workhouse": ("ruin", "OpenStreetMap: ruins of workhouse and old hospital"), "Old Hospital & Workhouse": ("ruin", "OpenStreetMap: ruins"),
       "Erpingham Union Workhouse": ("ruin", "OpenStreetMap: ruined hospital wing"), "The Workhouse, Southwell": ("museum", "National Trust museum (Wikipedia article)"),
       "Southwell Workhouse": ("museum", "National Trust museum (Wikipedia article)")}
N_OVR = 0
for x in traces:
    if x["name"] in OVR and x["kind"] == "building":
        x["reuse"], x["note"] = OVR[x["name"]]; N_OVR += 1

# ---------------------------------------------------------------- link Wikidata/Wikipedia/OSM buildings to list entries (grade)
LBg = LB.dropna(subset=["lat", "lon"])
from shapely.strtree import STRtree as _T
lbpts = [Point(a, b) for a, b in zip(LBg.lon, LBg.lat)]
lbtree = _T(lbpts)
STOP = set("the of and at to former old house building block former workhouse union poorhouse poor hospital road street lane including".split())
for x in traces:
    if x["src"] == "listed" or x["kind"] != "building" or x["lat"] is None:
        continue
    toks = {w for w in norm(x["name"]).split() if len(w) > 3 and w not in STOP}
    best = None
    for i in lbtree.query(Point(x["lon"], x["lat"]).buffer(.004)):
        r = LBg.iloc[i]
        d = hav(x["lat"], x["lon"], r.lat, r.lon)
        ln = norm(r["name"])
        same = norm(x["name"]) == ln or (toks and toks <= set(ln.split())) or (HIT.search(r["name"]) and d < 150)
        if same and d < 300 and (best is None or d < best[0]):
            best = (d, r)
    if best is not None:
        x["grade"] = str(best[1].grade); x["listed_id"] = best[1].id

# ---------------------------------------------------------------- place, nation, county
for x in traces:
    if x["lat"] is None or (isinstance(x["lat"], float) and math.isnan(x["lat"])):
        x["lat"] = x["lon"] = None; x["nation"] = x["county"] = ""
        if x["qid"] in ("Q27",):
            pass
        continue
    x["lat"], x["lon"] = round(float(x["lat"]), 5), round(float(x["lon"]), 5)
    n, c = locate(x["lat"], x["lon"])
    x["nation"], x["county"] = n or "", c or ""
# unplaced items: nation from their description or list where possible
for x in traces:
    if not x["nation"]:
        d = x["desc"] + " " + x["name"]
        x["nation"] = ("Northern Ireland" if re.search(r"Northern Ireland|Belfast", d) else "Wales" if re.search(r"Wales|Welsh|Llan|Crickhowell|Newcastle-in-Emlyn|Cardiff", d)
                       else "Scotland" if re.search(r"Scotland|Scottish", d) else "England" if re.search(r"England|London|Bristol|Cambridge|Suffolk|Lancaster|Stortford|Ashton|Whittlesey|Winchelsea|Reading|Sculcoates|Aldershot|Rugby|Derbyshire|Easingwold|Pancras|Stowmarket|Liverpool|Leytonstone|Weymouth", d) else "")

# ---------------------------------------------------------------- remove duplicates within a source and across sources
def dedupe(ts, radius, key):
    keep = []
    for x in ts:
        dup = None
        for y in keep:
            if key(x) == key(y) and x["lat"] is not None and y["lat"] is not None and hav(x["lat"], x["lon"], y["lat"], y["lon"]) < radius:
                dup = y; break
        if dup is None:
            x["dups"] = [x["src"] + ":" + str(x["ref"])]; keep.append(x)
        else:
            dup["dups"].append(x["src"] + ":" + str(x["ref"]))
    return keep


SRCRANK = {"listed": 0, "wikidata": 1, "wikipedia": 2, "osm": 3}
traces.sort(key=lambda x: (SRCRANK[x["src"]], str(x["ref"])))
# same street, place or business name: one trace per name per 1.5 km (streets are split into many ways)
named = dedupe([x for x in traces if x["kind"] in ("name", "business")], 1500, lambda x: (x["kind"], re.sub(r"^opp ", "", norm(x["name"]))))
# the same building or item in two sources (Wikidata item of a list entry, OSM way linked to a Wikidata item): same list
# entry, same Wikidata item, or a near-identical name within 150 m
rest = [x for x in traces if x["kind"] not in ("name", "business")]
for x in rest:
    x["qids"] = {x["qid"]} - {""}
keep = []
for x in rest:
    dup = None
    for y in keep:
        if x["kind"] != y["kind"] and not ({x["kind"], y["kind"]} <= {"building", "site"}):
            continue
        same_lb = x["listed_id"] and x["listed_id"] == y["listed_id"]
        same_q = x["qid"] and x["qid"] == y["qid"]
        near = x["lat"] is not None and y["lat"] is not None and hav(x["lat"], x["lon"], y["lat"], y["lon"]) < 150
        sim = norm(x["name"])[:18] == norm(y["name"])[:18] or norm(x["name"]) in norm(y["name"]) or norm(y["name"]) in norm(x["name"])
        if same_lb or same_q or (near and sim):
            dup = y; break
    if dup is None:
        x["dups"] = [x["src"] + ":" + str(x["ref"])]; keep.append(x)
    else:
        dup["dups"].append(x["src"] + ":" + str(x["ref"])); dup["qids"] |= {x["qid"]} - {""}
        if x["desc"] and x["desc"] not in dup["desc"]: dup["desc"] += "; " + x["desc"]
        if x["note"] and not dup["note"]: dup["note"] = x["note"]
        for k in ("qid", "wp", "grade", "listed_id"):
            if not dup[k] and x[k]: dup[k] = x[k]
        if dup["lat"] is None and x["lat"] is not None:
            for k in ("lat", "lon", "nation", "county"): dup[k] = x[k]
        if dup["reuse"] in ("", "unknown") and x["reuse"] not in ("", "unknown"): dup["reuse"] = x["reuse"]
        if x["kind"] == "building" and dup["kind"] == "site": dup["kind"] = "building"
# items with no coordinates (Wikipedia or Wikidata only): merge into a placed trace whose name holds all their distinctive words
GEN = set("the of and workhouse union poorhouse poor house industry parish former old building hospital".split())
for x in [k for k in keep if k["lat"] is None]:
    toks = {w for w in norm(x["name"]).split() if w not in GEN}
    if (not toks or x["name"].startswith("St ")) and not x["qid"]:
        continue
    cand = [y for y in keep if y["lat"] is not None and y["kind"] in ("building", "site") and (toks <= set(norm(y["name"]).split()) or (x["qid"] and x["qid"] in y["qids"]))]
    if cand and all(hav(c["lat"], c["lon"], cand[0]["lat"], cand[0]["lon"]) < 500 for c in cand):
        y = cand[0]; keep.remove(x); y["dups"] += x["dups"]
        for k in ("qid", "wp"):
            if not y[k] and x[k]: y[k] = x[k]
        if y["reuse"] in ("", "unknown") and x["reuse"] not in ("", "unknown"): y["reuse"] = x["reuse"]
# the same memorial walk or plaque mapped twice
k2 = []
for x in keep:
    d = next((y for y in k2 if x["kind"] == y["kind"] == "site" and norm(x["name"]) == norm(y["name"]) and hav(x["lat"], x["lon"], y["lat"], y["lon"]) < 2000), None)
    if d: d["dups"] += x["dups"]
    else: k2.append(x)
keep = k2
traces = keep + named
n_raw = {"listed_all": len(LB), "listed": int(LB["name"].str.contains(HIT).sum()), "osm": len(OSM), "wd": len(WD), "wp": len(WP["pages"])}

# ---------------------------------------------------------------- group into sites (buildings, sites, burial grounds within 350 m)
pts = [x for x in traces if x["kind"] in ("building", "site", "burial") and x["lat"] is not None]
parent = list(range(len(pts)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for i in range(len(pts)):
    for j in range(i + 1, len(pts)):
        if hav(pts[i]["lat"], pts[i]["lon"], pts[j]["lat"], pts[j]["lon"]) < 350:
            parent[find(i)] = find(j)
groups = defaultdict(list)
for i, x in enumerate(pts):
    groups[find(i)].append(x)
RANK = ["museum", "hospital", "education", "offices", "business", "homes", "ruin"]
GR = {"I": 1, "A": 1, "II*": 2, "B+": 2, "B": 3, "B1": 3, "B2": 3, "II": 4, "C": 5}
sites = []
for k, g in groups.items():
    kinds = {x["kind"] for x in g}
    status = "building" if "building" in kinds else "site" if "site" in kinds else "burial"
    reuses = [x["reuse"] for x in g if x["reuse"] and x["reuse"] != "unknown"]
    reuse = min(reuses, key=RANK.index) if reuses else ("unknown" if status == "building" else "")
    grades = [x["grade"] for x in g if x["grade"]]
    best = min(grades, key=lambda s: GR.get(s, 9)) if grades else ""
    WW = re.compile(r"work ?house|poor ?house|union|house of industry", re.I)
    main = sorted(g, key=lambda x: (["building", "site", "burial"].index(x["kind"]), 0 if x["wp"] and WW.search(x["wp"]) else 1 if x["wp"] else 2,
                                    0 if WW.search(x["name"]) and not re.search(r"chapel|laundry|water tower|lodge|casual|entrance|gate|admissions|fountain|cottages?|burial", x["name"], re.I) else 1, len(x["name"])))[0]
    title = main["wp"] if main["wp"] and (WW.search(main["wp"]) or not WW.search(main["name"])) else main["name"]
    lat = sum(x["lat"] for x in g) / len(g); lon = sum(x["lon"] for x in g) / len(g)
    sid = f"S{len(sites) + 1:03d}"
    for x in g: x["site"] = sid
    sites.append({"site": sid, "name": title, "lat": round(lat, 5), "lon": round(lon, 5), "nation": main["nation"], "county": main["county"],
                  "status": status, "reuse": reuse, "best_grade": best, "n_traces": len(g), "n_listed": sum(1 for x in g if x["src"] == "listed" or x["listed_id"]),
                  "has_burial": "burial" in kinds, "has_memorial": "site" in kinds,
                  "sources": "|".join(sorted({s.split(":")[0] for x in g for s in x["dups"]})), "members": "|".join(x["name"] for x in g)})
# businesses using the name at a workhouse site: they occupy the old buildings
for x in traces:
    x.setdefault("site", "")
    if x["kind"] == "business":
        near = [s for s in sites if hav(x["lat"], x["lon"], s["lat"], s["lon"]) < 400]
        x["at_site"] = near[0]["site"] if near else ""
    else:
        x["at_site"] = ""

# ---------------------------------------------------------------- write
traces.sort(key=lambda x: (NATIONS.index(x["nation"]) if x["nation"] in NATIONS else 9, x["county"], x["name"]))
for i, x in enumerate(traces):
    x["id"] = f"T{i + 1:03d}"
COLS = ["id", "kind", "name", "nation", "county", "lat", "lon", "reuse", "grade", "confidence", "site", "at_site", "src", "ref", "listed_id", "qid", "wp", "desc", "dups"]
with open(f"{DATA}/traces.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(COLS[:-1] + ["sources"])
    for x in traces:
        w.writerow([dash(str(x[c])) if x[c] is not None else "" for c in COLS[:-1]] + ["|".join(x["dups"])])
pd.DataFrame(sites).to_csv(f"{DATA}/sites.csv", index=False)
pd.DataFrame(excluded).to_csv(f"{DATA}/excluded.csv", index=False)
for x in traces:
    x.pop("qids", None)
jsave({"traces": traces, "sites": sites, "excluded": excluded, "n_raw": n_raw, "wd_abroad": WD_ABROAD, "n_ovr": N_OVR,
       "kinds": KINDS, "reuse_label": REUSE_LABEL}, f"{WORK}/traces.json")
print(len(traces), "traces;", Counter(x["kind"] for x in traces), "\n", len(sites), "sites", Counter(s["status"] for s in sites),
      "\nexcluded", len(excluded), "\nunplaced", sum(1 for x in traces if x["lat"] is None))
print(Counter((x["nation"], x["kind"]) for x in traces))
