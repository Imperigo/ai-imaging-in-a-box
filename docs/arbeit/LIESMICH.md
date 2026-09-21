# Der Text der Vertiefungsarbeit

Hier steht der **geschriebene Text**, nicht das Material dafür. Das Material liegt eine
Ebene höher in `docs/`: Befunde, Messungen, Entscheide, 29 Sitzungsprotokolle.

## Warum dieser Ordner erst am 19.09.2026 entstanden ist

Bei über 700 Commits stand **keine Zeile Text** der Arbeit. Das war keine technische
Hürde und keine Frage fehlenden Materials — das Gegenteil ist der Fall: Der Plan zum
Schreiben (`docs/STRUKTUR_VERTIEFUNGSARBEIT.md`) führt für jedes Kapitel auf, was es
behauptet, was es trägt und was ihm fehlt.

*Es war nur nie angefangen worden.* Der Ordner ist der Anfang.

## Was hier liegt

| Datei | Stand |
|---|---|
| `kapitel-03-die-randbedingungen.md` | **Entwurf, 19.09.2026.** Alle Zahlen darin sind **erzeugt, nicht zitiert** — aus `tools/beweis/19_regeln_ausfuehrbar.py`, gefahren für dieses Kapitel. |
| `kapitel-05-die-kamera.md` | **Entwurf, 19.09.2026.** Alle Zahlen für das Kapitel **gerechnet**, nicht zitiert — und eine Vorarbeit dabei berichtigt: «unter 2 mm» misst sich über die weitere Spanne als **2,01 mm**. |
| `kapitel-04-die-kette.md` | **Entwurf, 19.09.2026.** Alle Zeitangaben für das Kapitel **gemessen** (Beweis 05 und 23, beide gefahren). **Der Kapitelname der Gliederung ist überholt:** Dort heisst es «vier Knoten» — seit dem 19.09.2026 sind es sechs. |
| `kapitel-08-der-einbau.md` | **Entwurf, 19.09.2026.** Alle Zahlen **erzeugt**, nicht zitiert — `python tools/einbau.py --json`, gefahren für das Kapitel. **Zwei Angaben der Vorarbeit berichtigt:** Der Satz «seit acht Tagen hat keiner der drei Worker geantwortet» stimmt nicht mehr (einer hat), und für die beiden anderen sind daraus elf Tage geworden. |
| `kapitel-06-das-messen.md` | **Entwurf, 21.09.2026.** *Geltungsbereich nachgezogen:* Die Zahlen sind unverändert, sie bedienen aber seit E23 **eine von zwei Betriebsarten**. Neu 6.8 — die zweite Frage («was ist hinzugekommen, und wo?») samt den drei Gründen, warum sie heute unbeantwortbar ist. **Entwurf, 19.09.2026.** Das tragende Kapitel. Alle Zahlen am 19.09.2026 **neu gerechnet**. Die Strukturnotiz dazu ist überholt — ihre Kernbehauptung (ein zusammengesetzter Wert) wurde am 18.09.2026 widerlegt; das Kapitel ist um das neue Ergebnis herum geschrieben. |
| `kapitel-07-die-methode.md` | **Entwurf, 19.09.2026.** Erstes geschriebenes Kapitel. |

## Die Reihenfolge, in der geschrieben wird

Sie steht in `docs/STRUKTUR_VERTIEFUNGSARBEIT.md` und ist begründet. Kapitel 7 steht an
dritter Stelle der dortigen Liste — es ist belegt, es steht nicht unter Vorbehalt, und es
ist das Kapitel, das diese Arbeit von einem Softwareprojekt unterscheidet.

**Kapitel 6 ist als viertes geschrieben, obwohl es das erste der Liste ist.** Der Grund
steht in ihm selbst: Seine Kernbehauptung hat bis zum 18.09.2026 nicht gehalten. Wer es
früher geschrieben hätte, hätte es zweimal schreiben müssen — *ein Kapitel, dessen
Ergebnis noch in Bewegung ist, wird nicht besser davon, dass man es früh aufschreibt.*

**Kapitel 9 zuletzt.** Es kann sich noch ändern: Wenn eine der offenen Messungen anders
ausgeht als erwartet, ändert sich der Ton der ganzen Arbeit.

## Drei Regeln für diesen Ordner

1. **Jede Zahl ist im Repo belegt** und mit Datum auffindbar. Am Fuss jedes Kapitels steht
   eine Tabelle mit den Belegstellen.
2. **Jede Zahl trägt ihre Kennzahl und ihre Bedingung.** Der Entwurf von Kapitel 7 hat
   diesen Fehler beim ersten Schreiben selbst gemacht — zwei verschiedene Kennzahlen in
   einer Tabellenspalte — und er steht dort jetzt als Beispiel.
3. **Was nicht gemessen ist, steht als nicht gemessen da.** Nicht als Vorbehalt in einer
   Fussnote, sondern in demselben Satz wie das Ergebnis.
4. **Jedes Kapitel schliesst mit seinen eigenen Grenzen** — und zwar mit denen, die weh
   tun. Kapitel 7 sagt, dass die Regeln Fehler nicht verhindert, sondern nur auffindbar
   gemacht haben. Kapitel 3 sagt, dass seine These nicht widerlegbar formuliert ist.
   *Ein Kapitel, dessen Grenzen niemandem unangenehm sind, hat seine Grenzen nicht
   gesucht.*
