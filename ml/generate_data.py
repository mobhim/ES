# -*- coding: utf-8 -*-
"""
استباق (الطرق): مولّد البيانات
حقيقي:
  - شبكة الطرق: OpenStreetMap عبر Overpass (data/roads_raw.json)، تُقسَّم إلى مقاطع.
  - الطقس: Open-Meteo (أرشيف ERA5) لإحداثيات الهفوف.
اصطناعي (محاكاة شهرية فوق المقاطع الحقيقية):
  - خصائص المقطع غير المتاحة علناً (العمر، المياه الجوفية، الدمك، جودة الخلطة)
  - مؤشر حالة الرصف PCI وتدهوره، البلاغات، سجلات الصيانة، المقاولون.
المخرجات في data/: weather.csv, assets.csv, segments.json, reports.csv, maintenance.csv, panel.csv, state_now.csv, pci_monthly.csv
"""
import json, math, os, urllib.request
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)
rng = np.random.default_rng(2026)
START, END = "2023-01-01", "2026-10-31"
SEG_LEN = 300          # طول المقطع المستهدف بالمتر

# ---------------- 1) الطقس (حقيقي) ----------------
def get_weather():
    path = os.path.join(DATA, "weather.csv")
    if os.path.exists(path):
        w = pd.read_csv(path, encoding="utf-8-sig")
        if len(w) > 1000: return w
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=25.38&longitude=49.59"
           f"&start_date={START}&end_date={END}&daily=temperature_2m_max,precipitation_sum&timezone=Asia%2FRiyadh")
    with urllib.request.urlopen(url, timeout=40) as r: d = json.load(r)["daily"]
    w = pd.DataFrame({"date": d["time"], "tmax": d["temperature_2m_max"], "rain": d["precipitation_sum"]}).dropna()
    w["source"] = "open-meteo-era5"; w.to_csv(path, index=False, encoding="utf-8-sig"); return w
weather = get_weather(); weather["month"] = weather["date"].str[:7]
wm = weather.groupby("month").agg(tmax=("tmax", "mean"), hot_days=("tmax", lambda s: int((s >= 43).sum())), rain=("rain", "sum")).reset_index()
months = list(wm["month"]); T = len(months)

# ---------------- 2) شبكة الطرق (حقيقية) ----------------
GEO = {"الهفوف": (25.3790, 49.5870), "المبرز": (25.4100, 49.5810), "العيون": (25.6030, 49.5650), "العمران": (25.4560, 49.7050),
       "الشعبة": (25.4950, 49.6000), "المنيزلة": (25.3850, 49.6640), "الجشة": (25.4170, 49.7150), "الجفر": (25.3790, 49.7220), "الطرف": (25.3560, 49.7260)}
GW = {"الهفوف": 1.3, "المبرز": 1.6, "العيون": 3.2, "العمران": 2.8, "الشعبة": 3.6, "المنيزلة": 2.4, "الجشة": 3.0, "الجفر": 1.9, "الطرف": 2.6}
CLS = {"motorway": ("طريق سريع", .92), "trunk": ("طريق رئيسي", .85), "primary": ("شرياني", .70), "secondary": ("تجميعي", .50), "tertiary": ("محلي رئيسي", .34)}
def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))
raw = json.load(open(os.path.join(DATA, "roads_raw.json"), encoding="utf-8"))
rows, geoms = [], {}
def flush(wy, tg, cls, name, cur, acc, part):
    sid = f"S{wy['id']}-{part}"; mid = cur[len(cur) // 2]
    dist = min(GEO, key=lambda d: hav(mid, GEO[d]))
    rows.append((sid, wy["id"], name, cls, dist, round(acc), round(mid[0], 5), round(mid[1], 5)))
    geoms[sid] = [[round(a, 5), round(b, 5)] for a, b in cur]
for wy in raw["elements"]:
    if wy.get("type") != "way" or "geometry" not in wy: continue
    tg = wy.get("tags", {}); cls = tg.get("highway")
    if cls not in CLS: continue
    pts = [(p["lat"], p["lon"]) for p in wy["geometry"]]
    name = tg.get("name:ar") or tg.get("name") or (("طريق " + tg["ref"]) if tg.get("ref") else None)
    cur, acc, part = [pts[0]], 0.0, 0
    for a, b in zip(pts, pts[1:]):
        acc += hav(a, b); cur.append(b)
        if acc >= SEG_LEN:
            part += 1; flush(wy, tg, cls, name, cur, acc, part); cur, acc = [b], 0.0
    if acc >= 60:
        part += 1; flush(wy, tg, cls, name, cur, acc, part)
    elif part and len(cur) > 1:                                         # ذيل قصير: يُضم للمقطع السابق
        geoms[rows[-1][0]] += [[round(a, 5), round(b, 5)] for a, b in cur[1:]]
A = pd.DataFrame(rows, columns=["asset_id", "way_id", "osm_name", "cls", "district", "length_m", "lat", "lon"])
N = len(A)
A["cls_ar"] = A.cls.map(lambda c: CLS[c][0])
A["road"] = [n if isinstance(n, str) else f"{c} بدون اسم" for n, c in zip(A.osm_name, A.cls_ar)]
seq = A.groupby(["road", "district"]).cumcount() + 1
A["name"] = [f"{r}، {d} (مقطع {k})" for r, d, k in zip(A.road, A.district, seq)]
json.dump({k: geoms[k] for k in A.asset_id}, open(os.path.join(DATA, "segments.json"), "w"), separators=(",", ":"))

# ---------------- 3) خصائص اصطناعية للمقاطع ----------------
CONTR = {"أ": (.90, .20, 14), "ب": (.78, .35, 19), "ج": (.60, .60, 31), "د": (.45, .80, 42), "هـ": (.70, .45, 23), "و": (.85, .25, 16)}
ZONE = {"الهفوف": ["ج", "ب", "هـ"], "المبرز": ["د", "ب", "هـ"], "العيون": ["ب", "و"], "العمران": ["أ", "د"], "الشعبة": ["و", "أ"],
        "المنيزلة": ["و", "هـ"], "الجشة": ["و", "أ"], "الجفر": ["د", "ج"], "الطرف": ["أ", "ج"]}
A["age"] = rng.integers(1, 26, N)
A["gw_depth"] = np.clip([rng.normal(GW[d], .45) for d in A.district], .6, 6).round(2)
A["traffic"] = np.clip([rng.normal(CLS[c][1], .12) for c in A.cls], .05, 1).round(2)
q_true = np.clip(rng.beta(5, 2.2, N), .15, 1); c_true = np.clip(rng.beta(5, 2, N), .15, 1)
A["material_test"] = np.clip(q_true + rng.normal(0, .12, N), 0, 1).round(2)
A["compaction_test"] = np.clip(c_true + rng.normal(0, .12, N), 0, 1).round(2)
A["installer"] = [rng.choice(ZONE[d]) for d in A.district]
hidden = rng.normal(0, .5, N)

# ---------------- 4) المحاكاة الشهرية: PCI ثم الأعطال ثم الإصلاح ----------------
sig = lambda x: 1 / (1 + np.exp(-x))
age, gw, tr = A.age.values, A.gw_depth.values, A.traffic.values
gwx = np.clip(2.2 - gw, 0, None)
pci = np.clip(97 - age * 1.7 * (1 + .8 * (1 - c_true)) + rng.normal(0, 7, N), 22, 100)
last_fail = np.full(N, -99); last_surface = np.zeros(N, int); last_cq = np.full(N, .75); last_c = list(A.installer.values)
hist = [[] for _ in range(N)]; cstats = {c: {"jobs": 0, "returned": 0} for c in CONTR}
OBS = np.zeros((T, N)); reports, maint, panel = [], [], []
for t, m in enumerate(months):
    w = wm.iloc[t]; heat = max(0, w.tmax - 38) / 8; rain = min(w.rain, 60) / 20
    obs = np.clip(pci + rng.normal(0, 4, N), 0, 100); OBS[t] = obs       # قراءة PCI المرصودة (مسح دوري، فيها خطأ قياس)
    f3 = np.array([sum(1 for x in h if t - x <= 3) for h in hist]); f12 = np.array([sum(1 for x in h if t - x <= 12) for h in hist])
    since = np.where(last_fail < 0, 36, np.minimum(36, t - last_fail))
    ret = {c: (v["returned"] / v["jobs"] if v["jobs"] >= 15 else .2) for c, v in cstats.items()}
    snap = A[["asset_id"]].copy(); snap["month"] = m
    snap["pci_obs"] = obs.round(1); snap["pci_drop_6m"] = (OBS[max(0, t - 6)] - obs).round(1) if t else 0.0
    snap["fails_3m"], snap["fails_12m"], snap["months_since_repair"], snap["last_repair_surface"] = f3, f12, since, last_surface
    snap["contractor_return_rate"] = [round(ret[c], 3) for c in last_c]
    recent = since <= 6
    z = -7.35 + .058 * (100 - pci) + .45 * gwx + .7 * tr * heat + .3 * rain * (gw < 1.8) + hidden
    z += recent * last_surface * (1.1 + 1.7 * (1 - last_cq)) - recent * (1 - last_surface) * .9
    fail = rng.random(N) < sig(z)
    snap["failed"] = fail.astype(int); panel.append(snap)
    for i in np.where(fail)[0]:
        d = A.district[i]; date = f"{m}-{int(rng.integers(1, 28)):02d}"
        c = rng.choice(ZONE[d]); q, ps, rh = CONTR[c]; surface = int(rng.random() < ps)
        if last_fail[i] >= 0 and t - last_fail[i] <= 3: cstats[last_c[i]]["returned"] += 1
        cstats[c]["jobs"] += 1
        area = A.length_m[i] * 7.5 * .12                                   # مساحة الإصلاح التقريبية (12% من المقطع)
        cost = int(area * (55 if surface else 190) * rng.uniform(.8, 1.3))
        rid = f"R-{len(reports)+1:06d}"
        reports.append((rid, A.asset_id[i], date, d, rng.choice(["بلدي", "940", "جولة ميدانية"], p=[.55, .3, .15]),
                        rng.choice(["حفرة", "هبوط", "تشققات", "تخدد"], p=[.4, .2, .25, .15])))
        maint.append((f"M-{len(maint)+1:06d}", rid, A.asset_id[i], date, c, "سطحية" if surface else "جذرية", round(max(2, rng.normal(rh, rh * .3)), 1), cost,
                      int(np.clip(rng.normal(q * 100, 9), 20, 100))))
        if surface: pci[i] = min(100, pci[i] + 6 * q)                      # الترقيع يرفع المؤشر قليلاً ولا يعالج السبب
        else: pci[i] = max(pci[i], 84 + 10 * q); c_true[i] = max(c_true[i], .8)
        hist[i].append(t); last_fail[i] = t; last_surface[i] = surface; last_cq[i] = q; last_c[i] = c
    decay = .10 + .30 * tr * (.6 + heat) + .32 * gwx + .42 * (1 - c_true) + .22 * (1 - q_true) + .12 * heat
    pci = np.clip(pci - decay * rng.uniform(.6, 1.4, N), 5, 100)

A.to_csv(os.path.join(DATA, "assets.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(reports, columns=["report_id", "asset_id", "date", "district", "channel", "defect"]).to_csv(os.path.join(DATA, "reports.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(maint, columns=["maint_id", "report_id", "asset_id", "date", "contractor", "repair_type", "response_hours", "cost_sar", "inspection_score"]).to_csv(os.path.join(DATA, "maintenance.csv"), index=False, encoding="utf-8-sig")
P = pd.concat(panel); P.to_csv(os.path.join(DATA, "panel.csv"), index=False, encoding="utf-8-sig")
obs = np.clip(pci + rng.normal(0, 4, N), 0, 100)
ret = {c: (v["returned"] / v["jobs"] if v["jobs"] >= 15 else .2) for c, v in cstats.items()}
pd.DataFrame({"asset_id": A.asset_id, "pci_obs": obs.round(1), "pci_drop_6m": (OBS[T - 6] - obs).round(1), "pci_drop_12m": (OBS[T - 12] - obs).round(1),
              "fails_3m": [sum(1 for x in h if T - x <= 3) for h in hist], "fails_12m": [sum(1 for x in h if T - x <= 12) for h in hist],
              "months_since_repair": np.where(last_fail < 0, 36, np.minimum(36, T - last_fail)), "last_repair_surface": last_surface,
              "contractor_return_rate": [round(ret[c], 3) for c in last_c], "last_contractor": last_c}).to_csv(os.path.join(DATA, "state_now.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame({"month": months, "pci_mean": (OBS * A.length_m.values).sum(1) / A.length_m.sum()}).round(2).to_csv(os.path.join(DATA, "pci_monthly.csv"), index=False, encoding="utf-8-sig")
print(f"segments {N} | km {A.length_m.sum()/1000:.0f} | named {A.osm_name.notna().mean():.0%} | reports {len(reports)} | fail rate {P.failed.mean():.3f} | pci mean {obs.mean():.0f}")
print(A.cls.value_counts().to_dict(), A.district.value_counts().to_dict())
