# Aufträge **von** der HomeStation an den KosmoVis-Worker

Die Gegenrichtung zu `auftraege/offen/`. Dort liegen eure Aufträge an mich; hier liegen
meine an euch.

**Warum es diesen Ordner gibt (Owner, 21.08.2026):** *«bei aufgaben aufgeben, immer beim
jeweiligen worker antrag stellen und als auftrag markieren über repo mit prompt anleitung
etc. damit ich hier keine prompt hin und her kopieren muss.»*

Ein Befund gehört nach `docs/` und erklärt. Ein Auftrag gehört hierher und **verlangt**.

## Aufbau

```
auftraege/von-homestation/
  auf-vis-<datum>-<nr>.md      ← der Auftrag, mit fertigem Prompt zuoberst
```

**Zuoberst steht immer ein Block zum Kopieren**, den der Owner unverändert weitergeben
kann — genau wie in eurem `auftraege/README.md` verlangt. Darunter die Belege: gemessene
Zahlen, Dateinamen, Reproduktionsweg.

**Regel 3 gilt auch hier:** Zahlen, Urteile, Dateinamen — keine Bilder, keine Gewichte,
keine absoluten Pfade mit Benutzernamen.

Erledigt heisst: Der Auftrag verweist auf den Commit, der ihn schliesst.
