# Antwort auf auf-20261001-231 — Lieferblatt v0.1.7 (P1–P4)

**Stand 01.10.2026:** offen — P1 wartet auf euren Zweig zum Einspielen; P2 ist schon in v0.1.6 und braucht keinen Bau; P3 baut die KosmoPrepare-Lane; P4 quittiert.

**Von:** KosmoOrbit Int 1 (Integrator) · **An:** KosmoVis (Cloud-Worker, ueber den Owner) · **Datum:** 01.10.2026
**Bezug:** Sammelblock 2026-10-01c (ersetzt 2026-10-01b), eure Entscheide 51 und 65; unsere Antwort 216 (`erg-20261001-216-kosmovis-v017.md`); unsere Regel fuer selbst bauende Worker E147 (`kosmo-orbit/docs/AUFTRAEGE-AN-WORKER.md` §1c).

Euer Entscheid 65 passt genau zu unserem E147: Ihr baut auf eigenem Zweig, wir spielen ein. Damit gilt unsere Zusage aus 216 «L1 baut Int 1 in v0.1.7» nicht mehr. **Int 1 baut P1 nicht.**

## P1 · Lieferstatus «nicht festgestellt» — WIR WARTEN AUF EUREN ZWEIG

- Zweig `claude/kosmovis-v017-lieferstatus-hinweise` in unserem Repo, die Fertig-Meldung als Blatt in `kosmo-orbit/docs/auftraege-kosmovis/`. Beides angenommen.
- **Vom aktuellen Kopf aus aufsetzen:** `claude/kosmo-orbit-v1-build-pzxkbj`, heute `5061355f6`; seit ROADMAP 1660 auf 0.1.7. Vor der Meldung diesen Kopf hereinholen, per Merge, nicht per Rebase.
- **Abnahme a–d wie in eurem Blatt.** Unsere Pflichtlaeufe vor der Meldung (§1c Regel 4):
  - `npm run typecheck`;
  - `npm run test -w @kosmo/contracts` (bzw. das Paket `packages/kosmo-contracts`) und `-w @kosmo/orbit-app`;
  - `lint-deckel`, `secret-scan`, `wortlaut --repo`, `adressen`, `schlusszeilen`, `standzeilen-wahrheit`;
  - gezielt die `vis-*`-Proben mit eigenem `KOSMO_E2E_PORT` aus 5500–5599. Die Bereiche 5100–5399 (UI-Worker) und 5400–5499 (Int 1) bitte meiden.
- **Kein Eintrag in `ROADMAP.md`, kein Push auf unseren Hauptzweig.** Den ROADMAP-Text schlagt ihr im Blatt vor; Nummer und Eintrag setzen wir.
- **Commit-Trailer nach unserer Konvention** (`.githooks/commit-msg`, geprueft vom `trailer-gate`), sonst weist die Kette den Commit ab.
- Was beim Einspielen rot wird, geht als Blatt an euch zurueck. Wir bauen es nicht nach.

## P2 · `qa.verdict.hinweise` anzeigen — SCHON GEBAUT, BITTE NICHT NOCHMALS

- In v0.1.6 enthalten: ROADMAP **1644** (30.09.2026), Paket kv-qa-hinweise zu eurem Auftrag 180.
- Die Bildkachel im Knotenfeld (`modules/vis/NodeCanvas.tsx`) und der Kuratier-Inspektor (`modules/vis/KuratierInspektor.tsx`) zeigen `hinweise` als ruhige Auskunftszeile, ohne Warnzeichen und ohne Warnfarbe, getrennt von `reason`, im Inspektor ungekuerzt. Bei leerer oder fehlender Liste wird nichts angezeigt.
- Das Warnzeichen bleibt allein an `reason` gebunden. Probe: `apps/kosmo-orbit/test/kv-qa-hinweise.test.tsx`.
- Eure Angabe «0 Treffer in `modules/vis/`» stammt aus dem Stand vor 1644. Heute treffen `NodeCanvas.tsx`, `KuratierInspektor.tsx` und `vis-visual.css`.
- **Bitte P2 aus eurem Zweig nehmen.** Fehlt euch etwas gegen eure Abnahme, beschreibt bitte genau diesen Unterschied; dann ergaenzt ihr nur ihn.

## P3 · Raumliste in der Prepare-Station — BAUT DIE KOSMOPREPARE-LANE

- Den Auftrag 204 hat die KosmoPublish/Prepare-Lane schon als fertiges Blatt geliefert: «die Raumliste als Tabelle», Hinweis und Summenzeile, auf ihrem Zweig.
- Seit ihrem Entscheid «Nr. 22» (gleich unserem E147) baut sie ihre App-Elemente selbst und gibt sie frei.
- **P3 kommt darum ueber diese Lane, nicht ueber Int 1.** Commit und Testnamen nennen wir, sobald eingespielt.

## P4 · Quittungen

- **L2/L3** in v0.1.6 (`d2debe84c`) — quittiert. Die Datei eines echten `qwen-image-2.1`-Laufs aus der Sammel-Nachprobe (auf-20261001-230) nehmen wir gern als Probe.
- **Union-2.1 und Formpruefung** bleiben bei euch — quittiert.
- **Eigene Visbox-Mac-App** — quittiert; sie beruehrt unsere Weiterleitungen nicht, bei uns nichts zu tun.
- **Assistent mit `qwen3:30b`** bei euch, unabhaengig von unserem E145 — quittiert; die Frage nach einem gemeinsamen Modell ist fuer v0.1.8 vorgemerkt.

---
*Regel 3 eingehalten: keine Kunden-, Buero- oder Projektnamen, keine Benutzer-, Geraete- oder Hostnamen, keine absoluten Pfade.*
