import streamlit as st
from lohnrechner import LohnRechner
from uebersicht import generiere_uebersicht

# --- Basis-Setup ---
st.set_page_config(page_title="Mitarbeiterverwaltung", page_icon="💼", layout="wide")

# --- CSS laden ---
def load_css(file_name: str):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# --- Login mit Benutzername + Passwort + Rolle ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Login erforderlich")

    username = st.text_input("👤 Benutzername")
    password = st.text_input("🔑 Passwort", type="password")

    if st.button("Login"):
        users = st.secrets["users"]
        if username in users and password == users[username]["password"]:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success(f"Login erfolgreich ✅ (Rolle: {st.session_state.role})")
            st.rerun()
        else:
            st.error("Falscher Benutzername oder Passwort ❌")

    st.stop()

# --- Ab hier nur sichtbar bei korrektem Login ---
rechner = LohnRechner()

# Session State
if "eingabe_anzeigen" not in st.session_state:
    st.session_state.eingabe_anzeigen = False
if "liste_anzeigen" not in st.session_state:
    st.session_state.liste_anzeigen = True
if "bearbeiten_index" not in st.session_state:
    st.session_state.bearbeiten_index = None
if "bearbeite_tag_key" not in st.session_state:
    st.session_state.bearbeite_tag_key = {}

# --- Übersichtsdaten für Header ---
uebersichten = generiere_uebersicht()
if uebersichten:
    total_gesamtlohn = sum(e["Gesamtlohn (€)"] for e in uebersichten)
    total_basisstunden = sum(e["Basisstunden"] for e in uebersichten)
    total_ueberstunden = sum(e["Überstunden"] for e in uebersichten)
else:
    total_gesamtlohn = 0
    total_basisstunden = 0
    total_ueberstunden = 0

def format_euro_de(value: float) -> str:
    # Format 12345.67 -> 12.345,67
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# --- Header mit Summen-Widgets ---
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("💼 Mitarbeiterverwaltung")
with col2:
    st.metric("Alle Mitarbeiter", f"{rechner.anzahl_mitarbeiter()}")
with col3:
    st.metric("Basisstunden", f"{int(total_basisstunden)}")
with col4:
    st.metric("Überstunden", f"{int(total_ueberstunden)}")

st.divider()

# --- Nur Admin darf Mitarbeiter hinzufügen ---
if st.session_state.role == "admin":
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
                    st.success(f'Mitarbeiter "{name}" wurde gespeichert ✅')
                    st.session_state.eingabe_anzeigen = False
                    st.rerun()

    st.divider()

# --- Mitarbeiterliste ---
if st.button("📋 Mitarbeiterliste anzeigen/ausblenden"):
    st.session_state.liste_anzeigen = not st.session_state.liste_anzeigen

if st.session_state.liste_anzeigen:
    suchbegriff = st.text_input("🔍 Mitarbeiter suchen (Name)")
    gefilterte_mitarbeiter = [
        (i, m) for i, m in enumerate(rechner.mitarbeiter)
        if suchbegriff.lower() in m.get("name", "").lower()
    ] if suchbegriff else list(enumerate(rechner.mitarbeiter))

    # Alphabetisch sortieren nach Name
    gefilterte_mitarbeiter.sort(key=lambda x: x[1].get("name", "").lower())

    if not gefilterte_mitarbeiter:
        st.info("Keine Mitarbeiter gefunden.")
    else:
        for i, m in gefilterte_mitarbeiter:
            expanded = (st.session_state.bearbeiten_index == i)
            with st.expander(f'{m["name"]}', expanded=expanded):
                st.write(f'**Basislohn pro Stunde:** {m["lohn_pro_stunde"]} €')
                st.write(f'**Überstundenlohn pro Stunde:** {m["lohn_ueberstunde"]} €')

                # Arbeitstage anzeigen
                st.write("**Arbeitstage:**")
                if m.get("arbeitstage"):
                    for tag in m["arbeitstage"]:
                        d = tag["datum"]
                        st.write(f'- {d}: Basis {tag["basis"]} Std, Überstunden {tag["ueber"]} Std')

                        if st.session_state.role == "admin":
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

                # Admin darf neuen Arbeitstag hinzufügen
                if st.session_state.role == "admin":
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

                # Gesamteinkommen für den Mitarbeiter
                lohn = rechner.berechne_lohn(m)
                st.success(f"➡️ Gesamtlohn: {format_euro_de(lohn)} €")

                # Admin darf Mitarbeiter bearbeiten/löschen
                if st.session_state.role == "admin":
                    colA, colB = st.columns([1, 1])
                    with colA:
                        if st.button("📝 Mitarbeiter bearbeiten", key=f"edit_emp_btn_{i}"):
                            st.session_state.bearbeiten_index = i
                            st.rerun()
                    with colB:
                        if st.button("🗑 Mitarbeiter löschen", key=f"del_emp_btn_{i}"):
                            rechner.loesche_mitarbeiter(i)
                            st.warning("Mitarbeiter gelöscht ❌")
                            st.session_state.bearbeiten_index = None
                            st.session_state.bearbeite_tag_key.pop(i, None)
                            st.rerun()

# --- Übersicht (sichtbar für alle) ---
st.divider()
st.header("📊 Mitarbeiter-Übersicht")

if not uebersichten:
    st.info("Noch keine Daten vorhanden.")
else:
    # Tabelle
    st.dataframe(uebersichten, use_container_width=True)

    # Zusammenfassung unten zusätzlich (optional)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Gesamtlohn (€)", format_euro_de(total_gesamtlohn))
    with c2:
        st.metric("Basisstunden", f"{int(total_basisstunden)}")
    with c3:
        st.metric("Überstunden", f"{int(total_ueberstunden)}")
