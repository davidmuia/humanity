import pandas as pd
import time
import streamlit as st
import plotly.express as px

@st.cache
def load_dataset(data_link):
    dataset = pd.read_csv(data_link)
    return dataset

titanic_link = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv'
titanic_data = load_dataset(titanic_link)

st.title("My First Streamlit App")

st.header("#Hello")
st.subheader("#Hello Too")

st.markdown("#Just like a header")
st.markdown("#Just like a subheader")

# st.sidebar()

selected_class = st.radio("Select Class", titanic_data['class'].unique())
st.write("Selected Class:", selected_class)
st.write("Selected Class Type:", type(selected_class))

selected_sex = st.selectbox("Select Sex", titanic_data['sex'].unique())
st.write(f"Selected Option: {selected_sex!r}")

selected_decks = st.multiselect("Select Decks", titanic_data['deck'].unique())
st.write("Selected Decks:", selected_decks)


age_columns = st.beta_columns(2)
age_min = age_columns[0].number_input("Minimum Age", value=titanic_data['age'].min())
age_max = age_columns[0].number_input("Maximum Age", value=titanic_data['age'].max())


if age_max < age_min:
    st.error("The maximum age can't be smaller than the minimum age!")
else:
    st.success("Congratulations! Correct Parameters!")
    subset_age = titanic_data[(titanic_data['age'] <= age_max) & (age_min <= titanic_data['age'])]
    st.write(f"Number of Records With Age Between {age_min} and {age_max}: {subset_age.shape[0]}")

optionals = st.beta_expander("Optional Configurations", True)
fare_min = optionals.slider(
    "Minimum Fare",
    min_value=float(titanic_data['fare'].min()),
    max_value=float(titanic_data['fare'].max())
)
fare_max = optionals.slider(
    "Maximum Fare",
    min_value=float(titanic_data['fare'].min()),
    max_value=float(titanic_data['fare'].max())
)
subset_fare = titanic_data[(titanic_data['fare'] <= fare_max) & (fare_min <= titanic_data['fare'])]
st.write(f"Number of Records With Fare Between {fare_min} and {fare_max}: {subset_fare.shape[0]}")
