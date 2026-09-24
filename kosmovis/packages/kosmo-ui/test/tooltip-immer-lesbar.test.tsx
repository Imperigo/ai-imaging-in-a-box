// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { KTooltip } from '../src/tooltip';

/**
 * **P-KURZHILFE-LESBAR — der Ersatz war in einer Hinsicht schlechter als das
 * Ersetzte.**
 *
 * `KTooltip` soll das native `title=` ersetzen; 212 Stellen warten darauf.
 * Beim ERSTEN echten Austausch (B74, der technische IFC-Name an der
 * Klassenliste) ist aufgefallen, dass der Tausch die Auskunft fuer
 * Hilfstechnik **verschlechtert** haette:
 *
 *  - Ein natives `title` liegt **dauerhaft** im Zugaenglichkeitsbaum. Eine
 *    Sprachausgabe liest es, ohne dass jemand irgendwohin zeigt.
 *  - Die Blase gab ihren Text erst her, **wenn sie offen war** — und offen
 *    wird sie durch Zeigen, Tippen oder Fokus. **Eine Sprachausgabe zeigt
 *    nicht.**
 *
 * Aufgefallen ist es nicht durch Nachdenken, sondern weil ein bestehender
 * Waechter rot wurde: `p-b74-ifc-klasse-anzeige.test.tsx` verlangt, dass der
 * technische Name im Baum steht. Er hat den Rueckschritt gefangen, bevor er
 * ausgeliefert war.
 *
 * Behoben im Baustein, nicht an der Einsatzstelle — sonst muesste jede der
 * 212 kuenftigen Stellen denselben Umweg selbst bauen.
 */

describe('KTooltip — der Text steht IMMER im Baum, nicht erst beim Zeigen', () => {
  it('KONTROLLFALL: das Kind wird ueberhaupt gerendert', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="IfcColumn">
        <li>120× Stuetze</li>
      </KTooltip>,
    );
    expect(html).toContain('120× Stuetze');
  });

  it('der Text ist im geschlossenen Zustand da — das ist der ganze Fund', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="IfcColumn">
        <li>120× Stuetze</li>
      </KTooltip>,
    );
    expect(html, 'der Text erscheint erst beim Zeigen — fuer eine Sprachausgabe also nie').toContain('IfcColumn');
  });

  it('und er haengt am Kind, nicht bloss irgendwo im Baum', () => {
    // Ohne die Verknuepfung stuende der Text da und niemand wuesste, wozu er
    // gehoert.
    const html = renderToStaticMarkup(
      <KTooltip text="IfcColumn">
        <li>120× Stuetze</li>
      </KTooltip>,
    );
    const beschrieben = /aria-describedby="([^"]+)"/.exec(html);
    expect(beschrieben, 'kein aria-describedby am Kind').not.toBeNull();
    expect(html).toMatch(new RegExp(`id="${beschrieben![1]!.split(' ').pop()}"`));
  });

  it('er ist fuer das Auge unsichtbar — ueber die Klasse, nicht ueber display:none', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="IfcColumn">
        <li>120× Stuetze</li>
      </KTooltip>,
    );
    expect(html).toMatch(/class="k-nur-sr"/);
  });

  it('das Kurzzeichen wandert mit — sonst waere die halbe Auskunft still', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="Plan exportieren" kuerzel="⌘E">
        <button type="button">Export</button>
      </KTooltip>,
    );
    expect(html).toContain('Plan exportieren');
    expect(html).toContain('⌘E');
  });

  it('eine bereits vorhandene Beschriftung am Kind wird NICHT verdraengt, sondern ergaenzt', () => {
    // Der Fall, den eine naive Fassung still zerstoert: das Kind hatte schon
    // ein `aria-describedby`, und der Baustein ueberschreibt es.
    const html = renderToStaticMarkup(
      <KTooltip text="IfcColumn">
        <li aria-describedby="fremder-hinweis">120× Stuetze</li>
      </KTooltip>,
    );
    const beschrieben = /aria-describedby="([^"]+)"/.exec(html);
    expect(beschrieben).not.toBeNull();
    expect(beschrieben![1]!.split(' '), 'die fremde Beschriftung ist weg').toContain('fremder-hinweis');
    expect(beschrieben![1]!.split(' ').length).toBe(2);
  });
});
