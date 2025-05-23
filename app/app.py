import ast

import pandas as pd
import streamlit as st
from surprise import SVD, Dataset, Reader
from tabs import with_tab1, with_tab2, with_tab3


# Load data
@st.cache_data
def get_data():
    return (
        pd.read_pickle("./app/models/game_similarity.pkl"),
        pd.read_pickle("./app/models/clean_games_with_meta.pkl"),
        pd.read_pickle("./app/models/reviews_sample.pkl"),
    )


games_similarity, games_with_meta, clean_recommendations = get_data()


# Fit model
@st.cache_resource
def get_model():
    reader = Reader(rating_scale=(0, 1))
    data = Dataset.load_from_df(
        clean_recommendations[["user_id", "app_id", "is_recommended"]],
        reader,
    )
    trainset = data.build_full_trainset()
    model = SVD()
    model.fit(trainset)
    return model, reader


model, reader = get_model()


@st.cache_data
def get_all_tags():
    all_tags = set()
    for tags in games_with_meta["tags"].dropna():
        for tag in tags:
            all_tags.add(tag)
    return sorted(all_tags)


all_tags = get_all_tags()


def show_game_info(game):
    st.session_state.selected_game = games_with_meta[
        games_with_meta["app_id"] == game
    ].iloc[0]


def recommend_games_by_content(
    game_id, clean_games_with_meta, game_similarity_df, top_n=10
):
    if game_id not in game_similarity_df.index:
        return pd.DataFrame()
    similar_games = game_similarity_df[game_id].sort_values(ascending=False)
    recommended_games = similar_games.iloc[1 : top_n + 1]
    recommendations = clean_games_with_meta.set_index("app_id").loc[
        recommended_games.index
    ]
    recommendations["similarity_score"] = recommended_games.values
    return recommendations.reset_index()[
        ["app_id", "title", "similarity_score", "tags", "description"]
    ]


def recommend_games_for_user(
    user_id, clean_games_with_meta, clean_recommendations, model, top_n=10
):
    all_games = clean_games_with_meta["app_id"].unique()
    rated_games = clean_recommendations[clean_recommendations["user_id"] == user_id][
        "app_id"
    ].unique()
    unrated_games = [game for game in all_games if game not in rated_games]
    predictions = [(game, model.predict(user_id, game).est) for game in unrated_games]
    top_games = sorted(predictions, key=lambda x: x[1], reverse=True)[:top_n]
    recommended_df = pd.DataFrame(top_games, columns=["app_id", "predicted_score"])
    recommendations = recommended_df.merge(
        clean_games_with_meta, on="app_id", how="left"
    )
    return recommendations[["app_id", "title", "predicted_score"]]


def get_user_game_rating(user_id, app_id, user_reviews):
    user_game_rating = user_reviews[
        (user_reviews["user_id"] == user_id) & (user_reviews["app_id"] == app_id)
    ]
    if user_game_rating.empty:
        return None
    return user_game_rating["is_recommended"].values[0]


# Session state for user and reviews
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "user_reviews" not in st.session_state:
    st.session_state.user_reviews = clean_recommendations.copy()
if "games_displayed" not in st.session_state:
    st.session_state.games_displayed = 20
if "selected_game" not in st.session_state:
    st.session_state.selected_game = None

# Sidebar navigation
tab1, tab2, tab3 = st.tabs(["Search Games", "Get Recommendations", "My Reviews"])

# Tab: Search Games
with tab1:
    with_tab1(
        all_tags,
        get_user_game_rating,
        games_with_meta,
        recommend_games_by_content,
        games_similarity,
    )

# Tab: Get Recommendations
with tab2:
    with_tab2(
        all_tags,
        games_with_meta,
        recommend_games_for_user,
        reader,
        show_game_info,
        get_user_game_rating
    )


# Tab: My Reviews
with tab3:
    with_tab3(games_with_meta)
