# Kultur Odense — data

Selvkørende datafeed til Kultur Odense-appen. `build_feed.py` henter permanente
seværdigheder fra OpenStreetMap (Overpass) + Wikidata og skriver `feed.json`.
GitHub Actions kører dagligt (se `.github/workflows/update.yml`).

`feed.json` serveres via GitHub Pages:
**https://drhejmadi.github.io/kulturodense-data/feed.json**

Events (tidsbestemte) tilføjes når en GuideDanmark/Kultunaut-dataaftale er på plads
— feed-formatet har allerede et tomt `events`-felt klar.
