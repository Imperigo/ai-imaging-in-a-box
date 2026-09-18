<!--
Danke, dass Sie hier Zeit investieren.

Diese Vorlage ist länger als die üblichen. Der Grund steht in CONTRIBUTING.md: Es gibt
in diesem Repo heute KEINE automatische Prüfung. Was Sie nicht selbst laufen lassen,
hat niemand laufen lassen — die Vorlage ist also kein Formular, sondern die Prüfung.

Nichtzutreffendes NICHT löschen, sondern ankreuzen lassen und mit einer Zeile begründen.
Ein leeres Kästchen mit Grund ist eine Auskunft; ein gelöschter Punkt ist keine.

Die Kästchen stehen ABSICHTLICH ausserhalb dieser Kommentare: Was in einem
HTML-Kommentar steht, zeigt GitHub niemandem an. Eine Prüfliste, die die Prüfenden nicht
sehen, ist genau der Wächter, der nichts bewacht — der Fehler, den dieses Projekt schon
mehrfach bezahlt hat. Erläuterungen dürfen im Kommentar stehen, Antworten nicht.

Alles auf Deutsch, Schweizer Schreibung ("ss", kein Eszett).
-->

## Warum

<!--
Das WARUM, nicht das WAS. Was geändert wurde, steht im Diff; warum es geändert wurde,
steht nirgends sonst. Dasselbe gilt für die Commit-Nachrichten.

Falls es ein Issue dazu gibt: Nummer hier.
-->

## Was jetzt anders ist

<!-- Kurz, aus Sicht von jemandem, der die Software benutzt statt sie zu lesen. -->

## Gemessen oder gesetzt?

<!--
Falls Ihre Änderung eine Zahl enthält — eine Schwelle, eine Zeitgrenze, einen Faktor:

  GEMESSEN  Sie haben sie aus Läufen bestimmt. Wie viele Läufe, welche Fälle, welches
            Ergebnis? Bitte hierher.
  GESETZT   Sie haben sie festgelegt, weil eine Zahl gebraucht wurde. Auch das ist in
            Ordnung — aber es muss im Code danebenstehen.

Eine Zahl ohne diese Angabe wird beim Lesen zwangsläufig für einen Befund gehalten.
-->

- [ ] Meine Änderung enthält keine Zahl dieser Art.
- [ ] Sie enthält eine, und hier steht, ob sie GEMESSEN oder GESETZT ist:

      Zahl:           <welche, in welcher Datei>
      GEMESSEN/GESETZT: <welches von beiden>
      Woraus:         <wie viele Läufe, welche Fälle, welches Ergebnis>

## Die Mutationsprobe

<!--
PFLICHT, sobald Ihre Änderung irgendetwas prüft, sperrt oder bewacht.

Ein bestandener Test ist kein Beleg dafür, dass er etwas geprüft hat. Also:

  1. Den Wächter entschärfen (Schwelle verstellen, Bedingung umdrehen, Zeile
     auskommentieren).
  2. `python3 -m pytest` laufen lassen.
  3. Nachsehen, dass der erwartete Test WIRKLICH rot wird.
  4. Zurücksetzen.

Eintragen ist das ERGEBNIS, nicht die Absicht. Ein Wächter, der nicht fällt, bewacht
nichts. Das merkt man erst, wenn man ihn umstösst — und wenn es niemand tut, merkt man
es nie.
-->

- [ ] Mutationsprobe ausgeführt. Ergebnis:

      Entschärft:    <was genau, in welcher Zeile>
      Rot geworden:  <Name des Tests>
      Meldung:       <die Zeile, mit der er fiel>
      Zurückgesetzt: ja

- [ ] Nicht nötig, weil hier nichts geprüft oder gesperrt wird. Grund:
      <ein Satz>

## Prüfungen

- [ ] `python3 -m pytest` läuft durch. Ergebniszeile:

      <die Zeile aus Ihrem Lauf, z. B. "… passed in … s">

- [ ] Die Sammlung läuft weiterhin OHNE GPU und ohne Modellgewichte.
- [ ] Kein Test braucht das Netz.
- [ ] Neue Tests kamen dazu → die Testzahl im README stimmt wieder.

<!--
Zur letzten Zeile: Ein Wächter (tests/test_readme.py) vergleicht die im README genannte
Zahl mit der wirklich gesammelten. Wer sie nicht nachzieht, hinterlässt einen roten Lauf,
der nach seinem Fehler aussieht. Sind keine Tests dazugekommen, kreuzen Sie die Zeile
trotzdem an und schreiben "keine neuen Tests" daneben.
-->

## Die vier Regeln

<!--
Sie stehen in CLAUDE.md und in CONTRIBUTING.md. Jede hat einen Wächter in der
Testsammlung — dieser Abschnitt ersetzt ihn nicht, er macht die Antwort sichtbar.
-->

- [ ] **Regel 1** — Keine neue Abhängigkeit. ODER: eine neue, und hier steht Name,
      Fassung, Lizenz und wo ich die Lizenz nachgelesen habe (Primärquelle):

      <Name, Fassung, Lizenz, Quelle>

<!--
Kein GPL, kein AGPL — auch nicht als optionaler Zusatz. Bei einem Binärpaket gilt auch,
was statisch mitgelinkt ist. Bei Modellgewichten ist Non-Commercial ausgeschlossen, und
ein LoRA erbt die Lizenz seines Grundmodells. Ein GPL-Fund wird ausdrücklich gemeldet,
nicht stillschweigend umgangen.
-->

- [ ] **Regel 2** — Kein `import bpy`, kein bpy-Wheel, keine Add-on-Verpackung. Blender
      wird ausschliesslich als Subprozess aufgerufen.
- [ ] **Regel 3** — Keine echten Projektdaten, keine Büro-, Kunden- oder Projektnamen.
      Kein absoluter Pfad mit einem Benutzernamen — auch nicht in einem eingefügten
      Fehlertext, und die bringen ihn am häufigsten mit.
- [ ] **Regel 4** — Alles Neue ist aus Python heraus nutzbar, ohne dass eine Oberfläche
      läuft. Kein Oberflächen-Import im Kern.

## Sprache und Form

- [ ] Kommentare, Docstrings, Testnamen und Fehlermeldungen sind auf Deutsch.
- [ ] Durchgehend "ss", nirgends ein Eszett.
- [ ] Bezeichner sind ASCII ohne Umlaute; Fliesstext hat richtige Umlaute.
- [ ] Ich habe KEINE Wortersetzung über eine ganze Datei laufen lassen — sie trifft
      Bezeichner, und der Schaden verteilt sich danach über die ganze Datei.
- [ ] Kommentare tragen das Warum, nicht das Was.
- [ ] Die dritte Antwort ist gewahrt: `None` heisst NICHT GEMESSEN — nie "in Ordnung",
      nie 0, nie False.
- [ ] Fail-closed: Ungeprüftes geht nicht durch, aber "nicht gemessen" und
      "durchgefallen" bleiben im Ergebnis unterscheidbar.
- [ ] Neue Fachbegriffe stehen in `docs/LEXIKON.md` — für Laien erklärt, ohne einen
      anderen unerklärten Fachbegriff vorauszusetzen.
- [ ] Ein Thema in diesem Pull Request, keine nebenbei mitgelaufene
      Formatierungsänderung.

## Was ich NICHT geprüft habe

<!--
Bitte ausfüllen, auch wenn es unangenehm ist. Eine benannte Lücke ist besser als eine,
die nach Vollständigkeit aussieht — und sie kostet die Prüfenden viel weniger Zeit als
die Suche nach ihr.

Typisch: alles, was eine GPU, echte Modellgewichte, ein Blender einer bestimmten
Fassung oder eine andere Plattform braucht.
-->

## Lizenz

<!--
Es gibt keinen CLA. Mit dem Einreichen stellen Sie den Beitrag unter die Apache-2.0
dieses Projekts (Abschnitt 5 der Lizenz), sofern Sie hier nichts anderes hinschreiben.
-->

- [ ] Ich habe die Rechte an allem, was in diesem Pull Request steht.
