import streamlit as st
from lohnrechner import LohnRechner
from uebersicht import generiere_uebersicht

st.set_page_config(page_title="Mitarbeiterverwaltung", page_icon="💼", layout="wide")
rechner = LohnRechner()

# Session State
if "eingabe_anzeigen" not in st.session_state:
    st.session_state.eingabe_anzeigen = False
if "liste_anzeigen" not in st.session_state:
    st.session_state.liste_anzeigen = True
if "bearbeiten_index" not in st.session_state:
    st.session_state.bearbeiten_index = None
if "bearbeite_tag_key" not in st.session_state:
    # Map: index -> datum des Tags, der bearbeitet wird (oder None)
    st.session_state.bearbeite_tag_key = {}

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("💼 Mitarbeiterverwaltung")
with col2:
    st.metric("Gespeichert", f"{rechner.anzahl_mitarbeiter()} Mitarbeiter")

st.divider()

# Mitarbeiter hinzufügen
if st.button("➕ Neuen Mitarbeiter einfügen"):
    st.session_state.eingabe_anzeigen = True

if st.session_state.eingabe_anzeigen:
    with st.form("mitarbeiter_form"):
        name = st.text_input("Name")
        lohn_pro_stunde = st.number_input("Basislohn pro Stunde (€)", min_value=0.0, step=0.01, value=12.99)
        lohn_ueberstunde = st.number_input("Überstundenlohn pro Stunde (€)", min_value=0.0, step=0.01, value=13.99)

        st.write("---")
        st.caption("Optional: Ersten Arbeitstag direkt anlegen")
        tag_datum = st.text_input("Datum (YYYY-MM-DD)", value="")
        tag_basis = st.number_input("Basisstunden", min_value=0, step=1, value=8)
        tag_ueber = st.number_input("Überstunden", min_value=0, step=1, value=0)

        speichern = st.form_submit_button("Speichern")
        if speichern:
            if not name.strip():
                st.error("Bitte einen gültigen Namen eingeben.")
            else:
                initial_tage = []
                if tag_datum.strip():
                    initial_tage.append({
                        "datum": tag_datum.strip(),
                        "basis": int(tag_basis),
                        "ueber": int(tag_ueber),
                    })
                rechner.fuege_mitarbeiter_hinzu(name, lohn_pro_stunde, lohn_ueberstunde, initial_tage)
                st.success(f"Mitarbeiter „{name}“ wurde gespeichert ✅")
                st.session_state.eingabe_anzeigen = False
                st.rerun()

st.divider()

# Liste anzeigen/ausblenden
if st.button("📋 Mitarbeiterliste anzeigen/ausblenden"):
    st.session_state.liste_anzeigen = not st.session_state.liste_anzeigen

# Mitarbeiterliste
if st.session_state.liste_anzeigen:
    suchbegriff = st.text_input("🔍 Mitarbeiter suchen (Name)")
    gefilterte_mitarbeiter = [
        (i, m) for i, m in enumerate(rechner.mitarbeiter)
        if suchbegriff.lower() in m.get("name", "").lower()
    ] if suchbegriff else list(enumerate(rechner.mitarbeiter))

    if not gefilterte_mitarbeiter:
        st.info("Keine Mitarbeiter gefunden.")
    else:
        for i, m in gefilterte_mitarbeiter:
            # Expander automatisch offen, wenn gerade dieser Mitarbeiter bearbeitet wird
            expanded = (st.session_state.bearbeiten_index == i)
            with st.expander(f"{m['name']}", expanded=expanded):
                st.write(f"**Basislohn pro Stunde:** {m['lohn_pro_stunde']} €")
                st.write(f"**Überstundenlohn pro Stunde:** {m['lohn_ueberstunde']} €")

                # Arbeitstage anzeigen mit Einzelbearbeitung
                st.write("**Arbeitstage:**")
                if m.get("arbeitstage"):
                    for tag in m["arbeitstage"]:
                        d = tag["datum"]
                        st.write(f"- {d}: Basis {tag['basis']} Std, Überstunden {tag['ueber']} Std")

                        # Inline-Bearbeitung eines einzelnen Tages
                        if st.session_state.bearbeite_tag_key.get(i) == d:
                            with st.form(f"edit_tag_form_{i}_{d}"):
                                neues_datum = st.text_input("Datum (YYYY-MM-DD)", value=d, key=f"edit_tag_date_{i}_{d}")
                                basis = st.number_input("Basisstunden", min_value=0, step=1, value=int(tag["basis"]), key=f"edit_tag_basis_{i}_{d}")
                                ueber = st.number_input("Überstunden", min_value=0, step=1, value=int(tag["ueber"]), key=f"edit_tag_ueber_{i}_{d}")
                                save_tag = st.form_submit_button("💾 Tag speichern")
                                if save_tag:
                                    rechner.aktualisiere_arbeitstag(i, d, neues_datum, basis, ueber)
                                    st.success("Arbeitstag aktualisiert ✅")
                                    st.session_state.bearbeite_tag_key[i] = None
                                    st.rerun()
                        else:
                            c1, c2 = st.columns([1, 1])
                            with c1:
                                if st.button("📝 Tag bearbeiten", key=f"btn_edit_tag_{i}_{d}"):
                                    st.session_state.bearbeite_tag_key[i] = d
                                    st.rerun()
                            with c2:
                                if st.button("🗑 Tag entfernen", key=f"btn_del_tag_{i}_{d}"):
                                    rechner.entferne_arbeitstag(i, d)
                                    st.warning("Arbeitstag entfernt ❌")
                                    st.session_state.bearbeite_tag_key[i] = None
                                    st.rerun()
                else:
                    st.write("- Keine Arbeitstage eingetragen.")

                # Neuen Arbeitstag hinzufügen (Datum + Stunden)
                st.write("---")
                with st.form(f"add_day_form_{i}"):
                    neuer_tag_datum = st.text_input("Neuer Arbeitstag (YYYY-MM-DD)", key=f"new_day_date_{i}")
                    neuer_tag_basis = st.number_input("Basisstunden", min_value=0, step=1, value=8, key=f"new_day_basis_{i}")
                    neuer_tag_ueber = st.number_input("Überstunden", min_value=0, step=1, value=0, key=f"new_day_ueber_{i}")
                    add_day_submit = st.form_submit_button("➕ Tag hinzufügen")
                    if add_day_submit:
                        if not neuer_tag_datum.strip():
                            st.error("Bitte ein gültiges Datum eingeben (YYYY-MM-DD).")
                        else:
                            rechner.fuege_arbeitstag_hinzu(i, neuer_tag_datum.strip(), neuer_tag_basis, neuer_tag_ueber)
                            st.success("Arbeitstag hinzugefügt ✅")
                            st.rerun()

                # Gesamteinkommen
                lohn = rechner.berechne_lohn(m)
                st.success(f"➡️ Gesamtlohn: {lohn} €")

                # Aktionen: Mitarbeiter bearbeiten / löschen
                colA, colB = st.columns([1, 1])
                with colA:
                    if st.button("📝 Mitarbeiter bearbeiten", key=f"edit_emp_btn_{i}"):
                        st.session_state.bearbeiten_index = i
                        st.rerun()
                with colB:
                    if st.button("🗑 Mitarbeiter löschen", key=f"del_emp_btn_{i}"):
                        rechner.loesche_mitarbeiter(i)
                        st.warning("Mitarbeiter gelöscht ❌")
                        # Zustand säubern
                        st.session_state.bearbeiten_index = None
                        st.session_state.bearbeite_tag_key.pop(i, None)
                        st.rerun()

                # Bearbeiten-Felder für Mitarbeiter (Name/Löhne) nur bei Klick
                if st.session_state.bearbeiten_index == i:
                    st.write("---")
                    with st.form(f"edit_emp_form_{i}"):
                        name_edit = st.text_input("Name", value=m["name"], key=f"name_edit_{i}")
                        lohn_basis_edit = st.number_input("Basislohn pro Stunde (€)", min_value=0.0, step=0.01, value=float(m["lohn_pro_stunde"]), key=f"wage_edit_{i}")
                        lohn_ueber_edit = st.number_input("Überstundenlohn pro Stunde (€)", min_value=0.0, step=0.01, value=float(m["lohn_ueberstunde"]), key=f"ot_wage_edit_{i}")

                        save_emp = st.form_submit_button("💾 Änderungen speichern")
                        if save_emp:
                            if not name_edit.strip():
                                st.error("Bitte einen gültigen Namen eingeben.")
                            else:
                                rechner.bearbeite_mitarbeiter(i, name_edit, lohn_basis_edit, lohn_ueber_edit)
                                st.success("Mitarbeiterdaten aktualisiert ✅")
                                st.session_state.bearbeiten_index = None
                                st.rerun()

# Gesamtübersicht
st.divider()
st.header("📊 Mitarbeiter-Übersicht")

uebersichten = generiere_uebersicht()
if not uebersichten:
    st.info("Noch keine Daten vorhanden.")
else:
    st.dataframe(uebersichten, use_container_width=True)

    # Summen-Widget
    total_gesamtlohn = sum(e["Gesamtlohn (€)"] for e in uebersichten)
    total_basisstunden = sum(e["Basisstunden"] for e in uebersichten)
    total_ueberstunden = sum(e["Überstunden"] for e in uebersichten)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Gesamtlohn (alle)", f"{round(total_gesamtlohn, 2)} €")
    with c2:
        st.metric("Basisstunden (alle)", f"{total_basisstunden}")
    with c3:
        st.metric("Überstunden (alle)", f"{total_ueberstunden}")
