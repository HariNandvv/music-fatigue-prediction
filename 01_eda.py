
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. LOAD DATASET
# ==========================================

file_path = "data/spotify_data.csv"

print("Loading Spotify dataset...")

df = pd.read_csv(file_path)

print("\nFirst five records:")
print(df.head())

print("\nDataset shape:", df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())


# ==========================================
# 2. DATA CLEANING
# ==========================================

df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

df = df.dropna(
    subset=["ts", "spotify_track_uri", "track_name"]
).copy()

# Remove records with invalid listening duration.
df = df[df["ms_played"] >= 0].copy()

print("\nRecords after cleaning:", len(df))


# ==========================================
# 3. TOP 10 MOST PLAYED SONGS
# ==========================================

song_counts = (
    df.groupby(["spotify_track_uri", "track_name"])
      .size()
      .reset_index(name="play_count")
      .sort_values("play_count", ascending=False)
)

print("\nTop 10 most played songs:")
print(song_counts.head(10).to_string(index=False))

top_songs = song_counts.head(10).sort_values("play_count")

plt.figure(figsize=(10, 6))
plt.barh(
    top_songs["track_name"],
    top_songs["play_count"]
)
plt.xlabel("Number of listening events")
plt.ylabel("Song")
plt.title("Top 10 Most Played Songs")
plt.tight_layout()
plt.show()


# ==========================================
# 4. REPEATED LISTENING ANALYSIS
# ==========================================

# This dataset appears to represent one listening history,
# rather than multiple identified users.

total_plays = len(df)
unique_tracks = df["spotify_track_uri"].nunique()

repetition_rate = (
    (total_plays - unique_tracks) / total_plays * 100
    if total_plays else 0
)

print("\nTotal listening events:", total_plays)
print("Unique tracks:", unique_tracks)
print("Repeated-listening rate:", round(repetition_rate, 2), "%")

# Top repeated tracks
print("\nMost frequently played tracks:")
print(song_counts.head(10).to_string(index=False))


# ==========================================
# 5. TIME BETWEEN PLAYS OF THE SAME SONG
# ==========================================

df = df.sort_values(["spotify_track_uri", "ts"]).copy()

df["minutes_since_previous_play"] = (
    df.groupby("spotify_track_uri")["ts"]
      .diff()
      .dt.total_seconds()
      .div(60)
)

time_gaps = df["minutes_since_previous_play"].dropna()

print("\nTime between plays of the same song (minutes):")
print(time_gaps.describe())

plt.figure(figsize=(9, 5))
plt.hist(time_gaps[time_gaps <= 7 * 24 * 60], bins=30,
         edgecolor="black")
plt.xlabel("Minutes since previous play")
plt.ylabel("Number of repeated-track events")
plt.title("Time Between Plays of the Same Song (within 7 days)")
plt.tight_layout()
plt.show()


# ==========================================
# 6. SKIP ANALYSIS
# ==========================================

skip_counts = df["skipped"].value_counts().sort_index()

print("\nSkip counts:")
print(skip_counts)

skip_rate = df["skipped"].mean() * 100

print("Overall skip rate:", round(skip_rate, 2), "%")

plt.figure(figsize=(7, 5))
plt.bar(
    ["Not skipped", "Skipped"],
    [
        (df["skipped"] == False).sum(),
        (df["skipped"] == True).sum()
    ]
)
plt.ylabel("Number of listening events")
plt.title("Skipped vs Not Skipped")
plt.tight_layout()
plt.show()


# ==========================================
# 7. LISTENING DURATION ANALYSIS
# ==========================================

df["minutes_played"] = df["ms_played"] / 60000

print("\nListening duration in minutes:")
print(df["minutes_played"].describe())

# Average recorded duration by song
song_duration = (
    df.groupby("track_name")["minutes_played"]
      .mean()
      .sort_values(ascending=False)
)

print("\nSongs with the highest average recorded listening duration:")
print(song_duration.head(10))


# ==========================================
# 8. LISTENING ACTIVITY OVER TIME
# ==========================================

df["date"] = df["ts"].dt.date

daily_plays = df.groupby("date").size()

plt.figure(figsize=(12, 5))
plt.plot(daily_plays.index, daily_plays.values)
plt.xlabel("Date")
plt.ylabel("Listening events")
plt.title("Listening Activity Over Time")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


print("\nEDA completed successfully!")
