
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Sonora | Music Analytics",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

.stApp {
    background: #101019;
    color: #F5F3FF;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: rgba(16,16,25,0.9);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #F5F3FF !important;
}

p, label, [data-testid="stCaptionContainer"] {
    color: #AAA8BC;
}

[data-testid="stSidebar"] {
    background: #171722;
    border-right: 1px solid #2A293A;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #201F30, #191925);
    border: 1px solid #302D45;
    padding: 20px 22px;
    border-radius: 16px;
    min-height: 135px;
}

[data-testid="stMetricLabel"] {
    color: #AAA8BC !important;
}

[data-testid="stMetricValue"] {
    color: #C4B5FD !important;
    font-family: 'Space Grotesk', sans-serif;
}

[data-testid="stMetricDelta"] {
    color: #A7F3D0 !important;
}

[data-testid="stTabs"] button {
    color: #AAA8BC;
    font-weight: 600;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #C4B5FD !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #302D45;
    border-radius: 12px;
}

.stButton button, .stDownloadButton button {
    border-radius: 10px;
    border: 1px solid #7054CF;
    background: #7657DB;
    color: white;
    font-weight: 600;
}

.stButton button:hover, .stDownloadButton button:hover {
    background: #8B70EC;
    border-color: #A78BFA;
    color: white;
}

hr {
    border-color: #302D45;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

.hero {
    background: linear-gradient(115deg, #282044 0%, #1B1A2B 55%, #171725 100%);
    border: 1px solid #38304F;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 26px;
}

.hero-kicker {
    color: #C4B5FD;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 700;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 4vw, 42px);
    line-height: 1.15;
    color: #FFFFFF;
    font-weight: 700;
    margin: 12px 0;
}

.hero-description {
    color: #B5B1C9;
    font-size: 15px;
    max-width: 650px;
    line-height: 1.7;
}

.section-label {
    color: #A78BFA;
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 5px;
}

.small-note {
    background: #1B1A29;
    border: 1px solid #302D45;
    padding: 14px 16px;
    border-radius: 12px;
    color: #AAA8BC;
    font-size: 13px;
}

footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA LOADER
# ==========================================

REQUIRED_COLUMNS = [
    "spotify_track_uri",
    "ts",
    "ms_played",
    "track_name",
    "artist_name",
    "skipped"
]


@st.cache_data
def load_data(file_bytes):
    data = pd.read_csv(BytesIO(file_bytes))

    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    data["ts"] = pd.to_datetime(
        data["ts"], errors="coerce"
    )

    data["ms_played"] = pd.to_numeric(
        data["ms_played"], errors="coerce"
    )

    data["skipped"] = (
        data["skipped"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
    )

    data = data.dropna(
        subset=[
            "ts", "spotify_track_uri",
            "track_name", "ms_played"
        ]
    ).copy()

    data = data[data["ms_played"] >= 0].copy()

    data["minutes_played"] = data["ms_played"] / 60000
    data["date"] = data["ts"].dt.date

    return data


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown("## 🎧 SONORA")
    st.caption("PERSONAL MUSIC ANALYTICS")
    st.divider()

    st.markdown("### Your listening data")

    uploaded_file = st.file_uploader(
        "Upload Spotify history",
        type=["csv"],
        help="Choose your Spotify listening-history CSV."
    )

    st.caption(
        "Your CSV is processed by this app. "
        "Avoid uploading listening data you do not wish to share."
    )

if uploaded_file is None:
    st.markdown("""
    <div class="hero">
        <div class="hero-kicker">PERSONAL MUSIC ANALYTICS</div>
        <div class="hero-title">Your listening,<br>decoded.</div>
        <div class="hero-description">
            Discover your music habits, explore repeated tracks,
            understand skip behaviour, and investigate how your
            listening changes over time.
            Upload your Spotify listening-history CSV in the sidebar
            to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("Upload your spotify_data.csv file in the sidebar.")
    st.stop()

try:
    df = load_data(uploaded_file.getvalue())
except Exception as error:
    st.error(f"Unable to load the CSV: {error}")
    st.stop()

if df.empty:
    st.error("No usable listening records were found.")
    st.stop()


# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <div class="hero-kicker">YOUR PERSONAL LISTENING REPORT</div>
    <div class="hero-title">Your listening,<br>decoded.</div>
    <div class="hero-description">
        A closer look at your listening habits, favourite tracks,
        repetition patterns, and skip behaviour.
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# FILTERS
# ==========================================

with st.sidebar:
    st.divider()
    st.markdown("### Filters")

    artists = sorted(
        df["artist_name"].dropna().astype(str).unique().tolist()
    )

    selected_artists = st.multiselect(
        "Artists",
        options=artists,
        default=[]
    )

    min_date = df["ts"].min().date()
    max_date = df["ts"].max().date()

    date_range = st.date_input(
        "Listening date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

filtered = df.copy()

if selected_artists:
    filtered = filtered[
        filtered["artist_name"].isin(selected_artists)
    ]

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["date"].between(start_date, end_date)
    ]

if filtered.empty:
    st.warning("No listening events match your filters.")
    st.stop()


# ==========================================
# METRICS
# ==========================================

st.markdown('<div class="section-label">AT A GLANCE</div>',
            unsafe_allow_html=True)
st.header("Your listening overview")

total_events = len(filtered)
unique_tracks = filtered["spotify_track_uri"].nunique()

repeat_rate = (
    (total_events - unique_tracks) / total_events * 100
)

valid_skips = filtered["skipped"].dropna()

skip_rate = (
    valid_skips.mean() * 100
    if len(valid_skips) else 0
)

total_hours = filtered["ms_played"].sum() / 3_600_000

c1, c2, c3, c4 = st.columns(4)

c1.metric("Listening events", f"{total_events:,}")
c2.metric("Unique tracks", f"{unique_tracks:,}")
c3.metric("Repeat rate", f"{repeat_rate:.1f}%")
c4.metric("Skip rate", f"{skip_rate:.1f}%")

st.caption(
    f"{total_hours:.1f} hours of recorded listening · "
    f"{filtered['artist_name'].nunique():,} distinct artists"
)

st.divider()


# ==========================================
# TABS
# ==========================================

overview_tab, tracks_tab, behaviour_tab, history_tab = st.tabs([
    "◈  Overview",
    "♫  Top tracks",
    "↻  Listening behaviour",
    "◷  History & export"
])


# ==========================================
# OVERVIEW TAB
# ==========================================

with overview_tab:
    left, right = st.columns([1.5, 1], gap="large")

    with left:
        st.subheader("Listening activity")

        daily = filtered.groupby("date").size()
        daily.index = pd.to_datetime(daily.index)

        st.line_chart(
            daily,
            x_label="Date",
            y_label="Listening events",
            color="#A78BFA"
        )

    with right:
        st.subheader("Skip breakdown")

        skip_counts = (
            filtered["skipped"]
            .value_counts()
            .reindex([False, True], fill_value=0)
        )

        skip_chart = pd.DataFrame({
            "Listening outcome": [
                "Not skipped",
                "Skipped"
            ],
            "Events": [
                int(skip_counts.loc[False]),
                int(skip_counts.loc[True])
            ]
        })
        
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("#1B1A29")
        ax.set_facecolor("#1B1A29")

        ax.bar(
            ["Not skipped", "Skipped"],
            [skip_counts.loc[False], skip_counts.loc[True]],
            color=["#8B7BE8", "#E879A9"],
            width=0.6
        )

        ax.tick_params(colors="#B5B1C9")
        ax.set_ylabel("Listening events", color="#B5B1C9")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#454057")
        ax.set_title("Recorded skip status", color="#F5F3FF")

        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.markdown("""
    <div class="small-note">
        <strong>How to read this:</strong> Repetition and skipping
        can help describe listening behaviour. Neither one alone
        establishes that a listener is experiencing music fatigue.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# TOP TRACKS TAB
# ==========================================

with tracks_tab:
    st.subheader("Your most played tracks")
    st.caption("Ranked by the number of recorded listening events.")

    top_tracks = (
        filtered.groupby(
            ["spotify_track_uri", "track_name", "artist_name"],
            dropna=False
        )
        .size()
        .reset_index(name="plays")
        .sort_values("plays", ascending=False)
        .head(10)
    )

    left, right = st.columns([1, 1.3], gap="large")

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
        fig.patch.set_facecolor("#1B1A29")
        ax.set_facecolor("#1B1A29")

        ax.barh(
            chart_data["track_name"].fillna("Unknown"),
            chart_data["plays"],
            color="#9B87F5"
        )

        ax.tick_params(colors="#B5B1C9")
        ax.set_xlabel("Listening events", color="#B5B1C9")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#454057")
        ax.set_title("Most played tracks", color="#F5F3FF")

        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)


# ==========================================
# LISTENING BEHAVIOUR TAB
# ==========================================

with behaviour_tab:
    st.subheader("Repeated listening")

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

    repeated = ordered.dropna(subset=["gap_minutes"]).copy()
    repeated = repeated[repeated["gap_minutes"] >= 0]

    if repeated.empty:
        st.info("No repeated-track intervals were found in this selection.")
    else:
        c1, c2 = st.columns(2)

        c1.metric("Repeat events", f"{len(repeated):,}")
        c2.metric(
            "Average time gap",
            f"{repeated['gap_minutes'].mean():.1f} min"
        )

        gap_data = repeated.loc[
            repeated["gap_minutes"] <= 7 * 24 * 60,
            "gap_minutes"
        ]

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#1B1A29")
        ax.set_facecolor("#1B1A29")

        ax.hist(
            gap_data,
            bins=30,
            color="#9B87F5",
            edgecolor="#242033"
        )

        ax.set_xlabel("Minutes between consecutive plays",
                      color="#B5B1C9")
        ax.set_ylabel("Number of events", color="#B5B1C9")
        ax.tick_params(colors="#B5B1C9")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#454057")
        ax.set_title("Time between plays of the same track",
                     color="#F5F3FF")

        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        st.subheader("Most repeated tracks")

        st.dataframe(
            repeated.groupby(
                ["spotify_track_uri", "track_name", "artist_name"]
            )
            .size()
            .reset_index(name="repeat intervals")
            .sort_values("repeat intervals", ascending=False)
            .head(10)[
                ["track_name", "artist_name", "repeat intervals"]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("""
    <div class="small-note">
        Shorter gaps indicate closer-together recorded plays, not
        necessarily boredom or fatigue. The current analysis does
        not infer a listener's psychological state.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# HISTORY AND EXPORT TAB
# ==========================================

with history_tab:
    st.subheader("Recent listening events")

    recent = (
        filtered[
            [
                "ts", "track_name", "artist_name",
                "minutes_played", "skipped"
            ]
        ]
        .sort_values("ts", ascending=False)
        .head(100)
        .copy()
    )

    recent["minutes_played"] = recent["minutes_played"].round(2)

    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Export your filtered data")

    st.caption(
        "Download the rows matching your selected artists and date range."
    )

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        "↓  Download filtered CSV",
        data=csv_bytes,
        file_name="sonora_listening_report.csv",
        mime="text/csv",
        use_container_width=False
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.markdown("""
<div style="text-align:center; padding:12px 0 4px;">
    <div style="color:#A78BFA; font-weight:700; letter-spacing:3px;">
        SONORA
    </div>
    <div style="color:#77748B; font-size:12px; margin-top:8px;">
        PERSONAL MUSIC ANALYTICS · LISTEN BETTER, UNDERSTAND MORE
    </div>
</div>
""", unsafe_allow_html=True)
