"""Every number quoted anywhere (page, paper, blog, collage, post) goes into data/results.json from here.
Also writes the page data: data/site.json (traces, sites and labels), data/counties.json (UK and Irish counties with
counts, simplified) and data/cities.json (town names for the map)."""
import re
from collections import Counter, defaultdict
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from common import *

T = jload(f"{WORK}/traces.json")
traces, sites, excl = T["traces"], T["sites"], T["excluded"]
KL = dict(T["kinds"]); RL = T["reuse_label"]
KORD = [k for k, _ in T["kinds"]]
RORD = ["hospital", "homes", "museum", "offices", "business", "education", "ruin"]
R = {"meta": {"slug": SLUG, "page": PAGE, "repo": REPO, "retrieved": RETRIEVED}}

# ---------------------------------------------------------------- sources
R["raw"] = {"osm": T["n_raw"]["osm"], "wd": T["n_raw"]["wd"], "wp": T["n_raw"]["wp"], "listed_hits": T["n_raw"]["listed"],
            "wd_gbie": sum(1 for x in traces for s in x["dups"] if s.startswith("wikidata:")) + sum(1 for e in excl if e["source"] == "wikidata"),
            "wd_abroad": sum(T["wd_abroad"].values()), "excluded": len(excl),
            "excluded_by_source": dict(Counter(e["source"] for e in excl))}
WDC = {"Q183": "Germany", "Q30": "United States", "Q213": "Czech Republic", "Q29": "Spain", "Q55": "Netherlands", "Q159": "Russia", "Q40": "Austria"}
R["raw"]["wd_abroad_top"] = [{"name": WDC.get(k, k), "n": n} for k, n in Counter(T["wd_abroad"]).most_common(5)]
assert R["raw"]["wd_abroad_top"][0]["name"] == "Germany"

# ---------------------------------------------------------------- traces
placed = [x for x in traces if x["lat"] is not None]
R["traces"] = {"n": len(traces), "placed": len(placed), "unplaced": len(traces) - len(placed),
               "by_kind": {k: sum(1 for x in traces if x["kind"] == k) for k in KORD},
               "by_nation": {n: sum(1 for x in traces if x["nation"] == n) for n in NATIONS},
               "nation_kind": {n: {k: sum(1 for x in traces if x["nation"] == n and x["kind"] == k) for k in KORD} for n in NATIONS},
               "by_source_records": dict(Counter(s.split(":")[0] for x in traces for s in x["dups"]))}
R["traces"]["britain"] = sum(R["traces"]["by_nation"][n] for n in ("England", "Wales", "Scotland"))
R["traces"]["ireland_all"] = R["traces"]["by_nation"]["Ireland"] + R["traces"]["by_nation"]["Northern Ireland"]
assert sum(R["traces"]["by_nation"].values()) == len(traces)

# ---------------------------------------------------------------- sites
def share(a, b): return round(100 * a / b, 1) if b else 0.0
S = {"n": len(sites), "by_status": {k: sum(1 for s in sites if s["status"] == k) for k in ("building", "site", "burial")},
     "nation_status": {n: {k: sum(1 for s in sites if s["nation"] == n and s["status"] == k) for k in ("building", "site", "burial")} for n in NATIONS},
     "by_nation": {n: sum(1 for s in sites if s["nation"] == n) for n in NATIONS}}
S["one_source"] = sum(1 for s in sites if "|" not in s["sources"])
S["one_source_pct"] = share(S["one_source"], len(sites))
S["multi_source"] = len(sites) - S["one_source"]
S["with_listed"] = sum(1 for s in sites if s["n_listed"])
S["building_pct"] = share(S["by_status"]["building"], len(sites))
for n in NATIONS:
    S.setdefault("building_pct_nation", {})[n] = share(S["nation_status"][n]["building"], S["by_nation"][n])
gb = [s for s in sites if s["nation"] in ("England", "Wales", "Scotland")]
ir = [s for s in sites if s["nation"] in ("Ireland", "Northern Ireland")]
S["gb"] = {"n": len(gb), "building": sum(s["status"] == "building" for s in gb), "site": sum(s["status"] == "site" for s in gb), "burial": sum(s["status"] == "burial" for s in gb),
           "with_burial": sum(bool(s["has_burial"]) for s in gb)}
S["ie"] = {"n": len(ir), "building": sum(s["status"] == "building" for s in ir), "site": sum(s["status"] == "site" for s in ir), "burial": sum(s["status"] == "burial" for s in ir),
           "with_burial": sum(bool(s["has_burial"]) for s in ir)}
for k in ("gb", "ie"):
    S[k]["building_pct"] = share(S[k]["building"], S[k]["n"]); S[k]["notbuilding_pct"] = round(100 - S[k]["building_pct"], 1)
    S[k]["with_burial_pct"] = share(S[k]["with_burial"], S[k]["n"])
cty = Counter((s["nation"], s["county"]) for s in sites if s["county"] and s["nation"] != "Northern Ireland")
S["top_counties"] = [{"nation": a, "county": b, "n": n} for (a, b), n in cty.most_common(8)]
S["n_counties"] = len(cty)
R["sites"] = S

# ---------------------------------------------------------------- what surviving buildings became
bs = [s for s in sites if s["status"] == "building"]
known = [s for s in bs if s["reuse"] not in ("unknown", "")]
RU = {"n_building_sites": len(bs), "known": len(known), "unknown": len(bs) - len(known), "known_pct": share(len(known), len(bs)),
      "by": {k: sum(1 for s in known if s["reuse"] == k) for k in RORD}}
RU["pct_of_known"] = {k: share(v, len(known)) for k, v in RU["by"].items()}
RU["order"] = sorted(RORD, key=lambda k: -RU["by"][k])
RU["hosp_homes"] = RU["by"]["hospital"] + RU["by"]["homes"]
RU["hosp_homes_pct"] = share(RU["hosp_homes"], len(known))
RU["by_nation"] = {n: {k: sum(1 for s in known if s["reuse"] == k and s["nation"] == n) for k in RORD} for n in NATIONS}
RU["museums"] = sorted(s["name"] for s in known if s["reuse"] == "museum")
assert RU["order"][:2] == ["hospital", "homes"], RU["order"]
R["reuse"] = RU

# ---------------------------------------------------------------- listed buildings
L = [x for x in traces if x["src"] == "listed" or any(d.startswith("listed:") for d in x["dups"])]
Lw = [x for x in L if x["kind"] in ("building", "site")]
GORD = {"England": ["I", "II*", "II"], "Wales": ["I", "II*", "II"], "Scotland": ["A", "B", "C"], "Northern Ireland": ["A", "B+", "B1", "B2", "B"]}
LS = {"n": len(Lw), "n_entries": sum(sum(1 for d in x["dups"] if d.startswith("listed:")) for x in Lw),
      "by_nation": {n: sum(1 for x in Lw if x["nation"] == n) for n in NATIONS[:4]},
      "grades": {n: {g: sum(1 for x in Lw if x["nation"] == n and x["grade"] == g) for g in GORD[n]} for n in GORD},
      "named_streets_listed": sum(1 for x in L if x["kind"] == "name"),
      "top_grade": [x["name"] for x in Lw if x["grade"] in ("I", "A")],
      "starred": sum(1 for x in Lw if x["grade"] == "II*")}
LS["sites_with_listed"] = S["with_listed"]; LS["all_entries"] = T["n_raw"]["listed_all"]
assert sum("famine" in x["name"].lower() for x in traces if x["nation"] in ("England", "Wales", "Scotland")) == 0
LS["england_wales_ii_pct"] = share(sum(1 for x in Lw if x["nation"] in ("England", "Wales") and x["grade"] == "II"), sum(1 for x in Lw if x["nation"] in ("England", "Wales")))
eng = [x for x in Lw if x["nation"] in ("England", "Wales")]
par = [x for x in eng if re.search(r"poor ?house|poors house|parish|poorhouses", x["name"], re.I)]
uni = [x for x in eng if re.search(r"union|hundred|house of industry|poor law|guardians|casual ward|vagrant", x["name"], re.I)]
LS["ew_named_poorhouse"] = len(par); LS["ew_named_union"] = len(uni)
LS["ew_old_workhouse"] = sum(1 for x in eng if re.fullmatch(r"(the )?old workhouse", x["name"].lower()))
assert LS["top_grade"] == ["Poor House to Framlingham Castle"], LS["top_grade"]
R["listed"] = LS

# ---------------------------------------------------------------- names and businesses
N = [x for x in traces if x["kind"] == "name"]
word = lambda nm: next((w for w in ("Lane", "Road", "Hill", "Green", "End", "Corner", "Farm", "Wood", "Coppice", "Brook", "Bridge", "Square", "Cycleway", "Cottage", "Close", "Field", "Mead", "Piece", "Lake", "Loke", "Bank", "Yard") if w.lower() in nm.lower()), "Other")
NW = Counter(word(x["name"]) for x in N)
roads = sum(NW[w] for w in ("Lane", "Road", "Hill", "Cycleway", "Square", "Loke", "Yard"))
nat = Counter(x["nation"] for x in N)
ncty = Counter(x["county"] for x in N if x["nation"] == "England")
R["names"] = {"n": len(N), "roads": roads, "lanes": NW["Lane"], "by_word": dict(NW.most_common()), "by_nation": {n: nat[n] for n in NATIONS},
              "england_pct": share(nat["England"], len(N)), "top_counties": [{"county": c, "n": n} for c, n in ncty.most_common(5)],
              "workhouse_word": sum(1 for x in N if "workhouse" in x["name"].lower()),
              "poorhouse_word": sum(1 for x in N if re.search(r"poor ?house", x["name"], re.I)),
              "east_england": sum(1 for x in N if x["county"] in ("Norfolk", "Suffolk", "Essex", "Cambridgeshire", "Hertfordshire", "Bedfordshire", "Lincolnshire")),
              "places": sorted({x["name"] for x in N if re.search(r"Green|End|Corner", x["name"])})}
R["names"]["east_england_pct"] = share(R["names"]["east_england"], len(N))
tc = R["names"]["top_counties"]
assert {tc[0]["county"], tc[1]["county"]} == {"Essex", "Norfolk"} and tc[0]["n"] == tc[1]["n"] > tc[2]["n"], tc
B = [x for x in traces if x["kind"] == "business"]
R["business"] = {"n": len(B), "at_site": sum(1 for x in B if x["at_site"]), "gyms": sum(1 for x in B if re.search(r"gym|fitness|sports", x["name"] + x["desc"], re.I)),
                 "cafes": sum(1 for x in B if re.search(r"cafe|coffee", x["name"] + x["desc"], re.I))}

# ---------------------------------------------------------------- Ireland and the famine
IE = [x for x in traces if x["nation"] in ("Ireland", "Northern Ireland")]
GB = [x for x in traces if x["nation"] in ("England", "Wales", "Scotland")]
bur = [x for x in traces if x["kind"] == "burial"]
kil = next(x for x in traces if "Paupers' Remains" in x["name"])
m = re.search(r"remains of (\d+) famine victims.*?between (\w+ \d{4}) and (\w+ \d{4})", kil["note"])
osm_site_of = [x for x in traces if x["src"] == "osm" and x["kind"] == "site" and re.search(r"site of", x["name"], re.I)]
R["ireland"] = {"traces": len(IE), "traces_rep": sum(1 for x in IE if x["nation"] == "Ireland"), "traces_ni": sum(1 for x in IE if x["nation"] == "Northern Ireland"),
                "burial_ie": sum(1 for x in bur if x["nation"] in ("Ireland", "Northern Ireland")), "burial_gb": sum(1 for x in bur if x["nation"] in ("England", "Wales", "Scotland")),
                "burial_all": len(bur), "famine_named": sorted(x["name"] for x in traces if "famine" in x["name"].lower()),
                "kilkenny_n": int(m.group(1)), "kilkenny_from": m.group(2), "kilkenny_to": m.group(3),
                "site_of_osm": len(osm_site_of), "site_of_counties": len({x["county"] for x in osm_site_of}),
                "rep_listed": 0, "rep_sites": S["by_nation"]["Ireland"], "rep_building": S["nation_status"]["Ireland"]["building"],
                "rep_site_only": S["nation_status"]["Ireland"]["site"], "rep_burial_only": S["nation_status"]["Ireland"]["burial"],
                "rep_counties": len({s["county"] for s in sites if s["nation"] == "Ireland"}),
                "names_ie": sum(1 for x in IE if x["kind"] == "name"), "names_gb": sum(1 for x in GB if x["kind"] == "name")}
R["ireland"]["burial_ie_pct"] = share(R["ireland"]["burial_ie"], len(bur))
R["ireland"]["rep_notbuilding_pct"] = share(R["ireland"]["rep_site_only"] + R["ireland"]["rep_burial_only"], R["ireland"]["rep_sites"])
assert R["ireland"]["kilkenny_n"] == 970

# ---------------------------------------------------------------- completeness against the historical record (numbers from the literature, not data)
CTX = {"ew_unions": 600, "ie_unions_1838": 130, "ie_unions_1850s": 163}
R["context"] = CTX
ew_sites = S["by_nation"]["England"] + S["by_nation"]["Wales"]
ie_sites = S["by_nation"]["Ireland"] + S["by_nation"]["Northern Ireland"]
R["complete"] = {"ew_sites": ew_sites, "ie_sites": ie_sites, "ie_pct_of_163": share(ie_sites, CTX["ie_unions_1850s"]),
                 "ew_union_named": LS["ew_named_union"], "scot_sites": S["by_nation"]["Scotland"]}

R["method"] = {"n_ovr": T["n_ovr"]}
fr = [x for x in traces if x["name"] == "Poor House to Framlingham Castle"][0]
R["listed"]["framlingham_built"] = int(re.search(r"inception (\d{4})", fr["desc"]).group(1)) if "inception" in fr["desc"] else None
assert R["listed"]["framlingham_built"] == 1729, fr["desc"]
R["business"]["at_site_names"] = sorted(x["name"] + " @ " + next(s["name"] for s in sites if s["site"] == x["at_site"]) for x in B if x["at_site"])

# ---------------------------------------------------------------- page data
CC = defaultdict(lambda: Counter())
for x in placed:
    CC[(x["nation"], x["county"])][x["kind"]] += 1
UKC = jload(f"{GEO}/counties_uk.geojson"); ADM1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
IEMAP = {"Dún Laoghaire–Rathdown": "Dublin", "Fingal": "Dublin", "South Dublin": "Dublin", "North Tipperary": "Tipperary", "South Tipperary": "Tipperary", "Laoighis": "Laois"}
feats = []
def addf(nation, county, geom):
    g = geom.simplify(.004, preserve_topology=True)
    gj = mapping(g)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 3), round(c[1], 3)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    c = CC[(nation, county)]
    feats.append({"type": "Feature", "properties": {"n": nation, "c": county, "k": {k: c[k] for k in KORD if c[k]}}, "geometry": gj})
for f in UKC["features"]:
    addf(f["properties"]["nation"], f["properties"]["county"], shape(f["geometry"]).buffer(0))
ie = defaultdict(list)
for f in ADM1["features"]:
    if f["properties"]["adm0_a3"] == "IRL":
        ie[IEMAP.get(f["properties"]["name"], f["properties"]["name"])].append(shape(f["geometry"]).buffer(0))
for k, v in ie.items():
    addf("Ireland", k, unary_union(v))
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/counties.json")
R["geo"] = {"n_counties_map": len(feats)}

PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in PP["features"]:
    p = f["properties"]
    if p.get("adm0_a3") in ("GBR", "IRL") or p.get("sov_a3") in ("GBR", "IRL"):
        lon, lat = f["geometry"]["coordinates"]
        if -11 < lon < 2.2 and 49.8 < lat < 61:
            cities.append({"name": p["name"], "lat": round(lat, 4), "lon": round(lon, 4), "pop": int(p.get("pop_max") or 0)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")

LINKS = lambda x: [d for d in x["dups"]]
rows = []
for x in placed:
    rows.append([x["id"], round(x["lon"], 5), round(x["lat"], 5), KORD.index(x["kind"]), x["name"], x["nation"], x["county"],
                 x["reuse"] or "", x["grade"] or "", x["site"] or x["at_site"] or "", x["desc"], LINKS(x), x["qid"], x["wp"], x["note"][:400], x["confidence"]])
unpl = [[x["id"], x["name"], x["nation"], KORD.index(x["kind"]), x["reuse"], x["desc"], x["qid"], x["wp"]] for x in traces if x["lat"] is None]
site_rows = [[s["site"], s["lon"], s["lat"], s["name"], s["nation"], s["county"], s["status"], s["reuse"], s["best_grade"], s["n_traces"], s["sources"], bool(s["has_burial"])] for s in sites]
jsave({"kinds": [[k, KL[k]] for k in KORD], "reuse": [[k, RL[k]] for k in RORD + ["unknown"]], "t": rows, "u": unpl, "s": site_rows}, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("traces", "sites", "reuse", "listed", "names", "business", "ireland", "complete")}, indent=0, ensure_ascii=False)[:6000])
