
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Music Fatigue Analytics",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Music Fatigue Detection")
st.caption(
    "Explore your listening habits, repeated tracks, "
    "skips, and listening activity."
)

st.markdown(
    """
    This dashboard analyses your Spotify listening history
    to explore repetition, listening duration, and skip behaviour.
    """
)


# ==========================================
# 2. UPLOAD DATASET
# ==========================================

st.sidebar.header("Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload your Spotify listening history CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info(
        "Upload your spotify_data.csv file using the sidebar "
        "to start exploring your listening history."
    )
    st.stop()


# ==========================================
# 3. LOAD AND VALIDATE DATA
# ==========================================

@st.cache_data
def load_data(file_bytes):
    data = pd.read_csv(BytesIO(file_bytes))

    required_columns = [
        "spotify_track_uri",
        "ts",
        "ms_played",
        "track_name",
        "artist_name",
        "skipped"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    data["ts"] = pd.to_datetime(
        data["ts"],
        errors="coerce"
    )

    data["ms_played"] = pd.to_numeric(
        data["ms_played"],
        errors="coerce"
    )

    data["skipped"] = (
        data["skipped"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "true": True,
            "false": False
        })
    )

    # Remove rows missing essential information.
    data = data.dropna(
        subset=[
            "ts",
            "spotify_track_uri",
            "track_name",
            "ms_played"
        ]
    ).copy()

    data = data[data["ms_played"] >= 0].copy()

    data["minutes_played"] = data["ms_played"] / 60000
    data["date"] = data["ts"].dt.date

    return data


try:
    df = load_data(uploaded_file.getvalue())

except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()


if df.empty:
    st.error("The dataset contains no usable listening records.")
    st.stop()

st.sidebar.success(
    f"Loaded {len(df):,} listening records"
)


# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

artists = sorted(
    df["artist_name"].dropna().astype(str).unique().tolist()
)

selected_artists = st.sidebar.multiselect(
    "Filter by artist",
    options=artists,
    default=[]
)

if selected_artists:
    filtered = df[
        df["artist_name"].isin(selected_artists)
    ].copy()
else:
    filtered = df.copy()

if filtered.empty:
    st.warning("No records match the selected artist filters.")
    st.stop()


# ==========================================
# 5. KEY METRICS
# ==========================================

st.header("📊 Listening Overview")

total_plays = len(filtered)

unique_tracks = filtered["spotify_track_uri"].nunique()

repeat_rate = (
    (total_plays - unique_tracks) / total_plays * 100
    if total_plays > 0
    else 0
)

valid_skip_values = filtered["skipped"].dropna()

skip_rate = (
    valid_skip_values.mean() * 100
    if not valid_skip_values.empty
    else 0
)

total_hours = filtered["ms_played"].sum() / 3600000

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Listening Events",
    f"{total_plays:,}"
)

col2.metric(
    "Unique Tracks",
    f"{unique_tracks:,}"
)

col3.metric(
    "Repeat Rate",
    f"{repeat_rate:.1f}%"
)

col4.metric(
    "Skip Rate",
    f"{skip_rate:.1f}%"
)

st.metric(
    "Total Recorded Listening Time",
    f"{total_hours:.1f} hours"
)

st.caption(
    "Repeat rate measures listening events beyond the number "
    "of unique tracks. It is not a direct measure of music fatigue."
)

st.divider()


# ==========================================
# 6. TOP 10 MOST PLAYED TRACKS
# ==========================================

st.header("🎵 Most Played Tracks")

top_tracks = (
    filtered.groupby(
        [
            "spotify_track_uri",
            "track_name",
            "artist_name"
        ],
        dropna=False
    )
    .size()
    .reset_index(name="plays")
    .sort_values("plays", ascending=False)
    .head(10)
)

left, right = st.columns(2)

with left:
    st.subheader("Top Tracks Table")

    st.dataframe(
        top_tracks[
            ["track_name", "artist_name", "plays"]
        ].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

with right:
    st.subheader("Track Play Counts")

    chart_data = top_tracks.sort_values("plays")

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.barh(
        chart_data["track_name"].fillna("Unknown"),
        chart_data["plays"]
    )

    ax.set_xlabel("Number of listening events")
    ax.set_ylabel("Track")
    ax.set_title("Top 10 Most Played Tracks")

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


st.divider()


# ==========================================
# 7. LISTENING ACTIVITY OVER TIME
# ==========================================

st.header("📈 Listening Activity Over Time")

daily_activity = (
    filtered.groupby("date")
    .size()
    .rename("listening_events")
)

if not daily_activity.empty:
    daily_activity.index = pd.to_datetime(
        daily_activity.index
    )

    st.line_chart(
        daily_activity,
        x_label="Date",
        y_label="Listening Events"
    )
else:
    st.info("No listening activity is available for this filter.")


st.divider()


# ==========================================
# 8. SKIP BEHAVIOUR
# ==========================================

st.header("⏭️ Skip Behaviour")

skip_summary = (
    filtered["skipped"]
    .value_counts()
    .reindex([False, True], fill_value=0)
)

skip_table = pd.DataFrame({
    "Listening Outcome": [
        "Not marked skipped",
        "Marked skipped"
    ],
    "Events": [
        int(skip_summary.loc[False]),
        int(skip_summary.loc[True])
    ]
})

left, right = st.columns(2)

with left:
    st.dataframe(
        skip_table,
        use_container_width=True,
        hide_index=True
    )

with right:
    fig, ax = plt.subplots(figsize=(7, 4))

    ax.bar(
        skip_table["Listening Outcome"],
        skip_table["Events"]
    )

    ax.set_ylabel("Number of Events")
    ax.set_title("Skipped vs Not Skipped")
    ax.tick_params(axis="x", rotation=10)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


st.divider()


# ==========================================
# 9. REPEATED LISTENING AND TIME GAPS
# ==========================================

st.header("🔁 Repeated Listening Analysis")

ordered = filtered.sort_values(
    ["spotify_track_uri", "ts"]
).copy()

ordered["previous_play"] = (
    ordered.groupby("spotify_track_uri")["ts"].shift(1)
)

ordered["gap_minutes"] = (
    (
        ordered["ts"] - ordered["previous_play"]
    ).dt.total_seconds() / 60
)

repeat_events = ordered.dropna(
    subset=["gap_minutes"]
).copy()

if not repeat_events.empty:

    # Exclude negative gaps if timestamps are inconsistent.
    repeat_events = repeat_events[
        repeat_events["gap_minutes"] >= 0
    ]

    if not repeat_events.empty:

        avg_gap = repeat_events["gap_minutes"].mean()

        col1, col2 = st.columns(2)

        col1.metric(
            "Average Gap Between Plays",
            f"{avg_gap:.1f} minutes"
        )

        col2.metric(
            "Repeated-Track Events",
            f"{len(repeat_events):,}"
        )

        st.caption(
            "Time gap is calculated between consecutive recorded "
            "plays of the same track in this listening history."
        )

        gap_data = repeat_events.loc[
            repeat_events["gap_minutes"] <= 7 * 24 * 60,
            "gap_minutes"
        ]

        fig, ax = plt.subplots(figsize=(10, 4))

        ax.hist(
            gap_data,
            bins=30,
            edgecolor="black"
        )

        ax.set_xlabel("Minutes Since Previous Play")
        ax.set_ylabel("Number of Repeat Events")
        ax.set_title(
            "Time Between Plays of the Same Track "
            "(Within Seven Days)"
        )

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("No valid time gaps were found.")

else:
    st.info(
        "Not enough repeated-track events to calculate time gaps."
    )


st.divider()


# ==========================================
# 10. LISTENING DURATION
# ==========================================

st.header("⏱️ Listening Duration")

avg_minutes = filtered["minutes_played"].mean()

col1, col2 = st.columns(2)

col1.metric(
    "Average Recorded Duration per Event",
    f"{avg_minutes:.2f} minutes"
)

col2.metric(
    "Total Recorded Duration",
    f"{total_hours:.1f} hours"
)

st.subheader("Recent Listening Events")

recent_events = (
    filtered[
        [
            "ts",
            "track_name",
            "artist_name",
            "minutes_played",
            "skipped"
        ]
    ]
    .sort_values("ts", ascending=False)
    .head(20)
    .copy()
)

recent_events["minutes_played"] = (
    recent_events["minutes_played"].round(2)
)

st.dataframe(
    recent_events,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 11. DOWNLOAD FILTERED DATA
# ==========================================

st.divider()

st.header("⬇️ Export Data")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Listening Data",
    data=csv_data,
    file_name="filtered_music_listening_data.csv",
    mime="text/csv"
)


# ==========================================
# 12. FOOTER
# ==========================================

st.divider()

st.caption(
    "Music Fatigue Detection — Listening Analytics Dashboard. "
    "Repetition, short listening intervals, and skipping are "
    "behavioural signals, not proof of psychological fatigue. "
    "This dashboard currently performs analytics and does not "
    "yet make machine-learning predictions."
)
