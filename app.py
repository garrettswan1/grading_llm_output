import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Human Grading + Model Review Tool")

@st.cache_data
def load_data():
    df = pd.read_csv("grading_data.csv")
    return df

#df = load_data()

if "df" not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# ---------------------------
# Helpers
# ---------------------------
def parse_cats(cat_string):
    if pd.isna(cat_string) or cat_string == "":
        return []
    return [c.strip() for c in str(cat_string).split("|")]

def cats_to_string(cat_list):
    return "|".join(cat_list)

# ---------------------------
# Upload CSV
# ---------------------------
#uploaded_file = st.file_uploader("Upload grading CSV", type="csv")

#if uploaded_file is None:
#    st.info("Upload a CSV file to begin.")
#    st.stop()

#df = pd.read_csv(uploaded_file)

# Ensure required columns exist
required_cols = [
    "prompt", "question", "students_answer", "categories",
    "grade1_rating", "grader1_categories",
    "grader2_categories", "model_categories", "acceptable"
]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

# Add comment column if missing
if "grader1_comment" not in df.columns:
    df["grader1_comment"] = ""

# ---------------------------
# Filter rows needing grading (RUN ONCE PER SESSION)
# ---------------------------
if "rows_to_grade" not in st.session_state:
    rows = df[
        df["grader1_categories"].isna() &
        df["grader2_categories"].isna() &
        df["model_categories"].notna()
    ].index.tolist()

    st.session_state.rows_to_grade = rows
    st.session_state.row_index = 0
    st.session_state.submitted = False

rows_to_grade = st.session_state.rows_to_grade
total_items = len(rows_to_grade)

if total_items == 0:
    st.success("Nothing to grade 🎉")
    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name="graded_output.csv"
    )
    st.stop()

# Prevent crash when finished
if st.session_state.row_index >= total_items:
    st.success("All items graded!")

    st.download_button(
        "Download Updated CSV",
        df.to_csv(index=False),
        file_name="graded_output.csv"
    )
    st.stop()

row_id = rows_to_grade[st.session_state.row_index]
row = df.loc[row_id]

# ---------------------------
# Session State
# ---------------------------
if "row_index" not in st.session_state:
    st.session_state.row_index = 0
if "submitted" not in st.session_state:
    st.session_state.submitted = False

progress = st.session_state.row_index / total_items
st.progress(progress)
st.caption(f"Progress: {st.session_state.row_index} / {total_items}")

# ---------------------------
# Get current row
# ---------------------------
#row_id = rows_to_grade.index[st.session_state.row_index]
row_id = rows_to_grade[st.session_state.row_index]
row = df.loc[row_id]

# ---------------------------
# Display Text
# ---------------------------
st.subheader("Prompt")
st.write(row["prompt"])

st.subheader("Question")
st.write(row["question"])

st.subheader("Student Answer")
st.info(row["students_answer"])

st.divider()

# ---------------------------
# Step 1 — Grader Input (Blind)
# ---------------------------
#all_categories = sorted(set(
#    sum(df["categories"].dropna().apply(parse_cats).tolist(), [])
#))

all_categories = parse_cats(row["categories"])

if not st.session_state.submitted:

    score = st.selectbox("Select Score (1–10)", list(range(1, 11)))
    grader_selected = st.multiselect("Select Categories", all_categories)

    if st.button("Submit Grade"):
        st.session_state.score = score
        st.session_state.grader_selected = grader_selected
        st.session_state.submitted = True
        st.rerun()

# ---------------------------
# Step 2 — Model Comparison (After Submission)
# ---------------------------
else:
    grader_selected = st.session_state.grader_selected
    score = st.session_state.score

    model_selected = parse_cats(row["model_categories"])
    missing_from_grader = [c for c in model_selected if c not in grader_selected]

    st.subheader("Review")

    if missing_from_grader:
        st.warning("The model selected additional categories.")
        reveal = st.checkbox("Reveal model categories")

        if reveal:
            st.write("**Model Categories:**", ", ".join(model_selected))

        accept_model = st.radio(
            "Are the model's extra categories acceptable?",
            ["Yes", "No"]
        )
        comment = st.text_area("Optional comment")
        acceptable = 1 if accept_model == "Yes" else 0

    else:
        st.success("Your categories align with the model.")
        acceptable = 1
        comment = ""

    # Save and move on
    if st.button("Finalize and Next"):
        df.at[row_id, "grade1_rating"] = score
        df.at[row_id, "grader1_categories"] = cats_to_string(grader_selected)
        df.at[row_id, "acceptable"] = acceptable
        df.at[row_id, "grader1_comment"] = comment

        st.session_state.row_index += 1
        st.session_state.submitted = False
        st.rerun()

# ---------------------------
# Finished All Items
# ---------------------------
if st.session_state.row_index >= total_items:
    st.success("All items graded!")

    st.download_button(
        "Download Updated CSV",
        df.to_csv(index=False),
        file_name="graded_output.csv"
    )
