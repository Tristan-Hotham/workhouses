"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; site.json, results and town names are embedded, data/counties.json is loaded by the page.
Facts stated in words are checked here against the data. The full-screen map snippet is pasted before </body>."""
import re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
T = jload(f"{WORK}/traces.json")
tr = T["traces"]; sites = T["sites"]
by = lambda **k: [x for x in tr if all(x[a] == b for a, b in k.items())]


def check_facts():
    """Facts stated in words in the page, paper and blog."""
    nm = lambda n, c: any(x["name"] == n and x["county"] == c for x in tr if x["kind"] == "name")
    assert nm("Workhouse Green", "Suffolk") and nm("Workhouse Green", "South Yorkshire") and nm("Workhouse End", "Bedfordshire") and nm("Workhouse End", "Lincolnshire")
    words = R["names"]["by_word"]
    assert words["Brook"] >= 1 and words["Coppice"] >= 1 and words["Cycleway"] >= 1 and words["Bridge"] >= 2 and words["Farm"] >= 2 and words["Wood"] >= 2 and words["Hill"] >= 1
    assert [x["n"] for x in R["names"]["top_counties"][:3]] == [8, 8, 7] and R["names"]["top_counties"][2]["county"] == "Hampshire"
    B = by(kind="business")
    txt = " ".join(x["name"] + " " + x["desc"] for x in B).lower()
    for w in ("gym", "cafe", "hairdresser", "camp_site"):
        assert w in txt, w
    assert R["business"]["at_site_names"] == ["Workhouse Coffee @ Battle Hospital", "the workhouse @ Llanfyllin Workhouse"]
    bur = by(kind="burial")
    ie_c = {x["county"] for x in bur if x["nation"] == "Ireland" and re.search(r"graveyard|burial ground", x["name"], re.I)}
    assert {"Donegal", "Clare", "Laois", "Tipperary"} <= ie_c, ie_c
    for n in ("Bantry Workhouse Cillín", "Loughlinstown Workhouse Cemetery", "Naas Workhouse Cemetery", "Bawnboy Workhouse Burial Ground"):
        assert any(x["name"] == n and x["nation"] == "Ireland" for x in bur), n
    gbb = [x for x in bur if x["nation"] in ("England", "Wales", "Scotland")]
    assert len(gbb) == 1 and gbb[0]["name"] == "Bath Union Workhouse Burial Ground" and "Unmarked graves" in gbb[0]["desc"]
    so = [x for x in tr if x["src"] == "osm" and x["kind"] == "site" and "site of" in x["name"].lower()]
    from collections import Counter
    c = Counter(x["county"] for x in so)
    LEIN = {"Dublin", "Meath", "Kildare", "Wicklow", "Louth", "Wexford", "Carlow", "Kilkenny", "Laois", "Offaly", "Longford", "Westmeath"}
    assert sum(v for k, v in c.items() if k in LEIN or k == "Kerry") > len(so) / 2 and {"Meath", "Dublin", "Wicklow", "Kerry"} <= {k for k, v in c.items() if v >= 3}, c
    mus = set(R["reuse"]["museums"])
    assert {"The Workhouse, Southwell", "Gressenhall Farm and Workhouse", "Llanfyllin Workhouse", "Lambeth Workhouse", "Workhouse Museum", "Donaghmore Famine Workhouse Museum", "Dunfanaghy Workhouse"} <= mus, mus
    rip = [s for s in sites if s["name"] == "Workhouse Museum"][0]; assert rip["county"] == "North Yorkshire"
    lam = [x for x in tr if any("Cinema Museum" in d for d in x["dups"])]; assert lam and lam[0]["reuse"] == "museum"
    bus = [x for x in tr if x["kind"] == "building" and x["reuse"] == "business"]
    assert any("Clothing Factory" in x["name"] for x in bus) and any("Studio" in x["name"] for x in bus)
    assert any("Crafts School" in x["name"] and x["reuse"] == "education" for x in tr)
    assert R["sites"]["nation_status"]["Northern Ireland"]["site"] == 0 and R["reuse"]["by_nation"]["Northern Ireland"]["hospital"] >= 3
    assert R["sites"]["ie"]["building_pct"] < R["sites"]["gb"]["building_pct"]
    for n in ("Black Isle Combination Poorhouse", "Upper Nithsdale Combination Poorhouse", "Combination Poorhouse, Bonar Bridge"):
        assert any(n.lower() in x["name"].lower() for x in tr), n
    assert R["listed"]["grades"]["England"]["I"] == 1 and R["raw"]["wd_abroad_top"][0]["name"] == "Germany"


def build():
    check_facts()
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE)).replace("/*CITIES*/", J(jload(f"{DATA}/cities.json")))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
