import Foundation

/// Der Testbau der Mac-App läuft NEBEN der installierten und berührt sie nicht (A0255, E144).
///
/// Ein Bau von einem Zweig (nicht `main`) trägt die Kennung der installierten App mit der Endung
/// `.test` (die Prüfstrecke setzt sie in der Kopie der Plist). Er **liest nur**: Adresse und
/// Fingerabdruck des Heim-PC aus der Ablage der installierten Kennung, den Zugang und das Zertifikat
/// aus dem geteilten Schlüsselbund. Er **schreibt nichts in den geteilten Schlüsselbund** und
/// **erzeugt nie neu**; Koppeln und «Von Hand eintragen» sagen einen Satz. So bleiben die installierte
/// App und das gekoppelte iPad unberührt.
///
/// Reine Regel, ohne Apple-Teile — darum mit Proben unter Linux.
public enum Testbau {

    /// Die Endung der Kennung eines Testbaus.
    public static let endung = ".test"

    /// Ob diese Bündelkennung die eines Testbaus ist.
    public static func istTestbau(kennung: String?) -> Bool {
        guard let kennung else { return false }
        return kennung.hasSuffix(endung) && kennung.count > endung.count
    }

    /// Die Kennung der installierten App, zu der dieser Testbau gehört — `nil`, wenn es kein Testbau ist.
    public static func installierteKennung(testkennung: String) -> String? {
        istTestbau(kennung: testkennung) ? String(testkennung.dropLast(endung.count)) : nil
    }

    /// Was «Koppeln», «Von Hand eintragen» und «iPad koppeln» im Testbau sagen — einmal, statt zu speichern.
    public static var satzKoppeln: String {
        "Der Testbau koppelt und trägt nichts ein, er liest nur Adresse und Anmeldung der installierten "
            + "\(Marke.name) und lässt ihren Zugang und das gekoppelte iPad unberührt; gekoppelt wird in der "
            + "installierten \(Marke.name)."
    }

    /// Wenn der Testbau den Zugang fürs iPad nicht lesen kann: kein neuer, nichts abgelegt.
    public static var satzKeinZugang: String {
        "Der Testbau konnte den Zugang der installierten \(Marke.name) fürs iPad nicht lesen und legt keinen "
            + "neuen an, das iPad bleibt der installierten App vorbehalten."
    }

    /// Wenn der Testbau das Zertifikat nicht lesen kann: kein neues.
    public static var satzKeinZertifikat: String {
        "Der Testbau konnte das Zertifikat der installierten \(Marke.name) nicht lesen und erzeugt kein neues, "
            + "darum bietet er sich dem iPad nicht an."
    }

    /// Was der Testbau sagt, wenn jemand das Anbieten einschaltet — und was der Schalter dann tut: nichts.
    public static var satzKeinAnbieten: String {
        "Der Testbau bietet sich dem iPad nie an, der Schalter «iPad über diesen Mac anbieten» bleibt in ihm "
            + "ohne Wirkung, denn das iPad gehört der installierten \(Marke.name)."
    }

    /// Ob der Mac sich dem iPad anbietet und was er dazu sagt.
    public static func anbieten(gewuenscht: Bool, testbau: Bool) -> (an: Bool, satz: String?) {
        testbau ? (false, satzKeinAnbieten) : (gewuenscht, nil)
    }
}
