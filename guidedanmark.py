#!/usr/bin/env python3
"""
GuideDanmark-ingestion (VisitDenmarks officielle turisme-API).

Henter events (+ valgfrit attraktioner) for Odense og mapper til appens
Event/Attraction-skema. Credential-styret: hvis miljøvariablerne ikke er sat,
returnerer modulet tomme lister, så pipelinen kører videre på OSM alene.

Miljøvariabler (sæt som GitHub Actions secrets):
  GUIDEDANMARK_USER
  GUIDEDANMARK_PASS
  GUIDEDANMARK_ODENSE_MUNICIPALITY_ID   (valgfri; hentes ellers automatisk)

API-detaljer: https://api.guidedanmark.org  (OAuth2 password grant, token ~1t)
Kør batch EFTER kl. 04:00 CET (vedligehold 00–04). Kreditér fotograf/copyright.
"""
import os, time, datetime, urllib.parse, urllib.request, urllib.error, json

BASE = "https://api.guidedanmark.org"
CAT_EVENTS = "58"
CAT_ATTRACTIONS = "3"

# GuideDanmark-kategorinavn -> appens Category-enum (rawValue)
def map_event_category(name: str) -> str:
    n = (name or "").lower()
    table = [
        ("musik", "musik"), ("koncert", "musik"), ("teater", "teater"),
        ("scene", "teater"), ("kunst", "kunst"), ("udstilling", "kunst"),
        ("museum", "museum"), ("børn", "boern"), ("familie", "boern"),
        ("film", "film"), ("biograf", "film"), ("festival", "festival"),
        ("litteratur", "litteratur"), ("bog", "litteratur"),
        ("mad", "mad"), ("vin", "mad"), ("smagning", "mad"), ("marked", "mad"),
        ("foredrag", "foredrag"), ("talk", "foredrag"),
    ]
    for key, cat in table:
        if key in n:
            return cat
    return "festival"  # generisk fallback

_token = {"v": None, "exp": 0}

def _creds():
    return os.environ.get("GUIDEDANMARK_USER"), os.environ.get("GUIDEDANMARK_PASS")

def _get_token():
    if _token["v"] and time.time() < _token["exp"]:
        return _token["v"]
    user, pwd = _creds()
    body = urllib.parse.urlencode({
        "grant_type": "password", "username": user, "password": pwd}).encode()
    req = urllib.request.Request(BASE + "/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    _token["v"] = j["access_token"]
    _token["exp"] = time.time() + 3300
    return _token["v"]

def _api(path, **params):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for _ in range(2):
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {_get_token()}",
            "Accept": "application/json", "Accept-Language": "da"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                _token["v"] = None; continue
            raise
    return None

def _odense_municipality_id():
    forced = os.environ.get("GUIDEDANMARK_ODENSE_MUNICIPALITY_ID")
    if forced:
        return forced
    muns = _api("/api/Municipalities") or []
    for m in muns:
        if (m.get("Name") or "").lower() == "odense":
            return str(m.get("Id"))
    return None

def _first_image(files):
    for f in files or []:
        uri = f.get("Uri")
        if uri:
            return uri
    return None

def _long_desc(descs):
    best = ""
    for d in descs or []:
        text = d.get("Text") or ""
        if (d.get("DescriptionType") or "").lower().startswith("long") and text:
            return text
        if text and len(text) > len(best):
            best = text
    return best

def _to_event(p):
    addr = p.get("Address") or {}
    geo = addr.get("GeoCoordinate") or {}
    periods = p.get("Periods") or []
    per = periods[0] if periods else {}
    start_date = per.get("StartDate")
    if not start_date:
        return None
    start_time = per.get("StartTime") or "10:00"
    try:
        start = f"{start_date}T{start_time}:00"
        # valider
        datetime.datetime.fromisoformat(start)
    except Exception:
        start = f"{start_date}T10:00:00"
    price_groups = p.get("PriceGroups") or []
    price = None
    for pg in price_groups:
        if pg.get("Free"):
            price = 0; break
        if pg.get("PriceFrom") is not None:
            price = int(pg["PriceFrom"]); break
    link = (p.get("ContactInformation") or {}).get("Link") or p.get("CanonicalUrl")
    cat_name = (p.get("MainCategory") or p.get("Category") or {}).get("Name", "")
    return {
        "id": f"gd-{p.get('Id')}",
        "title": p.get("Name") or "Begivenhed",
        "category": map_event_category(cat_name),
        "venueID": f"gd-venue-{p.get('Id')}",
        "venueName": addr.get("City") and (p.get("Name") and addr.get("AddressLine1")) or addr.get("AddressLine1") or "Odense",
        "venueAddress": ", ".join(x for x in [addr.get("AddressLine1"), addr.get("PostalCode"), addr.get("City")] if x),
        "venueLatitude": geo.get("Latitude"),
        "venueLongitude": geo.get("Longitude"),
        "start": start,
        "durationMinutes": 120,
        "summary": (_long_desc(p.get("Descriptions")) or "")[:140],
        "description": _long_desc(p.get("Descriptions")) or "",
        "priceDKK": price,
        "ticketURL": link,
        "imageURL": _first_image(p.get("Files")),
        "source": "GuideDanmark",
    }

def fetch_events():
    """Returnér liste af event-dicts for Odense, eller [] hvis ingen credentials."""
    user, pwd = _creds()
    if not user or not pwd:
        print("GuideDanmark: ingen credentials sat — springer over (OSM-only).")
        return []
    mun = _odense_municipality_id()
    if not mun:
        print("GuideDanmark: kunne ikke finde Odense municipality-id.")
        return []
    events, offset, page = [], 0, 500
    while True:
        batch = _api("/api/SearchProducts",
                     categoryIds=CAT_EVENTS, municipalityIds=mun,
                     count=page, offset=offset) or []
        for p in batch:
            ev = _to_event(p)
            if ev:
                events.append(ev)
        if len(batch) < page:
            break
        offset += page
    print(f"GuideDanmark: {len(events)} events for Odense (municipality {mun}).")
    return events

if __name__ == "__main__":
    evs = fetch_events()
    print(json.dumps(evs[:3], ensure_ascii=False, indent=2))
