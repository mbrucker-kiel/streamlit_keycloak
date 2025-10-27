import streamlit as st

st.title("📔 Streamlit + Auth0 Production test")

st.markdown(
    "Hello DataFan, help me benchmark [Auth0](https://auth0.com/) for a future video by connecting with Google or creating an Email/Password account with verification 😁"
)


st.write("\n")

if st.button(
    "✨ Sign up to the DataFan Store",
    type="primary",
    key="checkout-button",
    use_container_width=True,
):
    # st.login("google")
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
    

st.html("./styles.html")