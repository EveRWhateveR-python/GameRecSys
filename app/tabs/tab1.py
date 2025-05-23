import pandas as pd
import streamlit as st


def with_tab1(
    all_tags,
    get_user_game_rating,
    games_with_meta,
    recommend_games_by_content,
    games_similarity,
):
    if st.session_state.selected_game is None:
        st.title("Browse Games")

        # Search and filter controls
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "Search for games", placeholder="Type game name..."
            )
        with col2:
            selected_genres = st.multiselect("Filter by genre", options=all_tags)

        # Filter games based on search
        filtered_games = games_with_meta.copy()
        if search_query:
            filtered_games = filtered_games[
                filtered_games["title"].str.contains(search_query, case=False, na=False)
            ]

        # Apply genre filter - completely rewritten
        if selected_genres:
            # First ensure tags are strings (convert NaN to empty string)
            filtered_games["tags"] = filtered_games["tags"].fillna("")

            # Create a mask for games that contain any of the selected genres
            mask = filtered_games["tags"].apply(
                lambda tags: all(genre in tags for genre in selected_genres)
            )
            filtered_games = filtered_games[mask]

        # Display games in grid
        st.write(
            f"Showing {min(st.session_state.games_displayed, len(filtered_games))} of {len(filtered_games)} games"
        )

        # Create responsive grid - 5 columns
        cols = st.columns(5)
        col_index = 0

        for _, game in filtered_games.head(st.session_state.games_displayed).iterrows():
            with cols[col_index]:
                # Create a clickable container for the entire game card
                image_url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{game['app_id']}/header.jpg"

                # Use markdown to make the entire card clickable
                st.markdown(
                    f"""
                    <div style='cursor: pointer; margin-bottom: 20px;' onclick='window.location.href="?game_id={game["app_id"]}"'>
                        <img src='{image_url}' style='width: 100%; border-radius: 5px;'/>
                        <p style='text-align: center; margin-top: 5px;'>{game["title"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Hidden button to trigger the selection
                if st.button(
                    "Select",
                    key=f"select_{game['app_id']}",
                    help=f"View details for {game['title']}",
                ):
                    st.session_state.selected_game = game
                    st.rerun()

            col_index = (col_index + 1) % 5

        # Load more button
        if st.session_state.games_displayed < len(filtered_games):
            if st.button("Load more games"):
                st.session_state.games_displayed += 20
                st.rerun()

    else:
        # Display selected game details
        game = st.session_state.selected_game
        st.title(game["title"])

        # Back button
        if st.button("← Back to browse"):
            st.session_state.selected_game = None
            st.session_state.games_displayed = 20
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
        if col1.button("👍 Like", key='Like_page1'):
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

        if col2.button("👎 Dislike", key='Dislike_page1'):
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

        if col3.button("Remove Rating", key='Rmr_page1'):
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
