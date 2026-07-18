#!/usr/bin/env python3
# filter_blueprints.py — v1.0 — Last updated 2026-07-18
#
# Flattens CCP's blueprints.jsonl into three tabular JSON arrays, filtered to
# the recursive material closure of T3 Cruiser hulls + subsystems. The EVE PI
# Manager v2 Apps Script (IndustryBlueprints.gs) consumes these as flat sheets:
#
#   blueprints.json         [{blueprintTypeID, activity, time, maxProductionLimit}]
#   blueprintMaterials.json [{blueprintTypeID, activity, materialTypeID, quantity}]
#   blueprintProducts.json  [{blueprintTypeID, activity, productTypeID, quantity, probability}]
#
# Only manufacturing | reaction | invention activities are kept (copying and
# research are irrelevant to build-cost). "Closure" = start from the finished
# T3 items, walk every manufacturing/reaction recipe's materials down to leaves
# (minerals, gas, salvage, datacores, relics), and pull in the invention recipe
# (relic + datacores) for every T3 BPC encountered.
#
# Inputs (produced earlier in the workflow):
#   blueprints.jsonl   — raw CCP nested blueprints
#   sde/types.json     — [{typeID, name, groupID, ...}]  (already slimmed)
#   sde/groups.json    — [{groupID, categoryID, name, ...}]
# Output: sde/blueprints.json, sde/blueprintMaterials.json, sde/blueprintProducts.json

import json
import sys

# T3C seed: everything in these groups/categories is a "finished item" we want a
# build cost for. 963 = Strategic Cruiser (hulls); category 32 = Subsystem.
# (Add group 1305 Tactical Destroyer + its subsystem groups here to extend later.)
SEED_GROUPS = {963}
SEED_CATEGORIES = {32}
KEEP_ACTIVITIES = ("manufacturing", "reaction", "invention")
BUILD_ACTIVITIES = ("manufacturing", "reaction")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    types = load_json("sde/types.json")
    groups = load_json("sde/groups.json")

    cat_by_group = {int(g["groupID"]): int(g["categoryID"]) for g in groups}
    seed = set()
    for t in types:
        gid = int(t["groupID"])
        if gid in SEED_GROUPS or cat_by_group.get(gid) in SEED_CATEGORIES:
            if t.get("published", True):
                seed.add(int(t["typeID"]))

    # Index the raw blueprints once. bp[bpID] = {activity: {time, mpl, mats, prods}}.
    bp = {}
    # producers[activity][productTypeID] = bpID
    producers = {a: {} for a in KEEP_ACTIVITIES}
    for row in read_jsonl("blueprints.jsonl"):
        bp_id = int(row["_key"])
        mpl = int(row.get("maxProductionLimit") or 0)
        acts = row.get("activities") or {}
        kept = {}
        for activity in KEEP_ACTIVITIES:
            a = acts.get(activity)
            if not a:
                continue
            mats = [{"typeID": int(m["typeID"]), "quantity": int(m["quantity"])}
                    for m in (a.get("materials") or [])]
            prods = [{"typeID": int(p["typeID"]), "quantity": int(p["quantity"]),
                      "probability": p.get("probability")}
                     for p in (a.get("products") or [])]
            kept[activity] = {"time": int(a.get("time") or 0), "mpl": mpl,
                              "materials": mats, "products": prods}
            for p in prods:
                producers[activity][p["typeID"]] = bp_id
        if kept:
            bp[bp_id] = kept

    # BFS closure over needed items.
    frontier = list(seed)
    needed_items = set()
    needed_bps = set()  # (bp_id, activity)
    while frontier:
        t = frontier.pop()
        if t in needed_items:
            continue
        needed_items.add(t)
        for activity in BUILD_ACTIVITIES:
            bp_id = producers[activity].get(t)
            if bp_id is None:
                continue
            needed_bps.add((bp_id, activity))
            for m in bp[bp_id][activity]["materials"]:
                frontier.append(m["typeID"])
            # A manufactured/reacted product's blueprint may itself be an
            # invention output (a T3 BPC). Pull in that invention recipe so the
            # BPC has a modelled cost (relic + datacores).
            inv_bp = producers["invention"].get(bp_id)
            if inv_bp is not None:
                needed_bps.add((inv_bp, "invention"))
                for m in bp[inv_bp]["invention"]["materials"]:
                    frontier.append(m["typeID"])

    # Emit flat rows.
    bp_rows, mat_rows, prod_rows = [], [], []
    for bp_id, activity in sorted(needed_bps):
        a = bp[bp_id][activity]
        bp_rows.append({"blueprintTypeID": bp_id, "activity": activity,
                        "time": a["time"], "maxProductionLimit": a["mpl"]})
        for m in a["materials"]:
            mat_rows.append({"blueprintTypeID": bp_id, "activity": activity,
                             "materialTypeID": m["typeID"], "quantity": m["quantity"]})
        for p in a["products"]:
            prob = p["probability"]
            prod_rows.append({"blueprintTypeID": bp_id, "activity": activity,
                              "productTypeID": p["typeID"], "quantity": p["quantity"],
                              "probability": "" if prob is None else prob})

    for name, rows in (("blueprints", bp_rows),
                       ("blueprintMaterials", mat_rows),
                       ("blueprintProducts", prod_rows)):
        with open("sde/%s.json" % name, "w", encoding="utf-8") as f:
            json.dump(rows, f, separators=(",", ":"))

    sys.stderr.write(
        "blueprints closure: %d finished-item seeds -> %d blueprints, "
        "%d material rows, %d product rows, %d items in closure\n"
        % (len(seed), len(bp_rows), len(mat_rows), len(prod_rows), len(needed_items)))


if __name__ == "__main__":
    main()
