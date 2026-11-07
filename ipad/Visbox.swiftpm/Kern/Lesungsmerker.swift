import Foundation

/// Die gemerkte Lesung des Schlüsselbunds (A0265, N1).
public struct Lesungsmerker<Lesung> {
    public private(set) var lesung: Lesung?
    public init() {}
    public mutating func uebernimm(_ neu: Lesung?) { lesung = neu }
    public mutating func fuehreNach(_ aendere: (inout Lesung) -> Void) {}
}
