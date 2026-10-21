import type { CSSProperties } from 'react';
import {
  farbWort,
  MATERIAL_VORGABEN,
  materialAusParams,
  paletteAusParams,
  paletteSatz,
  schreibeListe,
  VIS_BAUTEIL_ARTEN,
  VIS_MATERIAL_BIBLIOTHEK,
  type VisGraph,
  type VisNode,
} from '@kosmo/kernel';
import { KInput, KNumberField, KSelect, KSlider, KTabs, KTooltip, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { grundlagenNachfuehren } from './vis-jobs';
import { flaechenMuster, hell, MATERIAL_MUSTER, mische, VORSCHAUBILDER } from './knoten-neu-vorschau';
import './knoten-neu.css';

/*
 * Bauplan «Neue Knoten» F4 (Blatt 33, Entscheide 111 A/B/C, 113 (7)): die Körper der Knoten
 * «Oberfläche» (Typ `material`, früher «Material-Bausteine»), «Material» (`materialTextur`) und
 * «Farbpalette». Feste Höhen, damit die Knoten nicht springen (kv-b5).
 *
 * Die Texturen (CC0, ambientCG, Entscheid 107) liegen am Heim-PC; der Knoten «Material» zeigt die
 * Vorschau als Kugel, Würfel oder Fläche aus dem Grundton und einem angedeuteten Muster, bis
 * verkleinerte Vorschaubilder ausgeliefert sind (Schritt W, `knoten-neu-vorschau.ts`).
 */

function useSetze(graphId: string, nodeId: string) {
  const runCommand = useProject((s) => s.runCommand);
  return (params: Record<string, string | number | boolean>) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId, params });
      grundlagenNachfuehren(graphId);
    } catch (err) {
      meldeFehler(err);
    }
  };
}

// ── Oberfläche ─────────────────────────────────────────────────────────────

/** Höhe der Zuordnung über dem Klapptext der Wandschichten: zwei Zeilen Kleinschrift. */
export const OBERFLAECHE_ZUORDNUNG_H = 30;

/** Was an den fünf Eingängen hängt — für einen Menschen, die Arten ohne Material «aus dem Modell». */
export function oberflaecheZeile(graph: VisGraph, nodeId: string): { kurz: string; voll: string } {
  const teile = VIS_BAUTEIL_ARTEN.map(({ art, label }) => {
    const kante = graph.edges.find((e) => e.to === nodeId && e.toPort === art);
    const m = kante ? graph.nodes.find((n) => n.id === kante.from) : undefined;
    const eintrag = m?.typ === 'materialTextur' ? VIS_MATERIAL_BIBLIOTHEK.find((x) => x.id === m.params?.['bibliothek']) : undefined;
    return { label, material: eintrag?.label };
  });
  const gewaehlt = teile.filter((t) => t.material);
  const kurz =
    gewaehlt.length === 0
      ? 'Alle Bauteile: aus dem Modell'
      : gewaehlt.map((t) => `${t.label}: ${t.material}`).join(' · ');
  const voll = teile.map((t) => `${t.label}: ${t.material ?? 'aus dem Modell'}`).join(' · ') + ' — Türen zählen zu «Übrige».';
  return { kurz, voll };
}

export function OberflaecheZuordnung({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const z = oberflaecheZeile(graph, node.id);
  return (
    <KTooltip text={z.voll} lage="unten">
      <span tabIndex={0} className="vis-kn-satz vis-kn-zwei" data-testid="oberflaeche-zuordnung" style={{ height: OBERFLAECHE_ZUORDNUNG_H }}>
        {z.kurz}
      </span>
    </KTooltip>
  );
}

// ── Material ───────────────────────────────────────────────────────────────

export const MATERIAL_VORSCHAU = 96;
/** Feste Körperhöhe: Auswahl 24, Vorschau 96, Reiter 24, Massstab/Drehung 24, Relief 24, Abstände. */
export const MATERIAL_KOERPER_H = 24 + MATERIAL_VORSCHAU + 24 + 24 + 24 + 4 * 4;

export type VorschauForm = 'kugel' | 'wuerfel' | 'flaeche';

function vorschauStil(form: VorschauForm, farbe: string, muster: ReturnType<typeof flaechenMuster>, bild?: string, toenung?: { farbe: string; staerke: number }): CSSProperties {
  if (bild) {
    // Schritt W: die Farbkarte als Bild; eine Toenung als halbdurchsichtige Schicht darueber, die Kugel mit Licht.
    const ton = toenung ? `linear-gradient(${toenung.farbe}${Math.round(toenung.staerke * 255).toString(16).padStart(2, '0')}, ${toenung.farbe}${Math.round(toenung.staerke * 255).toString(16).padStart(2, '0')}), ` : '';
    const licht = form === 'kugel' ? 'radial-gradient(circle at 35% 30%, rgba(255,255,255,0.35), rgba(0,0,0,0) 45%, rgba(0,0,0,0.45) 100%), ' : '';
    return { background: `${licht}${ton}url("${bild}") center / cover`, ...(form === 'kugel' ? { borderRadius: '50%' } : {}) };
  }
  if (form === 'kugel') {
    return { background: `radial-gradient(circle at 35% 30%, ${hell(farbe, 0.35)}, ${farbe} 55%, ${hell(farbe, -0.4)} 100%)`, borderRadius: '50%' };
  }
  if (form === 'flaeche') return { background: muster };
  return {};
}

export function MaterialKoerper({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const setze = useSetze(graph.id, node.id);
  const p = node.params ?? {};
  const id = typeof p['bibliothek'] === 'string' ? p['bibliothek'] : VIS_MATERIAL_BIBLIOTHEK[0]!.id;
  const eintrag = VIS_MATERIAL_BIBLIOTHEK.find((m) => m.id === id) ?? VIS_MATERIAL_BIBLIOTHEK[0]!;
  const palKante = graph.edges.find((e) => e.to === node.id && e.toPort === 'palette');
  const palKnoten = palKante ? graph.nodes.find((n) => n.id === palKante.from) : undefined;
  const palette = palKnoten?.typ === 'farbpalette' ? paletteAusParams(palKnoten.params) : undefined;
  const wahl = materialAusParams(p, palette);
  const farbe = wahl?.toenung ? mische(eintrag.farbe, wahl.toenung.farbe, wahl.toenung.staerke) : eintrag.farbe;
  const form: VorschauForm = p['vorschau'] === 'wuerfel' || p['vorschau'] === 'flaeche' ? p['vorschau'] : 'kugel';
  const massstab = wahl?.massstab_m ?? MATERIAL_VORGABEN.massstab_m;
  const drehung = wahl?.drehungGrad ?? MATERIAL_VORGABEN.drehungGrad;
  const relief = wahl?.relief ?? MATERIAL_VORGABEN.relief;
  const muster = flaechenMuster(MATERIAL_MUSTER[eintrag.id] ?? 'beton', farbe, massstab);
  const bildUrl = VORSCHAUBILDER.materialien[eintrag.id];
  return (
    <div className="vis-kn vis-kn-material" data-testid="material-textur" style={{ height: MATERIAL_KOERPER_H }} onPointerDown={(e) => e.stopPropagation()}>
      <KSelect size="sm" value={eintrag.id} onChange={(e) => setze({ bibliothek: e.target.value })} data-testid="material-bibliothek" className="vis-kn-dehnt">
        {VIS_MATERIAL_BIBLIOTHEK.map((m) => (
          <option key={m.id} value={m.id}>
            {m.label}
          </option>
        ))}
      </KSelect>
      <div className="vis-kn-material-oben">
        <KTooltip text={`${eintrag.label}${wahl?.toenung ? `, getönt ${Math.round(wahl.toenung.staerke * 100)} % ${farbWort(wahl.toenung.farbe)}` : ''} — ${bildUrl ? 'Vorschau aus der Farbkarte' : 'Vorschau aus dem Grundton'}; die Textur (CC0, ambientCG) liegt am Heim-PC.`} lage="unten">
          <div className="vis-kn-material-vorschau" tabIndex={0} data-testid="material-vorschau" data-form={form} style={{ width: MATERIAL_VORSCHAU, height: MATERIAL_VORSCHAU }}>
            {form === 'wuerfel' ? (
              <svg width={MATERIAL_VORSCHAU} height={MATERIAL_VORSCHAU} viewBox="0 0 96 96" aria-hidden>
                {bildUrl ? (
                  <defs>
                    <pattern id={`mat-${node.id}`} patternUnits="userSpaceOnUse" width="96" height="96">
                      <image href={bildUrl} width="96" height="96" preserveAspectRatio="xMidYMid slice" />
                    </pattern>
                  </defs>
                ) : null}
                <polygon points="48,10 86,30 48,50 10,30" fill={bildUrl ? `url(#mat-${node.id})` : hell(farbe, 0.25)} />
                <polygon points="10,30 48,50 48,90 10,70" fill={bildUrl ? `url(#mat-${node.id})` : farbe} />
                <polygon points="48,50 86,30 86,70 48,90" fill={bildUrl ? `url(#mat-${node.id})` : hell(farbe, -0.25)} />
                {bildUrl ? (
                  <>
                    <polygon points="48,10 86,30 48,50 10,30" fill="#ffffff" opacity={0.18} />
                    <polygon points="48,50 86,30 86,70 48,90" fill="#000000" opacity={0.25} />
                    {wahl?.toenung ? <polygon points="48,10 86,30 86,70 48,90 10,70 10,30" fill={wahl.toenung.farbe} opacity={wahl.toenung.staerke} /> : null}
                  </>
                ) : null}
              </svg>
            ) : (
              <div className="vis-kn-material-form" data-bild={bildUrl ? 'foto' : 'grundton'} style={vorschauStil(form, farbe, muster, bildUrl, wahl?.toenung)} />
            )}
          </div>
        </KTooltip>
        <div className="vis-kn-material-karten">
          <KTooltip text="Die Karten der Textur (Farbe, Rauheit, Höhe für das Relief) liegen am Heim-PC und gehen dort in Blender. Fehlt eine, weist der Heim-PC den Auftrag mit einem Satz ab." lage="unten">
            <span tabIndex={0} className="vis-kn-satz vis-kn-drei">
              Karten am Heim-PC: Farbe · Rauheit · Relief
            </span>
          </KTooltip>
          <span className="vis-kn-leise">ambientCG, CC0</span>
        </div>
      </div>
      <KTabs
        size="sm"
        items={[
          { id: 'kugel', label: 'Kugel', testid: 'material-vorschau-kugel' },
          { id: 'wuerfel', label: 'Würfel', testid: 'material-vorschau-wuerfel' },
          { id: 'flaeche', label: 'Fläche', testid: 'material-vorschau-flaeche' },
        ]}
        aktiv={form}
        onChange={(f) => setze({ vorschau: f })}
        data-testid="material-vorschau-form"
      />
      <div className="vis-kn-zeile">
        <KTooltip text="Wie gross ein Bild der Textur auf dem Bauteil wird, in Metern" lage="unten">
          <span tabIndex={0} className="vis-kn-titel">Massstab</span>
        </KTooltip>
        <KNumberField value={massstab} abgeleitet={wahl?.massstab_m === undefined} suffix="m" step={0.1} min={0.05} max={20} onCommit={(v) => setze({ massstab: Math.min(20, Math.max(0.05, v)) })} data-testid="material-massstab" className="vis-kn-zahl" />
        <KTooltip text="Drehung der Textur auf dem Bauteil, in Grad" lage="unten">
          <span tabIndex={0} className="vis-kn-titel">Drehung</span>
        </KTooltip>
        <KNumberField value={drehung} abgeleitet={wahl?.drehungGrad === undefined} suffix="°" step={15} min={0} max={360} onCommit={(v) => setze({ drehung: ((Math.round(v) % 360) + 360) % 360 })} data-testid="material-drehung" className="vis-kn-zahl" />
      </div>
      <div className="vis-kn-zeile">
        <KTooltip text="Wie stark die Höhenkarte die Oberfläche plastisch macht (Bump in Blender), 0 bis 1" lage="unten">
          <span tabIndex={0} className="vis-kn-titel">Relief</span>
        </KTooltip>
        <KSlider
          size="sm"
          min={0}
          max={1}
          step={0.05}
          key={relief}
          defaultValue={relief}
          aria-label="Relief"
          data-testid="material-relief"
          onPointerUp={(e) => setze({ relief: Number((e.target as HTMLInputElement).value) })}
          onKeyUp={(e) => setze({ relief: Number((e.target as HTMLInputElement).value) })}
          className="vis-kn-regler"
        />
        <span className="vis-kn-wert">{relief.toFixed(2)}</span>
      </div>
    </div>
  );
}

// ── Farbpalette ────────────────────────────────────────────────────────────

/** Feste Körperhöhe: Farbfelder 28, Leitfarbe 24, Stärke 24, Satz 16, Abstände. */
export const FARBPALETTE_KOERPER_H = 28 + 24 + 24 + 16 + 3 * 4;

export function FarbpaletteKoerper({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const setze = useSetze(graph.id, node.id);
  const pal = paletteAusParams(node.params);
  const farben = pal.farben.length > 0 ? pal.farben : ['#e9e2d4'];
  const satz = paletteSatz(farben);
  const setzeFarbe = (i: number, wert: string) => {
    const neu = [...farben];
    neu[i] = wert;
    setze({ farben: schreibeListe(neu) });
  };
  return (
    <div className="vis-kn vis-kn-palette" data-testid="farbpalette" style={{ height: FARBPALETTE_KOERPER_H }} onPointerDown={(e) => e.stopPropagation()}>
      <div className="vis-kn-zeile vis-kn-farben">
        {[0, 1, 2, 3].map((i) =>
          i < farben.length ? (
            <KInput
              key={i}
              type="color"
              size="sm"
              value={farben[i]}
              aria-label={`Farbe ${i + 1}: ${farbWort(farben[i]!)}`}
              data-testid={`farbpalette-farbe-${i}`}
              onChange={(e) => setzeFarbe(i, e.target.value)}
              className={`vis-kn-farbe${i === pal.leitfarbe ? ' vis-kn-farbe--leit' : ''}`}
            />
          ) : (
            <KTooltip key={i} text="Weitere Farbe hinzufügen" lage="unten">
              <button type="button" className="vis-kn-farbe vis-kn-farbe--leer" data-testid={`farbpalette-dazu-${i}`} onClick={() => setze({ farben: schreibeListe([...farben, hell(farben[farben.length - 1]!, -0.2)]) })}>
                +
              </button>
            </KTooltip>
          ),
        )}
      </div>
      <KTooltip text="Diese Farbe tönt das angehängte Material" lage="unten">
        <div className="vis-kn-zeile" tabIndex={-1}>
          <span className="vis-kn-titel">Tönt mit</span>
          <KTabs
            size="sm"
            items={farben.map((f, i) => ({ id: String(i), label: String(i + 1), testid: `farbpalette-leit-${i}` }))}
            aktiv={String(pal.leitfarbe)}
            onChange={(i) => setze({ leitfarbe: Number(i) })}
            data-testid="farbpalette-leitfarbe"
          />
        </div>
      </KTooltip>
      <div className="vis-kn-zeile">
        <span className="vis-kn-titel">Stärke</span>
        <KSlider
          size="sm"
          min={0}
          max={1}
          step={0.05}
          key={pal.staerke}
          defaultValue={pal.staerke}
          aria-label="Stärke der Tönung"
          data-testid="farbpalette-staerke"
          onPointerUp={(e) => setze({ staerke: Number((e.target as HTMLInputElement).value) })}
          onKeyUp={(e) => setze({ staerke: Number((e.target as HTMLInputElement).value) })}
          className="vis-kn-regler"
        />
        <span className="vis-kn-wert">{Math.round(pal.staerke * 100)} %</span>
      </div>
      <KTooltip text={`${satz} — geht als Satz ans Bildmodell (über Oberfläche und Kombinierer).`} lage="unten">
        <span tabIndex={0} className="vis-kn-satz" data-testid="farbpalette-satz">
          {satz}
        </span>
      </KTooltip>
    </div>
  );
}
