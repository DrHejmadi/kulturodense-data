# GuideDanmark — sådan aktiverer du events

Pipelinen er **klar** til GuideDanmark. Events tilføjes automatisk så snart
credentials er lagt ind som GitHub Secrets. Indtil da kører feedet videre på
OpenStreetMap alene (events-feltet er tomt).

## 1. Få adgang (engangs)
1. Send ansøgningen i [ANSOEGNING-guidedanmark.md](ANSOEGNING-guidedanmark.md)
   til **guidedanmark@visitdenmark.com**.
2. Engangsgebyr: **5.000 kr. ekskl. moms** (ingen løbende abonnement fundet).
3. Ved godkendelse får du **username + password**.

## 2. Find de to id'er (efter du har credentials)
Kør lokalt med dine credentials:
```bash
GUIDEDANMARK_USER=... GUIDEDANMARK_PASS=... python3 -c "
import guidedanmark as g
print('Odense municipality:', g._odense_municipality_id())
"
```
(Find evt. også VisitOdenses owner/mediaChannel-id via `/api/Offices` hvis du
vil filtrere på kanal i stedet for kommune.)

## 3. Læg credentials ind som GitHub Secrets
I repoet → Settings → Secrets and variables → Actions → New repository secret:
- `GUIDEDANMARK_USER`
- `GUIDEDANMARK_PASS`
- `GUIDEDANMARK_ODENSE_MUNICIPALITY_ID` (valgfri — ellers slås det op automatisk)

Eller via CLI:
```bash
gh secret set GUIDEDANMARK_USER --repo DrHejmadi/kulturodense-data
gh secret set GUIDEDANMARK_PASS --repo DrHejmadi/kulturodense-data
```

## 4. Kør
Workflowen kører dagligt (04:30 UTC) og henter nu også events. Trig manuelt:
```bash
gh workflow run "Opdater feed" --repo DrHejmadi/kulturodense-data
```
`feed.json` får derefter et udfyldt `events`-felt, og appen viser dem automatisk
(ingen app-opdatering nødvendig — events vises via det remote feed).

## Vilkår
- Vis fotograf/copyright på billeder (felterne `Photographer`/`Copyright`).
- Angiv GuideDanmark som kilde. Bekræft den præcise krediteringstekst i aftalen.
- Kør batch efter kl. 04:00 CET (vedligehold 00–04). Brug delta-kald.
