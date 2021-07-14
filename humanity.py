from datetime import date

import base64
import os
import json
import pickle
import uuid
import re

from pandas.core.tools.datetimes import DatetimeScalarOrArrayConvertible

def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link


def file_selector(folder_path='.'):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox('Select a file', filenames)
    return os.path.join(folder_path, selected_filename)

import streamlit as st
import requests, json
import pandas as pd
import numpy as np

st.set_page_config(layout='wide')
st.sidebar.markdown("Select Parameter Filters")
start_date = st.sidebar.date_input("Pick a start date")
end_date = st.sidebar.date_input("Pick a end date")

access_token = st.sidebar.text_input("Enter your access token here")
# "8c5be1163ebe28cb60643eb4cb728b657ea1d14e"
@st.cache
def get_shifts(start_date,end_date):

    # shifts api
    shifts_url = f"https://www.humanity.com/api/v2/shifts?access_token={access_token}"

    shifts_params = {
        "start_date":start_date,
        "end_date":end_date
    }


    # custom reports api
    # url = "https://www.humanity.com/api/v2/reports/custom?access_token={access_token}"

    # params = {
    #     "start_date":start_date,
    #     "end_date":end_date,
    #     "fields": {'employee', 'eid', 'user', 'location', 'schedule_id', 'schedule_name', 'start_day', 'end_day', 'start_time', 'end_time', 'total_time'},
    #     # "type": enum[confirmedshifts]
    # }


    # locations api
    location_url = f"https://www.humanity.com/api/v2/locations?access_token={access_token}"

    location_params = {

    }


    shifts = requests.get(url = shifts_url,params = shifts_params).json()
    shifts = pd.DataFrame(shifts["data"])
    shifts["schedule_location_id"] = shifts["schedule_location_id"].apply(pd.to_numeric)

    locations = requests.get(url = location_url, params = location_params).json()
    locations = pd.DataFrame(locations["data"])
    locations["schedule_location_id"] = locations["id"]
    locations = locations[["schedule_location_id","name"]]

    df_join = pd.merge(
        shifts,
        locations,
        on = "schedule_location_id",
        how = "left"
    )

    # return requests.get(url = shifts_url,params = shifts_params).json()["data"]

    # select relevant columns  (removed id and user columns)
    df_join = df_join[["start_timestamp","end_timestamp","length","schedule_name","employees","name"]]
    df_join = df_join.rename(columns={"name": "schedule_location"})

    # expand/explode column with json/dict data to individual columns
    emp = df_join["employees"].apply(pd.Series)
    emp = emp[0].apply(pd.Series)
    emp = emp[["id", "name"]]
    emp = emp.rename(columns={'name': "employee_name"})
    
    del df_join["employees"]

    df_join[["employee_id", "employee_name"]] = emp[["id", "employee_name"]]

    # Employee payroll api, which contains primary location info and company employee id
    primary_location = requests.get(url = f"https://www.humanity.com/api/v2/payroll/report?start_date={start_date}&end_date={end_date}&type=scheduledhours&access_token={access_token}").json()
    primary_location = pd.Series(primary_location["data"])
    primary_location = pd.DataFrame(primary_location)
    primary_location = primary_location[0].apply(pd.Series)

    del primary_location["date"]
    del primary_location["out_date"]
    del primary_location["start_time"]
    del primary_location["end_time"]
    del primary_location["overnight"]
    del primary_location["clock"]
    del primary_location["shift_title"]
    del primary_location["in_location_name"]
    del primary_location["out_location_name"]
    del primary_location["daily"]
    del primary_location["weekly"]
    del primary_location["special"]

    location = primary_location["hours"].apply(pd.Series)
    location = location["location"].apply(pd.Series)
    location = location[["id", "name"]]
    primary_location[["location_id", "home_location"]] = location[["id", "name"]]
    primary_location = primary_location.rename(columns={"userid":"employee_id"})

    del primary_location["hours"]

    primary_location.drop_duplicates(keep=False, inplace=True)

    # merge with dataframe containing home location
    df_join_2 = pd.merge(
        df_join,
        primary_location,
        on = "employee_id",
        how = "left"
    )

    # create conditional column that identifies the remote mc
    df_join_2["shift_location"] = np.where(
        df_join_2["schedule_location"] != df_join_2["home_location"],
        df_join_2["schedule_location"],
        df_join_2["home_location"]
    )
    
    df_join_2["staff_movement"] = np.where(
        df_join_2["shift_location"] == df_join_2["home_location"],
        "No Movement",
        "Movement"
    )

    del df_join_2["home_location"]
    del df_join_2["schedule_location"]    

    return df_join_2

data = get_shifts(start_date,end_date)

row_num = len(data)

# if all:
#     selected_options = container.multiselect("Selet one or more options:", data['shift_location'].unique())
#     mask = data["shift_location"].isin(selected_options)
#     data = data[mask]
# else:
#     selected_options = container.multiselect("Selet one or more options:", data['shift_location'].unique())
#     mask = data["shift_location"].isin(selected_options)
#     data = data[mask]

# shift_location = data["shift_location"].unique()
# location_choice = st.sidebar.selectbox('Select shift location:', shift_location)
# staff_movement = data.loc[data["shift_location"] == location_choice]
# movement = staff_movement["staff_movement"].unique()
# movement_choice = st.sidebar.selectbox('Select movement:', movement)
# movement = staff_movement.loc[staff_movement["staff_movement"] == movement_choice ]
# schedule_name = movement[]

columns=["schedule_name", "employee_name", "shift_location", "staff_movement"]

for column in data.columns:
    if column in columns:
        options = pd.Series(["All"]).append(data[column], ignore_index=True).unique()
        choice = st.sidebar.selectbox("Select {}.".format(column), options)
        
        if choice != "All":
            data = data[data[column] == choice]


# def drop_filter_gen(data, columns=[]):
#     for column in data.columns:
#         if column in columns:
#             options = pd.Series(["All"]).append(data[column], ignore_index=True).unique()
#             choice = st.sidebar.selectbox("Select {}.".format(column), options)

#             if choice != "All":
#                 data = data[data[column] == choice]
        

# drop_filter_gen(data, columns=["schedule_name", "employee_name", "shift_location", "staff_movement"])




# movement_choice = data["staff_movement"].loc[data["staff_movement"] == movement_choice]

# shift_location = st.sidebar.selectbox('Select shift location:', shift_location)
# staff_movement = st.sidebar.selectbox('Select movement type', staff_movement)

# data = data.loc[
#     data["shift_location"] == shift_location and data["staff_movement"] == staff_movement
# ]

st.subheader(f"The selected data has {row_num} rows of data, from {start_date} to {end_date}")

st.dataframe(data)


# shift_location = data['shift_location'].unique()
# shift_location_choice = st.sidebar.selectbox('Select shift location:', shift_location)
# staff_mvmnt = data.loc[data["shift_location"] == shift_location_choice].drop_duplicates()
# staff_mvmnt_choice = st.sidebar.selectbox('Shift change:', staff_mvmnt)

# data = pd.DataFrame(data)

# unique_locations = data["shift_location"].unique()
# unique_locations_selected = st.sidebar.selectbox('Select location:', unique_locations)


# data = data.loc[data["shift_location"] == unique_locations_selected]

# mask_location = data["location"].isin(unique_locations_selected)

# data = data[mask_location]

# Download data
download_button_str = download_button(data, f"Staff_Schedules_{start_date}_to_{end_date}.csv", 'Download CSV', pickle_it=False)
st.sidebar.markdown(download_button_str, unsafe_allow_html=True)


# custom = requests.get(url="https://www.humanity.com/api/v2/reports/custom?access_token=e2ac8ad18ff5ba20f2127ad6dd520ad6f35a7f77&start_date=2021-06-01&end_date=2021-06-30&type=confirmedshifts&fields=start_day,end_day,start_time,end_time,title&employee=4015840").json()
# # custom = pd.DataFrame(custom["data"])
# st.json(custom)



