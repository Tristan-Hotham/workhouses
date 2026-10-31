"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
The Zenodo copy of the PDF is a hard link, so it takes no extra disk."""
import re, zipfile, json as _json
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_Whats_Left_of_the_Workhouse"
import importlib.util   # facts stated in words (shared with the page)
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "03_build_site.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.check_facts()

post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
post = re.sub(r"\{\{IMG\|([^|]+)\|([^|]+)\|([^}]+)\}\}", lambda mm: "{{IMG|%s|%s|%s}}" % (mm.group(1), fill(mm.group(2), R), mm.group(3)), post)
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\})", post), re.findall(r"\{\{[^}]*\}\}", post)[:4]
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "What's left of the workhouse? Buildings, street names and famine graves across Britain and Ireland",
        "slug": SLUG,
        "excerpt": f"There is no open list of Britain and Ireland's workhouses, so I mapped what they left behind in open data: {R['traces']['n']} traces, from hospitals and flats to Workhouse Lanes, and {R['ireland']['burial_ie']} of {R['ireland']['burial_all']} mapped workhouse burial grounds in Ireland.",
        "seo_description": f"A map of the traces Britain and Ireland's workhouses left in open data: surviving buildings, Workhouse Lanes and famine burial grounds.",
        "tags": ["workhouses", "poor law", "Irish famine", "listed buildings", "history", "maps", "data visualisation", "OpenStreetMap"],
        "header_alt": f"Title card reading 'What's left of the workhouse?' in black and brick red on cream, beside a map of Britain and Ireland dotted with {R['traces']['placed']} traces: brick red surviving buildings, ochre sites, dark green burial grounds mostly in Ireland, and slate blue Workhouse Lanes in eastern England."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
pdf = f"{REL}/paper/{NAME}.pdf"
if os.path.exists(f"{Z}/{NAME}.pdf"): os.remove(f"{Z}/{NAME}.pdf")
os.link(pdf, f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"{SLUG}/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "What's Left of the Workhouse? Traces of Britain and Ireland's Workhouses in Listed Building Registers, OpenStreetMap, Wikidata and Wikipedia",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: {BLOG}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["workhouses", "poor law", "Irish famine", "listed buildings", "historic environment", "historical geography", "OpenStreetMap", "Wikidata", "open data", "maps"],
         "license": "cc-by-4.0",
         "notes": "The traces table (data/traces.csv) contains OpenStreetMap data and is released under the ODbL 1.0.",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://doi.org/10.5281/zenodo.23761429", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.openstreetmap.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
