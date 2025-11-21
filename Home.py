import streamlit as st

st.title("📔 Datenauswertungen Rettungsdienst Schleswig-Flensburg")

st.write("\n")

# Check if user is already logged in
if not st.user.is_logged_in:
    st.title("🚑 RDSLFL Dashboard")
    st.write("Bitte melden Sie sich mit Ihrem Keycloak-Account an.")
    
    if st.button(
        "✨ RDSLFL Keycloak Login ✨",
        type="primary",
        use_container_width=True,
    ):
        st.login()
else:
    # User is logged in - show dashboard
    st.title("🚑 RDSLFL Dashboard")
    st.success(
        f"Willkommen, {st.user.name} ({st.user.email})!"
    )
    
    if st.button("Logout"):
        st.logout()

with st.expander("📝 Impressum & Datenschutz"):
    st.markdown("""
**Rettungsdienst des Kreises Schleswig-Flensburg**  
Anstalt des öffentlichen Rechts  
Thorshammer 8b  
24866 Busdorf  

**Vorstand:** Fridtjof Arens  
**E-Mail:** info@rettungsdienst-sl-fl.de  
**Telefon:** 04621 5308 000  

**Technische Rückfragen:** martin.brucker@rettungsdienst-sl-fl.de  
**Datenschutzerklärung:** https://www.rettungsdienst-sl-fl.de/datenschutz/
""")