
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# PAGE CONFIGURATION
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


# Replace your current dataset path/loading section with this.

uploaded_file = st.sidebar.file_uploader(
    "Upload your Spotify listening history CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload spotify_data.csv in the sidebar to use the dashboard.")
    st.stop()

@st.cache_data
def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file)

    required_columns = [
        "spotify_track_uri",
        "ts",
        "ms_played",
        "track_name",
        "artist_name",
        "skipped"
    ]

    missing = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    data["ts"] = pd.to_datetime(data["ts"], errors="coerce")
    data["ms_played"] = pd.to_numeric(
        data["ms_played"], errors="coerce"
    )
    data["skipped"] = (
        data["skipped"].astype(str).str.lower()
        .map({"true": True, "false": False})
    )

    data = data.dropna(
        subset=["ts", "spotify_track_uri", "track_name"]
    ).copy()

    data = data[data["ms_played"] >= 0].copy()
    data["minutes_played"] = data["ms_played"] / 60000
    data["date"] = data["ts"].dt.date

    return data

df = load_data(uploaded_file)



# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_data(path, modified_time):
    data = pd.read_csv(path)

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
        .str.lower()
        .map({"true": True, "false": False})
    )

    data = data.dropna(
        subset=["ts", "spotify_track_uri", "track_name"]
    ).copy()

    data = data[data["ms_played"] >= 0].copy()

    data["minutes_played"] = data["ms_played"] / 60000
    data["date"] = data["ts"].dt.date

    return data


if not DATA_PATH.exists():
    st.error(
        "Dataset not found. Put spotify_data.csv "
        "inside the project's data folder."
    )
    st.stop()

df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)


# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.header("Dashboard Filters")

artists = sorted(
    df["artist_name"].dropna().unique().tolist()
)

selected_artists = st.sidebar.multiselect(
    "Filter by artist",
    artists,
    default=[]
)

if selected_artists:
    filtered = df[
        df["artist_name"].isin(selected_artists)
    ].copy()
else:
    filtered = df.copy()

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# ==========================================
# KEY METRICS
# ==========================================

total_plays = len(filtered)

unique_tracks = filtered["spotify_track_uri"].nunique()

repeat_rate = (
    (total_plays - unique_tracks) / total_plays * 100
)

skip_rate = filtered["skipped"].mean() * 100

total_hours = filtered["ms_played"].sum() / 3600000

c1, c2, c3, c4 = st.columns(4)

c1.metric("Listening Events", f"{total_plays:,}")
c2.metric("Unique Tracks", f"{unique_tracks:,}")
c3.metric("Repeat Rate", f"{repeat_rate:.1f}%")
c4.metric("Skip Rate", f"{skip_rate:.1f}%")

st.metric("Total Recorded Listening Time", f"{total_hours:.1f} hours")

st.divider()


# ==========================================
# TOP TRACKS
# ==========================================

st.subheader("🎵 Most Played Tracks")

top_tracks = (
    filtered.groupby(["spotify_track_uri", "track_name", "artist_name"])
    .size()
    .reset_index(name="plays")
    .sort_values("plays", ascending=False)
    .head(10)
)

left, right = st.columns(2)

with left:
    st.dataframe(
        top_tracks[
            ["track_name", "artist_name", "plays"]
        ].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

with right:
    chart_data = top_tracks.sort_values("plays")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(chart_data["track_name"], chart_data["plays"])
    ax.set_xlabel("Listening events")
    ax.set_title("Top 10 Tracks")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# ==========================================
# LISTENING ACTIVITY OVER TIME
# ==========================================

st.subheader("📈 Listening Activity Over Time")

daily_activity = (
    filtered.groupby("date")
    .size()
    .reset_index(name="listening_events")
)

daily_activity["date"] = pd.to_datetime(daily_activity["date"])

st.line_chart(
    daily_activity.set_index("date")["listening_events"],
    x_label="Date",
    y_label="Listening events"
)


# ==========================================
# SKIP ANALYSIS
# ==========================================

st.subheader("⏭️ Skip Behaviour")

skip_summary = (
    filtered["skipped"]
    .value_counts()
    .reindex([False, True], fill_value=0)
)

skip_table = pd.DataFrame({
    "Listening outcome": ["Not marked skipped", "Marked skipped"],
    "Events": [
        int(skip_summary.loc[False]),
        int(skip_summary.loc[True])
    ]
})

left, right = st.columns(2)

with left:
    st.dataframe(skip_table, hide_index=True, use_container_width=True)

with right:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(
        skip_table["Listening outcome"],
        skip_table["Events"]
    )
    ax.set_ylabel("Number of events")
    ax.set_title("Skip Summary")
    ax.tick_params(axis="x", rotation=10)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# ==========================================
# REPEATED TRACKS AND TIME GAPS
# ==========================================

st.subheader("🔁 Repeated Listening Analysis")

ordered = filtered.sort_values(
    ["spotify_track_uri", "ts"]
).copy()

ordered["previous_play"] = (
    ordered.groupby("spotify_track_uri")["ts"].shift(1)
)

ordered["gap_minutes"] = (
    (ordered["ts"] - ordered["previous_play"])
    .dt.total_seconds() / 60
)

repeat_events = ordered.dropna(subset=["gap_minutes"]).copy()

if not repeat_events.empty:
    avg_gap = repeat_events["gap_minutes"].mean()

    st.metric(
        "Average Time Between Plays of the Same Track",
        f"{avg_gap:.1f} minutes"
    )

    st.caption(
        "This is the average gap between consecutive recorded plays "
        "of each track, within the selected data."
    )

    gap_data = repeat_events.loc[
        repeat_events["gap_minutes"].between(0, 7 * 24 * 60),
        "gap_minutes"
    ]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(gap_data, bins=30, edgecolor="black")
    ax.set_xlabel("Minutes since previous play")
    ax.set_ylabel("Number of repeat events")
    ax.set_title("Time Between Plays of the Same Track")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Not enough repeated-track events to calculate time gaps.")


# ==========================================
# LISTENING DURATION
# ==========================================

st.subheader("⏱️ Listening Duration")

avg_minutes = filtered["minutes_played"].mean()

st.metric(
    "Average Recorded Duration per Event",
    f"{avg_minutes:.2f} minutes"
)

st.dataframe(
    filtered[
        ["ts", "track_name", "artist_name", "minutes_played", "skipped"]
    ].sort_values("ts", ascending=False).head(20),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.caption(
    "Note: Repetition and skipping are behavioural signals, not proof "
    "of psychological music fatigue. This dashboard analyses listening "
    "history; it does not yet make machine-learning predictions."
)
