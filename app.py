import streamlit as st

st.title("📔 Datenauswertungen Rettungsdienst Schleswig-Flensburg")

st.write("\n")

# Check if user is already logged in
if not st.session_state.get("logged_in", False):
    st.title("🚑 RDSLFL Dashboard")
    st.write("Bitte melden Sie sich mit Ihrem Keycloak-Account an.")
    
    if st.button(
        "✨ RDSLFL Keycloak Login ✨",
        type="primary",
        use_container_width=True,
    ):
        st.login("keycloak")
else:
    # User is logged in - show dashboard
    st.title("🚑 RDSLFL Dashboard")
    st.success(f"Willkommen, {st.session_state.get('user_info', {}).get('name', 'Benutzer')}!")
    
    # Your dashboard content here
    st.write("Dashboard content...")
    
    if st.button("Logout"):
        st.logout()

with st.expander("📝 Impressum & Datenschutz"):
    st.markdown("""
Rettungsdienst des Kreises Schleswig-Flensburg
Anstalt des öffentlichen Rechts
Thorshammer 8b
24866 Busdorf

Vorstand: Fridtjof Arens
E-Mail: info@rettungsdienst-sl-fl.de
Telefon: 04621 5308 000
                
Bei technischen Rückfragen an martin.brucker(a)rettungsdienst-sl-fl.de wenden.
Datenschutzerklärung: https://www.rettungsdienst-sl-fl.de/datenschutz/
""")