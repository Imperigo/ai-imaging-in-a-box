# Der Text der Vertiefungsarbeit

Hier steht der **geschriebene Text**, nicht das Material dafür. Das Material liegt eine
Ebene höher in `docs/`: Befunde, Messungen, Entscheide, 29 Sitzungsprotokolle.

> **Berichtigt 29.09.2026 — zwei Angaben dieses Absatzes stimmen nicht mehr.**
> Erstens: Seit dem Owner-Entscheid vom 21.09.2026 schreibt **der Owner** den Text der
> Vertiefungsarbeit. Die Kapitelentwürfe in diesem Ordner sind seither **Material für ihn**,
> nicht sein Text; neue Kapitel werden nicht von sich aus angefangen (`CLAUDE.md`, «Der Owner
> schreibt die Arbeit, Claude schreibt die Unterlagen»). Die Unterlage zum Bauverlauf ist
> `docs/PRODUKT_DIE_SCHRITTE.md`. Zweitens: Am 29.09.2026 liegen **72**
> Sitzungsprotokolle in `docs/sitzungen/`, nicht 29.

## Warum dieser Ordner erst am 19.09.2026 entstanden ist

Bei über 700 Commits stand **keine Zeile Text** der Arbeit. Das war keine technische
Hürde und keine Frage fehlenden Materials — das Gegenteil ist der Fall: Der Plan zum
Schreiben (`docs/STRUKTUR_VERTIEFUNGSARBEIT.md`) führt für jedes Kapitel auf, was es
behauptet, was es trägt und was ihm fehlt.

*Es war nur nie angefangen worden.* Der Ordner ist der Anfang.

## Was hier liegt

> **Nachtrag 29.09.2026:** Alle sechs Entwürfe sind am 29.09.2026 auf den Stand der
> Sitzungen bis 72 nachgezogen worden — **sichtbar**: Was überholt ist, bleibt stehen und
> bekommt daneben einen Vermerk «Nachtrag 29.09.2026» oder «Berichtigt 29.09.2026». Die
> Zeilen unten nennen erst den alten Stand, dann, was der Nachtrag geändert hat.

| Datei | Stand |
|---|---|
| `kapitel-03-die-randbedingungen.md` | **Entwurf, 19.09.2026, nachgezogen 29.09.2026.** Alle Zahlen darin sind **erzeugt, nicht zitiert** — aus `tools/beweis/19_regeln_ausfuehrbar.py`, gefahren für dieses Kapitel und am 29.09.2026 erneut. *Nachtrag:* Registry jetzt 9 Einträge, 3 wählbar; die **Forschungs-Ausnahme** zu Regel 1 (Qwen-Image-2.1) und was sie für die These heisst; Glas mit Durchlass an der Dateigrenze (eigener Lesefehler); **berichtigt:** «0 Treffer» zu Regel 3 prüfte nur Benutzernamen — ein echter Projektname stand damals im Repo. |
| `kapitel-05-die-kamera.md` | **Entwurf, 19.09.2026, nachgezogen 29.09.2026.** Alle Zahlen für das Kapitel **gerechnet**, nicht zitiert — und eine Vorarbeit dabei berichtigt: «unter 2 mm» misst sich über die weitere Spanne als **2,01 mm**. *Nachtrag:* Wandabstand 10 m → 3 m, weil kleine Bauten unter dem Rahmungsriegel blieben (**berichtigt:** «Deckungsgrad exakt erreicht» galt nicht allgemein); Absturz bei Körpern unter Augenhöhe; die Zwillingserkennung, die im Betrieb nie griff; Innenansicht über die Mappe am Gerät belegt. |
| `kapitel-04-die-kette.md` | **Entwurf, 19.09.2026, nachgezogen 21.09. und 29.09.2026.** Alle Zeitangaben für das Kapitel **gemessen** (Beweis 05 und 23, beide gefahren). **Der Kapitelname der Gliederung ist überholt:** Dort heisst es «vier Knoten» — seit dem 19.09.2026 sind es sechs. *Nachtrag:* erster echter Lauf über die Mappe (22.09., 17,6 s, Bild zu Recht abgewiesen); Speicher in der Mappe erst aus, dann ohne Codestand; Vorgabemodell `z-image-turbo` auch für Bestellungen ohne Modellangabe; `qwen-image-2512` stillgelegt, an der Tiefen-Naht bleibt **ein** freies Modell; Forschungs-Ausnahme Qwen-Image-2.1 ohne ControlNet; Ebenen Schritt 1. **Berichtigt:** Die dritte Grenze ist gemessen — das Eingangsbild kommt am Vorgabe-Modell nicht an. |
| `kapitel-08-der-einbau.md` | **Entwurf, 19.09.2026, nachgezogen 29.09.2026.** Alle Zahlen **erzeugt**, nicht zitiert — `python tools/einbau.py --json`, gefahren für das Kapitel und am 29.09.2026 erneut. **Zwei Angaben der Vorarbeit berichtigt:** Der Satz «seit acht Tagen hat keiner der drei Worker geantwortet» stimmt nicht mehr (einer hat), und für die beiden anderen sind daraus elf Tage geworden. *Nachtrag:* 23 von 60 Posten nicht in der Software (16 davon gebaut, am Gerät unbestätigt), aber nur noch 6 Aufträge ohne Antwort; die Antwort auf B161, die **fünf Tage** nur bei uns lag, während KosmoOrbit v0.1.5 ohne das erste echte Bild schnitt; die direkte Zustellung in ihren Eingang und die sechs Antworten desselben Tages; E8, das nie als Auftrag abging. |
| `kapitel-06-das-messen.md` | **Nachgezogen 29.09.2026:** Widerspruch 0,93 gegen 0,36 aufgelöst — es ist der Bildanteil, nicht der Messweg (dabei eine Verwechslung in der Auflösung nachgewiesen: die Szene *Gebäude* vom 09.09. ist der Hochbau mit grosser Platte); das Paarurteil im Betrieb ruht auf ρ allein, zweites Bein abgeschaltet, Schwelle 0,80 **nicht kalibriert**; saubere Bilder «nicht messbar», die Ordnung an Tiefensprüngen trennte nicht und ist entfernt; die Tore laufen im Betrieb ohne Gegenprobe. **Entwurf, 21.09.2026.** *Geltungsbereich nachgezogen:* Die Zahlen sind unverändert, sie bedienen aber seit E23 **eine von zwei Betriebsarten**. Neu 6.8 — die zweite Frage («was ist hinzugekommen, und wo?») samt den drei Gründen, warum sie heute unbeantwortbar ist. **Entwurf, 19.09.2026.** Das tragende Kapitel. Alle Zahlen am 19.09.2026 **neu gerechnet**. Die Strukturnotiz dazu ist überholt — ihre Kernbehauptung (ein zusammengesetzter Wert) wurde am 18.09.2026 widerlegt; das Kapitel ist um das neue Ergebnis herum geschrieben. |
| `kapitel-07-die-methode.md` | **Entwurf, 19.09.2026, nachgezogen 29.09.2026.** Erstes geschriebenes Kapitel. *Nachtrag:* die dritte Antwort stand drüben im Vertrag, aber nicht in der Anzeige (7.2); **berichtigt:** der «Fehlalarm» aus 7.5 war keiner (Befund 21.09.); neue Fälle zu 7.4 und 7.6. |

**Anhang B, seit dem 22.09.2026:** `docs/SOFTWARE_VON_GRUND_AUF.md` — *Wie man eine
Software von Grund auf baut.* Die Grundkonzepte dieses Projekts für Leser:innen ohne
Informatikhintergrund. Es liegt als Unterlage in `docs/`, nicht hier: Den Text der Arbeit
schreibt der Owner.

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

*Nachtrag 29.09.2026:* Diese Reihenfolge ist seit dem 21.09.2026 eine Reihenfolge **für
den Owner**. Die noch fehlenden Kapitel werden in diesem Ordner nicht von sich aus
angefangen; die bestehenden werden als Material nachgeführt.

## Drei Regeln für diesen Ordner

*Berichtigt 29.09.2026: Es sind vier — die Liste unten hatte von Anfang an vier Punkte unter
der Überschrift «drei».*

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
