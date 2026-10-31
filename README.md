# What's left of the workhouse?

A map of the traces Britain and Ireland's workhouses left in the open record: surviving buildings and what they became, sites and memorials, burial grounds, streets and places named after them, and businesses that use the name. Built from the listed building registers of England, Scotland, Wales and Northern Ireland, OpenStreetMap, Wikidata and English Wikipedia: 356 traces grouped into 205 sites.

**This is not a complete list of workhouses.** There were around 600 poor law unions in England and Wales and 163 in Ireland by the 1850s; for the full record see Peter Higginbotham's https://www.workhouses.org.uk/ (not used as a source).

Interactive page: https://maps.tristanhotham.com/workhouses/
Paper: https://doi.org/10.5281/zenodo.23844517
Blog post: https://blog.tristanhotham.com/2026/10/31/workhouses/

## Headline results

- 356 traces: 212 surviving buildings, 32 sites or memorials, 15 burial grounds, 84 street or place names, 13 businesses using the name (27 have no coordinates).
- 205 workhouse sites, 168 with a surviving building in the record; 117 include a listed building. 96% of workhouse list entries in England and Wales are Grade II; the only Grade I is the poor house at Framlingham Castle (1729).
- Where the record says what a surviving building became (80 of 168): hospital 30, homes 29, museum 8, offices or community 5, ruin 4, business 3, school 1. Hospitals and homes are 74%.
- 84 streets, places and features carry the name (32 lanes), 92% in England; Essex and Norfolk have 8 each.
- Ireland: 55% of 62 sites on the island have a surviving building in the record against 94% in Britain, and 14 of 15 mapped workhouse burial grounds are Irish, including the Kilkenny memorial to 970 famine victims.
- The sources barely overlap: 82% of sites appear in only one of them.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/03_build_site.py`; trace data embedded, `data/counties.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/traces.csv` | Every trace: id, kind, name, nation, county, coordinates, later use, listed grade, confidence, site, source references, description. Contains OpenStreetMap data: ODbL 1.0. |
| `data/sites.csv` | 205 sites: status, later use, best grade, number of traces, sources, member names. ODbL 1.0 (derived in part from OpenStreetMap). |
| `data/excluded.csv` | 36 records found by the searches and removed, with the reason. |
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
- Later use read from words in names, descriptions and tags (9 hand corrections); a house name counts as homes, which is weak evidence.
- History (1601, 1723, 1834, 1838, 1845, 1930, 1948) is from the literature (Slack 1990; Crowther 1981; Morrison 1999; O'Connor 1995; Kinealy 1994; Fowler 2007; Higginbotham 2012), not the data.

## Caveats

- Not a list of workhouses: name searches miss workhouses listed or mapped under later names (most hospital conversions), and OpenStreetMap, Wikidata and Wikipedia cover places unevenly.
- The Republic of Ireland's historic building inventory is not included, which lowers the Irish share of surviving buildings.
- A few 'Union House' entries are probable rather than certain workhouses (flagged in `confidence`).
- Later use is known for fewer than half of surviving buildings.

## How to rerun

Needs Python 3 with pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node and Playwright for the QA check. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw2/workhouse/` (OpenStreetMap Overpass JSON, Wikidata TSV and Wikipedia JSON, retrieved 2026), `/home/claude/newdata/raw2/listed-buildings/data/listed_*.csv.gz` (the Listed Kingdom study's harmonised registers) and `/home/claude/newdata/raw/geo/` (county outlines, Natural Earth). Intermediate files go to `/dev/shm/workhouses/work` (set `WHTMP` to change).

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

Hotham, T. (2026) What's left of the workhouse? Traces of Britain and Ireland's workhouses in listed building registers, OpenStreetMap, Wikidata and Wikipedia. Zenodo. https://doi.org/10.5281/zenodo.23844517

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
