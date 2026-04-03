import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Fitness Analytics Dashboard", layout="wide")

DATA_DIR = "data"
MEALS_FILE = os.path.join(DATA_DIR, "meals.csv")
WORKOUTS_FILE = os.path.join(DATA_DIR, "workouts.csv")
WEIGHTS_FILE = os.path.join(DATA_DIR, "weights.csv")


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(MEALS_FILE):
        pd.DataFrame(columns=["date", "meal_name", "calories", "protein", "carbs", "fat"]).to_csv(
            MEALS_FILE, index=False
        )

    if not os.path.exists(WORKOUTS_FILE):
        pd.DataFrame(columns=["date", "exercise", "muscle_group", "sets", "reps", "weight"]).to_csv(
            WORKOUTS_FILE, index=False
        )

    if not os.path.exists(WEIGHTS_FILE):
        pd.DataFrame(columns=["date", "body_weight"]).to_csv(
            WEIGHTS_FILE, index=False
        )


def load_data():
    meals = pd.read_csv(MEALS_FILE)
    workouts = pd.read_csv(WORKOUTS_FILE)
    weights = pd.read_csv(WEIGHTS_FILE)

    if not meals.empty:
        meals["date"] = pd.to_datetime(meals["date"])
    if not workouts.empty:
        workouts["date"] = pd.to_datetime(workouts["date"])
    if not weights.empty:
        weights["date"] = pd.to_datetime(weights["date"])

    return meals, workouts, weights


def save_row(file_path, row_dict):
    df = pd.read_csv(file_path)
    df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df.to_csv(file_path, index=False)


def get_today_totals(meals_df):
    if meals_df.empty:
        return 0, 0
    today = pd.Timestamp(date.today())
    today_meals = meals_df[meals_df["date"] == today]
    calories = today_meals["calories"].sum() if not today_meals.empty else 0
    protein = today_meals["protein"].sum() if not today_meals.empty else 0
    return calories, protein


def get_weekly_workouts(workouts_df):
    if workouts_df.empty:
        return 0
    today = pd.Timestamp(date.today())
    week_start = today - pd.Timedelta(days=6)
    weekly = workouts_df[(workouts_df["date"] >= week_start) & (workouts_df["date"] <= today)]
    return len(weekly)


def generate_insights(meals_df, workouts_df, weights_df):
    insights = []

    if not meals_df.empty:
        last_7_days = pd.Timestamp(date.today()) - pd.Timedelta(days=6)
        recent_meals = meals_df[meals_df["date"] >= last_7_days]

        if not recent_meals.empty:
            avg_protein = recent_meals.groupby("date")["protein"].sum().mean()
            avg_calories = recent_meals.groupby("date")["calories"].sum().mean()

            if avg_protein < 120:
                insights.append(
                    f"Average protein over the last 7 days is {avg_protein:.0f}g, which may be low for muscle recovery."
                )

            if avg_calories > 3000:
                insights.append(
                    f"Average calories over the last 7 days is {avg_calories:.0f}, which may indicate a calorie surplus."
                )

    if not workouts_df.empty:
        last_7_days = pd.Timestamp(date.today()) - pd.Timedelta(days=6)
        recent_workouts = workouts_df[workouts_df["date"] >= last_7_days]

        if not recent_workouts.empty:
            muscle_counts = recent_workouts["muscle_group"].value_counts()

            if "Legs" not in muscle_counts.index:
                insights.append("No leg workouts were logged in the last 7 days. Consider adding lower body training.")

            if muscle_counts.get("Chest", 0) + muscle_counts.get("Shoulders", 0) > muscle_counts.get("Back", 0) + 1:
                insights.append("Upper-body pushing volume appears higher than back volume. Consider balancing your training.")

    if not weights_df.empty and len(weights_df) >= 2:
        recent_weights = weights_df.sort_values("date").tail(7)
        if len(recent_weights) >= 2:
            first_weight = recent_weights.iloc[0]["body_weight"]
            last_weight = recent_weights.iloc[-1]["body_weight"]

            if last_weight > first_weight + 1:
                insights.append(
                    f"Body weight increased from {first_weight:.1f} to {last_weight:.1f} over recent entries."
                )
            elif last_weight < first_weight - 1:
                insights.append(
                    f"Body weight decreased from {first_weight:.1f} to {last_weight:.1f} over recent entries."
                )

    if not insights:
        insights.append("Not enough data yet for strong insights. Keep logging meals, workouts, and weight.")

    return insights


ensure_data_files()
meals_df, workouts_df, weights_df = load_data()

st.title("Fitness Analytics Dashboard")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Log Meal", "Log Workout", "Log Weight", "Insights"]
)

if page == "Dashboard":
    calories_today, protein_today = get_today_totals(meals_df)
    weekly_workouts = get_weekly_workouts(workouts_df)
    latest_weight = weights_df.sort_values("date").iloc[-1]["body_weight"] if not weights_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calories Today", f"{calories_today:.0f}")
    col2.metric("Protein Today", f"{protein_today:.0f}g")
    col3.metric("Workouts This Week", weekly_workouts)
    col4.metric("Latest Weight", f"{latest_weight:.1f}" if latest_weight else "No data")

    st.subheader("Meal Data")
    st.dataframe(meals_df.sort_values("date", ascending=False), use_container_width=True)

    st.subheader("Workout Data")
    if not workouts_df.empty:
        display_workouts = workouts_df.copy()
        display_workouts["volume"] = (
            display_workouts["sets"] * display_workouts["reps"] * display_workouts["weight"]
        )
        st.dataframe(display_workouts.sort_values("date", ascending=False), use_container_width=True)
    else:
        st.dataframe(workouts_df, use_container_width=True)

    st.subheader("Weight Data")
    st.dataframe(weights_df.sort_values("date", ascending=False), use_container_width=True)

    if not meals_df.empty:
        daily_meals = meals_df.groupby("date", as_index=False)[["calories", "protein"]].sum()

        fig_calories = px.line(
            daily_meals,
            x="date",
            y="calories",
            title="Calories Over Time",
            markers=True
        )
        st.plotly_chart(fig_calories, use_container_width=True)

        fig_protein = px.line(
            daily_meals,
            x="date",
            y="protein",
            title="Protein Over Time",
            markers=True
        )
        st.plotly_chart(fig_protein, use_container_width=True)

    if not weights_df.empty:
        fig_weight = px.line(
            weights_df.sort_values("date"),
            x="date",
            y="body_weight",
            title="Body Weight Trend",
            markers=True
        )
        st.plotly_chart(fig_weight, use_container_width=True)

    if not workouts_df.empty:
        workout_chart_df = workouts_df.copy()
        workout_chart_df["volume"] = (
            workout_chart_df["sets"] * workout_chart_df["reps"] * workout_chart_df["weight"]
        )
        daily_volume = workout_chart_df.groupby("date", as_index=False)["volume"].sum()

        fig_volume = px.bar(
            daily_volume,
            x="date",
            y="volume",
            title="Workout Volume Over Time"
        )
        st.plotly_chart(fig_volume, use_container_width=True)

elif page == "Log Meal":
    st.subheader("Log Meal")

    with st.form("meal_form"):
        meal_date = st.date_input("Date", value=date.today())
        meal_name = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0, step=1)
        protein = st.number_input("Protein (g)", min_value=0, step=1)
        carbs = st.number_input("Carbs (g)", min_value=0, step=1)
        fat = st.number_input("Fat (g)", min_value=0, step=1)
        submitted = st.form_submit_button("Save Meal")

        if submitted:
            save_row(
                MEALS_FILE,
                {
                    "date": meal_date,
                    "meal_name": meal_name,
                    "calories": calories,
                    "protein": protein,
                    "carbs": carbs,
                    "fat": fat,
                },
            )
            st.success("Meal saved.")
            st.rerun()

elif page == "Log Workout":
    st.subheader("Log Workout")

    with st.form("workout_form"):
        workout_date = st.date_input("Date", value=date.today())
        exercise = st.text_input("Exercise")
        muscle_group = st.selectbox(
            "Muscle Group",
            ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Other"]
        )
        sets = st.number_input("Sets", min_value=1, step=1)
        reps = st.number_input("Reps", min_value=1, step=1)
        weight = st.number_input("Weight Used", min_value=0.0, step=5.0)
        submitted = st.form_submit_button("Save Workout")

        if submitted:
            save_row(
                WORKOUTS_FILE,
                {
                    "date": workout_date,
                    "exercise": exercise,
                    "muscle_group": muscle_group,
                    "sets": sets,
                    "reps": reps,
                    "weight": weight,
                },
            )
            st.success("Workout saved.")
            st.rerun()

elif page == "Log Weight":
    st.subheader("Log Weight")

    with st.form("weight_form"):
        weight_date = st.date_input("Date", value=date.today())
        body_weight = st.number_input("Body Weight", min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Save Weight")

        if submitted:
            save_row(
                WEIGHTS_FILE,
                {
                    "date": weight_date,
                    "body_weight": body_weight,
                },
            )
            st.success("Weight saved.")
            st.rerun()

elif page == "Insights":
    st.subheader("AI-Style Insights")

    insights = generate_insights(meals_df, workouts_df, weights_df)

    for insight in insights:
        st.info(insight)
