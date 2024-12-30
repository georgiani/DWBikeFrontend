import streamlit as st
from requests import get, post
import pandas as pd

st.set_page_config(page_title="Main", page_icon="🚵")

st.session_state["av_bike_list"] = get("http://localhost:5000/getAllAvailableBikes").json()
st.session_state["bike_list"] = get("http://localhost:5000/getAllBikes").json()
st.session_state["user_rentals"] = get("http://localhost:5000/getUserRentals?user_id=User1").json()
if "current_bike" not in st.session_state:
    st.session_state["current_bike"] = None

if "last_paid_msg" not in st.session_state:
    st.session_state["last_paid_msg"] = ""

if "rentals_page" not in st.session_state:
    st.session_state["rentals_page"] = False

if "current_rental" not in st.session_state:
    st.session_state["current_rental"] = None

if "user" not in st.session_state:
    st.session_state["user"] = "User1"

def start_rent_click(bike_id):
    # post to startRent
    rental_id = post("http://localhost:5000/startRental", json = {"bike_id": bike_id, "start_location": "Aleea Pinilor 1"}).content.decode("utf-8")
    st.session_state["current_rental"] = rental_id

def stop_rent_click(rental_id):
    resp = post("http://localhost:5000/stopRental", json = {"rental_id": rental_id, "location_end": "Aleea Padurilor 3"}).content.decode("utf-8")
    st.session_state["last_paid_msg"] = resp
    st.session_state["current_rental"] = None
    print(resp)

def select_rentals():
    st.session_state["rentals_page"] = True

def select_profile():
    st.session_state["profile_page"] = True

def select_rental(bike_id, rental_id):
    st.session_state["rentals_page"] = False
    st.session_state["current_bike"] = bike_id
    st.session_state["current_rental"] = rental_id

def select_bike(bike_id):
    st.session_state["current_bike"] = bike_id

def home():
    st.session_state["current_bike"] = None
    st.session_state["current_rental"] = None
    st.session_state["rentals_page"] = False
    st.session_state["profile_page"] = False

with st.container():
    st.title("DWBike")

if st.session_state["rentals_page"]:
    home_button = st.button(key=f"hb", label="Home", type="primary", on_click=home)
    # for k in st.session_state["user_rentals"]:
    for k in st.session_state["user_rentals"]:
        current_rental = st.session_state["user_rentals"][k]
        
        rental_id = k
        bike_id = current_rental["bike_id"]
        active = current_rental["end_time"] is None
        active_since = current_rental["start_time"]

        container = st.container(key=f"{rental_id}", border=True)

        with container:
            info_column, button_column = st.columns(2, gap="medium", vertical_alignment="center")
            info_column.write("Rental ID: " + rental_id)
            info_column.write("Active" if active else "Not Active")
            
            if active:
                info_column.write("Active since: " + active_since)

            with button_column:
                view_rental_button = st.button(key=f"view_{rental_id}", label="View", type="secondary", on_click=select_rental, args=(bike_id, rental_id))
elif st.session_state["current_bike"] is None:
    rentals, profile = st.columns(2)

    with rentals:
        rentals_page_button = st.button(key=f"rentals_page_bt", label="Rentals", type="primary", on_click=select_rentals)

    for k in st.session_state["av_bike_list"]:
        current_bike = st.session_state["av_bike_list"][k]
        bike_id = current_bike["BikeID"]
        container = st.container(key=f"{bike_id}", border=True)

        with container:
            info_column, button_column = st.columns(2)
            info_column.write("Bike Name: " + bike_id)
            info_column.write("Bike Producer: " + current_bike["BikeProducer"])
            
            with button_column:
                view_bike_button = st.button(key=f"view_{bike_id}", label="Select", type="secondary", on_click=select_bike, args=(bike_id,))
else:
    container = st.container(key=f"detail_{st.session_state["current_bike"]}")
    with container:
        home_button = st.button(key=f"hb", label="Home", type="primary", on_click=home)

    current_bike_details = st.session_state["bike_list"][st.session_state["current_bike"]]
    container.write("Bike Name: " + current_bike_details["BikeID"])
    container.write("Bike Producer: " + current_bike_details["BikeProducer"])
    container.write("Tarif: " + str(current_bike_details["Tarif"]))

    available = int(get(f"http://localhost:5000/checkAvailability?bike_id={st.session_state["current_bike"]}").content)
    container.write("Available" if available else "Not Available")
    with container:
        start_rent_button = st.button(key=f"sr_{st.session_state["current_bike"]}", label="Start Rent", type="secondary", disabled=not available, on_click=start_rent_click, args=(st.session_state["current_bike"],))
        end_rent_button = st.button(key=f"er_{st.session_state["current_bike"]}", label="End Rent", type="secondary", disabled=available, on_click=stop_rent_click, args=(st.session_state["current_rental"],))

    container.write(st.session_state["last_paid_msg"])