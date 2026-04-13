"""
EDA Visualizations module.
Creates interactive Plotly charts for the Analytics dashboard.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# Cinematic color palette
COLORS = {
    "primary": "#E50914",       # Netflix red
    "secondary": "#F5C518",     # IMDb gold
    "accent": "#00D4AA",        # Teal accent
    "bg_dark": "#0D1117",       # Dark background
    "surface": "#161B22",       # Card surface
    "text": "#E6EDF3",          # Light text
    "text_muted": "#8B949E",    # Muted text
    "gradient": ["#E50914", "#FF6B35", "#F5C518", "#00D4AA", "#4A9EFF", "#A855F7"]
}

PLOTLY_TEMPLATE = "plotly_dark"


def _style_figure(fig, title=""):
    """Apply consistent dark cinematic styling to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color=COLORS["text"], family="Inter")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_muted"], family="Inter", size=12),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=COLORS["surface"], font_size=13, font_family="Inter"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
    return fig


def genre_distribution_chart(df):
    """Horizontal bar chart showing movie count per genre."""
    if "genres" not in df.columns:
        return go.Figure()

    # Explode genres
    genre_counts = (
        df["genres"].dropna()
        .str.split(", ")
        .explode()
        .value_counts()
        .head(20)
        .sort_values(ascending=True)
    )

    fig = go.Figure(go.Bar(
        x=genre_counts.values,
        y=genre_counts.index,
        orientation="h",
        marker=dict(
            color=genre_counts.values,
            colorscale=[[0, "#4A9EFF"], [0.5, "#F5C518"], [1, "#E50914"]],
            line=dict(width=0),
            cornerradius=4,
        ),
        text=genre_counts.values,
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
    ))

    return _style_figure(fig, "🎭 Genre Distribution")


def rating_distribution_chart(df):
    """Histogram of vote_average ratings."""
    if "vote_average" not in df.columns:
        return go.Figure()

    filtered = df[df["vote_average"] > 0]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=filtered["vote_average"],
        nbinsx=30,
        marker=dict(
            color=COLORS["accent"],
            line=dict(width=1, color="rgba(255,255,255,0.1)"),
        ),
        opacity=0.85,
        name="Count",
    ))

    # Add a KDE-like line
    from numpy import histogram, linspace
    counts, bin_edges = histogram(filtered["vote_average"].dropna(), bins=30)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    fig.add_trace(go.Scatter(
        x=bin_centers, y=counts,
        mode="lines",
        line=dict(color=COLORS["secondary"], width=2, shape="spline"),
        name="Trend",
    ))

    fig.update_layout(xaxis_title="Rating", yaxis_title="Number of Movies")
    return _style_figure(fig, "⭐ Rating Distribution")


def movies_over_time_chart(df):
    """Line chart of movie releases by year."""
    if "release_date" not in df.columns:
        return go.Figure()

    df_copy = df.copy()
    df_copy["year"] = pd.to_datetime(df_copy["release_date"], errors="coerce").dt.year
    yearly = df_copy.groupby("year").size().reset_index(name="count")
    yearly = yearly[(yearly["year"] >= 1950) & (yearly["year"] <= 2025)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yearly["year"], y=yearly["count"],
        mode="lines+markers",
        line=dict(color=COLORS["primary"], width=3, shape="spline"),
        marker=dict(size=4, color=COLORS["secondary"]),
        fill="tozeroy",
        fillcolor="rgba(229,9,20,0.1)",
        name="Movies Released",
    ))

    fig.update_layout(xaxis_title="Year", yaxis_title="Number of Movies")
    return _style_figure(fig, "📅 Movies Released Per Year")


def top_rated_movies_chart(df, limit=15):
    """Bar chart of top rated movies."""
    if "vote_average" not in df.columns or "title" not in df.columns:
        return go.Figure()

    if "vote_count" in df.columns:
        top = df[df["vote_count"] >= 100].nlargest(limit, "vote_average")
    else:
        top = df.nlargest(limit, "vote_average")

    top = top.sort_values("vote_average", ascending=True)

    fig = go.Figure(go.Bar(
        x=top["vote_average"],
        y=top["title"],
        orientation="h",
        marker=dict(
            color=top["vote_average"],
            colorscale=[[0, "#4A9EFF"], [0.6, "#F5C518"], [1, "#E50914"]],
            cornerradius=4,
        ),
        text=[f"⭐ {r:.1f}" for r in top["vote_average"]],
        textposition="outside",
        textfont=dict(color=COLORS["secondary"], size=11),
    ))

    fig.update_layout(xaxis_title="Rating", height=max(400, limit * 35))
    return _style_figure(fig, "🏆 Top Rated Movies")


def genre_vs_rating_chart(df):
    """Box plot comparing ratings across genres."""
    if "genres" not in df.columns or "vote_average" not in df.columns:
        return go.Figure()

    exploded = df.assign(genre=df["genres"].str.split(", ")).explode("genre")
    exploded = exploded[exploded["genre"].notna() & (exploded["genre"] != "")]
    exploded = exploded[exploded["vote_average"] > 0]

    # Get top 12 genres by count
    top_genres = exploded["genre"].value_counts().head(12).index.tolist()
    exploded = exploded[exploded["genre"].isin(top_genres)]

    fig = go.Figure()
    for i, genre in enumerate(top_genres):
        genre_data = exploded[exploded["genre"] == genre]["vote_average"]
        fig.add_trace(go.Box(
            y=genre_data,
            name=genre,
            marker_color=COLORS["gradient"][i % len(COLORS["gradient"])],
            boxpoints="outliers",
            line=dict(width=1.5),
        ))

    fig.update_layout(
        yaxis_title="Rating",
        showlegend=False,
        height=500,
    )
    return _style_figure(fig, "📊 Rating Distribution by Genre")


def budget_vs_revenue_chart(df):
    """Scatter plot of budget vs revenue with genre coloring."""
    if "budget" not in df.columns or "revenue" not in df.columns:
        return go.Figure()

    filtered = df[(df["budget"] > 1000000) & (df["revenue"] > 1000000)].copy()
    if filtered.empty:
        return go.Figure()

    filtered["primary_genre"] = filtered["genres"].apply(
        lambda x: x.split(", ")[0] if pd.notna(x) and x else "Unknown"
    )

    fig = px.scatter(
        filtered,
        x="budget",
        y="revenue",
        color="primary_genre",
        size="vote_average",
        hover_name="title",
        hover_data={"budget": ":$,.0f", "revenue": ":$,.0f", "vote_average": ":.1f"},
        opacity=0.7,
        size_max=15,
        color_discrete_sequence=COLORS["gradient"],
        template=PLOTLY_TEMPLATE,
    )

    # Add break-even line
    max_val = max(filtered["budget"].max(), filtered["revenue"].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(dash="dash", color="rgba(255,255,255,0.3)", width=1),
        name="Break Even",
        showlegend=True,
    ))

    fig.update_layout(
        xaxis_title="Budget ($)",
        yaxis_title="Revenue ($)",
        height=550,
    )
    return _style_figure(fig, "💰 Budget vs Revenue")


def popularity_treemap(df):
    """Treemap of genres by total popularity."""
    if "genres" not in df.columns or "popularity" not in df.columns:
        return go.Figure()

    exploded = df.assign(genre=df["genres"].str.split(", ")).explode("genre")
    exploded = exploded[exploded["genre"].notna() & (exploded["genre"] != "")]

    genre_pop = exploded.groupby("genre").agg(
        total_popularity=("popularity", "sum"),
        movie_count=("movie_id", "count"),
        avg_rating=("vote_average", "mean")
    ).reset_index()

    genre_pop = genre_pop.nlargest(15, "total_popularity")

    fig = go.Figure(go.Treemap(
        labels=genre_pop["genre"],
        parents=[""] * len(genre_pop),
        values=genre_pop["total_popularity"],
        text=[f"{c} movies<br>Avg: {r:.1f}⭐" for c, r in
              zip(genre_pop["movie_count"], genre_pop["avg_rating"])],
        textinfo="label+text",
        marker=dict(
            colors=genre_pop["avg_rating"],
            colorscale=[[0, "#4A9EFF"], [0.5, "#F5C518"], [1, "#E50914"]],
            line=dict(width=2, color=COLORS["bg_dark"]),
        ),
        hovertemplate="<b>%{label}</b><br>Popularity: %{value:,.0f}<br>%{text}<extra></extra>",
    ))

    fig.update_layout(height=500)
    return _style_figure(fig, "🔥 Genre Popularity Treemap")


def runtime_distribution_chart(df):
    """Violin plot of movie runtime distribution."""
    if "runtime" not in df.columns:
        return go.Figure()

    filtered = df[(df["runtime"] > 30) & (df["runtime"] < 300)]

    fig = go.Figure(go.Violin(
        y=filtered["runtime"],
        box_visible=True,
        meanline_visible=True,
        fillcolor=COLORS["accent"],
        opacity=0.7,
        line_color=COLORS["text"],
        name="Runtime",
    ))

    fig.update_layout(yaxis_title="Runtime (minutes)", height=400)
    return _style_figure(fig, "⏱️ Runtime Distribution")


def generate_wordcloud_figure(df):
    """Generate a word cloud from movie overviews. Returns a matplotlib figure."""
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        import matplotlib

        matplotlib.use("Agg")

        text = " ".join(df["overview"].dropna().tolist())
        if not text.strip():
            return None

        wc = WordCloud(
            width=1000,
            height=500,
            background_color="#0D1117",
            colormap="magma",
            max_words=150,
            contour_width=0,
            min_font_size=10,
            max_font_size=80,
            prefer_horizontal=0.7,
        ).generate(text)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        fig.patch.set_facecolor("#0D1117")
        plt.tight_layout(pad=0)
        return fig
    except ImportError:
        return None
