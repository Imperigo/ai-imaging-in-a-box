# Visbox 0.3.0 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.0 auf `main` (die Mac-App bringt die Knotenansicht selbst mit); Vorgänger 0.2.12 = Tag `v0.2.12` (20.10.2026)

**Grundlage:** Owner-Auftrag 20.10.2026 «baue nächste version richtig!»; Plan
`docs/PLAN_VISBOX_EIGENSTAENDIG_2026-10-20.md` (Schritt 1); Entscheide 103–103c; Protokoll 74 §146

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.0

Mit 0.3.x zieht die Oberfläche auf das Gerät: Visbox läuft am Mac, der Heim-PC wird zum Rechenserver. Der erste Schritt:
**Die Mac-App bringt die Knotenansicht selbst mit.** Bis 0.2.12 lud sie sie vom Heim-PC — ohne Heim-PC keine Knoten, und
jede Änderung an den Knoten kam über `git pull` am Heim-PC statt mit der App.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: Die Knotenansicht kommt aus dem App-Bündel (eigenes Adressschema `visbox://app/knoten/`), nicht mehr vom Heim-PC | Plan Schritt 1 | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Mappe, Graph, Modell, Skizzen, «Datei laden …» und die Render-Aufträge reicht die App an den Heim-PC weiter — mit ihrer Anmeldung und dem angehefteten Zertifikat | Plan Schritt 1 | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Ohne eingerichteten Heim-PC laden die Knoten trotzdem; Mappe und Rechnen antworten sofort mit einem Satz, statt zu hängen | Plan Schritt 1 | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Formulare mit Datei (Modell beim Bestellen, «Datei laden …») gehen als fertige Bytes an die App, damit unterwegs nichts verloren geht | Plan Schritt 1 | gebaut, mit Probe; am Gerät unbestätigt |
| Prüfstrecke: Der Bau der Knotenansicht liegt im Mac-Bündel (`Contents/Resources/Knoten`); ein neuer Bau startet den Mac-Lauf | Plan Schritt 1 | gebaut, mit Probe |

## Entschieden (Entscheide 103–103c, Owner 20.10.2026)

Die Fragen aus Plan §9 hat der Owner am 20.10.2026 per Auswahl entschieden (`docs/ENTSCHEIDE_IPAD_2026-09-21.md`):

* **103 — Die Mappe liegt am Mac.** In diesem Schritt liegt sie **noch am Heim-PC**: Die App reicht `./mappe`,
  `./graph`, `./modell.glb`, `./skizze` und `./modell-laden` dorthin durch. Schritt 3 holt sie ans Gerät.
* **103a — Das iPad holt die Mappe vom Mac.** In diesem Schritt unverändert (das iPad spricht weiter mit dem Heim-PC);
  Schritt 4.
* **103b — Der Vorführmodus entfällt.** In diesem Schritt **noch nicht abgebaut**: Ohne Heim-PC zeigt die Mac-App ihn
  weiter. Die Zeile «ohne Heim-PC» kommt in Schritt 2, nach Blatt 28 der Entwurfsfläche.
* **103c — Die Visbox-Seite kommt nicht in die App, sie wird Knoten.** In diesem Schritt kommt sie **weiter vom
  Heim-PC** («Darstellung → Visbox-Seite»); ins Bündel kommt nichts von ihr.

## Stand am Gerät

* **Mac:** die neue App laden und öffnen. Die Knoten erscheinen auch, wenn der Heim-PC aus ist; dann steht beim Laden
  der Mappe «Kein Heim-PC eingerichtet …» bzw. «Der Heim-PC ist nicht erreicht: …».
* **Heim-PC:** unverändert. Er liefert die Knoten weiter für einen Browser aus; die Mac-App braucht davon nur noch
  die Datenwege.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft.** WebKit-Eigenheiten des eigenen Schemas (Ursprung, `localStorage`, Rumpf von Formularen,
  Modul-Skripte) sind nach bestem Wissen behandelt, aber erst der Mac zeigt, ob alles trägt. Unsicher ist vor allem
  der Rumpf: Kommt ein Formular dennoch leer an, sagt der Heim-PC, dass die Datei fehlt.
* **Kein Weiterstreamen:** Eine Antwort des Heim-PC (etwa ein grosses Modell) kommt erst ganz an die App und dann an die
  Seite — bei grossen glb kurz spürbar, und sie liegt so lange im Arbeitsspeicher.
* **Fortschritt beim Hochladen** zeigt die Seite nicht mehr feiner als «läuft»: Die App reicht den Rumpf in einem Stück
  weiter.
* **Knotenänderungen kommen jetzt mit der Mac-App**, nicht mehr mit `git pull` am Heim-PC. Wer die Knoten ändert, braucht
  eine Mac-Freigabe.
* Der `localStorage` der Knoten (Adresse der Brücke, Kurztasten) lebt nur, solange das Fenster offen ist — wie bisher,
  weil das Webfenster nichts auf die Platte schreibt.

## Prüfung

Kern: `swift test` grün (Knotenwege, Flaechenwahl). Volle Suite ohne GPU, grün (Zahl in `README.md`); Knotenansicht:
`npm test` in `kosmovis/` grün, Bau neu gestempelt. Mac: Prüfstrecke `.github/workflows/ipad.yml`, Job «Mac-App bauen»
mit Auskunft «Liegt die Knotenansicht im Buendel?»; der Job `freigabe` legt die Freigabe erst auf `main` mit neuer
Nummer an.
