import streamlit as st
import time
import json
import os
from datetime import date, timedelta

st.set_page_config(page_title="Gym Tracker", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0a0a; }
    .block-container { padding: 2rem 2rem; max-width: 800px; margin: 0 auto; }
    .stButton>button { background-color: #8b1a1a; color: #ffffff; border: none; font-weight: 600; width: 100%; border-radius: 10px; padding: 0.6rem 1rem; }
    .stButton>button:hover { background-color: #c41e1e; }
    .stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>div { background-color: #111111; color: white; border: 0.5px solid #1a1a1a; border-radius: 10px; }
    .stSlider [data-baseweb="slider"] [role="slider"] { background-color: #8b1a1a !important; }
    .stSlider [data-baseweb="slider"] div[data-testid="stSliderTrackFill"] { background-color: #8b1a1a !important; }
    label { color: #999999 !important; font-size: 11px !important; letter-spacing: 0.08em; text-transform: uppercase; }
    h1 { color: white !important; font-weight: 600 !important; font-size: 28px !important; }
    h3 { color: #c41e1e !important; font-weight: 600 !important; font-size: 11px !important; letter-spacing: 0.1em; text-transform: uppercase; }
    p { color: #999999; font-size: 14px; }
    .stAlert { background-color: #0f1a0a; border: 0.5px solid #166534; color: #86efac; border-radius: 10px; }
    div[data-testid="metric-container"] { background-color: #111111; border: 0.5px solid #1a1a1a; border-radius: 12px; padding: 1.2rem; }
    div[data-testid="metric-container"] label { color: #555555 !important; font-size: 10px !important; }
    div[data-testid="metric-container"] [data-testid="metric-value"] { color: white !important; font-size: 24px !important; font-weight: 600 !important; }
    hr { border-color: #1a1a1a !important; }
    .stProgress > div > div { background-color: #8b1a1a; }
    </style>
""", unsafe_allow_html=True)

# list of exercises for the dropdown
EXERCISES = sorted([
    "Bench press", "Incline bench press", "Shoulder press",
    "Tricep pushdown", "Lateral raise", "Chest fly",
    "Pull up", "Lat pulldown", "Barbell row", "Bicep curl",
    "Squat", "Romanian deadlift", "Leg press", "Leg curl",
    "Hip thrust", "Calf raise", "Face pull", "Rear delt fly"
])

DATA_FILE = "gym_data.json"

# reads save file, returns empty structure if file doesn't exist
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"prs": {}}

# writes data to save file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# epley formula — estimates 1 rep max
def calc_1rm(weight, reps):
    return round(weight * (1 + reps / 30), 1)

# load saved data
data = load_data()
today = str(date.today())

# wipe log if it's a new day
if "last_date" not in st.session_state:
    st.session_state.last_date = today
if st.session_state.last_date != today:
    st.session_state.log = []
    st.session_state.last_date = today

# set up log and prs in memory
if "log" not in st.session_state:
    st.session_state.log = []
if "prs" not in st.session_state:
    st.session_state.prs = data.get("prs", {})

# ---- HEADER ----
st.title("Gym Tracker")
st.caption(date.today().strftime("%A, %B %d · %Y"))
st.divider()

# ---- SPLIT SELECTOR ----
st.subheader("TODAY'S SPLIT")
# slider to pick what day it is
split = st.select_slider(" ", options=["Push", "Pull", "Legs", "Rest"])
st.divider()

# ---- LOG A SET ----
st.subheader("LOG A SET")
# searchable dropdown
exercise_name = st.selectbox("Exercise", EXERCISES)

# three inputs side by side
col1, col2, col3 = st.columns(3)
with col1:
    weight = st.number_input("Weight (lbs)", min_value=0)
with col2:
    sets = st.number_input("Sets", min_value=0)
with col3:
    reps = st.number_input("Reps", min_value=0)

# live 1rm estimate
if weight > 0 and reps > 0:
    st.caption(f"Estimated 1RM → {calc_1rm(weight, reps)} lbs")

if st.button("Log set"):
    # block duplicate weight on same exercise
    duplicate = next((e for e in st.session_state.log
                     if e["exercise"] == exercise_name and e["weight"] == weight), None)
    if duplicate:
        st.warning(f"Already logged {weight}lbs on {exercise_name}.")
    else:
        entry = {"exercise": exercise_name, "weight": weight, "sets": sets, "reps": reps}
        st.session_state.log.append(entry)
        # check if new PR
        if exercise_name not in st.session_state.prs or weight > st.session_state.prs[exercise_name]:
            prev = st.session_state.prs.get(exercise_name, 0)
            st.session_state.prs[exercise_name] = weight
            data["prs"][exercise_name] = weight
            save_data(data)
            if prev > 0:
                st.success(f"★ New PR — {weight}lbs on {exercise_name}!")

st.divider()

# ---- TODAY'S LOG ----
st.subheader("TODAY'S LOG")
if st.session_state.log:
    for i, entry in enumerate(st.session_state.log):
        # check if this entry is a PR
        is_pr = entry["exercise"] in st.session_state.prs and entry["weight"] == st.session_state.prs[entry["exercise"]]
        c1, c2 = st.columns([4, 1])
        with c1:
            tag = "★ " if is_pr else ""
            st.markdown(f"{'🔴' if is_pr else '⚪'} **{tag}{entry['exercise']}** — {entry['weight']}lbs · {entry['sets']} sets · {entry['reps']} reps")
        with c2:
            # unique key for each delete button
            if st.button("✕", key=f"del_{i}"):
                st.session_state.log.pop(i)
                st.rerun()
else:
    st.caption("Nothing logged yet.")

st.divider()

# ---- ALL TIME PRS ----
st.subheader("ALL TIME PRS")
if st.session_state.prs:
    # display in 3 columns
    cols = st.columns(3)
    for i, (ex, w) in enumerate(st.session_state.prs.items()):
        cols[i % 3].metric(ex, f"{w} lbs")
else:
    st.caption("No PRs yet.")

st.divider()

# ---- REST TIMER ----
st.subheader("REST TIMER")
rest_time = st.select_slider("Duration", options=[30, 60, 90, 120, 180], value=90)
progress_bar = st.progress(0)
if st.button("Start timer"):
    timer_placeholder = st.empty()
    # counts down one second at a time
    for i in range(rest_time, 0, -1):
        mins = i // 60
        secs = i % 60
        timer_placeholder.markdown(f"## {mins}:{secs:02d}")
        progress_bar.progress((rest_time - i) / rest_time)
        time.sleep(1)
    timer_placeholder.markdown("## Done.")
    progress_bar.progress(1.0)