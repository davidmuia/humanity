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
# "a5cf5a4b43922cb412cbeb89d726e12bbfcbf92e"
# access_token = "8e039db994a0a6f2afd9c590ddfebe5cbccfaf75"

st.header("MC Staff Movement")

with st.beta_expander("Click me to view instruction on how to use the tool"):
    st.write("Select a date range from the sidebar to view staff movements across MCs.")
    st.info("Please note for the tool to work, you have to select day(s) prior to the current day to see movement")

@st.cache(suppress_st_warning=True)
def get_shifts(start_date,end_date):

    custom_report = requests.get(url = f"https://www.humanity.com/api/v2/reports/custom?start_date={start_date}&end_date={end_date}&fields=id,employee,eid,user,location,schedule_id,schedule_name,start_day,end_day,start_time,end_time,total_time&type=shifts&access_token={access_token}").json()
    custom_report = custom_report["data"].values()
    custom_report = list(custom_report)[1:]
    custom_report = pd.Series(custom_report)
    custom_report = pd.DataFrame(custom_report)
    custom_report = custom_report[0].apply(pd.Series)
    custom_report['start_day'] = pd.to_datetime(custom_report['start_day'])
    custom_report['end_day'] = pd.to_datetime(custom_report['end_day'])
    print(custom_report.info())
    custom_report = custom_report.sort_values(by=['employee', 'start_day'],ascending=True)
    # custom_report['prev_employee'] = custom_report.employee.eq(custom_report.employee.shift()).astype('bool')
    # custom_report['prev_location'] = custom_report.location.eq(custom_report.location.shift()).astype('bool')    

    def comp_prev(a):
        return np.concatenate(([False],a[1:] == a[:-1]))
    custom_report['prev_employee'] = comp_prev(custom_report.employee.values)
    custom_report['prev_location'] = comp_prev(custom_report.location.values)

    custom_report['prev_employee'] = custom_report['prev_employee'].replace(True,1).astype(int)
    custom_report['prev_employee'] = custom_report['prev_employee'].replace(False,0).astype(int)
    custom_report['prev_location'] = custom_report['prev_location'].replace(True,1).astype(int)
    custom_report['prev_location'] = custom_report['prev_location'].replace(False,0).astype(int)

    
    custom_report["Movement"] = np.where(
        (custom_report["prev_employee"] == 1) & (custom_report["prev_location"] == 0),
        "Movement",
        "No Movement"
    )
        
    del custom_report['prev_employee']
    del custom_report['prev_location']

    return custom_report

data = get_shifts(start_date,end_date)

row_num = len(data)

columns=["schedule_name", "employee", "location", "Movement"]

for column in data.columns:
    if column in columns:
        options = pd.Series(["All"]).append(data[column], ignore_index=True).unique()
        choice = st.sidebar.selectbox("Select {}.".format(column), options)
        
        if choice != "All":
            data = data[data[column] == choice]

st.subheader(f"The selected data has {row_num} rows of data, from {start_date} to {end_date}")
st.dataframe(data)

# Download data
download_button_str = download_button(data, f"Staff_Schedules_{start_date}_to_{end_date}.csv", 'Download CSV', pickle_it=False)
st.sidebar.markdown(download_button_str, unsafe_allow_html=True)
