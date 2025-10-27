import streamlit as st

st.title("📔 Datenauswertungen Rettungsdienst Schleswig-Flensburg")

st.write("\n")

if st.button(
    "✨ RDSLFL Keycloak Login ✨",
    type="primary",
    key="checkout-button",
    use_container_width=True,
):
    st.login("keycloak")

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