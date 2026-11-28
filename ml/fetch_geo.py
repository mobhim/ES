# -*- coding: utf-8 -*-
"""
صاهود: جلب البيانات الجغرافية الحقيقية المساندة (يُشغَّل مرة واحدة، والنتائج تُخزَّن في data/)
1) أسماء الأحياء والبلدات: OpenStreetMap عبر Overpass  -> data/neighbourhoods_raw.json
2) ارتفاع منتصف كل مقطع: Open-Meteo Elevation (نموذج Copernicus DEM 90m) -> data/elevation.csv
يُشغَّل بعد generate_data.py (يحتاج assets.csv)، ثم يُعاد تشغيل generate_data.py ليستخدم النتائج.
"""
import json, os, time, urllib.parse, urllib.request
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "sahood-hackathon-prototype/1.0"}

def neighbourhoods():
    path = os.path.join(DATA, "neighbourhoods_raw.json")
    if os.path.exists(path): return
    q = '[out:json][timeout:60];(node["place"~"^(suburb|neighbourhood|quarter|village|town|city)$"](25.28,49.48,25.66,49.80););out tags center;'
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r: open(path, "wb").write(r.read())

def elevation():
    path = os.path.join(DATA, "elevation.csv")
    A = pd.read_csv(os.path.join(DATA, "assets.csv"), encoding="utf-8-sig")[["asset_id", "lat", "lon"]]
    done = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=["asset_id", "elev"])
    todo = A[~A.asset_id.isin(done.asset_id)]
    rows = done.values.tolist()
    for i in range(0, len(todo), 100):                       # الحد 100 نقطة للطلب، وطلب واحد في الثانية
        ch = todo.iloc[i:i + 100]
        url = "https://api.open-meteo.com/v1/elevation?latitude=" + ",".join(map(str, ch.lat)) + "&longitude=" + ",".join(map(str, ch.lon))
        for attempt in range(8):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: res = json.load(r)["elevation"]
                break
            except Exception as e:
                print("retry", i, e); time.sleep(10 + attempt * 10)
        else: raise SystemExit("elevation fetch failed")
        rows += [[sid, x] for sid, x in zip(ch.asset_id, res)]
        pd.DataFrame(rows, columns=["asset_id", "elev"]).to_csv(path, index=False)
        time.sleep(.6)
    print("elevation rows", len(rows))

if __name__ == "__main__":
    neighbourhoods(); elevation()
