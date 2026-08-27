#!/usr/bin/env bash
# EIN DURCHGANG DES HOMEWORKERS — holen, rechnen, zurueckgeben.
#
# WOZU. Bis zum 26.08.2026 war der Ritus von Hand: `git pull`, `homeworker.py --alle`,
# dann `git add auftraege/ergebnisse && git commit && git push`. Drei Schritte, die
# jemand tippen musste — und solange niemand tippte, lagen Auftraege beliebig lange.
# Am 26.08. waren es siebzehn, der aelteste drei Tage.
#
# Der Abholer hat seinen Takt seit dem 22.08. (`kosmo-abholer.timer`); der Homeworker
# hatte keinen. Das ist der Unterschied zwischen "beauftragt" und "wird auch gemacht".
#
# WAS ER NICHT TUT. Er entscheidet nichts. Die GPU-Schranke sitzt im Homeworker selbst
# (fail-closed, `darf_starten`), der Deckel je Durchgang steht unten als Zahl, und ein
# Auftrag, der nicht laufen darf, bekommt ein Ergebnis mit `abgelehnt` statt zu warten.
#
# VOR DEM INSTALLIEREN: `<nutzer>` in der .service-Datei ersetzen. Hier steht kein Pfad —
# das Arbeitsverzeichnis setzt systemd (Regel 3).
set -euo pipefail

HOECHSTENS="${1:-1}"

# --ff-only, nicht `pull`: Ein Merge in einem Dienst, den niemand beaufsichtigt, ist der
# Anfang eines Konflikts, den niemand aufloest. Laesst sich nicht vorspulen, bricht der
# Durchgang ab und der naechste Takt versucht es wieder — sichtbar im Journal.
git pull --ff-only

# Der Rueckgabewert des Homeworkers sagt, ob GERECHNET wurde, nicht ob BESTANDEN wurde.
# Ein durchgefallenes Bild ist ein gelungener Auftrag mit klarem Befund; `|| true` waere
# hier trotzdem falsch, denn ein Absturz soll im Journal stehen.
python3 tools/homeworker.py --alle --hoechstens "$HOECHSTENS"

# Nur committen, wenn wirklich etwas dasteht. Ein leerer Commit je Takt fuellt die
# Historie mit Nichts und macht die echten unauffindbar.
git add auftraege/ergebnisse
if ! git diff --cached --quiet; then
    git commit -m "Ergebnisse der HomeStation (automatischer Durchgang)"
    git push
fi
