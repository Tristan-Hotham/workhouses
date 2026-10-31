"""Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png) and paper figures
(release/paper/f_*.png). All numbers come from data/results.json or the traces used to make it."""
from collections import Counter
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
T = jload(f"{WORK}/traces.json")
TR = [x for x in T["traces"] if x["lat"] is not None]
SITES = T["sites"]
BL = os.path.join(ROOT, "release", "blog"); PP = os.path.join(ROOT, "release", "paper")
for d in (BL, PP):
    os.makedirs(d, exist_ok=True)
fmt = lambda v: f"{round(v):,}"
MAPEXT = (2.88e6, 3.80e6, 3.07e6, 4.05e6)
KORD = ["name", "business", "burial", "site", "building"]   # drawing order: buildings on top


def both(fig, name):
    fig.savefig(f"{BL}/b_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(f"{PP}/f_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def dots(ax, items, colour, size=14, edge="#FFFFFF", lw=.5, z=3, marker="o"):
    if not items:
        return
    x, y = proj([t["lon"] for t in items], [t["lat"] for t in items])
    ax.scatter(x, y, s=size, c=colour, edgecolors=edge, linewidths=lw, zorder=z, marker=marker)


def kind_dots(ax, scale=1.0):
    for k in KORD:
        its = [t for t in TR if t["kind"] == k]
        if k == "business":
            x, y = proj([t["lon"] for t in its], [t["lat"] for t in its])
            ax.scatter(x, y, s=16 * scale, facecolors=BG, edgecolors=KC[k], linewidths=1.3 * scale, zorder=3)
        else:
            dots(ax, its, KC[k], size=(26 if k in ("building", "burial", "site") else 14) * scale, lw=.5 * scale, z=4 if k == "building" else 3)


def legend_kinds(fig, x, y, ncol=1, size=11, counts=True):
    prop = SERP.copy(); prop.set_size(size)
    pc = Counter(t["kind"] for t in TR)
    h = [Line2D([], [], marker="o", ls="", ms=8, mfc=(BG if k == "business" else KC[k]), mec=KC[k] if k == "business" else "white", mew=1.4,
                label=KL[k] + (f"  {pc[k]:,}" if counts else "")) for k in ["building", "site", "burial", "name", "business"]]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, prop=prop, handletextpad=.4, labelspacing=.5, columnspacing=1.2)


# ---------------------------------------------------------------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(.045, .86, "What's left of", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .72, "the workhouse?", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(.045, .56, f"{R['traces']['n']:,} traces in open data: {R['sites']['by_status']['building']} sites\nwith a surviving building, {R['names']['n']} streets and\nplaces named after them, and {R['ireland']['burial_ie']} of {R['ireland']['burial_all']}\nmapped workhouse burial grounds in Ireland.",
         fontproperties=SERP, fontsize=18, color=FG, va="top", linespacing=1.45)
legend_kinds(fig, .035, .215, ncol=2, size=11, counts=False)
fig.text(.045, .035, "maps.tristanhotham.com/workhouses", family=MONO, fontsize=12, color=MUT)
ax = fig.add_axes([.53, .0, .47, 1])
isles(ax, ext=MAPEXT)
kind_dots(ax, scale=.9)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)

# ---------------------------------------------------------------- the map
fig = plt.figure(figsize=(10, 11), facecolor=BG)
ax = fig.add_axes([0, 0, 1, .93])
isles(ax, ext=MAPEXT)
kind_dots(ax, scale=1.15)
fig.text(.04, .975, "Traces of the workhouse in the open record", fontproperties=DISPB, fontsize=22, color=FG, va="top")
fig.text(.04, .94, f"{R['traces']['placed']:,} mapped traces from the listed building registers, OpenStreetMap, Wikidata and Wikipedia",
         fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
legend_kinds(fig, .03, .9, size=12)
fig.text(.04, .015, "Not a complete list of workhouses: a map of what the open record holds.", family=MONO, fontsize=10, color=MUT)
both(fig, "map")

# ---------------------------------------------------------------- sites by nation and status
NAT = ["England", "Wales", "Scotland", "Northern Ireland", "Ireland"]
SK = [("building", "Surviving building", KC["building"]), ("site", "Site or memorial only", KC["site"]), ("burial", "Burial ground only", KC["burial"])]
fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=BG); ax.set_facecolor(BG)
for i, n in enumerate(NAT[::-1]):
    v = R["sites"]["nation_status"][n]; x = 0
    for k, l, c in SK:
        ax.barh(i, v[k], left=x, color=c, height=.62)
        if v[k] >= 6: ax.text(x + v[k] / 2, i, str(v[k]), ha="center", va="center", color="white", fontsize=11, fontweight="medium")
        x += v[k]
    ax.text(x + 1.2, i, str(x), va="center", fontsize=11.5, color=FG)
ax.set_yticks(range(len(NAT))); ax.set_yticklabels(NAT[::-1], fontsize=12)
for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
ax.set_xticks([]); ax.tick_params(left=False)
ax.legend(handles=[Patch(fc=c, label=l) for k, l, c in SK], loc="lower right", frameon=False, fontsize=11)
ax.set_title(f"{R['sites']['n']} workhouse sites, by nation and what is left in the record", loc="left", fontproperties=DISPB, fontsize=16, color=FG, pad=12)
fig.tight_layout(); both(fig, "sites")

# ---------------------------------------------------------------- what they became
fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
ax = fig.add_axes([.23, .14, .28, .66]); ax.set_facecolor(BG)
order = R["reuse"]["order"][::-1]
ax.barh(range(len(order)), [R["reuse"]["by"][k] for k in order], color=[RC[k] for k in order], height=.66)
for i, k in enumerate(order):
    ax.text(R["reuse"]["by"][k] + .6, i, f"{R['reuse']['by'][k]} ({R['reuse']['pct_of_known'][k]:.0f}%)", va="center", fontsize=11)
ax.set_yticks(range(len(order))); ax.set_yticklabels([RL[k] for k in order], fontsize=11)
for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
ax.set_xticks([]); ax.tick_params(left=False); ax.set_xlim(0, max(R["reuse"]["by"].values()) * 1.3)
fig.text(.04, .95, "What surviving workhouses became", fontproperties=DISPB, fontsize=20, color=FG, va="top")
fig.text(.04, .895, f"{R['reuse']['known']} of {R['reuse']['n_building_sites']} sites with a surviving building have a recorded later use", fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
fig.text(.04, .04, f"Read from names, descriptions and map tags. Use not stated for {R['reuse']['unknown']} sites (grey on the map).", family=MONO, fontsize=9.5, color=MUT)
ax2 = fig.add_axes([.58, .02, .41, .86])
isles(ax2, ext=MAPEXT)
bs = [s for s in SITES if s["status"] == "building"]
for k in ["unknown", "ruin", "education", "business", "offices", "museum", "homes", "hospital"]:
    its = [s for s in bs if (s["reuse"] or "unknown") == k]
    dots(ax2, its, RC[k], size=12 if k == "unknown" else 30, z=3 if k == "unknown" else 4)
both(fig, "reuse")

# ---------------------------------------------------------------- names
N = [t for t in TR if t["kind"] == "name"]
fig = plt.figure(figsize=(12, 7.6), facecolor=BG)
ax = fig.add_axes([.0, .0, .5, .9])
isles(ax, ext=(3.15e6, 3.80e6, 3.07e6, 3.78e6))
dots(ax, [t for t in TR if t["kind"] == "building"], "#D9CBBE", size=10, z=2, lw=0)
dots(ax, N, KC["name"], size=26, z=4)
for t in N:
    if t["name"] in ("Workhouse Green", "Workhouse End", "Workhouse Corner"):
        x, y = proj(t["lon"], t["lat"])
        off = {"Suffolk": (14, 8), "South Yorkshire": (14, 6), "Bedfordshire": (-14, 14), "Lincolnshire": (14, 6), "Essex": (14, -12)}.get(t["county"], (12, 6))
        ax.annotate(t["name"], (x, y), xytext=off, textcoords="offset points", fontsize=9.5, family=MONO, color=FG, ha="left" if off[0] > 0 else "right",
                    bbox=dict(boxstyle="round,pad=.15", fc=BG, ec="none", alpha=.85), zorder=6)
fig.text(.04, .965, "Workhouse Lane, Workhouse Green, Workhouse End", fontproperties=DISPB, fontsize=20, color=FG, va="top")
fig.text(.04, .91, f"{R['names']['n']} streets, places and features named after a workhouse or poorhouse ({R['names']['england_pct']:.0f}% in England); pale dots are surviving buildings",
         fontproperties=SERP, fontsize=12, color=MUT, va="top")
ax2 = fig.add_axes([.62, .14, .33, .66]); ax2.set_facecolor(BG)
bw = R["names"]["by_word"]; keys = [k for k in sorted(bw, key=lambda k: -bw[k]) if k != "Other"][:8]
rest = sum(v for k, v in bw.items() if k not in keys)
rows = [(k, bw[k]) for k in keys] + [("Other", rest)]
ax2.barh(range(len(rows))[::-1], [v for _, v in rows], color=[KC["name"]] * len(keys) + ["#9AAABA"], height=.64)
for i, (k, v) in enumerate(rows):
    ax2.text(v + .5, len(rows) - 1 - i, str(v), va="center", fontsize=11)
ax2.set_yticks(range(len(rows))[::-1]); ax2.set_yticklabels([k for k, _ in rows], fontsize=11.5)
for s in ("top", "right", "bottom"): ax2.spines[s].set_visible(False)
ax2.set_xticks([]); ax2.tick_params(left=False)
ax2.set_title("What the name is attached to", loc="left", fontsize=12, color=FG)
both(fig, "names")

# ---------------------------------------------------------------- Ireland
fig = plt.figure(figsize=(12, 8), facecolor=BG)
ax = fig.add_axes([.0, .0, .56, .88])
isles(ax, ext=(2.88e6, 3.36e6, 3.24e6, 3.78e6))
ie = [s for s in SITES if s["nation"] in ("Ireland", "Northern Ireland")]
for k, c, sz in (("building", KC["building"], 46), ("site", KC["site"], 46), ("burial", KC["burial"], 52)):
    dots(ax, [s for s in ie if s["status"] == k], c, size=sz, z=4)
bur = [t for t in TR if t["kind"] == "burial" and t["nation"] in ("Ireland", "Northern Ireland")]
x, y = proj([t["lon"] for t in bur], [t["lat"] for t in bur])
ax.scatter(x, y, s=150, facecolors="none", edgecolors=KC["burial"], linewidths=1.6, zorder=5)
kx, ky = proj(-7.245, 52.656)
ax.annotate(f"Kilkenny: the remains of\n{R['ireland']['kilkenny_n']} famine victims, 2005", (kx, ky), xytext=(3.13e6, 3.26e6), fontsize=10, family=MONO, color=FG, ha="left",
            arrowprops=dict(arrowstyle="-", color=FG, lw=.8), bbox=dict(boxstyle="round,pad=.25", fc=BG, ec="none"), zorder=7)
fig.text(.04, .965, "The famine workhouse: sites and graves", fontproperties=DISPB, fontsize=20, color=FG, va="top")
fig.text(.04, .915, f"{R['sites']['ie']['n']} workhouse sites on the island of Ireland, by what survives in the record; rings mark the {R['ireland']['burial_ie']} burial grounds",
         fontproperties=SERP, fontsize=12, color=MUT, va="top")
ax2 = fig.add_axes([.62, .52, .34, .22]); ax2.set_facecolor(BG)
for i, (lab, v) in enumerate((("Ireland", R["sites"]["ie"]), ("Britain", R["sites"]["gb"]))):
    x0 = 0
    for k, l, c in SK:
        w = 100 * v[k] / v["n"]
        ax2.barh(i, w, left=x0, color=c, height=.6)
        if w > 8: ax2.text(x0 + w / 2, i, f"{w:.0f}%", ha="center", va="center", color="white", fontsize=10.5)
        x0 += w
ax2.set_yticks([0, 1]); ax2.set_yticklabels(["Ireland", "Britain"], fontsize=12); ax2.set_xlim(0, 100); ax2.set_xticks([])
for s in ("top", "right", "bottom"): ax2.spines[s].set_visible(False)
ax2.tick_params(left=False)
ax2.set_title("Share of sites by what is left", loc="left", fontsize=11.5, color=FG)
ax2.legend(handles=[Patch(fc=c, label=l) for k, l, c in SK], loc="upper left", bbox_to_anchor=(-.02, -.08), frameon=False, fontsize=10)
fig.text(.62, .3, f"Mapped workhouse burial grounds:\n{R['ireland']['burial_ie']} in Ireland, {R['ireland']['burial_gb']} in Britain", fontproperties=SERB, fontsize=15, color=MOSS, va="top", linespacing=1.4)
fig.text(.62, .19, "The Republic's register of historic\nbuildings is not among the sources,\nso Irish buildings reach the map only\nthrough OpenStreetMap, Wikidata\nand Wikipedia.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.5)
both(fig, "ireland")

# ---------------------------------------------------------------- coverage: how the sources overlap
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.1]})
src_n = Counter(len(s["sources"].split("|")) for s in SITES)
ax = axs[0]; ax.set_facecolor(BG)
ks = sorted(src_n)
ax.bar([str(k) for k in ks], [src_n[k] for k in ks], color=[HOT if k == 1 else "#C9A79A" for k in ks], width=.62)
for k in ks: ax.text(ks.index(k), src_n[k] + 2, str(src_n[k]), ha="center", fontsize=11)
ax.set_xlabel("number of sources a site appears in", fontsize=11)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.set_yticks([]); ax.set_title(f"{R['sites']['one_source_pct']:.0f}% of sites appear in only one source", loc="left", fontproperties=DISPB, fontsize=14, color=FG)
ax = axs[1]; ax.set_facecolor(BG)
rows = [("England and Wales", R["complete"]["ew_sites"], R["context"]["ew_unions"], "poor law unions (about)"),
        ("Island of Ireland", R["complete"]["ie_sites"], R["context"]["ie_unions_1850s"], "unions by the 1850s")]
for i, (lab, a, b, what) in enumerate(rows[::-1]):
    ax.barh(i, b, color="none", edgecolor=FG, height=.5, lw=1.2)
    ax.barh(i, a, color=HOT if i == 1 else MOSS, height=.5)
    ax.text(b + 8, i, f"{a} sites found\nvs {b} {what}", va="center", fontsize=10.5)
ax.set_yticks([0, 1]); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=11.5); ax.set_xlim(0, 900); ax.set_xticks([])
for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
ax.tick_params(left=False)
ax.set_title("Sites found against the historical number of unions", loc="left", fontproperties=DISPB, fontsize=14, color=FG)
fig.text(.01, .01, "Union numbers from Crowther (1981) and O'Connor (1995). Many sites in England and Wales are small parish poorhouses, not union workhouses.", family=MONO, fontsize=9, color=MUT)
fig.tight_layout(rect=(0, .05, 1, 1)); both(fig, "coverage")
print("figures ok")
