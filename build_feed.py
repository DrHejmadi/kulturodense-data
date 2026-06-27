#!/usr/bin/env python3
"""
Kultur Odense — datapipeline.

Henter PERMANENTE seværdigheder i Odense fra OpenStreetMap (Overpass) og
beriger dem med billede/beskrivelse fra Wikidata. Skriver et feed.json som
appen henter remote. Kører gratis, uden nøgle, og er beregnet til at køre
dagligt via GitHub Actions.

Events (tidsbestemte) tilføjes senere fra GuideDanmark/Kultunaut når en
dataaftale er på plads — feed-formatet har allerede et "events"-felt.
"""
import json, sys, time, urllib.parse, urllib.request, datetime

OVERPASS = "https://overpass-api.de/api/interpreter"
WIKIDATA = "https://www.wikidata.org/w/api.php"
# Odense bounding box (S,W,N,E)
BBOX = (55.34, 10.32, 55.45, 10.46)

# OSM-tag -> appens attraktionskategori
def categorize(tags):
    if tags.get("memorial") == "stolperstein" or tags.get("memorial:type") == "stolperstein":
        return "snublesten"
    if tags.get("tourism") == "museum":
        return "museum"
    if tags.get("tourism") == "artwork":
        return "kunst"
    if tags.get("tourism") == "gallery":
        return "kunst"
    h = tags.get("historic")
    if h in ("memorial", "monument", "memorial_plaque"):
        return "monument"
    if h:
        return "historisk"
    return None

def overpass_query():
    s, w, n, e = BBOX
    box = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:90];
(
  node["memorial"="stolperstein"]({box});
  node["memorial:type"="stolperstein"]({box});
  node["tourism"="artwork"]({box});
  way["tourism"="artwork"]({box});
  node["tourism"="museum"]({box});
  way["tourism"="museum"]({box});
  node["tourism"="gallery"]({box});
  node["historic"]({box});
  way["historic"]({box});
);
out center tags;
"""

def fetch_overpass():
    data = urllib.parse.urlencode({"data": overpass_query()}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "KulturOdense/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def wikidata_info(qids):
    """Hent billede + dansk/engelsk beskrivelse for en liste af Q-id'er."""
    out = {}
    for i in range(0, len(qids), 40):
        chunk = qids[i:i+40]
        params = {
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "claims|descriptions", "languages": "da|en", "format": "json",
        }
        url = WIKIDATA + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "KulturOdense/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
        except Exception as ex:
            print("wikidata fejl:", ex, file=sys.stderr); continue
        for qid, ent in d.get("entities", {}).items():
            img = None
            claims = ent.get("claims", {})
            if "P18" in claims:  # image
                try:
                    fn = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                    fn2 = fn.replace(" ", "_")
                    img = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(fn2)
                except Exception:
                    pass
            desc = ent.get("descriptions", {})
            text = (desc.get("da") or desc.get("en") or {}).get("value")
            out[qid] = {"image": img, "desc": text}
        time.sleep(0.3)
    return out

def main():
    print("Henter fra Overpass…", file=sys.stderr)
    raw = fetch_overpass()
    elements = raw.get("elements", [])
    print(f"  {len(elements)} OSM-elementer", file=sys.stderr)

    attractions = []
    qids = []
    for el in elements:
        tags = el.get("tags", {})
        cat = categorize(tags)
        if not cat:
            continue
        name = tags.get("name") or tags.get("name:da") or tags.get("inscription")
        if not name:
            continue
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        qid = tags.get("wikidata")
        if qid:
            qids.append(qid)
        attractions.append({
            "id": f"osm-{el['type']}-{el['id']}",
            "title": name.strip(),
            "category": cat,
            "latitude": round(float(lat), 6),
            "longitude": round(float(lon), 6),
            "summary": tags.get("inscription") or "",
            "description": "",
            "imageURL": None,
            "wikidata": qid,
            "website": tags.get("website") or tags.get("contact:website"),
        })

    print(f"  {len(attractions)} relevante seværdigheder, {len(qids)} med Wikidata", file=sys.stderr)

    if qids:
        info = wikidata_info(list(dict.fromkeys(qids)))
        for a in attractions:
            q = a.get("wikidata")
            if q and q in info:
                if info[q]["image"]:
                    a["imageURL"] = info[q]["image"]
                if info[q]["desc"] and not a["description"]:
                    a["description"] = info[q]["desc"]

    # sortér: snublesten og museer øverst, derefter alfabetisk
    order = {"museum": 0, "snublesten": 1, "kunst": 2, "monument": 3, "historisk": 4}
    attractions.sort(key=lambda a: (order.get(a["category"], 9), a["title"]))

    feed = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "OpenStreetMap (ODbL) + Wikidata",
        "attractions": attractions,
        "events": [],   # udfyldes senere fra GuideDanmark/Kultunaut
    }
    out_path = sys.argv[1] if len(sys.argv) > 1 else "feed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)
    print(f"Skrev {out_path}: {len(attractions)} seværdigheder", file=sys.stderr)

if __name__ == "__main__":
    main()
