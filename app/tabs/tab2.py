import streamlit as st
from surprise import SVD, Dataset
import pandas as pd


def with_tab2(
    all_tags, games_with_meta, recommend_games_for_user, reader, show_game_info, get_user_game_rating
):
    if st.session_state.selected_game is None:
        st.title("Recommended For You")

        # Add genre filter to recommendations
        rec_genres = st.multiselect(
            "Filter recommendations by genre", options=all_tags, key="rec_genres"
        )

        user_id = st.session_state.user_id
        updated_model = SVD()
        new_data = Dataset.load_from_df(
            st.session_state.user_reviews[["user_id", "app_id", "is_recommended"]],
            reader,
        )
        updated_model.fit(new_data.build_full_trainset())

        # Get all recommendations first
        all_recommendations = recommend_games_for_user(
            user_id,
            games_with_meta,
            st.session_state.user_reviews,
            updated_model,
            top_n=100,  # Get more to filter from
        )

        # Apply genre filter if any genres selected
        if rec_genres:
            # Merge with full game data to get tags
            all_recommendations = all_recommendations.merge(
                games_with_meta[["app_id", "tags"]], on="app_id", how="left"
            )
            # Fill NA tags with empty string
            all_recommendations["tags"] = all_recommendations["tags"].fillna("")
            # Filter by selected genres
            genre_mask = all_recommendations["tags"].apply(
                lambda tags: any(genre in tags for genre in rec_genres)
            )
            all_recommendations = all_recommendations[genre_mask]

        # Display top 5 filtered recommendations
        recommendations = all_recommendations.head(5)

        for _, game in recommendations.iterrows():
            col1, col2 = st.columns([1, 3])

            with col1:
                image_url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{game['app_id']}/header.jpg"
                st.image(image_url, use_container_width=True)

            with col2:
                st.markdown(f"**{game['title']}**")
                game_info = games_with_meta[
                    games_with_meta["app_id"] == game["app_id"]
                ].iloc[0]
                st.markdown(f"{game_info['description'][:300]}...")

                # Show tags if available
                if "tags" in game:
                    st.markdown(f"**Tags:** {game['tags']}")
                else:
                    game_tags = games_with_meta[
                        games_with_meta["app_id"] == game["app_id"]
                    ]["tags"].values[0]
                    st.markdown(f"**Tags:** {game_tags}")

                # Rating prediction score
                st.markdown(f"**Predicted score:** {game['predicted_score']:.2f}")

            # Make the whole recommendation clickable
            # print(game["app_id"])
            st.button(
                "View details!",
                key=f"rec_details_{game['app_id']}",
                on_click=lambda x=game["app_id"]: show_game_info(x),
            )
            st.markdown("---")
    else:
        # Display selected game details
        game = st.session_state.selected_game
        st.title(game["title"])

        # Back button
        if st.button("← Back to recomendations"):
            st.session_state.selected_game = None
            st.rerun()
        
        # Game details
        image_url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{game['app_id']}/header.jpg"
        st.image(image_url, use_container_width=True)

        st.write(f"**Tags:** {game['tags']}")
        st.write(f"**Description:** {game['description'][:300]}...")
        store_url = f"https://store.steampowered.com/app/{game['app_id']}/"
        st.markdown(f"[View on Steam]({store_url})")

        # Rating buttons
        current_rating = get_user_game_rating(
            st.session_state.user_id, game["app_id"], st.session_state.user_reviews
        )

        col1, col2, col3 = st.columns(3)
        if col1.button("👍 Like", key='Like_page2'):
            # Remove any existing rating
            st.session_state.user_reviews = st.session_state.user_reviews[
                ~(
                    (
                        st.session_state.user_reviews["user_id"]
                        == st.session_state.user_id
                    )
                    & (st.session_state.user_reviews["app_id"] == game["app_id"])
                )
            ]
            # Add new rating
            st.session_state.user_reviews = pd.concat(
                [
                    st.session_state.user_reviews,
                    pd.DataFrame(
                        [[st.session_state.user_id, game["app_id"], 1]],
                        columns=["user_id", "app_id", "is_recommended"],
                    ),
                ],
                ignore_index=True,
            )
            st.rerun()

        if col2.button("👎 Dislike", key='Dislike_page2'):
            # Remove any existing rating
            st.session_state.user_reviews = st.session_state.user_reviews[
                ~(
                    (
                        st.session_state.user_reviews["user_id"]
                        == st.session_state.user_id
                    )
                    & (st.session_state.user_reviews["app_id"] == game["app_id"])
                )
            ]
            # Add new rating
            st.session_state.user_reviews = pd.concat(
                [
                    st.session_state.user_reviews,
                    pd.DataFrame(
                        [[st.session_state.user_id, game["app_id"], 0]],
                        columns=["user_id", "app_id", "is_recommended"],
                    ),
                ],
                ignore_index=True,
            )
            st.rerun()

        if col3.button("Remove Rating", key='Rmr_page2'):
            st.session_state.user_reviews = st.session_state.user_reviews[
                ~(
                    (
                        st.session_state.user_reviews["user_id"]
                        == st.session_state.user_id
                    )
                    & (st.session_state.user_reviews["app_id"] == game["app_id"])
                )
            ]
            st.rerun()
            st.markdown("---")