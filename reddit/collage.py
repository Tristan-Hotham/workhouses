"""r/dataisbeautiful collage for workhouses: 2400 x 3000 px on a light background. Numbers from data/results.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

R = jload(f"{DATA}/results.json"); T = jload(f"{WORK}/traces.json")
TR = [x for x in T["traces"] if x["lat"] is not None]
BG2 = "#F7F3EB"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG2)
fig.text(.045, .972, "What's left of the workhouse?", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .918, f"{R['traces']['n']} traces of Britain and Ireland's workhouses in open data: surviving buildings, sites and memorials,\nburial grounds, Workhouse Lanes and businesses that borrowed the name.",
         fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.4)

# map
ax = fig.add_axes([.30, .40, .70, .48])
isles(ax, ext=(2.88e6, 3.80e6, 3.07e6, 4.05e6), fc="#E6DDCC", ec=BG2)
for k in ["name", "business", "burial", "site", "building"]:
    its = [t for t in TR if t["kind"] == k]
    x, y = proj([t["lon"] for t in its], [t["lat"] for t in its])
    if k == "business":
        ax.scatter(x, y, s=22, facecolors=BG2, edgecolors=KC[k], linewidths=1.5, zorder=3)
    else:
        ax.scatter(x, y, s=34 if k != "name" else 18, c=KC[k], edgecolors="white", linewidths=.5, zorder=4 if k == "building" else 3)
from collections import Counter
pc = Counter(t["kind"] for t in TR)
LEG = SERP.copy(); LEG.set_size(13)
h = [Line2D([], [], marker="o", ls="", ms=10, mfc=(BG2 if k == "business" else KC[k]), mec=(KC[k] if k == "business" else "white"), mew=1.5, label=f"{KL[k]}  {pc[k]}")
     for k in ["building", "site", "burial", "name", "business"]]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.035, .86), frameon=False, prop=LEG, labelspacing=.8, title="Each dot is one trace", title_fontproperties=SERB)
fig.text(.045, .665, "What surviving buildings\nbecame, where recorded:", fontproperties=SERB, fontsize=13, color=FG, va="top", linespacing=1.35)
ax2 = fig.add_axes([.14, .45, .16, .16]); ax2.set_facecolor(BG2)
order = R["reuse"]["order"][::-1]
ax2.barh(range(len(order)), [R["reuse"]["by"][k] for k in order], color=[RC[k] for k in order], height=.7)
for i, k in enumerate(order):
    ax2.text(R["reuse"]["by"][k] + .6, i, str(R["reuse"]["by"][k]), va="center", fontsize=10.5)
short = {"hospital": "Hospital", "homes": "Homes, flats", "museum": "Museum", "offices": "Offices", "ruin": "Ruin", "business": "Business", "education": "School"}
ax2.set_yticks(range(len(order))); ax2.set_yticklabels([short[k] for k in order], fontsize=10.5)
for s in ("top", "right", "bottom"): ax2.spines[s].set_visible(False)
ax2.set_xticks([]); ax2.tick_params(left=False); ax2.set_xlim(0, 38)

# big numbers
nums = [(f"{R['sites']['by_status']['building']}", HOT, f"workhouse sites with a\nsurviving building, of\n{R['sites']['n']} sites found"),
        (f"{R['reuse']['hosp_homes_pct']:.0f}%", "#3F6FA0", f"of buildings with a known\nlater use became hospitals\nor homes"),
        (f"{R['names']['n']}", "#4F6D8A", f"streets and places named\nafter a workhouse,\n{R['names']['england_pct']:.0f}% in England"),
        (f"{R['ireland']['burial_ie']} of {R['ireland']['burial_all']}", MOSS, "mapped workhouse burial\ngrounds are in Ireland,\nthe famine's legacy")]
for i, (big, col, small) in enumerate(nums):
    x = .045 + i * .235
    fig.text(x, .37, big, fontproperties=DISP, fontsize=40, color=col, va="top")
    fig.text(x, .315, small, family=MONO, fontsize=11, color=FG, va="top", linespacing=1.45)

# Britain vs Ireland
ax3 = fig.add_axes([.17, .13, .78, .095]); ax3.set_facecolor(BG2)
SK = [("building", "Surviving building", KC["building"]), ("site", "Site or memorial only", KC["site"]), ("burial", "Burial ground only", KC["burial"])]
for i, (lab, v) in enumerate((("Ireland", R["sites"]["ie"]), ("Britain", R["sites"]["gb"]))):
    x0 = 0
    for k, l, c in SK:
        w = 100 * v[k] / v["n"]
        ax3.barh(i, w, left=x0, color=c, height=.62)
        if w > 6: ax3.text(x0 + w / 2, i, f"{w:.0f}%", ha="center", va="center", color="white", fontsize=12)
        x0 += w
ax3.set_yticks([0, 1]); ax3.set_yticklabels([f"Ireland ({R['sites']['ie']['n']} sites)", f"Britain ({R['sites']['gb']['n']} sites)"], fontsize=11.5)
ax3.set_xlim(0, 100); ax3.set_xticks([])
for s in ("top", "right", "bottom"): ax3.spines[s].set_visible(False)
ax3.tick_params(left=False)
fig.text(.045, .248, "What is left of each workhouse site in the record", fontproperties=SERB, fontsize=14, color=FG, va="top")
ax3.legend(handles=[Patch(fc=c, label=l) for k, l, c in SK], loc="upper left", bbox_to_anchor=(-.17, -.05), ncol=3, frameon=False, fontsize=11)

fig.text(.045, .022, "Sources: Historic England NHLE, Historic Environment Scotland, Cadw, NI Department for Communities listed building registers (OGL);\n"
         "OpenStreetMap contributors (ODbL); Wikidata (CC0); English Wikipedia (CC BY-SA 4.0). Not a complete list of workhouses: about\n"
         f"{R['context']['ew_unions']} unions in England and Wales and {R['context']['ie_unions_1850s']} in Ireland existed; this maps what the open record holds.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/workhouses", family=MONO, fontsize=9.3, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whats_left_of_the_workhouse.png")
fig.savefig(out, facecolor=BG2, dpi=200)
print("ok", out)
