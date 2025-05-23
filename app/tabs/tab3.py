import streamlit as st


def with_tab3(games_with_meta):
    st.title("My Reviews")
    user_id = st.session_state.user_id
    user_reviews = st.session_state.user_reviews[
        st.session_state.user_reviews["user_id"] == user_id
    ]
    user_reviews = user_reviews.merge(games_with_meta, on="app_id", how="left")
    user_reviews = user_reviews[user_reviews["is_recommended"].notnull()]
    st.dataframe(user_reviews[["title", "is_recommended"]])
