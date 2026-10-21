# Visbox 0.3.17 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.17 auf `main` («Datei laden» vom Mac stellt die Heim-Mappe nicht mehr um; neue Kamera-Knoten auf «Auto»); Vorgänger 0.3.16 = Tag `v0.3.16`

**Grundlage:** Entscheide 118a, 119 (eingetragen, noch nicht gebaut); Befund 304 B1; Folgeauftrag des Integrators zu
§176; Protokoll 74 §179–§180; Einbau-Stand C107. Abgeglichen gegen alle Änderungen seit `v0.3.16`
(`git log v0.3.16..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.17

Die Messung 304 fand, dass «Datei laden …» in einer Mappe am Mac am Heim-PC die zuletzt geöffnete Mappe für alle Geräte
umstellte. Die Behebung braucht die neue Mac-App.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Datei laden …» in einer Mappe am Mac legt das Modell nur in diese Mappe; die Mappe der anderen Geräte am Heim-PC bleibt stehen | — (304) | gebaut, mit Probe; Messung 307 offen |
| Neue Kamera-Knoten beginnen auf «Auto»; bestehende behalten ihre Einstellung | — (Integrator) | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Danach in einer Mappe am Mac «Datei laden …» — die Visbox-Seite und das iPad zeigen weiter
  ihre Mappe.
* **Heim-PC:** `git pull`; Laden vom Mac stellt die zuletzt geöffnete Mappe nicht mehr um (Ansage lag vorab). Am Rechnen
  ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine Mac-App mit 0.3.16 verhält sich noch wie vor der Behebung — bitte zuerst aktualisieren.
* Der breitere Render-Knoten (Entscheid 119) und das Ende des direkten iPad-Wegs (118a) sind noch im Bau.
* Die Stimmung wird im KI-Bild der Knotenansicht nur halb übersetzt (Messung 306); die Behebung ist im Bau.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
