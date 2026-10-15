import {
  schreibeListe,
  variantenAchsenSatz,
  variantenWarnt,
  variantenZaehlerSatz,
  VIS_STIMMUNGEN,
  type VisGraph,
  type VisNode,
} from '@kosmo/kernel';
import { KButton, KCheckbox, KTooltip, melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { useVisRuntime } from './vis-runtime';
import {
  alleFreigeben,
  DAUER_ANNAHME_SATZ,
  SKIZZE_STANDPUNKT,
  dauerSatz,
  ungefaehreDauer,
  useVariantenBestellung,
  variantenAuswahl,
  variantenBestellenKlick,
  variantenZellen,
  wartendeLaeufe,
} from './varianten';

/**
 * Koerper des Knotens «Varianten» (Owner-Entscheide 92/92a/92b, Blatt 23; L24 Bildweg Varianten,
 * E246). Eigene Datei, damit `NodeCanvas.tsx` nur Einfuhr, Hoehe und einen `case` bekommt.
 *
 * Von oben: der Zaehler «N Bilder (S × St × E)», die drei Achsen zum Anhaken, eine Zeile fuer
 * die Warnung ab 12 Bildern (mit ungefaehrer Dauer, kein Limit) und den Stand der letzten
 * Bestellung, darunter EIN Knopf «N Bilder bestellen» und EIN Knopf «Alle freigeben». Die Hoehe
 * ist fest (`KOERPER_H.varianten`); eine lange Liste bricht um und steht ganz in der Kurzhilfe.
 *
 * Jedes Anhaken ist ein `vis.nodeParametrieren` (ein Rueckgaengig-Schritt). Bestellt wird mit
 * `vis.varianten` — demselben Befehl, den Kosmo und Claude rufen.
 */
export function VariantenKoerper({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const runCommand = useProject((s) => s.runCommand);
  const doc = useProject.getState().doc;
  const bestellung = useVariantenBestellung((s) => s.bestellungen[node.id]);
  const laeufe = useVisRuntime((s) => s.laeufe);
  const a = variantenAuswahl(doc, graph, node);
  const s = a.zeilen.length;
  const st = a.achsen.stimmungen.length;
  const e = a.achsen.entwuerfe.length;

  const setze = (feld: 'standpunkte' | 'stimmungen' | 'entwuerfe', liste: string[]) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId: graph.id, nodeId: node.id, params: { [feld]: schreibeListe(liste) } });
    } catch (err) {
      meldeFehler(err);
    }
  };
  const umschalten = (feld: 'standpunkte' | 'stimmungen' | 'entwuerfe', gewaehlt: readonly string[], id: string) =>
    setze(feld, gewaehlt.includes(id) ? gewaehlt.filter((x) => x !== id) : [...gewaehlt, id]);

  const zellen = bestellung ? variantenZellen(bestellung, laeufe) : [];
  const fertig = zellen.filter((z) => z.zustand === 'fertig').length;
  const fehl = zellen.filter((z) => z.zustand === 'fehlgeschlagen' || z.zustand === 'nicht-gesendet').length;
  const warten = wartendeLaeufe(node.id).length;
  void laeufe; // abonniert: `wartendeLaeufe` liest den Speicher selbst
  const standSatz = !a.render
    ? 'Mit dem Bild eines Render-Knotens verbinden.'
    : bestellung
    ? `Bestellung ${bestellung.nr}: ${fertig} von ${zellen.length} fertig${fehl ? `, ${fehl} fehlgeschlagen` : ''}${warten ? `, ${warten} ${warten === 1 ? 'Auftrag wartet' : 'Aufträge warten'} auf Freigabe` : ''}`
    : '';

  const warnt = variantenWarnt(a.anzahl);
  const ohneRender = !a.render;

  const freigeben = () => {
    void alleFreigeben(node.id).then((n) => {
      if (n > 0) melde(`${n} ${n === 1 ? 'Auftrag' : 'Aufträge'} freigegeben.`, { ton: 'info' });
    });
  };

  return (
    <div className="vis-varianten" data-testid="varianten" onPointerDown={(ev) => ev.stopPropagation()}>
      <KTooltip text={`${variantenAchsenSatz(s, st, e)} — ein Auftrag je Stimmung und Entwurf, mit allen Standpunkten.`} lage="unten">
        <span tabIndex={0} className="vis-varianten-zaehler" data-testid="varianten-zaehler">
          {variantenZaehlerSatz(s, st, e)}
        </span>
      </KTooltip>

      <Achse titel="Standpunkte" testid="varianten-standpunkte" voll={a.zeilen.join(', ')}>
        {a.heim && a.heim[0] === SKIZZE_STANDPUNKT ? (
          <span className="vis-varianten-satz" data-testid="varianten-skizze">
            Die Skizze führt das Bild — eines je Stimmung und Entwurf, von ihrem Standpunkt.
          </span>
        ) : a.heim ? (
          <span className="vis-varianten-satz" data-testid="varianten-heim">
            Die {a.heim.length} Richtungen des Heim-PCs ({a.heim.join(', ')}) kommen zusammen.
          </span>
        ) : a.standpunkte.length === 0 ? (
          <span className="vis-varianten-satz">Keine Standpunkte — erst ein Modell laden oder einen Blick sichern.</span>
        ) : (
          a.standpunkte.map((p) => (
            <KCheckbox
              key={p.name}
              size="sm"
              label={p.name}
              checked={a.achsen.standpunkte.includes(p.name)}
              onChange={() => umschalten('standpunkte', a.achsen.standpunkte, p.name)}
              data-testid={`varianten-standpunkt-${p.name}`}
            />
          ))
        )}
      </Achse>

      <Achse titel="Stimmungen" testid="varianten-stimmungen" voll={a.achsen.stimmungen.map((x) => VIS_STIMMUNGEN[x]?.label ?? x).join(', ')}>
        {a.stimmungen.map((m) => (
          <KCheckbox
            key={m.id}
            size="sm"
            label={m.label}
            checked={a.achsen.stimmungen.includes(m.id)}
            onChange={() => umschalten('stimmungen', a.achsen.stimmungen, m.id)}
            data-testid={`varianten-stimmung-${m.id}`}
          />
        ))}
      </Achse>

      <Achse titel="Entwürfe" testid="varianten-entwuerfe" voll={a.entwuerfe.filter((x) => a.achsen.entwuerfe.includes(x.id)).map((x) => x.name).join(', ')}>
        {a.entwuerfe.map((x) => (
          <KCheckbox
            key={x.id}
            size="sm"
            label={x.name}
            checked={a.achsen.entwuerfe.includes(x.id)}
            onChange={() => umschalten('entwuerfe', a.achsen.entwuerfe, x.id)}
            data-testid={`varianten-entwurf-${x.id}`}
          />
        ))}
      </Achse>

      {warnt ? (
        <KTooltip text={DAUER_ANNAHME_SATZ} lage="unten">
          <span tabIndex={0} className="vis-varianten-zeile vis-varianten-warnung" data-testid="varianten-warnung">
            Viele Bilder: {dauerSatz(a.anzahl, a.sekundenJeBild)}
          </span>
        </KTooltip>
      ) : (
        <span className="vis-varianten-zeile" data-testid="varianten-dauer">
          {a.anzahl > 0 && a.sekundenJeBild > 0 ? ungefaehreDauer(a.anzahl, a.sekundenJeBild) : ''}
        </span>
      )}
      <KTooltip text={standSatz || 'Noch nichts bestellt.'} lage="unten">
        <span tabIndex={0} className="vis-varianten-zeile vis-varianten-stand" data-testid="varianten-stand">
          {standSatz || 'Noch nichts bestellt.'}
        </span>
      </KTooltip>

      <div className="vis-varianten-knoepfe">
        <KButton
          size="sm"
          data-testid="varianten-bestellen"
          disabled={ohneRender || a.anzahl === 0}
          onClick={() => variantenBestellenKlick(graph.id, node.id)}
        >
          {a.anzahl} {a.anzahl === 1 ? 'Bild' : 'Bilder'} bestellen
        </KButton>
        <KButton size="sm" tone="ghost" data-testid="varianten-freigeben" disabled={warten === 0} onClick={freigeben}>
          Alle freigeben
        </KButton>
      </div>
    </div>
  );
}

function Achse({ titel, testid, voll, children }: { titel: string; testid: string; voll: string; children: React.ReactNode }) {
  return (
    <div className="vis-varianten-achse" data-testid={testid}>
      <KTooltip text={voll ? `${titel}: ${voll}` : `${titel}: keine gewählt`} lage="unten">
        <span tabIndex={0} className="k-label vis-varianten-achse-titel">
          {titel}
        </span>
      </KTooltip>
      <div className="vis-varianten-wahl">{children}</div>
    </div>
  );
}
