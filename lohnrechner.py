import json

class LohnRechner:
    def __init__(self, datei="mitarbeiter.json"):
        self.datei = datei
        self.mitarbeiter = self.lade_daten()

    def lade_daten(self):
        """JSON laden und Datenstruktur sicherstellen/migrieren."""
        try:
            with open(self.datei, "r", encoding="utf-8") as f:
                daten = json.load(f)
        except FileNotFoundError:
            self.mitarbeiter = []
            return self.mitarbeiter

        migrierte = []
        for d in daten:
            # Pflichtfelder und Typen absichern
            d["name"] = str(d.get("name", "")).strip()
            d["lohn_pro_stunde"] = float(d.get("lohn_pro_stunde", 0.0))
            d["lohn_ueberstunde"] = float(d.get("lohn_ueberstunde", 0.0))

            # arbeitstage zu Liste von Dicts mit datum/basis/ueber transformieren
            tage = d.get("arbeitstage", [])
            norm_tage = []
            if isinstance(tage, list):
                for t in tage:
                    if isinstance(t, dict):
                        norm_tage.append({
                            "datum": str(t.get("datum", "")).strip(),
                            "basis": int(t.get("basis", 0)),
                            "ueber": int(t.get("ueber", 0))
                        })
                    else:
                        # falls noch alte Struktur (Strings)
                        norm_tage.append({"datum": str(t).strip(), "basis": 0, "ueber": 0})
            elif isinstance(tage, str) and tage.strip():
                # kommagetrennt → placeholder ohne Stunden
                for s in tage.split(","):
                    norm_tage.append({"datum": s.strip(), "basis": 0, "ueber": 0})
            d["arbeitstage"] = norm_tage
            migrierte.append(d)

        self.mitarbeiter = migrierte
        self.speichere_daten()
        return self.mitarbeiter

    def speichere_daten(self):
        with open(self.datei, "w", encoding="utf-8") as f:
            json.dump(self.mitarbeiter, f, ensure_ascii=False, indent=4)

    def fuege_mitarbeiter_hinzu(self, name, lohn_pro_stunde, lohn_ueberstunde, arbeitstage=None):
        if arbeitstage is None:
            arbeitstage = []
        neuer_mitarbeiter = {
            "name": str(name).strip(),
            "lohn_pro_stunde": float(lohn_pro_stunde),
            "lohn_ueberstunde": float(lohn_ueberstunde),
            "arbeitstage": [
                {
                    "datum": str(t.get("datum", "")).strip(),
                    "basis": int(t.get("basis", 0)),
                    "ueber": int(t.get("ueber", 0))
                } for t in arbeitstage
            ]
        }
        self.mitarbeiter.append(neuer_mitarbeiter)
        self.speichere_daten()

    def loesche_mitarbeiter(self, index):
        if 0 <= index < len(self.mitarbeiter):
            del self.mitarbeiter[index]
            self.speichere_daten()

    def bearbeite_mitarbeiter(self, index, name, lohn_pro_stunde, lohn_ueberstunde):
        if 0 <= index < len(self.mitarbeiter):
            self.mitarbeiter[index]["name"] = str(name).strip()
            self.mitarbeiter[index]["lohn_pro_stunde"] = float(lohn_pro_stunde)
            self.mitarbeiter[index]["lohn_ueberstunde"] = float(lohn_ueberstunde)
            self.speichere_daten()

    def fuege_arbeitstag_hinzu(self, index, datum, basis, ueber):
        """Neuen Arbeitstag mit Basis- und Überstunden hinzufügen."""
        if 0 <= index < len(self.mitarbeiter) and str(datum).strip():
            tag = {
                "datum": str(datum).strip(),
                "basis": int(basis),
                "ueber": int(ueber)
            }
            self.mitarbeiter[index].setdefault("arbeitstage", []).append(tag)
            self.speichere_daten()

    def entferne_arbeitstag(self, index, datum):
        """Arbeitstag anhand des Datums entfernen."""
        if 0 <= index < len(self.mitarbeiter) and str(datum).strip():
            datum = str(datum).strip()
            tage = self.mitarbeiter[index].get("arbeitstage", [])
            self.mitarbeiter[index]["arbeitstage"] = [t for t in tage if t.get("datum") != datum]
            self.speichere_daten()

    def aktualisiere_arbeitstag(self, index, altes_datum, neues_datum, basis, ueber):
        """Bestehenden Arbeitstag bearbeiten (Datum/Basis/Überstunden)."""
        if 0 <= index < len(self.mitarbeiter):
            tage = self.mitarbeiter[index].get("arbeitstage", [])
            for t in tage:
                if t.get("datum") == str(altes_datum).strip():
                    t["datum"] = str(neues_datum).strip()
                    t["basis"] = int(basis)
                    t["ueber"] = int(ueber)
                    self.speichere_daten()
                    break

    def berechne_lohn(self, mitarbeiter):
        """Summiert Basisstunden × Basislohn und Überstunden × Überstundenlohn über alle Tage."""
        basis_lohn = float(mitarbeiter.get("lohn_pro_stunde", 0.0))
        ueber_lohn = float(mitarbeiter.get("lohn_ueberstunde", 0.0))
        gesamt = 0.0
        for tag in mitarbeiter.get("arbeitstage", []):
            basis = int(tag.get("basis", 0))
            ueber = int(tag.get("ueber", 0))
            gesamt += basis * basis_lohn + ueber * ueber_lohn
        return round(gesamt, 2)

    def anzahl_mitarbeiter(self):
        return len(self.mitarbeiter)
