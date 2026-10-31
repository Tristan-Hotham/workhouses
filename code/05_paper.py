"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex."""
import re, shutil, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Whats_Left_of_the_Workhouse"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "word": return fmt(v, "word")
    return tex(str(v))


src = R["traces"]["by_source_records"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was searched, records kept as traces (before merging) and licences.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.6cm}>{\\raggedright\\arraybackslash}p{6.2cm}r>{\\raggedright\\arraybackslash}p{2.3cm}}\\toprule Source & Searched & Kept & Licence\\\\\\midrule\n"
      f"UK listed building registers & {R['listed']['all_entries']:,} list entries, by name & {src['listed']:,} & OGL v3.0\\\\\n"
      f"OpenStreetMap & {R['raw']['osm']:,} named features & {src['osm']:,} & ODbL 1.0\\\\\n"
      f"Wikidata & {R['raw']['wd_gbie']:,} workhouse and poorhouse items in UK and Ireland & {src['wikidata']:,} & CC0\\\\\n"
      f"English Wikipedia & {R['raw']['wp']:,} category pages & {src['wikipedia']:,} & CC BY-SA 4.0\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
NAT = ["England", "Wales", "Scotland", "Northern Ireland", "Ireland"]
K = [("building", "Building"), ("site", "Site"), ("burial", "Burial"), ("name", "Name"), ("business", "Business")]
rows = ""
for n in NAT:
    v = R["traces"]["nation_kind"][n]
    rows += f"{n} & " + " & ".join(str(v[k]) for k, _ in K) + f" & {R['traces']['by_nation'][n]} & {R['sites']['by_nation'][n]}\\\\\n"
tot = R["traces"]["by_kind"]
rows += "\\midrule All & " + " & ".join(str(tot[k]) for k, _ in K) + f" & {R['traces']['n']} & {R['sites']['n']}\\\\\n"
assert sum(R["traces"]["by_nation"].values()) == R["traces"]["n"] and sum(R["sites"]["by_nation"].values()) == R["sites"]["n"]
TK = ("\\begin{table}[tbp]\\centering\\small\\caption{Traces by nation and kind, and sites.}\\label{tab:kinds}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Nation & Building & Site & Burial & Name & Business & Traces & Sites\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = fill(t, R, fmtf=lambda v, f: tfmt(v, f or "raw"))
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_KINDS}}", TK)
assert not re.search(r"\{\{(?!DOI\}\})", t), re.findall(r"\{\{[^}]*\}\}", t)
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.startswith("f_"): pass
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
