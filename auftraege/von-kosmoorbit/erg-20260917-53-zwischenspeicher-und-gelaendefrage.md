# erg-20260917-53 — `auf-20260826-53` (an: ui): U7/U8 sind bei uns NICHT baubar — es fehlt das Vertragsfeld, nicht der UI-Wille

**Stand 17.09.2026:** offen — woran gemessen: beide Vertragsfelder
(`zwischenspeicher.{treffer,schluessel,gerechnet_unter}` und
`gelaende_befund/gelaende_geprueft/gelaende_begruendung`) fehlen im heutigen
`packages/kosmo-contracts/src/render-result.ts` vollstaendig. Eine Anzeige kann nicht gebaut
werden, bevor das Feld ankommt — das Blatt selbst formuliert seine Lieferung im
Futur («was wir liefern»), nicht als bereits gesendet, das deckt sich mit dem Befund.

Arbeitsstand: `kosmo-orbit` HEAD `407b0cc3` (2026-09-17). Reine Lesemessung.

---

## U7 · Zwischenspeicher-Treffer am Bild erkennbar machen

**Befund: kein Vertragsfeld, keine Anzeige, keine Bauabhaengigkeit verletzt.**

Befehl:
```
grep -rn "zwischenspeicher" packages/kosmo-contracts/src/render-result.ts
grep -rln "zwischenspeicher" apps/kosmo-orbit/src --include=*.ts --include=*.tsx
```
Beide liefern 0 Treffer im relevanten Code (Gegenprobe: derselbe Suchweg findet das Wort
sehr wohl in `docs/auftraege-kosmovis/auf-20260826-53.md` selbst und in einer frueheren
internen Messnotiz — der Suchbefehl funktioniert, das Feld fehlt echt). Der Anzeigeteil
(eine unaufdringliche Badge an der Bildkachel, geschaetzt 10-20 Zeilen, an
`KuratierFlaeche.tsx`/`NodeCanvas.tsx`) ist damit **klein und baubar, sobald das Feld
ankommt** — hier bewusst NICHT gebaut, weil dieser Durchgang nichts baut und weil die
Grundlage fehlt.

**U7a — reicht `zwischenspeicher.treffer` je Kamera, oder auch je Auftrag zusammengefasst?**
Antwort: je Kamera reicht als Datenquelle. Eine Zusammenfassung je Auftrag («2 von 3
Kameras aus dem Speicher») ist reine Anzeigelogik ueber denselben Kamera-Werten — sie
braucht kein zweites Feld, nur eine `.filter(...).length`-Zeile auf unserer Seite. Ihr
muesst also nichts zusaetzlich aggregiert liefern.

## U8 · Die Gelaendefrage vorlegen statt abverlangen

**Befund: kein Vertragsfeld, keine Rueckfrage im Code.**

Befehl:
```
grep -rn "gelaende_befund\|gelaende_geprueft\|gelaende_begruendung\|kein_gelaende\|nicht_entscheidbar" packages/kosmo-contracts/src/*.ts apps/kosmo-orbit/src/modules/vis/*.ts apps/kosmo-orbit/src/modules/vis/*.tsx
```
0 Treffer — weder das Vertragsfeld noch eine Rueckfrage-UI existieren im aktuellen Baum.
Dieselbe Lage wie U7: nicht gebaut, weil die Grundlage fehlt, nicht weil der Vorschlag
verworfen wurde.

**U8a — ist die Rueckfrage bei `kein_gelaende_belegt` zumutbar?** Das ist keine Code-Messung,
sondern eine Abwaegungsfrage (ein zusaetzlicher Klick pro betroffenem Lauf gegen den Nutzen,
eine unvollstaendige Wortliste sichtbar zu machen). Unsere Einschaetzung, kein
OWNER-ENTSCHEID: **zumutbar**, unter der im Blatt selbst gesetzten Bedingung, dass sie nur
bei `kein_gelaende_belegt` erscheint und bei `nicht_entscheidbar` ausdruecklich schweigt —
eine Rueckfrage, die nur in einem klar messbaren Fall auftaucht (Baustoffe wurden geprueft,
keiner traf), ist kein «Wegklick-Reflex»-Fall, weil sie einen konkreten Inhalt zeigt (die
Namensliste), nicht nur eine Ja/Nein-Floskel.

**U8b — wie kaeme «Doch, es gibt Gelaende» zu euch zurueck?** Ein Feld im naechsten
Ergebnis-Request ist uns tatsaechlich am liebsten, wie ihr selbst vorschlagt — das ist aber
ein Feld im **Auftrag**, nicht im Ergebnis (`RenderScene`/`kosmovis.render-scene`), also
ebenfalls eine Frage an den Cloud-Worker-Vertrag (`auf-20260826-49`), nicht an uns zu
entscheiden.

---

## Was hier nicht gemessen wurde

* Ob eine Anzeige fuer beide Felder inzwischen an anderer Stelle **entworfen**, aber noch
  nicht committet liegt — nur der committete Baum wurde geprueft.
* Keine Bildschirmmessung, kein Build.

**Zeile:** offen — beide Punkte sind bei uns nicht baubar, solange die Vertragsfelder beim
Cloud-Worker fehlen; die drei gestellten Fragen (U7a, U8a, U8b) sind beantwortet.
