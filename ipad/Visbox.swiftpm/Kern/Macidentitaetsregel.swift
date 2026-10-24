import Foundation

/// Was der Mac beim Start mit seinem Zertifikat für die Leitung zum iPad tut — **nie still ein
/// neues, wenn es schon eines gab** (Befund Demolauf 0.3.54, 24.10.2026).
///
/// Bis 0.3.54 legte `Macidentitaet` ein neues Zertifikat an, sobald es das alte nicht lesen
/// konnte — ohne ein Wort. Nach jedem Update der Mac-App war das so (die App ist bei jedem Bau
/// anders unterschrieben, und der Schlüsselbund gibt den Schlüssel nur der App, die ihn anlegte),
/// und jedes gekoppelte iPad sah danach «Der Mac zeigt ein anderes Zertifikat als beim Koppeln».
/// Im Schlüsselbund sammelten sich die alten Einträge «Visbox Mac …».
///
/// Die Regel hier entscheidet, der Mac-Teil fragt nur den Schlüsselbund:
///
/// * **Lesbar** (das gemerkte Zertifikat ist da, sein Schlüssel unterschreibt): behalten — oder
///   erneuern, wenn die Frist abläuft (wie bisher).
/// * **Keines** im Schlüsselbund: das erste anlegen. Gab es schon eines (gemerkter Fingerabdruck),
///   zählt das als Verlust — die iPads müssen neu koppeln, und das steht am Mac.
/// * **Da, aber nicht lesbar:** **einmal** ein neues, mit dem Satz «iPads neu koppeln». Ist in
///   **derselben Fassung** schon einmal eines ersetzt worden, **kein weiteres** — dann sagt der
///   Mac, warum er sich dem iPad nicht anbietet, statt bei jedem Start ein neues anzulegen.
///
/// Mit Proben (`MacidentitaetsregelTests`); der Mac-Teil ist am Gerät unbestätigt.
public enum Macidentitaetsregel {

    /// Was der Mac im Schlüsselbund fand.
    public enum Fund: Equatable, Sendable {
        /// Das gemerkte Zertifikat ist da, und sein Schlüssel unterschreibt.
        case lesbar
        /// Kein Zertifikat «<Marke> Mac …» im Schlüsselbund.
        case keines
        /// Zertifikate «<Marke> Mac …» sind da, aber das gemerkte nicht darunter, oder sein
        /// Schlüssel verweigert die Unterschrift (Zugriff verweigert, Abfrage abgebrochen).
        case nichtLesbar
    }

    /// Was der Mac daraufhin tut.
    public enum Schritt: Equatable, Sendable {
        /// Das gelesene behalten.
        case behalten
        /// Die Frist läuft ab: das gelesene löschen und ein neues anlegen (wie bisher).
        case erneuern
        /// Noch nie eines: das erste anlegen, ohne Meldung.
        case erstesMal
        /// Es gab eines, es ist nicht (mehr) lesbar: **einmal** ein neues, mit Meldung.
        case ersetzenNachVerlust
        /// In dieser Fassung schon einmal ersetzt und wieder nicht lesbar: **kein weiteres**.
        case anhalten
    }

    /// - Parameters:
    ///   - fund: was im Schlüsselbund stand.
    ///   - fristLaeuftAb: `Maczertifikat.erneuern(bis:jetzt:)`.
    ///   - gemerkt: ob der Mac sich den Fingerabdruck eines früheren Zertifikats gemerkt hat.
    ///   - ersetztIn: in welcher Fassung zuletzt nach einem Verlust ersetzt wurde (`nil`: nie).
    ///   - fassung: die laufende Fassung der App (Versionsnummer und Baunummer).
    public static func schritt(fund: Fund, fristLaeuftAb: Bool, gemerkt: Bool,
                               ersetztIn: String?, fassung: String) -> Schritt {
        switch fund {
        case .lesbar:
            return fristLaeuftAb ? .erneuern : .behalten
        case .keines:
            // NICHTS MEHR DA (von Hand aufgeraeumt oder verloren): anlegen. Kein Anhalten — es
            // bleibt kein unlesbarer Rest liegen, der sich ansammeln koennte.
            return gemerkt ? .ersetzenNachVerlust : .erstesMal
        case .nichtLesbar:
            return ersetztIn == fassung ? .anhalten : .ersetzenNachVerlust
        }
    }

    /// Die Zeile «iPad» am Mac, solange nach einem Verlust noch kein iPad neu gekoppelt hat —
    /// `nil`, wenn nichts zu sagen ist oder gerade eine Zahl zum Koppeln gilt (die geht vor).
    public static func zeilenhinweis(neuKoppeln: Bool, zahlOffen: Bool) -> String? {
        guard neuKoppeln, !zahlOffen else { return nil }
        return satzNeuKoppeln
    }

    /// Nach einem Verlust: was der Mensch am Mac wissen muss.
    public static let satzNeuKoppeln =
        "Der Mac konnte sein bisheriges Zertifikat nach dem Update nicht mehr lesen und hat ein "
        + "neues — jedes iPad muss einmal neu koppeln: «iPad koppeln» im Menü «iPad»."

    /// Wenn er in dieser Fassung schon einmal ersetzt hat und es wieder nicht lesen kann.
    public static let satzAngehalten =
        "Der Mac kann sein Zertifikat für das iPad nicht lesen (der Schlüsselbund verweigert den "
        + "Zugriff), und er hat in dieser Fassung schon einmal ein neues angelegt — ein weiteres "
        + "legt er nicht still an. Beim nächsten Start den Zugriff erlauben, oder die alten "
        + "Einträge im Schlüsselbund löschen (Blatt «Feste Unterschrift für die Mac-App»)."
}
