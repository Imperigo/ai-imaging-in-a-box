import { lazy, Suspense, useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import {
  augeImModell,
  exportGlb,
  fovAusBrennweiteGrad,
  kameraArtAusParams,
  kameraAutoAusParams,
  kameraManuellAusParams,
  KAMERA_AUTO_VORGABEN,
  KAMERA_RICHTUNGEN,
  projektKameras,
  schreibeListe,
  type KameraArt,
  type KameraAutoWahl,
  type KameraManuell,
  type KosmoDoc,
  type VisNode,
} from '@kosmo/kernel';
import { KButton, KCheckbox, KNumberField, KSelect, KTabs, KTooltip, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { interiorFaehrt, istUeberDiesenWegBestellbar, grundlagenNachfuehren, szeneBauteileAnzahl } from './vis-jobs';
import { abonniereHeimStandpunkte, hatStandpunkteAbfrage, heimStandpunkte, heimStandpunkteFassung, standpunkteFuer, wahlSchluessel, type HeimStandpunkt } from './heim-standpunkte';
import { modellLadenWirt, modellLadeStand } from './modell-laden';
import { modellStand } from './ModellKnoten';
import type { Blickvorschau, VorschauKamera } from './modell-vorschau-3d-kern';
import './knoten-neu.css';

const ModellVorschau3d = lazy(() => import('./modell-vorschau-3d').then((m) => ({ default: m.ModellVorschau3d })));

/*
 * Bauplan «Neue Knoten» F2 (Blatt 31, Entscheide 109 B/C und 113 (3)/(5)): der Körper des Knotens
 * «Kamera».
 *
 *  - **Auto** (Vorgabe): der Heim-PC rechnet die Standpunkte aus Richtungen, Augenhöhe, Brennweite,
 *    Abstand und Perspektive — eine Rechnung für beide Programme. Bestellt wird `cameras: 'auto'` mit
 *    `cameras_auto`. Die Kegel im kleinen 3D-Fenster und der Blick darunter kommen aus derselben
 *    Rechnung (Wirt-Abfrage, `heim-standpunkte.ts`), live bei jeder Änderung.
 *  - **Manuell**: «Manuell übernehmen» friert die Auto-Standpunkte ein; dann Werte tippen (Auge und
 *    Blickpunkt in Metern, Ost/Nord/Höhe). Bestellt wird die Liste, mit `perspektive`.
 *  - **Modell** (nur, wo es Standpunkte aus dem Entwurf gibt, KosmoOrbit): wie bisher — Eingang,
 *    Übersicht, bei Räumen Innenraum. Alte Graphen ohne `art` stehen hier; nichts ändert sich, bis man
 *    umschaltet.
 *
 * Feste Höhe (`KAMERA_KOERPER_H`), damit der Knoten beim Umschalten nicht springt (kv-b5).
 */

/** Höhe des 3D-Fensters und des Blicks — je 96 px (UI-Vorgabe «Bilder nicht unter 96 px»). */
export const KAMERA_3D_H = 96;
export const KAMERA_BLICK_H = 96;
/** Feste Körperhöhe: Reiter 24, vier Bedienzeilen (Auto: Richtungen 2 × 18, drei Zeilen 24), 3D, Blick, Fusszeile 24, Abstände. */
export const KAMERA_KOERPER_H = 24 + 36 + 3 * 24 + KAMERA_3D_H + KAMERA_BLICK_H + 24 + 7 * 4;

/** Bestellformat der Vorschau (1600 × 1000, wie die Vorgabe am Heim-PC). */
const SEITENVERHAELTNIS = 1.6;

/** Heim-PC (Meter, Z oben) → glTF (Meter, Y oben): (x, y, z) → (x, z, −y). */
export function heimZuGltf(p: readonly [number, number, number]): [number, number, number] {
  return [p[0], p[2], -p[1]];
}
/** glTF → Ost/Nord/Höhe (wie am Heim-PC). */
export function gltfZuHeim(p: readonly [number, number, number]): [number, number, number] {
  return [p[0], -p[2], p[1]];
}

/** Die Standpunkte des Heim-PCs als Kegel (glTF). */
export function kegelAusHeim(standpunkte: readonly HeimStandpunkt[], wahl: KameraAutoWahl): VorschauKamera[] {
  const fov = fovAusBrennweiteGrad(wahl.brennweite_mm ?? KAMERA_AUTO_VORGABEN.brennweite_mm);
  return standpunkte.map((s) => ({
    name: s.name,
    position: heimZuGltf(s.auge),
    target: heimZuGltf(s.blick_auf),
    fov,
    seitenverhaeltnis: SEITENVERHAELTNIS,
  }));
}

/**
 * Befund B3 aus auf-20261021-306: Die senkrechte Auto-Kamera blickt waagrecht und verschiebt das Objektiv
 * (`shift_y`); eingefroren ohne Shift stand das Haus 6 % höher im Bild. Der Vertrag kennt keinen Shift —
 * aber der Heim-PC rechnet ihn bei `perspektive: 'senkrecht'` aus der Neigung zum Ziel zurück
 * (`kameras.shift_aus_ziel`: shift_mm = Brennweite · tan Neigung, shift_y = shift_mm / 36 mm). Beim
 * Einfrieren wird darum das Ziel so weit angehoben, dass genau dieser Shift wieder herauskommt.
 */
export function zielMitShift(auge: readonly [number, number, number], blickAuf: readonly [number, number, number], shiftY: number, brennweiteMm: number): [number, number, number] {
  const abstand = Math.hypot(blickAuf[0] - auge[0], blickAuf[1] - auge[1]);
  if (!Number.isFinite(shiftY) || shiftY === 0 || abstand <= 1e-9) return [blickAuf[0], blickAuf[1], blickAuf[2]];
  const tangens = (shiftY * 36) / brennweiteMm;
  return [blickAuf[0], blickAuf[1], auge[2] + abstand * tangens];
}

/** «Manuell übernehmen»: die Auto-Standpunkte eingefroren, in der Form des Parameters `kameras`. */
export function einfrieren(standpunkte: readonly HeimStandpunkt[], wahl: KameraAutoWahl): KameraManuell[] {
  const brennweite = wahl.brennweite_mm ?? KAMERA_AUTO_VORGABEN.brennweite_mm;
  const fov = Math.round(fovAusBrennweiteGrad(brennweite) * 1000) / 1000;
  return standpunkte.map((s) => ({
    name: s.name,
    position: heimZuGltf(s.auge),
    target: heimZuGltf(s.shift_y ? zielMitShift(s.auge, s.blick_auf, s.shift_y, brennweite) : s.blick_auf),
    fov,
  }));
}

function rund(x: number, stellen = 2): number {
  const f = 10 ** stellen;
  return Math.round(x * f) / f;
}

export function KameraKoerper({ graphId, node, knotenZoom = 1 }: { graphId: string; node: VisNode; knotenZoom?: number }) {
  const runCommand = useProject((s) => s.runCommand);
  const doc = useProject((s) => s.doc);
  useProject((s) => s.revision);
  useSyncExternalStore(abonniereHeimStandpunkte, heimStandpunkteFassung, heimStandpunkteFassung);
  const p = node.params ?? {};
  const modellKameras = projektKameras(doc);
  const artGesetzt = kameraArtAusParams(p);
  // Ohne `art` und ohne Standpunkte aus dem Entwurf (Visbox): das ist Auto mit den Vorgaben.
  const art: KameraArt = artGesetzt === 'modell' && modellKameras.length === 0 ? 'auto' : artGesetzt;
  const wahl = kameraAutoAusParams(p);
  const manuell = kameraManuellAusParams(p);
  const [blickNr, setBlickNr] = useState(0);
  const [manuellNr, setManuellNr] = useState(0);

  const setze = (params: Record<string, string | number | boolean>) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params });
      grundlagenNachfuehren(graphId);
    } catch (err) {
      meldeFehler(err);
    }
  };

  const tabs = [
    ...(modellKameras.length > 0 ? [{ id: 'modell', label: 'Modell', testid: 'kamera-art-modell' }] : []),
    { id: 'auto', label: 'Auto', testid: 'kamera-art-auto' },
    { id: 'manuell', label: 'Manuell', testid: 'kamera-art-manuell', disabled: manuell.length === 0 && art !== 'manuell' },
  ];

  const abfrage = art === 'auto' ? standpunkteFuer(wahl) : null;
  // Die drei Standpunkte, die der Wirt beim Laden der Mappe schon mitbringt (Entscheid 92) — sie
  // gelten, solange die Wahl die Vorgabe ist (ohne Abfrage, oder bis die Antwort da ist).
  const vorgabe = art === 'auto' && wahlSchluessel(wahl) === wahlSchluessel(kameraAutoAusParams({})) ? heimStandpunkte() : null;
  const heim = abfrage?.ergebnis?.standpunkte ?? vorgabe?.standpunkte ?? [];
  const kegel: VorschauKamera[] =
    art === 'auto'
      ? kegelAusHeim(heim, wahl)
      : art === 'manuell'
        ? manuell.map((k) => ({ ...k, seitenverhaeltnis: SEITENVERHAELTNIS }))
        : modellKameras.map((k) => ({ name: k.name, position: k.position, target: k.target, fov: k.fov }));

  const stand =
    art === 'auto'
      ? abfrage?.stand === 'da' && abfrage.ergebnis
        ? abfrage.ergebnis.satz
        : vorgabe && (!hatStandpunkteAbfrage() || abfrage?.stand === 'laedt')
          ? vorgabe.satz
          : !hatStandpunkteAbfrage()
        ? 'Die Standpunkte rechnet der Heim-PC beim Rendern.'
        : abfrage?.stand === 'laedt'
          ? 'Der Heim-PC rechnet die Standpunkte …'
          : abfrage?.stand === 'fehler'
            ? `Keine Vorschau: ${abfrage.satz ?? 'der Heim-PC antwortet nicht'}`
            : abfrage?.ergebnis?.satz ?? ''
      : art === 'manuell'
        ? `${manuell.length} ${manuell.length === 1 ? 'Standpunkt' : 'Standpunkte'} von Hand`
        : 'Vorschlag aus dem Modell';

  return (
    <div className="vis-kn vis-kn-kamera" data-testid="kamera" data-art={art} style={{ height: KAMERA_KOERPER_H }} onPointerDown={(e) => e.stopPropagation()}>
      <KTabs
        size="sm"
        items={tabs}
        aktiv={art}
        onChange={(a) => setze({ art: a })}
        data-testid="kamera-art"
      />
      {art === 'auto' ? (
        <AutoEinstellungen wahl={wahl} p={p} setze={setze} />
      ) : art === 'manuell' ? (
        <ManuellEinstellungen kameras={manuell} nr={manuellNr} setNr={setManuellNr} p={p} setze={setze} />
      ) : (
        <ModellListe doc={doc} />
      )}
      <KameraFenster kegel={kegel} blickNr={blickNr} setBlickNr={setBlickNr} knotenZoom={knotenZoom} />
      <div className="vis-kn-zeile">
        <KTooltip text={stand || 'Standpunkte'} lage="unten">
          <span tabIndex={0} className="vis-kn-satz vis-kn-dehnt" data-testid="kamera-stand">
            {stand}
          </span>
        </KTooltip>
        {art === 'auto' ? (
          <KTooltip text="Friert diese Standpunkte ein — danach von Hand verschieben." lage="unten">
            <KButton
              size="sm"
              tone="ghost"
              data-testid="kamera-manuell-uebernehmen"
              disabled={heim.length === 0}
              onClick={() => setze({ art: 'manuell', kameras: JSON.stringify(einfrieren(heim, wahl)), perspektive: wahl.perspektive ?? KAMERA_AUTO_VORGABEN.perspektive })}
            >
              Manuell
            </KButton>
          </KTooltip>
        ) : null}
      </div>
    </div>
  );
}

function AutoEinstellungen({
  wahl,
  p,
  setze,
}: {
  wahl: KameraAutoWahl;
  p: Record<string, string | number | boolean>;
  setze: (params: Record<string, string | number | boolean>) => void;
}) {
  const umschalten = (kuerzel: string) => {
    const an = wahl.richtungen.includes(kuerzel);
    if (an && wahl.richtungen.length === 1) return;
    const neu = an ? wahl.richtungen.filter((r) => r !== kuerzel) : [...wahl.richtungen, kuerzel];
    setze({ art: 'auto', richtungen: schreibeListe(KAMERA_RICHTUNGEN.map((r) => r.kuerzel).filter((r) => neu.includes(r))) });
  };
  const fest = p['abstandArt'] === 'fest';
  const brennweite = wahl.brennweite_mm ?? KAMERA_AUTO_VORGABEN.brennweite_mm;
  const fuellt = wahl.abstand?.art === 'auto' && wahl.abstand.fuellt !== undefined ? wahl.abstand.fuellt : KAMERA_AUTO_VORGABEN.fuellt;
  const meter = typeof p['abstandM'] === 'number' ? p['abstandM'] : 40;
  return (
    <>
      <div className="vis-kn-raster vis-kn-raster--4" data-testid="kamera-richtungen">
        {KAMERA_RICHTUNGEN.map((r) => (
          <KCheckbox
            key={r.kuerzel}
            size="sm"
            label={r.chip}
            checked={wahl.richtungen.includes(r.kuerzel)}
            onChange={() => umschalten(r.kuerzel)}
            data-testid={`kamera-richtung-${r.kuerzel}`}
          />
        ))}
      </div>
      <div className="vis-kn-zeile">
        <KTooltip text="Augenhöhe über dem Gelände am Standpunkt, in Metern" lage="unten">
          <span tabIndex={0} className="vis-kn-titel">Auge</span>
        </KTooltip>
        <KNumberField
          value={wahl.augenhoehe_m ?? KAMERA_AUTO_VORGABEN.augenhoehe_m}
          abgeleitet={wahl.augenhoehe_m === undefined}
          suffix="m"
          step={0.1}
          min={0.5}
          max={50}
          onCommit={(v) => setze({ art: 'auto', augenhoehe: rund(v) })}
          data-testid="kamera-augenhoehe"
          className="vis-kn-zahl"
        />
        <KTabs
          size="sm"
          items={[24, 35, 50].map((b) => ({ id: String(b), label: String(b), testid: `kamera-brennweite-${b}` }))}
          aktiv={String(brennweite)}
          onChange={(b) => setze({ art: 'auto', brennweite: Number(b) })}
          data-testid="kamera-brennweite"
        />
      </div>
      <div className="vis-kn-zeile">
        <KTooltip text={fest ? 'Fester Abstand vom Bauwerk, in Metern' : 'Das Haus füllt so viel der Bildbreite (Vorgabe 70 %)'} lage="unten">
          <span tabIndex={0} className="vis-kn-titel">Abstand</span>
        </KTooltip>
        <KTabs
          size="sm"
          items={[
            { id: 'auto', label: 'füllt', testid: 'kamera-abstand-auto' },
            { id: 'fest', label: 'fest', testid: 'kamera-abstand-fest' },
          ]}
          aktiv={fest ? 'fest' : 'auto'}
          onChange={(a) => setze({ art: 'auto', abstandArt: a, ...(a === 'fest' && typeof p['abstandM'] !== 'number' ? { abstandM: meter } : {}) })}
          data-testid="kamera-abstand"
        />
        {fest ? (
          <KNumberField value={meter} suffix="m" step={1} min={2} max={2000} onCommit={(v) => setze({ art: 'auto', abstandArt: 'fest', abstandM: Math.round(v) })} data-testid="kamera-abstand-m" className="vis-kn-zahl" />
        ) : (
          <KNumberField
            value={Math.round(fuellt * 100)}
            abgeleitet={wahl.abstand === undefined}
            suffix="%"
            step={5}
            min={20}
            max={95}
            onCommit={(v) => setze({ art: 'auto', abstandArt: 'auto', fuellt: Math.min(0.95, Math.max(0.2, rund(v / 100))) })}
            data-testid="kamera-fuellt"
            className="vis-kn-zahl"
          />
        )}
      </div>
      <PerspektiveZeile wert={wahl.perspektive ?? KAMERA_AUTO_VORGABEN.perspektive} onWahl={(v) => setze({ art: 'auto', perspektive: v })} />
    </>
  );
}

function PerspektiveZeile({ wert, onWahl }: { wert: 'senkrecht' | 'frei'; onWahl: (v: 'senkrecht' | 'frei') => void }) {
  return (
    <KTooltip text="Senkrechte gerade: die übliche Architektur-Perspektive (Zwei-Punkt), Senkrechten bleiben senkrecht. Frei: die Kamera kippt auf das Ziel." lage="unten">
      <div className="vis-kn-zeile" tabIndex={-1}>
        <span className="vis-kn-titel">Perspektive</span>
        <KTabs
          size="sm"
          items={[
            { id: 'senkrecht', label: 'Senkrecht', testid: 'kamera-perspektive-senkrecht' },
            { id: 'frei', label: 'Frei', testid: 'kamera-perspektive-frei' },
          ]}
          aktiv={wert}
          onChange={(v) => onWahl(v === 'frei' ? 'frei' : 'senkrecht')}
          data-testid="kamera-perspektive"
        />
      </div>
    </KTooltip>
  );
}

function ManuellEinstellungen({
  kameras,
  nr,
  setNr,
  p,
  setze,
}: {
  kameras: KameraManuell[];
  nr: number;
  setNr: (n: number) => void;
  p: Record<string, string | number | boolean>;
  setze: (params: Record<string, string | number | boolean>) => void;
}) {
  const i = Math.min(nr, Math.max(0, kameras.length - 1));
  const k = kameras[i];
  const aendere = (feld: 'position' | 'target', achse: 0 | 1 | 2, wert: number) => {
    if (!k) return;
    const heim = gltfZuHeim(k[feld]);
    heim[achse] = wert;
    const neu = kameras.map((x, j) => (j === i ? { ...x, [feld]: heimZuGltf(heim).map((v) => rund(v, 3)) } : x));
    setze({ kameras: JSON.stringify(neu) });
  };
  const zeile = (titel: string, hilfe: string, feld: 'position' | 'target') => {
    const w = k ? gltfZuHeim(k[feld]) : [0, 0, 0];
    return (
      <div className="vis-kn-zeile">
        <KTooltip text={hilfe} lage="unten">
          <span tabIndex={0} className="vis-kn-titel">{titel}</span>
        </KTooltip>
        {(['O', 'N', 'H'] as const).map((achse, a) => (
          <KNumberField
            key={achse}
            value={rund(w[a]!)}
            step={0.5}
            aria-label={`${titel} ${achse === 'O' ? 'Ost' : achse === 'N' ? 'Nord' : 'Höhe'}, Meter`}
            onCommit={(v) => aendere(feld, a as 0 | 1 | 2, v)}
            data-testid={`kamera-${feld === 'position' ? 'auge' : 'blick'}-${achse.toLowerCase()}`}
            className="vis-kn-zahl vis-kn-zahl--klein"
          />
        ))}
      </div>
    );
  };
  return (
    <>
      <div className="vis-kn-zeile">
        <KSelect size="sm" value={String(i)} onChange={(e) => setNr(Number(e.target.value))} data-testid="kamera-manuell-wahl" className="vis-kn-dehnt">
          {kameras.map((x, j) => (
            <option key={`${x.name}-${j}`} value={String(j)}>
              {x.name}
            </option>
          ))}
        </KSelect>
        <KTooltip text="Zurück zur Rechnung des Heim-PCs; die Standpunkte von Hand bleiben gespeichert." lage="unten">
          <KButton size="sm" tone="ghost" data-testid="kamera-zurueck-auto" onClick={() => setze({ art: 'auto' })}>
            Auto
          </KButton>
        </KTooltip>
      </div>
      {zeile('Auge', 'Standpunkt der Kamera: Ost, Nord und Höhe in Metern (Weltkoordinaten des Modells)', 'position')}
      {zeile('Blick', 'Wohin die Kamera schaut: Ost, Nord und Höhe in Metern', 'target')}
      <PerspektiveZeile wert={p['perspektive'] === 'frei' ? 'frei' : 'senkrecht'} onWahl={(v) => setze({ perspektive: v })} />
    </>
  );
}

function ModellListe({ doc }: { doc: KosmoDoc }) {
  // Wie bisher (s. Geschichte in `NodeCanvas.tsx` bis 21.10.2026): dieselbe Quelle wie der Auftrag.
  const kameras = projektKameras(doc);
  const uebernommen = new Set((doc.settings.uebernommeneKameras ?? []).map((k) => k.name));
  const interiorMoeglich = interiorFaehrt(doc);
  return (
    <div className="vis-node-kamera-liste vis-kn-modell" data-testid="vis-auto-kamera-liste">
      {kameras.map((k) =>
        uebernommen.has(k.name) ? (
          <KTooltip key={k.name} text={k.begruendung}>
            <div data-testid={`vis-kamera-uebernommen-${k.name}`}>
              <b>{k.name}</b> — von Hand gesetzt, übernommen
              {augeImModell(doc, k.position) === false && <span className="vis-node-kamera-nicht-bestellt"> · Auge ausserhalb dieses Modells</span>}
            </div>
          </KTooltip>
        ) : istUeberDiesenWegBestellbar(k.name, interiorMoeglich) ? (
          <KTooltip key={k.name} text={k.begruendung}>
            <div>
              <b>{k.name}</b> — Vorschlag aus dem Modell
            </div>
          </KTooltip>
        ) : (
          <KTooltip key={k.name} text={k.begruendung}>
            <div className="vis-node-kamera-nicht-bestellt">
              <b>{k.name}</b> — abgeleitet, über diesen Weg nicht bestellbar (braucht IFC)
            </div>
          </KTooltip>
        ),
      )}
    </div>
  );
}

/** Das kleine 3D-Fenster mit den Kegeln und darunter der Blick aus einem Standpunkt (Klick: nächster). */
function KameraFenster({
  kegel,
  blickNr,
  setBlickNr,
  knotenZoom,
}: {
  kegel: VorschauKamera[];
  blickNr: number;
  setBlickNr: (n: number) => void;
  knotenZoom: number;
}) {
  const doc = useProject((s) => s.doc);
  const wirt = modellLadenWirt();
  const zustand = modellLadeStand().zustand;
  const hatModell = wirt ? zustand.stand === 'geladen' : szeneBauteileAnzahl(doc) > 0;
  const schluessel = `${modellStand(doc)}·${zustand.stand === 'geladen' ? `${zustand.mappe}#${zustand.fassung ?? 1}` : ''}`;
  const quelle = useCallback(() => {
    void schluessel;
    return exportGlb(doc, doc.settings.projectName);
  }, [doc, schluessel]);
  const [bilder, setBilder] = useState<readonly (Blickvorschau | null)[]>([]);
  const leinwand = useRef<HTMLCanvasElement>(null);
  const i = kegel.length > 0 ? blickNr % kegel.length : 0;
  const bild = bilder[i] ?? null;
  useEffect(() => {
    const c = leinwand.current;
    if (!c || !bild) return;
    c.width = bild.breite;
    c.height = bild.hoehe;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    ctx.putImageData(new ImageData(new Uint8ClampedArray(bild.daten), bild.breite, bild.hoehe), 0, 0);
  }, [bild]);
  const name = kegel[i]?.name ?? '';
  return (
    <>
      <Suspense fallback={<div className="vis-kn-3d-platz" style={{ height: KAMERA_3D_H }} />}>
        <ModellVorschau3d
          glb={hatModell ? quelle : null}
          kameras={kegel}
          knotenZoom={knotenZoom}
          breite="100%"
          hoehe={KAMERA_3D_H}
          className="vis-modell-3d--knoten"
          data-testid="kamera-3d"
          onBlickvorschau={setBilder}
          blickvorschauGroesse={{ breite: 184, hoehe: KAMERA_BLICK_H }}
        />
      </Suspense>
      <KTooltip text={kegel.length > 1 ? `Blick aus «${name}» — Klick: nächster Standpunkt` : name ? `Blick aus «${name}»` : 'Noch kein Standpunkt'} lage="unten">
        <button
          type="button"
          className="vis-kn-blick"
          style={{ height: KAMERA_BLICK_H }}
          data-testid="kamera-blick"
          disabled={kegel.length < 2}
          onClick={() => setBlickNr(i + 1)}
        >
          {bild ? <canvas ref={leinwand} className="vis-kn-blick-bild" aria-hidden /> : null}
          <span className="vis-kn-bild-name">{name || 'Blick'}</span>
        </button>
      </KTooltip>
    </>
  );
}
