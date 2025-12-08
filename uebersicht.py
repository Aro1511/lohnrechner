from lohnrechner import LohnRechner

def generiere_uebersicht(datei="mitarbeiter.json"):
    """
    Übersicht für alle Mitarbeiter:
    - Name
    - Summe Basisstunden
    - Summe Überstunden
    - Lohn für Basisstunden
    - Lohn für Überstunden
    - Anzahl Werktage
    - Gesamtlohn
    """
    rechner = LohnRechner(datei)
    uebersichten = []

    for m in rechner.mitarbeiter:
        name = m.get("name", "")
        arbeitstage = m.get("arbeitstage", [])
        basis_stunden = sum(tag.get("basis", 0) for tag in arbeitstage)
        ueberstunden = sum(tag.get("ueber", 0) for tag in arbeitstage)
        lohn_basis = basis_stunden * float(m.get("lohn_pro_stunde", 0.0))
        lohn_ueberstunden = ueberstunden * float(m.get("lohn_ueberstunde", 0.0))
        gesamtlohn = rechner.berechne_lohn(m)
        werktage = len(arbeitstage)

        uebersichten.append({
            "Name": name,
            "Basisstunden": basis_stunden,
            "Überstunden": ueberstunden,
            "Lohn Basis (€)": round(lohn_basis, 2),
            "Lohn Überstunden (€)": round(lohn_ueberstunden, 2),
            "Werktage": werktage,
            "Gesamtlohn (€)": gesamtlohn
        })

    return uebersichten
