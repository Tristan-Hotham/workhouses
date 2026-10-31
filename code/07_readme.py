"""README.md, LICENSE and reddit/post.md, with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
f = lambda p, k="int": fmt(get(R, p), k)
readme = f"""# What's left of the workhouse?

A map of the traces Britain and Ireland's workhouses left in the open record: surviving buildings and what they became, sites and memorials, burial grounds, streets and places named after them, and businesses that use the name. Built from the listed building registers of England, Scotland, Wales and Northern Ireland, OpenStreetMap, Wikidata and English Wikipedia: {f('traces.n')} traces grouped into {f('sites.n')} sites.

**This is not a complete list of workhouses.** There were around {f('context.ew_unions')} poor law unions in England and Wales and {f('context.ie_unions_1850s')} in Ireland by the 1850s; for the full record see Peter Higginbotham's https://www.workhouses.org.uk/ (not used as a source).

Interactive page: {PAGE}
Paper: https://doi.org/{{{{DOI}}}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/workhouses/}}

## Headline results

- {f('traces.n')} traces: {f('traces.by_kind.building')} surviving buildings, {f('traces.by_kind.site')} sites or memorials, {f('traces.by_kind.burial')} burial grounds, {f('traces.by_kind.name')} street or place names, {f('traces.by_kind.business')} businesses using the name ({f('traces.unplaced')} have no coordinates).
- {f('sites.n')} workhouse sites, {f('sites.by_status.building')} with a surviving building in the record; {f('sites.with_listed')} include a listed building. {f('listed.england_wales_ii_pct','pc')} of workhouse list entries in England and Wales are Grade II; the only Grade I is the poor house at Framlingham Castle ({f('listed.framlingham_built','raw')}).
- Where the record says what a surviving building became ({f('reuse.known')} of {f('reuse.n_building_sites')}): hospital {f('reuse.by.hospital')}, homes {f('reuse.by.homes')}, museum {f('reuse.by.museum')}, offices or community {f('reuse.by.offices')}, ruin {f('reuse.by.ruin')}, business {f('reuse.by.business')}, school {f('reuse.by.education')}. Hospitals and homes are {f('reuse.hosp_homes_pct','pc')}.
- {f('names.n')} streets, places and features carry the name ({f('names.lanes')} lanes), {f('names.england_pct','pc')} in England; Essex and Norfolk have {f('names.top_counties.0.n')} each.
- Ireland: {f('sites.ie.building_pct','pc')} of {f('sites.ie.n')} sites on the island have a surviving building in the record against {f('sites.gb.building_pct','pc')} in Britain, and {f('ireland.burial_ie')} of {f('ireland.burial_all')} mapped workhouse burial grounds are Irish, including the Kilkenny memorial to {f('ireland.kilkenny_n')} famine victims.
- The sources barely overlap: {f('sites.one_source_pct','pc')} of sites appear in only one of them.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/03_build_site.py`; trace data embedded, `data/counties.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/traces.csv` | Every trace: id, kind, name, nation, county, coordinates, later use, listed grade, confidence, site, source references, description. Contains OpenStreetMap data: ODbL 1.0. |
| `data/sites.csv` | {f('sites.n')} sites: status, later use, best grade, number of traces, sources, member names. ODbL 1.0 (derived in part from OpenStreetMap). |
| `data/excluded.csv` | {f('raw.excluded')} records found by the searches and removed, with the reason. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/counties.json`, `data/cities.json` | Page data: traces, county outlines with counts, town names. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates; `code/qa.js` is the browser check. |
| `release/` | Paper PDF and LaTeX source, blog figures, post and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Listed buildings: entry names containing workhouse, poorhouse, poor house, house of industry, union house, poor law, casual ward, board of guardians or vagrants; bridewells, houses of correction, pauper asylums and other false friends removed; farms, bridges and yards named after a workhouse count as names.
- OpenStreetMap: features named workhouse, union house, poor house or house of industry, classed by their tags; transformers, canal, insurer and credit union names and a townland removed.
- Wikidata (instances of workhouse and poorhouse in the UK and Ireland) and English Wikipedia's workhouse categories; poems, people, societies and almshouses removed.
- Duplicates merged by shared list entry, shared Wikidata item or near-identical names within 150 m; streets of the same name within 1.5 km count once; buildings, sites and burial grounds within 350 m form one site.
- Later use read from words in names, descriptions and tags ({f('method.n_ovr','int')} hand corrections); a house name counts as homes, which is weak evidence.
- History (1601, 1723, 1834, 1838, 1845, 1930, 1948) is from the literature (Slack 1990; Crowther 1981; Morrison 1999; O'Connor 1995; Kinealy 1994; Fowler 2007; Higginbotham 2012), not the data.

## Caveats

- Not a list of workhouses: name searches miss workhouses listed or mapped under later names (most hospital conversions), and OpenStreetMap, Wikidata and Wikipedia cover places unevenly.
- The Republic of Ireland's historic building inventory is not included, which lowers the Irish share of surviving buildings.
- A few 'Union House' entries are probable rather than certain workhouses (flagged in `confidence`).
- Later use is known for fewer than half of surviving buildings.

## How to rerun

Needs Python 3 with pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node and Playwright for the QA check. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw2/workhouse/` (OpenStreetMap Overpass JSON, Wikidata TSV and Wikipedia JSON, retrieved {R['meta']['retrieved']}), `/home/claude/newdata/raw2/listed-buildings/data/listed_*.csv.gz` (the Listed Kingdom study's harmonised registers) and `/home/claude/newdata/raw/geo/` (county outlines, Natural Earth). Intermediate files go to `/dev/shm/workhouses/work` (set `WHTMP` to change).

```
python3 code/01_traces.py      # find, classify, place, merge and group traces
python3 code/02_results.py     # results.json and page data
python3 code/03_build_site.py  # index.html (checks facts stated in words)
python3 code/04_figures.py     # header, blog and paper figures
python3 code/05_paper.py       # paper PDF
python3 code/07_readme.py      # README, LICENSE, reddit post
python3 code/06_release.py     # blog post, Zenodo files
python3 reddit/collage.py      # collage
LEAFLET_DIR=/path/to/node_modules/leaflet node code/qa.js   # browser QA, screenshots in qa/
```

## Sources and licences

- National Heritage List for England (Historic England), Historic Environment Scotland, Cadw and Northern Ireland Department for Communities listed building data. Open Government Licence v3.0.
- OpenStreetMap contributors (https://www.openstreetmap.org/copyright), via the Overpass API. ODbL 1.0.
- Wikidata (CC0), via QLever; English Wikipedia (CC BY-SA 4.0).
- ONS and OSNI boundaries (OGL); Natural Earth (public domain).
- Base map tiles on the page: © Esri.

## Licence

Code: MIT. Text, figures and derived data: CC BY 4.0, except `data/traces.csv` and `data/sites.csv`, which contain or derive from OpenStreetMap data and are shared under the ODbL 1.0. See `LICENSE`.

## Citation

Hotham, T. (2026) What's left of the workhouse? Traces of Britain and Ireland's workhouses in listed building registers, OpenStreetMap, Wikidata and Wikipedia. Zenodo. https://doi.org/{{{{DOI}}}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and data

Text, figures and derived data are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/, except data/traces.csv and data/sites.csv, which contain or are derived from OpenStreetMap data (c) OpenStreetMap contributors and are licensed under the Open Database License 1.0 (ODbL), https://opendatacommons.org/licenses/odbl/1-0/. Listed building data: Open Government Licence v3.0 (Historic England, Historic Environment Scotland, Cadw, Department for Communities NI). Wikidata: CC0. Wikipedia text: CC BY-SA 4.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""## Title

[OC] What's left of the workhouse? {f('traces.n')} traces of Britain and Ireland's workhouses in open data, and {f('ireland.burial_ie')} of the {f('ireland.burial_all')} mapped workhouse burial grounds are in Ireland

## Body

There is no open list of the workhouses of Britain and Ireland, so I mapped what they left behind in the listed building registers, OpenStreetMap, Wikidata and Wikipedia: {f('traces.n')} traces grouped into {f('sites.n')} sites, {f('sites.by_status.building')} with a surviving building. Where the record says what a surviving workhouse became, {f('reuse.hosp_homes_pct','pc')} are hospitals or homes. {f('names.n')} streets and places still carry the name, {f('names.england_pct','pc')} of them in England. In Ireland only {f('sites.ie.building_pct','pc')} of sites have a surviving building in the record, against {f('sites.gb.building_pct','pc')} in Britain, and almost all the workhouse burial grounds are Irish, a legacy of the famine. Caveat: this is far from complete ({f('sites.one_source_pct','pc')} of sites appear in only one source, and there were around {f('context.ew_unions')} unions in England and Wales alone). Interactive map: {PAGE}

## Source comment

Source: listed building registers of Historic England (NHLE), Historic Environment Scotland, Cadw and the NI Department for Communities (OGL v3.0); OpenStreetMap contributors via Overpass (ODbL 1.0); Wikidata via QLever (CC0); English Wikipedia workhouse categories (CC BY-SA 4.0); ONS, OSNI and Natural Earth outlines. History from Crowther (1981), Morrison (1999), O'Connor (1995) and Kinealy (1994). For the full record of any workhouse see workhouses.org.uk (not used as a source).

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: {{{{DOI_URL}}}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/workhouses/}}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme.replace("|---|---|", ""), lic, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t, bad
print("readme ok")
