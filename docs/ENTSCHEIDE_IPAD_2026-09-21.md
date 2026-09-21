# Entscheide zur iPad-Oberfläche — 21.09.2026

**Grundlage:** keine — hier steht kein Messwert, sondern was der Owner entschieden hat
**Codestand:** `3ffbffd`

Zwanzig Fragen zum Entwurf, vom Owner am 21.09.2026 beantwortet. Diese Liste ist die
Grundlage für den Bau; was hier steht, wird nicht neu verhandelt.

Der Entwurf selbst liegt als Entwurfsfläche ausserhalb des Repos (elf Blätter). Diese
Datei ist die Fassung, die bleibt — *was nicht in einer Datei steht, ist weg.*

---

## Der Stift

| # | Frage | Entschieden |
|---|---|---|
| 1 | Querformat oder Hochformat | **Beide gleichwertig.** Eigene Anordnung je Haltung, gleicher Inhalt |
| 2 | Doppeltipp am Stift | **Radierer** |
| 3 | Was der Druck steuert | **Strichbreite** |
| 4 | Wer zeichnen darf | **Nur der Stift.** Der Finger schiebt und zoomt |
| 5 | Radierer | **Beides, umschaltbar** — ganze Striche und flächig |
| 6 | Tiefe von «Zurück» | **Die letzten 20 Schritte.** Fester Deckel |
| 7 | Ebenen | **Mehrere, frei anlegbar.** Jede Ebene ist eine Variante |
| 8 | Bedeutung der Stiftfarbe | **Keine.** Frei wählbar |

**Was Nummer 7 nach sich zieht, und es ist keine Kleinigkeit:** Wenn eine Ebene eine
Variante ist, muss entschieden sein, *was gerechnet wird.* Festgelegt: **gerechnet wird,
was sichtbar ist.** Eine ausgeblendete Ebene geht nicht mit. Sonst rechnet das Gerät etwas
anderes, als auf dem Schirm steht — und das ist derselbe Fehler wie ein erfundener
Fortschrittsbalken, nur eine Etage tiefer.

## Leiste und Bildschirm

| # | Frage | Entschieden |
|---|---|---|
| 9 | Wo die Werkzeugleiste sitzt | **Umlegbar per Knopf**, links oder rechts |
| 10 | Vollbild | **Ja, mit einem Wisch von unten** |

## Das Rechnen

| # | Frage | Entschieden |
|---|---|---|
| 11 | Nach «In die Mappe legen» | **Bleibt offen liegen.** Nichts rechnet von selbst |
| 12 | HomeStation nicht erreichbar | **Lokal parken**, später von selbst nachschicken |
| 13 | Rechnet das iPad selbst | **Nie.** Ein Ort, ein Ergebnis, vergleichbar |
| 14 | Abbruch eines Laufs | **Fertiges bleibt in der Mappe** und wird nicht neu gerechnet |

## Das Urteil

| # | Frage | Entschieden |
|---|---|---|
| 15 | Prüfen oder Entwerfen | **Schalter am Bild**, jederzeit umlegbar |
| 16 | Was das Abzeichen trägt | **Farbe, Wort und Zahl** — immer, auch beim Teilen |
| 17 | Vorher und Nachher | **Beides umschaltbar**: nebeneinander und Wischregler |

## Die Mappe

| # | Frage | Entschieden |
|---|---|---|
| 18 | Varianten nebeneinander | **Drei** |
| 19 | Benennung | **Nach der Zeit**, ein eigener Name nachträglich möglich |
| 20 | Was beim Teilen mitgeht | **Bild mit Prüfzeichen** |

**Was Nummer 20 entscheidet, ohne gefragt worden zu sein:** Wenn das Prüfzeichen in das
geteilte Bild hineingerechnet wird, muss die Schrift dafür **auf dem Gerät** liegen. Eine
Schrift von einem fremden Server ist eine Netzverbindung, und die Auflage dieses Projekts
lautet, dass zum Start keine nötig sein darf. Also: **Schriften werden mitgeliefert, nicht
geladen.** Damit bleibt auch die zweite Schriftfrage beantwortet — eigene Schriften sind
zulässig, solange sie im Paket stecken und permissiv lizenziert sind.

---

## Die Verbindung zwischen iPad und Rechner

**Owner-Wunsch vom 21.09.2026:** Die beiden Geräte sollen als *ein* zusammenhängendes
Werkzeug wirken — das Senden einer fertigen Skizze soll als Bewegung beginnen und auf dem
Rechner weitergehen.

**Der Gedanke, auf den es hinausläuft:** Ein Gegenstand, ein Weg. Die Skizze verschwindet
auf dem iPad nicht und taucht drüben auf, sondern **reist**: Sie schrumpft auf eine Marke
zusammen, wandert an den Rand, auf dem der Rechner liegt, fliegt auf einem Faden hinüber
und legt sich dort als **dieselbe Marke** oben in die Warteschlange — gleiche Farbe,
gleiche Form, gleiche Grösse. Kommt das Bild zurück, nimmt es denselben Faden und legt
sich genau an die Stelle, von der die Skizze kam.

**Vier Regeln, und alle vier sind Anwendungen der bestehenden Lehre auf die Bewegung:**

1. **Bewegt sich etwas, ist etwas unterwegs.** Eine Animation, die weiterläuft, während
   nichts passiert, ist eine Lüge mit Zeitverlauf — dasselbe wie ein erfundener Balken.
2. **Gleichmässig heisst gezählt.** Der Flug läuft nur dort gleichmässig, wo Bytes
   gezählt werden. Wo nur gewartet wird, atmet die Marke an Ort und Stelle.
3. **Die Animation endet nicht vor der Ankunft.** Sie hält kurz vor dem Ziel und rastet
   erst ein, wenn die Gegenseite bestätigt hat. *Eine Animation, die vor der Ankunft
   endet, behauptet eine Ankunft.*
4. **Ein Gegenstand, ein Weg.** Was abhebt und was landet, ist dieselbe Marke — nie zwei
   Dinge, die sich ähnlich sehen.

**Und der Abbruchfall gehört dazu:** Bricht die Verbindung, hört die Bewegung auf der
Stelle auf und die Marke **fällt zurück aufs iPad**. Sie verschwindet nie in der Mitte.

**Zeiten:** Ablegen 220 ms, Abheben 180 ms, Flug so lange wie die Übertragung wirklich
dauert, Einrasten 140 ms nach der Bestätigung, Warten als Atmen mit 1.8 s.

**Bewegungsreduktion:** Wer am Gerät Bewegung abgestellt hat, bekommt denselben Weg ohne
Bewegung — die Marke erscheint am Ziel, der Balken bleibt. *Eine Aussage, die nur in der
Bewegung steckt, ist für diese Leute keine Aussage.*

---

## Was daraus noch nicht entschieden ist

* **Wie die Geräte sich finden.** Heimnetz mit Kennwort ist entschieden (E25); wie das
  iPad die HomeStation erstmals entdeckt, ist es nicht.
* **Was bei zwei iPads passiert.** Die Mappe kennt heute keinen zweiten Schreiber.
* **Wie gross eine Skizze werden darf**, bevor das Senden spürbar wird. Ohne Messung am
  Gerät ist das eine Vermutung — also ein unverschickter Auftrag und keine offene Frage.
