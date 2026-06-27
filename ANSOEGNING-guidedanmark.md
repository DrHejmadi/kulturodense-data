# Ansøgning til GuideDanmark (klar til afsendelse)

**Til:** guidedanmark@visitdenmark.com (kopi: support@visitdenmark.com)
**Emne:** Ansøgning om adgang til GuideDanmark Web Service — kulturapp for Odense

---

Kære VisitDenmark / GuideDanmark-team

Jeg vil gerne ansøge om adgang til GuideDanmark Web Service (api.guidedanmark.org) til brug i en mobilapp.

**Om projektet**
"Kultur Odense" er en gratis iPhone-app, der samler kultur- og oplevelseslivet i Odense ét sted — begivenheder, attraktioner, museer og erhvervstilbud (fx koncerter, teater, udstillinger, familiearrangementer og events som vinsmagninger). Appen er allerede udgivet på App Store (App ID 6784834304) og henter i dag permanente seværdigheder automatisk fra OpenStreetMap. Vi ønsker at supplere med jeres officielle og kvalitetssikrede data for tidsbestemte events og attraktioner.

Det er hensigten, at produktet på sigt overdrages til Odense Kommune / Odense Erhvervsforening som et offentligt, ikke-kommercielt tilbud til borgere og turister.

**Hvad vi ønsker at hente**
- Geografi: Odense Kommune (og evt. Fyn)
- Produkttyper: Events (kategori 58), Attraktioner (kategori 3) og spisesteder/erhverv (kategori 62)
- Sprog: dansk (evt. engelsk)

**Teknisk brug**
- Ét dagligt batch-kald (efter kl. 04:00 CET), via en automatiseret pipeline (GitHub Actions). Vi bruger delta-hentning (modifiedSince / Product/deleted) for at minimere belastning.
- Vi viser fotograf- og copyright-kreditering på billeder og angiver GuideDanmark som datakilde i appen, i henhold til jeres vilkår.

**Praktisk**
Jeg er indforstået med engangsgebyret for adgang og beder jer venligst sende:
1. Ansøgnings-/aftaleformular
2. Bekræftelse af pris og licensvilkår (herunder den præcise krediteringstekst)
3. Tekniske credentials (username/password) ved godkendelse

Kontakt:
- Navn: Michael Skov Hejmadi
- E-mail: hejmadi@gmail.com
- App: Kultur Odense (App Store), bundle id com.hejmadi.kulturodense

Tak på forhånd — jeg ser frem til at høre fra jer.

Venlig hilsen
Michael Skov Hejmadi
