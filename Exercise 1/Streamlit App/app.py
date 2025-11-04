import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import numpy as np

# Page configuration
st.set_page_config(
    page_title="🎬 TOP-250 Movies Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px 20px;
        color: white;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.3);
    }
    h1, h2, h3 {
        color: white;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Title and description
st.title("🎬 TOP-250 Movies Explorer")
st.markdown("### *Discover insights from the greatest films of all time*")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Upload Dataset")
    uploaded_file = st.file_uploader(
        "Choose a CSV or JSON file",
        type=["csv", "json"],
        help="Upload your TOP-250 movies dataset",
    )

    if uploaded_file:
        st.success("✅ File uploaded successfully!")

    st.markdown("---")
    st.markdown("### 📊 About This App")
    st.info(
        "Analyze the TOP-250 movies with interactive visualizations "
        "and discover fascinating insights about cinema history."
    )


# Load data function
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        data = json.load(file)
        df = pd.DataFrame(data)

    # Clean and prepare data
    if "castList" in df.columns and isinstance(df["castList"].iloc[0], str):
        df["castList"] = df["castList"].apply(eval)
    if "directorList" in df.columns and isinstance(df["directorList"].iloc[0], str):
        df["directorList"] = df["directorList"].apply(eval)
    if "genreList" in df.columns and isinstance(df["genreList"].iloc[0], str):
        df["genreList"] = df["genreList"].apply(eval)

    return df


# Main content
if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Display overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Movies", len(df), help="Number of movies in dataset")
    with col2:
        st.metric(
            "Avg Rating", f"{df['ratingValue'].mean():.2f}", help="Average rating"
        )
    with col3:
        st.metric(
            "Total Gross", f"${df['gross'].sum() / 1e9:.2f}B", help="Total box office"
        )
    with col4:
        st.metric(
            "Years Span",
            f"{df['year'].min()}-{df['year'].max()}",
            help="Time period covered",
        )

    st.markdown("---")

    # Data preview
    with st.expander("📋 View Full Dataset", expanded=False):
        st.dataframe(df, use_container_width=True, height=400)

    st.markdown("---")

    # Create tabs
    tabs = st.tabs(
        [
            "⏱️ Patience",
            "🎥 Binge Watching",
            "🌟 Screen Time",
            "💼 Workhorse",
            "💰 Cash Horse",
            "🏆 Genre Analysis",
            "📈 Timeline Explorer",
            "🔮 Movie Recommender",
        ]
    )

    # Tab 1: Patience (Movies >= 220 minutes)
    with tabs[0]:
        st.header("⏱️ Epic Movies: 220+ Minutes")
        long_movies = df[df["duration"] >= 220].sort_values("duration", ascending=False)

        if len(long_movies) > 0:
            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.bar(
                    long_movies,
                    x="title",
                    y="duration",
                    color="ratingValue",
                    title="Epic Movies by Duration",
                    labels={"duration": "Duration (minutes)", "title": "Movie Title"},
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.metric("Total Epic Movies", len(long_movies))
                st.metric("Longest Movie", f"{long_movies.iloc[0]['duration']} min")
                st.dataframe(
                    long_movies[["title", "duration", "year", "ratingValue"]],
                    use_container_width=True,
                    height=400,
                )
        else:
            st.warning("No movies found with duration >= 220 minutes")

    # Tab 2: Binge Watching Steven Spielberg
    with tabs[1]:
        st.header("🎥 Steven Spielberg Marathon")

        spielberg_movies = df[
            df["directorList"].apply(
                lambda x: "Steven Spielberg" in x if isinstance(x, list) else False
            )
        ]

        if len(spielberg_movies) > 0:
            total_duration = spielberg_movies["duration"].sum()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Movies", len(spielberg_movies))
            with col2:
                st.metric("Total Duration", f"{total_duration} min")
            with col3:
                st.metric("Watch Time", f"{total_duration / 60:.1f} hours")

            st.markdown("---")

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.scatter(
                    spielberg_movies,
                    x="year",
                    y="ratingValue",
                    size="gross",
                    color="duration",
                    hover_data=["title"],
                    title="Spielberg Movies: Rating vs Year",
                    labels={"year": "Release Year", "ratingValue": "Rating"},
                    color_continuous_scale="Sunset",
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.dataframe(
                    spielberg_movies[
                        ["title", "year", "duration", "ratingValue"]
                    ].sort_values("year"),
                    use_container_width=True,
                    height=450,
                )
        else:
            st.info("No Steven Spielberg movies found in the dataset")

    # Tab 3: This is about me (Screen time)
    with tabs[2]:
        st.header("🌟 TOP-10 Actors by Total Screen Time")

        actor_duration = {}
        for _, row in df.iterrows():
            if isinstance(row["castList"], list):
                for actor in row["castList"]:
                    actor_duration[actor] = (
                        actor_duration.get(actor, 0) + row["duration"]
                    )

        top_actors = sorted(actor_duration.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
        actors_df = pd.DataFrame(top_actors, columns=["Actor", "Total Minutes"])
        actors_df["Hours"] = (actors_df["Total Minutes"] / 60).round(1)

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.bar(
                actors_df,
                x="Actor",
                y="Total Minutes",
                title="Actors with Most Screen Time",
                color="Total Minutes",
                color_continuous_scale="Blues",
                text="Hours",
            )
            fig.update_traces(texttemplate="%{text}h", textposition="outside")
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                actors_df.reset_index(drop=True), use_container_width=True, height=450
            )

    # Tab 4: Workhorse (Most active actors)
    with tabs[3]:
        st.header("💼 TOP-10 Most Active Actors")

        actor_counts = Counter()
        for cast_list in df["castList"]:
            if isinstance(cast_list, list):
                actor_counts.update(cast_list)

        top_active = actor_counts.most_common(10)
        active_df = pd.DataFrame(top_active, columns=["Actor", "Movie Count"])

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=active_df["Actor"],
                        y=active_df["Movie Count"],
                        marker=dict(
                            color=active_df["Movie Count"],
                            colorscale="Greens",
                            showscale=True,
                        ),
                        text=active_df["Movie Count"],
                        textposition="outside",
                    )
                ]
            )
            fig.update_layout(
                title="Most Prolific Actors", xaxis_tickangle=-45, height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                active_df.reset_index(drop=True), use_container_width=True, height=450
            )

    # Tab 5: Cash Horse (Most successful actors)
    with tabs[4]:
        st.header("💰 TOP-10 Highest Grossing Actors")

        actor_gross = {}
        for _, row in df.iterrows():
            if isinstance(row["castList"], list) and pd.notna(row["gross"]):
                for actor in row["castList"]:
                    actor_gross[actor] = actor_gross.get(actor, 0) + row["gross"]

        top_gross = sorted(actor_gross.items(), key=lambda x: x[1], reverse=True)[:10]
        gross_df = pd.DataFrame(top_gross, columns=["Actor", "Total Gross"])
        gross_df["Gross (Billions)"] = (gross_df["Total Gross"] / 1e9).round(2)

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.bar(
                gross_df,
                x="Actor",
                y="Gross (Billions)",
                title="Box Office Champions",
                color="Gross (Billions)",
                color_continuous_scale="Reds",
                text="Gross (Billions)",
            )
            fig.update_traces(texttemplate="$%{text}B", textposition="outside")
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                gross_df[["Actor", "Gross (Billions)"]].reset_index(drop=True),
                use_container_width=True,
                height=450,
            )

    # WOW Feature 1: Genre Analysis
    with tabs[5]:
        st.header("🏆 Genre Deep Dive")

        genre_counts = Counter()
        genre_ratings = {}
        genre_gross = {}

        for _, row in df.iterrows():
            if isinstance(row["genreList"], list):
                for genre in row["genreList"]:
                    genre_counts[genre] += 1
                    if genre not in genre_ratings:
                        genre_ratings[genre] = []
                        genre_gross[genre] = []
                    genre_ratings[genre].append(row["ratingValue"])
                    if pd.notna(row["gross"]):
                        genre_gross[genre].append(row["gross"])

        genre_df = (
            pd.DataFrame(
                {
                    "Genre": list(genre_counts.keys()),
                    "Count": list(genre_counts.values()),
                    "Avg Rating": [
                        np.mean(genre_ratings[g]) for g in genre_counts.keys()
                    ],
                    "Total Gross (M)": [
                        sum(genre_gross[g]) / 1e6 if genre_gross[g] else 0
                        for g in genre_counts.keys()
                    ],
                }
            )
            .sort_values("Count", ascending=False)
            .head(15)
        )

        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(
                genre_df,
                x="Count",
                y="Avg Rating",
                size="Total Gross (M)",
                color="Avg Rating",
                hover_data=["Genre"],
                title="Genre Performance Matrix",
                color_continuous_scale="RdYlGn",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.treemap(
                genre_df.head(10),
                path=["Genre"],
                values="Count",
                title="Genre Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)

    # WOW Feature 2: Timeline Explorer
    with tabs[6]:
        st.header("📈 Cinema Through Time")

        timeline_df = (
            df.groupby("year")
            .agg({"ratingValue": "mean", "gross": "sum", "title": "count"})
            .reset_index()
        )
        timeline_df.columns = ["Year", "Avg Rating", "Total Gross", "Movie Count"]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=timeline_df["Year"],
                y=timeline_df["Avg Rating"],
                name="Average Rating",
                line=dict(color="gold", width=3),
                yaxis="y",
            )
        )

        fig.add_trace(
            go.Bar(
                x=timeline_df["Year"],
                y=timeline_df["Movie Count"],
                name="Number of Movies",
                marker=dict(color="lightblue"),
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Movie Quality and Quantity Over Time",
            yaxis=dict(title="Average Rating"),
            yaxis2=dict(title="Movie Count", overlaying="y", side="right"),
            hovermode="x unified",
            height=600,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Decade analysis
        df["decade"] = (df["year"] // 10) * 10
        decade_stats = (
            df.groupby("decade")
            .agg({"title": "count", "ratingValue": "mean", "gross": "sum"})
            .reset_index()
        )

        st.subheader("📊 Decade Breakdown")
        st.dataframe(decade_stats, use_container_width=True)

    # WOW Feature 3: Movie Recommender
    with tabs[7]:
        st.header("🔮 Find Your Next Favorite Movie")

        col1, col2 = st.columns(2)

        with col1:
            min_rating = st.slider("Minimum Rating", 7.0, 9.5, 8.0, 0.1)
            selected_genres = st.multiselect(
                "Select Genres",
                options=sorted(
                    set(
                        genre
                        for genres in df["genreList"]
                        if isinstance(genres, list)
                        for genre in genres
                    )
                ),
                default=[],
            )

        with col2:
            year_range = st.slider(
                "Year Range",
                int(df["year"].min()),
                int(df["year"].max()),
                (int(df["year"].min()), int(df["year"].max())),
            )
            max_duration = st.slider("Max Duration (minutes)", 60, 300, 180)

        # Filter movies
        filtered_df = df[
            (df["ratingValue"] >= min_rating)
            & (df["year"] >= year_range[0])
            & (df["year"] <= year_range[1])
            & (df["duration"] <= max_duration)
        ]

        if selected_genres:
            filtered_df = filtered_df[
                filtered_df["genreList"].apply(
                    lambda x: any(g in x for g in selected_genres)
                    if isinstance(x, list)
                    else False
                )
            ]

        st.subheader(f"🎬 {len(filtered_df)} Movies Match Your Criteria")

        if len(filtered_df) > 0:
            # Random recommendation
            if st.button("🎲 Give Me a Random Recommendation!"):
                random_movie = filtered_df.sample(1).iloc[0]
                st.success(
                    f"### How about: **{random_movie['title']}** ({random_movie['year']})?"
                )
                st.write(f"⭐ Rating: {random_movie['ratingValue']}")
                st.write(f"⏱️ Duration: {random_movie['duration']} minutes")
                st.write(f"📝 {random_movie['description']}")

            # Show filtered results
            st.dataframe(
                filtered_df[
                    ["title", "year", "ratingValue", "duration", "directorList"]
                ].sort_values("ratingValue", ascending=False),
                use_container_width=True,
            )

else:
    # Welcome screen
    st.markdown("""
    ## 👋 Welcome to the TOP-250 Movies Explorer!
    
    ### Getting Started:
    1. 📁 Upload your CSV or JSON file using the sidebar
    2. 🔍 Explore various analyses across different tabs
    3. 📊 Interact with beautiful visualizations
    
    ### Features Include:
    - ⏱️ **Patience**: Discover epic movies over 220 minutes
    - 🎥 **Binge Watching**: Steven Spielberg marathon planner
    - 🌟 **Screen Time**: Actors with most screen time
    - 💼 **Workhorse**: Most prolific actors
    - 💰 **Cash Horse**: Highest-grossing actors
    - 🏆 **Genre Analysis**: Deep dive into movie genres
    - 📈 **Timeline Explorer**: Cinema through the decades
    - 🔮 **Movie Recommender**: Find your perfect movie
    
    ### 🎬 Let's begin your cinematic journey!
    """)
