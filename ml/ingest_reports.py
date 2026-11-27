"""
ingest_reports.py -- replace the simulated failure labels with the municipality's real reports, then retrain.

Usage
-----
  python ml/ingest_reports.py <reports.csv> [--radius 150] [--dry-run] [--no-train]

Input: the municipality reports file in the template data/templates/reports.csv
       (report_id,date,street_name,district,latitude,longitude,defect_type,channel,status,closed_date).

What it does
  1. Matches each report to the nearest road segment (data/segments.json) within --radius metres.
  2. Rewrites data/reports.csv in the model's internal format (simulated file backed up to data/sim_backup/).
  3. Rebuilds the failure target and history features in data/panel.csv and data/state_now.csv
     from the real reports: failed, fails_3m, fails_12m, months_since_repair.
  4. Writes data/provenance.json and runs ml/train_model.py, which regenerates data/model_output.js.

What stays simulated until the matching municipality files exist
  PCI, maintenance records, contractors and materials. The provenance file says so.
"""
import argparse, datetime, json, math, os, shutil, subprocess, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
REQ = ["date", "latitude", "longitude"]


def nearest_segment(geom, radius):
    """Return a matcher (lat, lon) -> asset_id or None, using every vertex of every segment."""
    ids, lat, lon = [], [], []
    for aid, pts in geom.items():
        for la, lo in pts:
            ids.append(aid); lat.append(la); lon.append(lo)
    ids, lat, lon = np.array(ids), np.array(lat), np.array(lon)

    def match(la, lo):
        k = math.cos(math.radians(la))
        d2 = (lat - la) ** 2 + ((lon - lo) * k) ** 2
        i = int(d2.argmin())
        return ids[i] if math.sqrt(d2[i]) * 111320 <= radius else None
    return match


def history(fail_months, month_index, T):
    """fails_3m, fails_12m, months_since_repair at month index T from earlier failure months (strictly before T)."""
    past = [m for m in fail_months if m < T]
    f3 = sum(1 for m in past if T - m <= 3)
    f12 = sum(1 for m in past if T - m <= 12)
    since = 36 if not past else min(36, T - max(past))
    return f3, f12, since


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reports"); ap.add_argument("--radius", type=float, default=150)
    ap.add_argument("--dry-run", action="store_true", help="match and report only, write nothing")
    ap.add_argument("--no-train", action="store_true", help="write the data files but do not retrain")
    a = ap.parse_args()

    src = pd.read_csv(a.reports, encoding="utf-8-sig", dtype=str)
    src.columns = [c.strip().lower() for c in src.columns]
    miss = [c for c in REQ if c not in src.columns]
    if miss:
        sys.exit(f"missing columns: {', '.join(miss)} (use data/templates/reports.csv)")

    geom = json.load(open(os.path.join(DATA, "segments.json")))
    assets = pd.read_csv(os.path.join(DATA, "assets.csv"), encoding="utf-8-sig")
    match = nearest_segment(geom, a.radius)

    src["lat"] = pd.to_numeric(src.latitude, errors="coerce")
    src["lon"] = pd.to_numeric(src.longitude, errors="coerce")
    src["month"] = pd.to_datetime(src.date, errors="coerce").dt.strftime("%Y-%m")
    no_xy = src.lat.isna() | src.lon.isna()
    no_date = src.month.isna()
    ok = src[~no_xy & ~no_date].copy()
    ok["asset_id"] = [match(la, lo) for la, lo in zip(ok.lat, ok.lon)]
    off = ok.asset_id.isna()
    ok = ok[~off]

    panel = pd.read_csv(os.path.join(DATA, "panel.csv"), encoding="utf-8-sig")
    months = sorted(panel.month.unique())
    in_range = ok.month.isin(months)
    out_range = int((~in_range).sum())
    ok = ok[in_range]

    print(f"rows {len(src)} | matched {len(ok)} | off-network {int(off.sum())} | no coordinates {int(no_xy.sum())} | "
          f"no date {int((no_date & ~no_xy).sum())} | outside {months[0]}..{months[-1]} {out_range}")
    if ok.empty:
        sys.exit("no report matched a segment inside the panel period; nothing written")
    if a.dry_run:
        print("dry run: nothing written"); return

    # 1. back up the simulated files once
    bk = os.path.join(DATA, "sim_backup"); os.makedirs(bk, exist_ok=True)
    for f in ("reports.csv", "panel.csv", "state_now.csv"):
        if not os.path.exists(os.path.join(bk, f)):
            shutil.copy2(os.path.join(DATA, f), os.path.join(bk, f))

    # 2. reports in the internal format
    dist = assets.set_index("asset_id").district
    rep = pd.DataFrame({"report_id": ok.get("report_id", pd.Series(range(len(ok)))).values, "asset_id": ok.asset_id.values,
                        "date": pd.to_datetime(ok.date).dt.strftime("%Y-%m-%d").values,
                        "district": [dist.get(x, "") for x in ok.asset_id],
                        "channel": ok.get("channel", pd.Series([""] * len(ok))).fillna("").values,
                        "defect": ok.get("defect_type", pd.Series([""] * len(ok))).fillna("").values})
    rep.to_csv(os.path.join(DATA, "reports.csv"), index=False, encoding="utf-8-sig")

    # 3. failure target and history features from the real reports
    mi = {m: i for i, m in enumerate(months)}
    fails = rep.assign(t=rep.date.str[:7].map(mi)).groupby("asset_id").t.apply(lambda s: sorted(set(s))).to_dict()
    t_col = panel.month.map(mi)
    feats = [history(fails.get(aid, []), mi, t) for aid, t in zip(panel.asset_id, t_col)]
    panel["fails_3m"], panel["fails_12m"], panel["months_since_repair"] = zip(*feats)
    hit = set(zip(rep.asset_id, rep.date.str[:7]))
    panel["failed"] = [int((aid, m) in hit) for aid, m in zip(panel.asset_id, panel.month)]
    panel.to_csv(os.path.join(DATA, "panel.csv"), index=False, encoding="utf-8-sig")

    now = pd.read_csv(os.path.join(DATA, "state_now.csv"), encoding="utf-8-sig")
    T = len(months)
    feats = [history(fails.get(aid, []), mi, T) for aid in now.asset_id]
    now["fails_3m"], now["fails_12m"], now["months_since_repair"] = zip(*feats)
    now.to_csv(os.path.join(DATA, "state_now.csv"), index=False, encoding="utf-8-sig")

    json.dump({"reports": "municipality", "file": os.path.basename(a.reports), "matched": int(len(rep)),
               "radius_m": a.radius, "period": [months[0], months[-1]], "fail_rate": round(float(panel.failed.mean()), 4),
               "still_simulated": ["pci", "maintenance", "contractors", "materials"],
               "ingested_at": datetime.datetime.now().isoformat(timespec="seconds")},
              open(os.path.join(DATA, "provenance.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"failure rate {panel.failed.mean():.4f} | panel and state rebuilt | simulated files kept in data/sim_backup/")

    # 4. retrain
    if not a.no_train:
        subprocess.run([sys.executable, os.path.join(ROOT, "ml", "train_model.py")], check=True)


if __name__ == "__main__":
    main()
