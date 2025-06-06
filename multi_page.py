import streamlit as st

st.set_page_config(layout="wide")

stock_page = st.Page(
    page = 'views/stocks.py',
    title = 'Stocks',
    icon='💰',
    default=True
)
flux_page = st.Page(
    page = 'views/flux.py',
    title = 'Flux',
    icon='📇',
    default=False
)

pg = st.navigation({"Situation actuelle":[stock_page, flux_page]})
pg.run()