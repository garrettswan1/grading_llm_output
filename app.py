import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("grading_data.csv")
    return df

df = load_data()

# ---------- Helper functions ----------
def parse_cats(cat_string):
    if pd.isna(cat_string) or cat_string == "":
        return []
    return [c.strip() for c in cat_string.split("|")]

def cats_to_string(cat_list):
    return "|".join(cat_list)

# ---------- Filter rows to grade ----------
rows_to_grade = df[
    df["grader1_categories"].isna() &
    df["grader2_categories"].isna() &
    df["model_categories"].notna()
]

if "row_index" not in st.session_state:
    st.session_state.row_index = 0

if st.session_state.row_index >= len(rows_to_grade):
    st.success("🎉 All items graded!")
    if st.button("Save file"):
        df.to_csv("grading_data_UPDATED.csv", index=False)
        st.success("File saved!")
    st.stop()

row_id = rows_to_grade.index[st.session_state.row_index]
row = df.loc[row_id]

# ---------- Display text ----------
st.title("Grading Interface")

st.subheader("Prompt")
st.write(row["prompt"])

st.subheader("Question")
st.write(row["question"])

st.subheader("Student Answer")
st.info(row["students_answer"])

# ---------- Grader inputs ----------
st.divider()

score = st.selectbox("Select Score (1–10)", list(range(1, 11)))

all_categories = sorted(set(
    sum(df["categories"].dropna().apply(parse_cats).tolist(), [])
))

grader_selected = st.multiselect(
    "Select Categories",
    options=all_categories
)

model_selected = parse_cats(row["model_categories"])

# ---------- Compare with model ----------
st.divider()

missing_from_grader = [c for c in model_selected if c not in grader_selected]

acceptable = 1  # default

if missing_from_grader:
    st.warning("The model selected categories you did not.")
    st.write("**Model Categories:**", ", ".join(model_selected))

    accept_model = st.radio(
        "Are the model's extra categories acceptable?",
        ["Yes", "No"]
    )

    comment = st.text_area("Optional note about disagreement")

    acceptable = 1 if accept_model == "Yes" else 0
else:
    st.success("Your categories match the model.")
    acceptable = 1
    comment = ""

# ---------- Save + Next ----------
if st.button("Save and Next"):
    df.at[row_id, "grade1_rating"] = score
    df.at[row_id, "grader1_categories"] = cats_to_string(grader_selected)
    df.at[row_id, "acceptable"] = acceptable
    df.at[row_id, "grader1_comment"] = comment

    st.session_state.row_index += 1
    st.rerun()
