# Visbox 0.3.55 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.55 auf `main` (Folgen aus dem Demotest am Mac und iPad mit 0.3.54); Vorgänger 0.3.54 = Tag `v0.3.54`

**Grundlage:** Demotest 24.10. (Mac, echtes iPad, Simulator); Protokoll 74 §277–§280; Einbau-Stand C195–C199;
Entscheide 99, 128, 144, 145. Abgeglichen gegen alle Änderungen seit `v0.3.54` (`git log v0.3.54..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.55

Jedes Mac-Update trennte still alle iPads, «Mac in der Nähe» brach ab, bevor der Mac zustimmen konnte, im Adressfeld
stand eine fremde Adresse, und «Bild aus Skizze» sagte bei einer Skizze am Mac «nicht in der Mappe».

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Nach einem Update meldet der Mac klar «iPads einmal neu koppeln» und legt höchstens einen neuen Ausweis an; «Erlauben» bei der Passwortfrage hält die Kopplung | 128, 144 | gebaut, mit Probe; am Gerät offen |
| «Mac in der Nähe» wartet auf den Klick am Mac: Die Verbindung steht sofort, der Schein geht erst nach «Koppeln» | 99 | gebaut, mit Probe; am Gerät offen |
| Keine fremde Adresse im Adressfeld; eine alte Adresse steht nur als Hinweis «vielleicht veraltet» | — | gebaut, mit Probe; am Gerät offen |
| «Bild aus Skizze» sagt bei einer Skizze am Mac, dass sie nur am Mac liegt, und nennt den Umweg | 129 | gebaut, mit Probe |
| Knotenansicht: Einzahl bei eins («1 Bild»), Stand wie das Partnerprogramm | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac und iPad:** beide aktualisieren, dann **einmal neu koppeln**. Danach am Demotag den Mac nicht mehr
  aktualisieren (Entscheid 144). Die alten Schlüsselbund-Einträge «Visbox Mac …» löschst du nach
  `docs/MAC_UNTERSCHRIFT_EINRICHTEN.md`.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ohne feste Unterschrift fragt der Mac nach jedem Update nach dem Passwort; ohne «Erlauben» müssen die iPads neu koppeln.
* Eine Skizze aus einer Mappe am Mac reist beim Bestellen noch nicht zum Heim-PC.
* Ein neues iPad gegen einen Mac 0.3.54 koppelt über «Mac in der Nähe» nicht — beide müssen auf 0.3.55.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
