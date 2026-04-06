import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Fitness Analytics Dashboard", layout="wide")


defaults = {
    # Meal form
    "meal_name": "",
    "calories": 0,
    "protein": 0,
    "carbs": 0,
    "fat": 0,

    # Workout form
    "exercise": "",
    "muscle_group": "Chest",
    "sets": 1,
    "reps": 1,
    "weight": 0.0,

    # Weight form
    "body_weight": 0.0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

DATA_DIR = "data"
MEALS_FILE = os.path.join(DATA_DIR, "meals.csv")
WORKOUTS_FILE = os.path.join(DATA_DIR, "workouts.csv")
WEIGHTS_FILE = os.path.join(DATA_DIR, "weights.csv")


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(MEALS_FILE):
        pd.DataFrame(
            columns=["date", "meal_name", "calories", "protein", "carbs", "fat"]
        ).to_csv(MEALS_FILE, index=False)

    if not os.path.exists(WORKOUTS_FILE):
        pd.DataFrame(
            columns=["date", "exercise", "muscle_group", "sets", "reps", "weight"]
        ).to_csv(WORKOUTS_FILE, index=False)

    if not os.path.exists(WEIGHTS_FILE):
        pd.DataFrame(
            columns=["date", "body_weight"]
        ).to_csv(WEIGHTS_FILE, index=False)


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


def overwrite_csv(file_path, df):
    df_to_save = df.copy()

    if "date" in df_to_save.columns:
        df_to_save["date"] = pd.to_datetime(df_to_save["date"]).dt.strftime("%Y-%m-%d")

    df_to_save.to_csv(file_path, index=False)


def get_latest_day_data(df):
    if df.empty:
        return df

    today = pd.Timestamp(date.today())

    if today in df["date"].values:
        return df[df["date"] == today]

    
    latest_date = df["date"].max()
    return df[df["date"] == latest_date]



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
    weekly = workouts_df[
        (workouts_df["date"] >= week_start) & (workouts_df["date"] <= today)
    ]
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

            if avg_calories < 2000:
                insights.append(
                    f"Average calories over the last 7 days is {avg_calories:.0f}, which may be too low to support performance or muscle growth."
                )

    if not workouts_df.empty:
        last_7_days = pd.Timestamp(date.today()) - pd.Timedelta(days=6)
        recent_workouts = workouts_df[workouts_df["date"] >= last_7_days]

        if not recent_workouts.empty:
            muscle_counts = recent_workouts["muscle_group"].value_counts()

            if "Legs" not in muscle_counts.index:
                insights.append(
                    "No leg workouts were logged in the last 7 days. Consider adding lower body training."
                )

            push_count = muscle_counts.get("Chest", 0) + muscle_counts.get("Shoulders", 0)
            back_count = muscle_counts.get("Back", 0)

            if push_count > back_count + 1:
                insights.append(
                    "Upper-body pushing volume appears higher than back volume. Consider balancing your training."
                )

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
        insights.append(
            "Not enough data yet for strong insights. Keep logging meals, workouts, and weight."
        )

    return insights


ensure_data_files()
meals_df, workouts_df, weights_df = load_data()

st.title("Fitness Analytics Dashboard")
st.write("Track nutrition, workouts, and body weight with charts and AI-style insights.")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Log Meal", "Log Workout", "Log Weight", "Manage Data", "Insights"]
)

# -----------------------------

if page == "Dashboard":
    calories_today, protein_today = get_today_totals(meals_df)
    weekly_workouts = get_weekly_workouts(workouts_df)
    latest_weight = (
        weights_df.sort_values("date").iloc[-1]["body_weight"]
        if not weights_df.empty
        else None
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calories Today", f"{calories_today:.0f}")
    col2.metric("Protein Today", f"{protein_today:.0f}g")
    col3.metric("Workouts This Week", weekly_workouts)
    col4.metric("Latest Weight", f"{latest_weight:.1f}" if latest_weight is not None else "No data")

    if not meals_df.empty:
        daily_calories = meals_df.groupby("date")["calories"].sum().tail(7)
        avg_calories_7d = daily_calories.mean() if not daily_calories.empty else 0
        st.metric("Avg Calories (7d)", f"{avg_calories_7d:.0f}")

    st.subheader("Recent Meal Data")
    latest_meals = get_latest_day_data(meals_df)
    st.dataframe(latest_meals, use_container_width=True)
    

    st.subheader("Recent Workout Data")
    if not workouts_df.empty:
        display_workouts = workouts_df.copy()
        display_workouts["volume"] = (
            display_workouts["sets"] * display_workouts["reps"] * display_workouts["weight"]
        )
        latest_workouts = get_latest_day_data(workouts_df)
        st.dataframe(latest_workouts, use_container_width=True)
    else:
        st.dataframe(workouts_df, use_container_width=True)

    st.subheader("Recent Weight Data")
    latest_weights = get_latest_day_data(weights_df)
    st.dataframe(latest_weights, use_container_width=True)

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

    
            st.subheader("Muscle Group Distribution")

    days = st.slider("Show past days", 3, 14, 5)

    if not workouts_df.empty:
        muscle_df = workouts_df.copy()

        cutoff_date = pd.Timestamp(date.today()) - pd.Timedelta(days=days - 1)
        muscle_df = muscle_df[muscle_df["date"] >= cutoff_date]

        muscle_counts = (
            muscle_df["muscle_group"]
            .value_counts()
            .reset_index()
        )

        muscle_counts.columns = ["muscle_group", "count"]

        fig_pie = px.pie(
            muscle_counts,
            names="muscle_group",
            values="count",
            title=f"Muscle Group Distribution (Last {days} Days)"
        )

        st.plotly_chart(fig_pie, use_container_width=True)


elif page == "Log Meal":
    st.subheader("Log Meal")

    with st.form("meal_form", clear_on_submit=True):
        meal_date = st.date_input("Date", value=date.today())
        meal_name = st.text_input("Meal Name", key="meal_name")
        calories = st.number_input("Calories", min_value=0, step=1, key="calories")
        protein = st.number_input("Protein (g)", min_value=0, step=1, key="protein")
        carbs = st.number_input("Carbs (g)", min_value=0, step=1, key="carbs")
        fat = st.number_input("Fat (g)", min_value=0, step=1, key="fat")
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

    with st.form("workout_form", clear_on_submit=True):
        workout_date = st.date_input("Date", value=date.today())
        exercise = st.text_input("Exercise", key="exercise")
        muscle_group = st.selectbox(
            "Muscle Group",
            ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Other"],
            key="muscle_group"
        )
        sets = st.number_input("Sets", min_value=1, step=1, key="sets")
        reps = st.number_input("Reps", min_value=1, step=1, key="reps")
        weight = st.number_input("Weight Used", min_value=0.0, step=5.0, key="weight")
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

    with st.form("weight_form", clear_on_submit=True):
        weight_date = st.date_input("Date", value=date.today())
        body_weight = st.number_input("Body Weight", min_value=0.0, step=0.1, key="body_weight")
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


elif page == "Manage Data":
    st.subheader("Manage Data")
    dataset = st.selectbox("Choose data to manage", ["Meals", "Workouts", "Weights"])

    if dataset == "Meals":
        if meals_df.empty:
            st.info("No meal data to manage.")
        else:
            manage_df = meals_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
            manage_df.insert(0, "row_id", manage_df.index)

            st.dataframe(manage_df, use_container_width=True)

            selected_row = st.selectbox(
                "Select meal row",
                manage_df["row_id"].tolist(),
                format_func=lambda x: f"Row {x} - {manage_df.loc[manage_df['row_id'] == x, 'meal_name'].iloc[0]}"
            )

            selected_data = manage_df[manage_df["row_id"] == selected_row].iloc[0]

            st.markdown("### Edit Meal")
            with st.form("edit_meal_form"):
                edit_date = st.date_input("Date", value=selected_data["date"].date(), key="edit_meal_date")
                edit_meal_name = st.text_input("Meal Name", value=selected_data["meal_name"], key="edit_meal_name")
                edit_calories = st.number_input("Calories", min_value=0, step=1, value=int(selected_data["calories"]), key="edit_calories")
                edit_protein = st.number_input("Protein (g)", min_value=0, step=1, value=int(selected_data["protein"]), key="edit_protein")
                edit_carbs = st.number_input("Carbs (g)", min_value=0, step=1, value=int(selected_data["carbs"]), key="edit_carbs")
                edit_fat = st.number_input("Fat (g)", min_value=0, step=1, value=int(selected_data["fat"]), key="edit_fat")

                col1, col2 = st.columns(2)
                update_clicked = col1.form_submit_button("Update Meal")
                delete_clicked = col2.form_submit_button("Delete Meal")

                if update_clicked:
                    original_df = meals_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df.loc[selected_row, "date"] = pd.to_datetime(edit_date)
                    original_df.loc[selected_row, "meal_name"] = edit_meal_name
                    original_df.loc[selected_row, "calories"] = edit_calories
                    original_df.loc[selected_row, "protein"] = edit_protein
                    original_df.loc[selected_row, "carbs"] = edit_carbs
                    original_df.loc[selected_row, "fat"] = edit_fat

                    overwrite_csv(MEALS_FILE, original_df)
                    st.success("Meal updated.")
                    st.rerun()

                if delete_clicked:
                    original_df = meals_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df = original_df.drop(index=selected_row).reset_index(drop=True)

                    overwrite_csv(MEALS_FILE, original_df)
                    st.success("Meal deleted.")
                    st.rerun()

    elif dataset == "Workouts":
        if workouts_df.empty:
            st.info("No workout data to manage.")
        else:
            manage_df = workouts_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
            manage_df.insert(0, "row_id", manage_df.index)
            manage_df["volume"] = manage_df["sets"] * manage_df["reps"] * manage_df["weight"]

            st.dataframe(manage_df, use_container_width=True)

            selected_row = st.selectbox(
                "Select workout row",
                manage_df["row_id"].tolist(),
                format_func=lambda x: f"Row {x} - {manage_df.loc[manage_df['row_id'] == x, 'exercise'].iloc[0]}"
            )

            selected_data = manage_df[manage_df["row_id"] == selected_row].iloc[0]

            st.markdown("### Edit Workout")
            with st.form("edit_workout_form"):
                edit_date = st.date_input("Date", value=selected_data["date"].date(), key="edit_workout_date")
                edit_exercise = st.text_input("Exercise", value=selected_data["exercise"], key="edit_exercise")
                options = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Other"]
                current_index = options.index(selected_data["muscle_group"]) if selected_data["muscle_group"] in options else 0
                edit_muscle_group = st.selectbox("Muscle Group", options, index=current_index, key="edit_muscle_group")
                edit_sets = st.number_input("Sets", min_value=1, step=1, value=int(selected_data["sets"]), key="edit_sets")
                edit_reps = st.number_input("Reps", min_value=1, step=1, value=int(selected_data["reps"]), key="edit_reps")
                edit_weight = st.number_input("Weight Used", min_value=0.0, step=5.0, value=float(selected_data["weight"]), key="edit_weight")

                col1, col2 = st.columns(2)
                update_clicked = col1.form_submit_button("Update Workout")
                delete_clicked = col2.form_submit_button("Delete Workout")

                if update_clicked:
                    original_df = workouts_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df.loc[selected_row, "date"] = pd.to_datetime(edit_date)
                    original_df.loc[selected_row, "exercise"] = edit_exercise
                    original_df.loc[selected_row, "muscle_group"] = edit_muscle_group
                    original_df.loc[selected_row, "sets"] = edit_sets
                    original_df.loc[selected_row, "reps"] = edit_reps
                    original_df.loc[selected_row, "weight"] = edit_weight

                    overwrite_csv(WORKOUTS_FILE, original_df)
                    st.success("Workout updated.")
                    st.rerun()

                if delete_clicked:
                    original_df = workouts_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df = original_df.drop(index=selected_row).reset_index(drop=True)

                    overwrite_csv(WORKOUTS_FILE, original_df)
                    st.success("Workout deleted.")
                    st.rerun()

    elif dataset == "Weights":
        if weights_df.empty:
            st.info("No weight data to manage.")
        else:
            manage_df = weights_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
            manage_df.insert(0, "row_id", manage_df.index)

            st.dataframe(manage_df, use_container_width=True)

            selected_row = st.selectbox(
                "Select weight row",
                manage_df["row_id"].tolist(),
                format_func=lambda x: f"Row {x} - {manage_df.loc[manage_df['row_id'] == x, 'date'].iloc[0].date()}"
            )

            selected_data = manage_df[manage_df["row_id"] == selected_row].iloc[0]

            st.markdown("### Edit Weight Entry")
            with st.form("edit_weight_form"):
                edit_date = st.date_input("Date", value=selected_data["date"].date(), key="edit_weight_date")
                edit_body_weight = st.number_input(
                    "Body Weight",
                    min_value=0.0,
                    step=0.1,
                    value=float(selected_data["body_weight"]),
                    key="edit_body_weight"
                )

                col1, col2 = st.columns(2)
                update_clicked = col1.form_submit_button("Update Weight")
                delete_clicked = col2.form_submit_button("Delete Weight")

                if update_clicked:
                    original_df = weights_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df.loc[selected_row, "date"] = pd.to_datetime(edit_date)
                    original_df.loc[selected_row, "body_weight"] = edit_body_weight

                    overwrite_csv(WEIGHTS_FILE, original_df)
                    st.success("Weight entry updated.")
                    st.rerun()

                if delete_clicked:
                    original_df = weights_df.sort_values("date", ascending=False).reset_index(drop=True).copy()
                    original_df = original_df.drop(index=selected_row).reset_index(drop=True)

                    overwrite_csv(WEIGHTS_FILE, original_df)
                    st.success("Weight entry deleted.")
                    st.rerun()
