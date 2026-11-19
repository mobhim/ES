# -*- coding: utf-8 -*-
"""
استباق (الطرق): تدريب نموذج التنبؤ بأعطال مقاطع الطرق وتقييمه وتصدير النتائج للمنصة.
1) نموذج تصنيف: هل يتعطل المقطع خلال الشهر القادم؟ (تقسيم زمني، مقارنة بخط أساس)
2) تحليل بقاء (Kaplan-Meier): كم يصمد الإصلاح قبل عودة العطل، حسب نوع المعالجة والمقاول
3) إسقاط مؤشر حالة الرصف PCI لكل مقطع
4) أمثلية أوامر العمل: تجميع المقاطع المتجاورة وترتيبها حسب العائد
المخرجات: data/model_output.js|json و data/segments.js
"""
import json, math, os
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DATA = os.path.join(ROOT, "data")
rd = lambda f: pd.read_csv(os.path.join(DATA, f), encoding="utf-8-sig")
A, P, NOW, M, R, W, PM = rd("assets.csv"), rd("panel.csv"), rd("state_now.csv"), rd("maintenance.csv"), rd("reports.csv"), rd("weather.csv"), rd("pci_monthly.csv")
GEOM = json.load(open(os.path.join(DATA, "segments.json")))
RAW = json.load(open(os.path.join(DATA, "roads_raw.json"), encoding="utf-8"))
rng = np.random.default_rng(7); TEST_FROM = "2026-01"; pct = lambda x: int(round(float(x) * 100))

# ---------- الطقس: معدلات شهرية من فترة التدريب فقط ----------
W["month"] = W.date.str[:7]; W["cal"] = W.date.str[5:7].astype(int)
wm = W.groupby("month").agg(tmax=("tmax", "mean"), hot=("tmax", lambda s: (s >= 43).sum()), rain=("rain", "sum"), cal=("cal", "first")).reset_index()
norm = wm[wm.month < TEST_FROM].groupby("cal")[["tmax", "hot", "rain"]].mean(); norm.columns = ["tmax_norm", "hot_norm", "rain_norm"]

# ---------- السمات ----------
dcodes = {d: i for i, d in enumerate(sorted(A.district.unique()))}; ccodes = {c: i for i, c in enumerate(["tertiary", "secondary", "primary", "trunk", "motorway"])}
mcodes = {"تقليدية (60/70)": 0, "سوبربيف": 1, "معدّلة بالبوليمر (PMB)": 2}; bcodes = {"حصى مدرّج": 0, "أساس مثبت بالإسمنت": 1}
def build(df, cal):
    X = df.merge(A, on="asset_id"); X["cal"] = cal if np.isscalar(cal) else cal.values
    X = X.join(norm, on="cal"); X["district_code"] = X.district.map(dcodes); X["cls_code"] = X.cls.map(ccodes)
    X["mix_code"] = X.mix.map(mcodes); X["base_code"] = X.base_mat.map(bcodes); return X
FEATS = ["cls_code", "district_code", "length_m", "rel_elev", "age", "gw_depth", "traffic", "material_test", "mix_code", "base_code", "compaction_test", "pci_obs", "pci_drop_6m",
         "fails_3m", "fails_12m", "months_since_repair", "last_repair_surface", "contractor_return_rate", "tmax_norm", "hot_norm", "rain_norm"]
GROUPS = {"حالة الرصف (PCI)": ["pci_obs", "pci_drop_6m"], "سجل الأعطال السابقة": ["fails_3m", "fails_12m", "months_since_repair"],
          "المعالجة السطحية السابقة": ["last_repair_surface"], "أداء المقاول": ["contractor_return_rate"], "منسوب المياه الجوفية": ["gw_depth"],
          "الحمل المروري": ["traffic", "cls_code"], "ضعف دمك طبقة الأساس": ["compaction_test"], "جودة الخلطة الأسفلتية": ["material_test", "mix_code", "base_code"],
          "الإجهاد الحراري": ["tmax_norm", "hot_norm"], "الأمطار وانخفاض الموقع": ["rain_norm", "rel_elev"], "عمر الطريق": ["age"], "الموقع": ["district_code"]}
PHYS = ["منسوب المياه الجوفية", "الحمل المروري", "ضعف دمك طبقة الأساس", "جودة الخلطة الأسفلتية", "الإجهاد الحراري"]

X = build(P, P.month.str[5:7].astype(int)); X = X[X.month >= "2023-07"]
tr, te = X[X.month < TEST_FROM], X[X.month >= TEST_FROM]
model = HistGradientBoostingClassifier(max_iter=350, learning_rate=.05, max_leaf_nodes=15, l2_regularization=1.0,
                                       categorical_features=[FEATS.index("district_code")], random_state=0).fit(tr[FEATS], tr.failed)
te = te.copy(); te["p"] = model.predict_proba(te[FEATS])[:, 1]
te["base"] = te.fails_12m + .5 * te.fails_3m + rng.random(len(te)) * 1e-3          # خط الأساس: «ما تعطل سابقاً سيتعطل»
def topk(df, col, k=.05):
    flag = df.groupby("month")[col].transform(lambda s: s.rank(ascending=False, method="first") <= math.ceil(len(s) * k))
    tp = int((flag & (df.failed == 1)).sum()); fp = int((flag & (df.failed == 0)).sum()); fn = int((~flag & (df.failed == 1)).sum()); tn = int((~flag & (df.failed == 0)).sum())
    return {"prec": round(tp / (tp + fp), 3), "rec": round(tp / (tp + fn), 3), "tp": tp, "fp": fp, "fn": fn, "tn": tn}
mm, bm = topk(te, "p"), topk(te, "base")
dec = pd.qcut(te.p.rank(method="first"), 10, labels=False)
metrics = {"roc": round(roc_auc_score(te.failed, te.p), 3), "pr": round(average_precision_score(te.failed, te.p), 3), "base_rate": round(float(te.failed.mean()), 4),
           "model": mm, "baseline": {**bm, "roc": round(roc_auc_score(te.failed, te.base), 3), "pr": round(average_precision_score(te.failed, te.base), 3)},
           "lift": [round(float(te.failed[dec == d].mean()), 4) for d in range(9, -1, -1)]}
def perm(df, reps=3):
    base = average_precision_score(df.failed, model.predict_proba(df[FEATS])[:, 1]); out = {}
    for g, cols in GROUPS.items():
        dr = []
        for _ in range(reps):
            Z = df[FEATS].copy(); idx = rng.permutation(len(Z))
            for c in cols: Z[c] = Z[c].values[idx]
            dr.append(base - average_precision_score(df.failed, model.predict_proba(Z)[:, 1]))
        out[g] = max(0.0, float(np.mean(dr)))
    tot = sum(out.values()) or 1
    return sorted([[g, round(v / tot * 100)] for g, v in out.items() if v / tot >= .02], key=lambda x: -x[1])
importance = perm(te)

# ---------- تنبؤ الأشهر القادمة ----------
S = {cal: model.predict_proba(build(NOW, cal)[FEATS])[:, 1] for cal in (11, 12, 1, 2)}
Xn = build(NOW, 11); Xn["p"] = S[11]; Xn["p3"] = 1 - (1 - S[11]) * (1 - S[12]) * (1 - S[1])
q = Xn.p3.quantile([.65, .88, .96]).values; SEV = [pct(q[2]), pct(q[1]), pct(q[0])]          # حدود مستويات الخطورة (ترتيب نسبي داخل الشبكة)
Xn["lv"] = np.select([Xn.p3 >= q[2], Xn.p3 >= q[1], Xn.p3 >= q[0]], [3, 2, 1], 0)
slope = np.clip(Xn.pci_drop_12m / 12, .15, 3.0); Xn["pci6"] = np.clip(Xn.pci_obs - slope * 6, 0, 100); Xn["pci12"] = np.clip(Xn.pci_obs - slope * 12, 0, 100)
wk_month = [11, 12, 12, 12, 12, 12, 1, 1, 1, 1, 2, 2]; W["doy"] = pd.to_datetime(W.date).dt.dayofyear; st = pd.Timestamp("2026-11-22").dayofyear
wr = np.array([W[W.doy.isin([(st + 7 * i + k - 1) % 365 + 1 for k in range(7)])].rain.mean() for i in range(12)]); wr = wr / (wr.mean() or 1)
weeks = [int(round(S[m].sum() * 7 / 30.4 * (.8 + .2 * min(wr[i], 2.5)))) for i, m in enumerate(wk_month)]

# ---------- تفسير محلي ----------
med = tr[FEATS].median()
def explain(rows):
    base = model.predict_proba(rows[FEATS])[:, 1]; out = {}
    for g, cols in GROUPS.items():
        if g == "الموقع": continue
        Z = rows[FEATS].copy()
        for c in cols: Z[c] = med[c]
        out[g] = base - model.predict_proba(Z)[:, 1]
    return pd.DataFrame(out, index=rows.index)
ISSUE = {"منسوب المياه الجوفية": "هبوط أسفلت", "الحمل المروري": "تخدد المسار", "ضعف دمك طبقة الأساس": "حفر متكررة", "الإجهاد الحراري": "نزيف وتشققات حرارية",
         "جودة الخلطة الأسفلتية": "تفكك السطح", "حالة الرصف (PCI)": "تدهور متسارع في الرصف", "_": "تشققات وحفر"}
ACT = {"منسوب المياه الجوفية": "إعادة تأهيل طبقة الأساس مع تصريف جانبي للمياه.", "الحمل المروري": "تقوية المسار بطبقة مقاومة للتخدد.",
       "ضعف دمك طبقة الأساس": "معالجة عميقة لطبقة الأساس بدل الترقيع السطحي.", "الإجهاد الحراري": "معالجة سطحية وقائية بخلطة معدّلة بالبوليمر قبل الصيف.",
       "جودة الخلطة الأسفلتية": "كشط وإعادة سفلتة بخلطة مطابقة للمواصفة.", "حالة الرصف (PCI)": "صيانة وقائية قبل نزول المؤشر عن حد إعادة الإنشاء.",
       "سجل الأعطال السابقة": "فحص ميداني عاجل ومعالجة جذرية للموقع المتكرر.", "المعالجة السطحية السابقة": "استبدال الترقيع السطحي السابق بمعالجة جذرية.",
       "أداء المقاول": "إسناد المعالجة لمقاول أعلى تقييماً مع فحص استلام مستقل.", "عمر الطريق": "إدراج المقطع في برنامج إعادة التأهيل الدوري."}
# افتراضات التكلفة (ريال/م²)، تُستبدل بأسعار عقود الأمانة
AREA = lambda L: L * 7.5 * .12; C_PREV, C_FAIL, MOB, EFF = 90, 190 * 2.2, 15000, .7
Xn["pc"] = (AREA(Xn.length_m) * C_PREV).round(-3); Xn["rc"] = (AREA(Xn.length_m) * C_FAIL).round(-3)

cand = Xn.sort_values("p3", ascending=False).head(60); cand = cand[cand.groupby("road").cumcount() < 2].head(12)
ex = explain(cand); alerts = []
for i, r in cand.iterrows():
    c = ex.loc[i].sort_values(ascending=False); c = [g for g in c.index if c[g] > .004][:2] or ["سجل الأعطال السابقة"]
    phys = ex.loc[i, PHYS].idxmax(); p = float(r.p)
    hist = f"{int(r.fails_12m)} أعطال خلال 12 شهراً" + ("، وآخر معالجة كانت سطحية" if r.last_repair_surface and r.fails_12m else "")
    alerts.append({"id": r.asset_id, "t": r["name"], "ty": "طرق", "cls": r.cls_ar, "d": r.district, "h": r.area, "elev": (None if pd.isna(r.elev) else int(r.elev)), "rel": float(r.rel_elev), "len": int(r.length_m), "p": pct(r.p3), "p30": pct(p),
                   "days": int(min(90, max(4, round(30 * math.log(2) / -math.log(1 - min(p, .98)))))), "pci": int(round(r.pci_obs)), "pci6": int(round(r.pci6)), "pci12": int(round(r.pci12)),
                   "issue": ISSUE.get(phys, ISSUE["_"]), "cause": "أبرز العوامل حسب النموذج: " + " ثم ".join(c) + f". العامل الفيزيائي الأبرز: {phys}. السجل: {hist}.",
                   "k": r.last_contractor, "act": ACT[phys], "pc": int(r.pc), "rc": int(r.rc), "ll": [float(r.lat), float(r.lon)]})

# ---------- المناطق ----------
exd = explain(Xn.nlargest(500, "p3")); g = Xn.groupby("district"); mp = g.p.mean(); lo, hi = mp.min(), mp.max(); districts = []
for d in mp.index:
    idx = [i for i in exd.index if Xn.district[i] == d]
    districts.append({"n": d, "a": int(g.size()[d]), "km": int(round(g.length_m.sum()[d] / 1000)), "risk": int(round(22 + 66 * (mp[d] - lo) / (hi - lo))),
                      "p": int(round(g.p.sum()[d])), "pci": int(round(g.pci_obs.mean()[d])), "c": exd.loc[idx].mean().idxmax() if idx else "عمر الطريق"})

# ---------- الأحياء (أسماء حقيقية) ----------
hoods = []
for h, d in Xn[Xn.hood.notna()].groupby("hood"):
    if len(d) >= 8: hoods.append({"n": h, "segs": int(len(d)), "km": round(float(d.length_m.sum() / 1000), 1), "mp": float(d.p3.mean()), "pci": int(round(d.pci_obs.mean())), "hi": int((d.lv >= 2).sum())})
if hoods:
    lo_, hi_ = min(h["mp"] for h in hoods), max(h["mp"] for h in hoods)
    for h in hoods: h["risk"] = int(round(20 + 70 * (h["mp"] - lo_) / (hi_ - lo_ or 1))); del h["mp"]
    hoods.sort(key=lambda h: -h["risk"])
geo = {"hoods_named": int(Xn.hood.nunique()), "segs_with_hood": pct(Xn.hood.notna().mean()), "elev_n": int(Xn.elev.notna().sum()),
       "elev_min": (None if Xn.elev.isna().all() else int(Xn.elev.min())), "elev_max": (None if Xn.elev.isna().all() else int(Xn.elev.max())), "low_spots": int((Xn.rel_elev <= -3).sum())}

# ---------- تحليل البقاء: صمود الإصلاح ----------
M["ym"] = M.date.str[:7]; mo = sorted(P.month.unique()); mi = {m: i for i, m in enumerate(mo)}; Tn = len(mo)
fa = {a: sorted(mi[m] for m in d.ym) for a, d in M.groupby("asset_id")}
dur, ev = [], []
for a, m in zip(M.asset_id, M.ym):
    nxt = [x for x in fa[a] if x > mi[m]]
    dur.append((nxt[0] - mi[m]) if nxt else (Tn - mi[m])); ev.append(1 if nxt else 0)
M["dur"], M["ev"] = dur, ev
M["returned"] = (M.ev == 1) & (M.dur <= 3); M["repeat"] = [any(0 < mi[m] - x <= 12 for x in fa[a]) for a, m in zip(M.asset_id, M.ym)]
def km(df, horizon=18):
    s, out = 1.0, [1.0]
    for t in range(1, horizon + 1):
        at_risk = (df.dur >= t).sum(); d = ((df.dur == t) & (df.ev == 1)).sum()
        if at_risk: s *= 1 - d / at_risk
        out.append(round(s, 3))
    return out
def medsurv(c): return next((i for i, v in enumerate(c) if v <= .5), None)
surv = {"type": [{"n": k, "s": km(d), "jobs": int(len(d))} for k, d in M.groupby("repair_type")],
        "contractor": [{"n": "المقاول " + k, "s": km(d), "jobs": int(len(d))} for k, d in M.groupby("contractor")]}
for grp in surv.values():
    for c in grp: c["med"] = medsurv(c["s"]); c["s12"] = pct(c["s"][12])

# ---------- المواد (نموذج افتراضي) ----------
yrs = Tn / 12; fcount = M.groupby("asset_id").size(); A["nf"] = A.asset_id.map(fcount).fillna(0)
NOWA = NOW.merge(A, on="asset_id")
def matgroup(col):
    out = []
    for k, d in A.groupby(col):
        km_ = d.length_m.sum() / 1000
        out.append({"n": k, "km": int(round(km_)), "share": pct(km_ / (A.length_m.sum() / 1000)), "rate": round(float(d.nf.sum() / km_ / yrs * 100), 1),
                    "drop": round(float(NOWA[NOWA[col] == k].pci_drop_12m.mean()), 1), "test": pct(d.material_test.mean())})
    return sorted(out, key=lambda r: r["rate"])
rep_s = [{"n": k, "s": km(d), "jobs": int(len(d))} for k, d in M.groupby("repair_material")]
for c in rep_s: c["med"] = medsurv(c["s"]); c["s12"] = pct(c["s"][12])
cm = [{"n": "المقاول " + c, **{k: pct((d.repair_material == k).mean()) for k in ["ترقيع بارد", "خلطة ساخنة", "خلطة معدّلة بالبوليمر"]}} for c, d in M.groupby("contractor")]
materials = {"mix": matgroup("mix"), "base": matgroup("base_mat"), "supplier": matgroup("supplier"), "repair": sorted(rep_s, key=lambda c: -c["s12"]), "contractor": cm}

# ---------- المقاولون ----------
Mk = M[M.ym <= mo[-4]]; contractors = []
for c, d in M.groupby("contractor"):
    k = {"n": "المقاول " + c, "pr": int(len(d)), "q": int(round(d.inspection_score.mean())), "rep": pct(d.repeat.mean()), "resp": int(round(d.response_hours.mean())),
         "ret": pct(Mk[Mk.contractor == c].returned.mean()), "surf": pct((d.repair_type == "سطحية").mean())}
    k["s"] = int(round(.35 * k["q"] + .25 * (100 - k["rep"]) + .2 * max(0, 100 - k["ret"] * 1.5) + .2 * max(0, 100 - k["resp"] * 1.5))); contractors.append(k)

# ---------- أنماط محسوبة من السجلات ----------
PA = P.merge(A, on="asset_id").merge(wm[["month", "hot"]], on="month")
ratio = lambda df, mask: round(df[mask].failed.mean() / df[~mask].failed.mean(), 1)
rs, rr = pct(Mk[Mk.repair_type == "سطحية"].returned.mean()), pct(Mk[Mk.repair_type == "جذرية"].returned.mean())
pats = [[f"<em>{rs}%</em> من المعالجات السطحية عاد عطلها خلال 90 يوماً، مقابل <em>{rr}%</em> للمعالجات الجذرية.", "المعالجة: اعتماد المعالجة الجذرية لأي مقطع تكرر فيه البلاغ."],
        [f"المقاطع التي نزل مؤشر رصفها عن 55 تتعطل <em>{ratio(PA, PA.pci_obs < 55)} مرة</em> أكثر من غيرها.", "المعالجة: صيانة وقائية قبل الوصول لهذا الحد."],
        [f"الأعطال أعلى بـ <em>{ratio(PA, PA.gw_depth < 1.5)} مرة</em> حيث يقل عمق المياه الجوفية عن 1.5 م.", "المعالجة: اشتراط تصريف جانبي في مواصفة هذه المقاطع."],
        [f"في الأشهر شديدة الحرارة (15 يوماً فأكثر فوق 43°م) ترتفع أعطال الطرق عالية الحركة <em>{ratio(PA[PA.traffic > .6], PA[PA.traffic > .6].hot >= 15)} مرة</em>.", "المعالجة: خلطات معدّلة بالبوليمر للطرق الشريانية."]]
causes = {"طرق": {"f": importance[:7], "pat": pats}}

# ---------- أمثلية أوامر العمل: تجميع المقاطع المتجاورة على الطريق نفسه ----------
Xn["p12"] = 1 - (1 - Xn.p3) ** 4                                   # افتراض: ثبات معدل الخطر على مدى 12 شهراً
hot = Xn[Xn.p12 * EFF * Xn.rc > Xn.pc].copy()                         # نرشّح فقط المقاطع التي عائد وقايتها موجب
hot["cause"] = explain(hot)[PHYS].idxmax(axis=1); recs = []
hot["grp"] = np.where(hot.osm_name.notna(), hot.road, hot.road + " #" + hot.way_id.astype(str))
for (gk, d), grp in hot.groupby(["grp", "district"]):
    road = grp.road.iloc[0]; cost = MOB + grp.pc.sum(); f = (grp.p12 * EFF).sum(); s = (grp.p12 * EFF * grp.rc).sum()
    recs.append({"t": f"{road}: {ACT[grp.cause.mode()[0]].rstrip('.')}", "d": d, "n": int(len(grp)), "km": round(grp.length_m.sum() / 1000, 1),
                 "c": int(round(cost, -3)), "f": round(float(f), 1), "s": int(round(s, -3))})
single_roi = float((hot.p12 * EFF * hot.rc).sum() / (hot.pc.sum() + MOB * len(hot))); group_roi = sum(r["s"] for r in recs) / sum(r["c"] for r in recs)
recs = sorted([r for r in recs if r["f"] >= .4], key=lambda r: -r["s"] / r["c"])[:10]
optim = {"candidates": int(len(hot)), "orders": int(hot.groupby(["grp", "district"]).ngroups), "total_cost": int(sum(r["c"] for r in recs)), "total_saving": int(sum(r["s"] for r in recs)), "roi_grouped": round(group_roi, 2), "roi_single": round(single_roi, 2), "mob": MOB}

# ---------- الشبكة و PCI ----------
bands = [("ممتاز (85 فأعلى)", 85, 101), ("جيد (70–85)", 70, 85), ("مقبول (55–70)", 55, 70), ("ضعيف (40–55)", 40, 55), ("متهالك (أقل من 40)", -1, 40)]
pci_bands = [[n, round(float(Xn.length_m[(Xn.pci_obs >= a) & (Xn.pci_obs < b)].sum() / 1000), 1)] for n, a, b in bands]
below12 = float(Xn.length_m[(Xn.pci_obs >= 55) & (Xn.pci12 < 55)].sum() / 1000)
network = {"segments": int(len(A)), "km": int(round(A.length_m.sum() / 1000)), "ways": int(A.way_id.nunique()), "named": pct(A.osm_name.notna().mean()),
           "osm_time": RAW.get("osm3s", {}).get("timestamp_osm_base", "")[:10], "pci_avg": int(round(np.average(Xn.pci_obs, weights=Xn.length_m))),
           "pci_bands": pci_bands, "pci_hist": [round(float(x), 1) for x in PM.pci_mean.tail(8)], "below55_in_12m_km": round(below12, 1)}

# ---------- مؤشرات اللوحة ----------
fm = P.groupby("month").failed.sum(); rm = M.groupby("ym").repeat.mean()
kpi = {"pred30": int(round(S[11].sum())), "pred_hist": [int(x) for x in fm.tail(7)] + [int(round(S[11].sum()))], "last_actual": int(fm.iloc[-1]),
       "repeat": pct(rm.tail(3).mean()), "repeat_prev": pct(rm.iloc[-9:-6].mean()), "repeat_hist": [pct(x) for x in rm.tail(8)], "recall5": pct(mm["rec"])}

out = {"roads": True, "sev": SEV,
       "meta": {"weather_source": W.source.iloc[0], "weather_days": int(len(W)), "n_assets": int(len(A)), "n_reports": int(len(R)), "n_maint": int(len(M)), "period": [mo[0], mo[-1]],
                "train_rows": int(len(tr)), "test_rows": int(len(te)), "test_from": TEST_FROM, "algo": "Gradient Boosting (scikit-learn HistGradientBoosting)", "n_features": len(FEATS)},
       "metrics": metrics, "importance": importance, "weeks": weeks, "districts": districts, "alerts": alerts, "causes": causes, "contractors": contractors,
       "recs": recs, "optim": optim, "surv": surv, "materials": materials, "hoods": hoods, "geo": geo, "network": network, "kpi": kpi}
js = json.dumps(out, ensure_ascii=False)
open(os.path.join(DATA, "model_output.json"), "w", encoding="utf-8").write(js)
open(os.path.join(DATA, "model_output.js"), "w", encoding="utf-8").write("window.MODEL=" + js + ";")
# المقاطع للخريطة: [الإحداثيات، المستوى، الاحتمالية%، PCI، فهرس الاسم، الطول]
names = sorted(Xn.road.unique()); ni = {n: i for i, n in enumerate(names)}; hn = sorted(Xn.area.unique()); hi2 = {n: i for i, n in enumerate(hn)}
segs = [[GEOM[r.asset_id], int(r.lv), pct(r.p3), int(round(r.pci_obs)), ni[r.road], int(r.length_m), hi2[r.area], (None if pd.isna(r.elev) else int(r.elev))] for r in Xn.itertuples()]
open(os.path.join(DATA, "segments.js"), "w", encoding="utf-8").write("window.SEGS=" + json.dumps({"names": names, "areas": hn, "rows": segs}, ensure_ascii=False, separators=(",", ":")) + ";")
print(json.dumps({"metrics": metrics, "kpi": kpi, "weeks": weeks, "importance": importance, "sev": SEV, "optim": optim, "network": network}, ensure_ascii=False))
print([(a["p"], a["p30"], a["pci"], a["pci12"], a["pc"], a["rc"]) for a in alerts])
print([(c["n"], c["med"], c["s12"]) for g in surv.values() for c in g]); print([(k["n"], k["s"], k["ret"]) for k in contractors])
for r in recs[:10]: print(round(r["s"] / r["c"], 1), r["n"], r["km"], r["c"], r["f"], r["t"][:60], r["d"])
print(json.dumps(hoods[:8], ensure_ascii=False)); print(geo)
