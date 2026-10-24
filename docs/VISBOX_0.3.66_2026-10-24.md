# Visbox 0.3.66 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.66 auf `main` (Umfeld im Umkreis des Hauptbaus, Rest ruhig); Vorgänger 0.3.65 = Tag `v0.3.65`

**Grundlage:** Ergebnis 363; Entscheid 150; Protokoll 74 §288 (Nachtrag 363); Einbau-Stand C205; Auftrag 364.
Abgeglichen gegen alle Änderungen seit `v0.3.65` (`git log v0.3.65..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.66

Messung 363: Beim Bau mit Innenhof stand nichts — jede flache 2-m-Platte ringsum galt als Gebäude mit Abstand, und der
Umkreis von 12,8 m war schmaler als dieser Plattengürtel. Der Rest verteilte sich über die ganze Anlage.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Umkreis um den Hauptbau ist mindestens 25 m; zuerst freier Boden, dann flache Platten als Standfläche — nie über eine Plattenkante | 150 | gebaut, mit Probe; Messung 364 offen |
| Was dort keinen Platz findet, geht nur zu den drei nächsten Bauten (höchstens ein Drittel); der Rest wird weggelassen, damit die Anlage ruhig bleibt | 150 | gebaut, mit Probe; Messung 364 offen |
| Der Bericht nennt, was den Umkreis versperrt, und zählt Umkreis, nebenan und weggelassen | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 364.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ohne freien Boden kann ein Baum auf einer Nachbarplatte stehen — ob sie Belag oder Grundriss ist, sagt das Modell nicht.
* Es werden oft weniger Stücke gestellt als bestellt — mit Absicht, damit der Rest der Anlage ruhig bleibt.
* Der Innenhof bleibt leer: Er liegt in der Box der Platte und lässt sich nicht von ihr unterscheiden.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
