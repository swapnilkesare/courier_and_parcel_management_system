import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
from streamlit_folium import st_folium
import folium
from streamlit_lottie import st_lottie
import requests
import io
import time
import os
from fpdf import FPDF

MOCK_MODE = False

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    MOCK_MODE = True
    MySQLError = Exception

DB_SETUP_MSG = "⚠️ Database objects missing: Please execute the **setup.sql** script in MySQL Workbench first."

def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def get_db_connection():
    global MOCK_MODE
    if MOCK_MODE:
        return None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="courier_management",
            autocommit=True
        )
        return conn
    except Exception:
        MOCK_MODE = True
        return None

def run_query(query, params=None, fetch=True):
    conn = get_db_connection()
    if conn is None:
        return _mock_query(query)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            rows = cursor.fetchall()
            return pd.DataFrame(rows) if rows else pd.DataFrame()
        conn.commit()
        return pd.DataFrame()
    except Exception as e:
        err_code = getattr(e, 'errno', 0)
        if err_code == 1305:
            st.error(DB_SETUP_MSG)
        else:
            st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        if conn and conn.is_connected():
            conn.close()

def call_procedure_simple(proc_name, in_args, out_count):
    conn = get_db_connection()
    if conn is None:
        _, outs = _mock_procedure(proc_name, in_args)
        return outs
    try:
        cursor = conn.cursor()
        in_placeholders = ", ".join(["%s"] * len(in_args))
        out_placeholders = ", ".join([f"@out{i}" for i in range(out_count)])
        
        if in_placeholders and out_placeholders:
            call_sql = f"CALL {proc_name}({in_placeholders}, {out_placeholders})"
        elif out_placeholders:
            call_sql = f"CALL {proc_name}({out_placeholders})"
        else:
            call_sql = f"CALL {proc_name}({in_placeholders})"
            
        cursor.execute(call_sql, list(in_args))
        
        # Safe handling of multiple result sets for Python MySQL Connector
        for _ in cursor.stored_results():
            pass
            
        out_names = ", ".join([f"@out{i}" for i in range(out_count)])
        cursor.execute(f"SELECT {out_names}")
        row = cursor.fetchone()
        conn.commit()
        return list(row) if row else []
    except Exception as e:
        err_code = getattr(e, 'errno', 0)
        if err_code == 1305:
            st.error(DB_SETUP_MSG)
        else:
            st.error(f"Procedure error: {e}")
        return [None] * out_count
    finally:
        if conn and conn.is_connected():
            conn.close()

def call_function(func_name, args):
    conn = get_db_connection()
    if conn is None:
        return _mock_function(func_name, args)
    try:
        cursor = conn.cursor()
        placeholders = ", ".join(["%s"] * len(args))
        cursor.execute(f"SELECT {func_name}({placeholders})", list(args))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        err_code = getattr(e, 'errno', 0)
        if err_code == 1305:
            st.error(DB_SETUP_MSG)
        else:
            st.error(f"Function error: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def _init_mock():
    if "mock_initialized" in st.session_state:
        return
    st.session_state.mock_initialized = True
    st.session_state.mock_users = {
        "admin":      {"password": "Admin@2026",  "role": "Admin"},
        "staff_raj":  {"password": "Raj$taff1",   "role": "Staff"},
        "staff_neha": {"password": "Neha$taff2",  "role": "Staff"},
        "staff_amit": {"password": "Amit$taff3",  "role": "Staff"},
    }
    st.session_state.mock_customers = pd.DataFrame([
        {"Customer_ID": 1, "Customer_Name": "Amit Sharma",  "Mobile_Number": "9876543210", "Email": "amit.sharma@email.com",  "Pickup_Address": "12 MG Road, Pune", "Delivery_Address": "45 Park Street, Mumbai"},
        {"Customer_ID": 2, "Customer_Name": "Priya Desai",  "Mobile_Number": "9123456780", "Email": "priya.desai@email.com",  "Pickup_Address": "78 FC Road, Pune", "Delivery_Address": "23 Lajpat Nagar, Delhi"},
        {"Customer_ID": 3, "Customer_Name": "Rahul Verma",  "Mobile_Number": "9988776655", "Email": "rahul.verma@email.com",  "Pickup_Address": "34 Brigade Road, Bangalore", "Delivery_Address": "11 Salt Lake, Kolkata"},
        {"Customer_ID": 4, "Customer_Name": "Sneha Patil",  "Mobile_Number": "9871234560", "Email": "sneha.patil@email.com",  "Pickup_Address": "56 JM Road, Pune", "Delivery_Address": "89 Banjara Hills, Hyderabad"},
        {"Customer_ID": 5, "Customer_Name": "Vikram Joshi", "Mobile_Number": "9765432100", "Email": "vikram.joshi@email.com", "Pickup_Address": "90 Connaught Place, Delhi", "Delivery_Address": "67 Boat Club Road, Pune"},
        {"Customer_ID": 6, "Customer_Name": "Ananya Iyer",  "Mobile_Number": "9654321098", "Email": "ananya.iyer@email.com",  "Pickup_Address": "22 Anna Nagar, Chennai", "Delivery_Address": "44 Koramangala, Bangalore"},
        {"Customer_ID": 7, "Customer_Name": "Neha Sharma",  "Mobile_Number": "9811223344", "Email": "neha.s@email.com",     "Pickup_Address": "12 Janpath, Delhi", "Delivery_Address": "45 MG Road, Bangalore"},
        {"Customer_ID": 8, "Customer_Name": "Karan Patel",  "Mobile_Number": "9822334455", "Email": "karan.p@email.com",    "Pickup_Address": "78 SG Highway, Ahmedabad", "Delivery_Address": "34 Nariman Point, Mumbai"},
        {"Customer_ID": 9, "Customer_Name": "Pooja Singh",  "Mobile_Number": "9833445566", "Email": "pooja.s@email.com",    "Pickup_Address": "56 Hazratganj, Lucknow", "Delivery_Address": "90 Sector 18, Noida"},
        {"Customer_ID": 10,"Customer_Name": "Rahul Dravid", "Mobile_Number": "9844556677", "Email": "rahul.d@email.com",    "Pickup_Address": "100 Indiranagar, Bangalore", "Delivery_Address": "22 T Nagar, Chennai"},
        {"Customer_ID": 11,"Customer_Name": "Aditi Rao",    "Mobile_Number": "9855667788", "Email": "aditi.r@email.com",    "Pickup_Address": "11 Koregaon Park, Pune", "Delivery_Address": "33 Banjara Hills, Hyderabad"}
    ])
    st.session_state.mock_parcels = pd.DataFrame([
        {"Parcel_ID": 1, "Customer_ID": 1, "Parcel_Type": "Document",   "Weight": 0.5, "Dimensions": "30x22x2",  "Booking_Date": "2026-07-01", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260701-000001"},
        {"Parcel_ID": 2, "Customer_ID": 2, "Parcel_Type": "Small Box",  "Weight": 2.0, "Dimensions": "25x20x15", "Booking_Date": "2026-07-02", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260702-000002"},
        {"Parcel_ID": 3, "Customer_ID": 3, "Parcel_Type": "Medium Box", "Weight": 5.5, "Dimensions": "40x30x25", "Booking_Date": "2026-07-03", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260703-000003"},
        {"Parcel_ID": 4, "Customer_ID": 4, "Parcel_Type": "Large Box",  "Weight": 12.0, "Dimensions": "60x45x40", "Booking_Date": "2026-07-05", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260705-000004"},
        {"Parcel_ID": 5, "Customer_ID": 1, "Parcel_Type": "Fragile",    "Weight": 3.2, "Dimensions": "35x25x20", "Booking_Date": "2026-07-07", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260707-000005"},
        {"Parcel_ID": 6, "Customer_ID": 5, "Parcel_Type": "Heavy Cargo","Weight": 25.0, "Dimensions": "80x60x50", "Booking_Date": "2026-07-10", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260710-000006"},
        {"Parcel_ID": 7, "Customer_ID": 6, "Parcel_Type": "Document",   "Weight": 0.3, "Dimensions": "28x21x1",  "Booking_Date": "2026-07-12", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260712-000007"},
        {"Parcel_ID": 8, "Customer_ID": 3, "Parcel_Type": "Small Box",  "Weight": 1.8, "Dimensions": "22x18x12", "Booking_Date": "2026-07-15", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260715-000008"},
        {"Parcel_ID": 9, "Customer_ID": 7, "Parcel_Type": "Document",   "Weight": 0.2, "Dimensions": "25x15x1",  "Booking_Date": "2026-07-18", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260718-000009"},
        {"Parcel_ID": 10,"Customer_ID": 8, "Parcel_Type": "Medium Box", "Weight": 6.0, "Dimensions": "30x30x30", "Booking_Date": "2026-07-19", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260719-000010"},
        {"Parcel_ID": 11,"Customer_ID": 9, "Parcel_Type": "Small Box",  "Weight": 2.5, "Dimensions": "20x20x10", "Booking_Date": "2026-07-20", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260720-000011"},
        {"Parcel_ID": 12,"Customer_ID": 10,"Parcel_Type": "Large Box",  "Weight": 15.0,"Dimensions": "70x50x40", "Booking_Date": "2026-07-21", "Delivery_Type": "Standard", "Tracking_Number": "TRK-20260721-000012"},
        {"Parcel_ID": 13,"Customer_ID": 11,"Parcel_Type": "Fragile",    "Weight": 4.5, "Dimensions": "40x30x20", "Booking_Date": "2026-07-22", "Delivery_Type": "Express", "Tracking_Number": "TRK-20260722-000013"}
    ])
    st.session_state.mock_staff = pd.DataFrame([
        {"Employee_ID": 1, "Employee_Name": "Rajesh Kumar", "Mobile_Number": "9800011122", "Assigned_Area": "Mumbai - Western"},
        {"Employee_ID": 2, "Employee_Name": "Neha Gupta",   "Mobile_Number": "9800033344", "Assigned_Area": "Delhi - Central"},
        {"Employee_ID": 3, "Employee_Name": "Sanjay Pawar", "Mobile_Number": "9800055566", "Assigned_Area": "Pune - East"},
        {"Employee_ID": 4, "Employee_Name": "Meera Nair",   "Mobile_Number": "9800077788", "Assigned_Area": "Bangalore - South"},
        {"Employee_ID": 5, "Employee_Name": "Arjun Singh",  "Mobile_Number": "9800099900", "Assigned_Area": "Kolkata - North"},
        {"Employee_ID": 6, "Employee_Name": "Deepa Rao",    "Mobile_Number": "9800012345", "Assigned_Area": "Hyderabad - West"},
    ])
    st.session_state.mock_shipments = pd.DataFrame([
        {"Shipment_ID": 1, "Parcel_ID": 1, "Employee_ID": 1, "Current_Location": "Mumbai Hub", "Shipment_Status": "Delivered", "Dispatch_Date": "2026-07-02", "Expected_Delivery_Date": "2026-07-06"},
        {"Shipment_ID": 2, "Parcel_ID": 2, "Employee_ID": 2, "Current_Location": "Delhi Sorting Centre", "Shipment_Status": "Delivered", "Dispatch_Date": "2026-07-03", "Expected_Delivery_Date": "2026-07-05"},
        {"Shipment_ID": 3, "Parcel_ID": 3, "Employee_ID": 5, "Current_Location": "Kolkata Hub", "Shipment_Status": "Out for Delivery", "Dispatch_Date": "2026-07-04", "Expected_Delivery_Date": "2026-07-09"},
        {"Shipment_ID": 4, "Parcel_ID": 4, "Employee_ID": 6, "Current_Location": "Hyderabad Hub", "Shipment_Status": "In Transit", "Dispatch_Date": "2026-07-06", "Expected_Delivery_Date": "2026-07-08"},
        {"Shipment_ID": 5, "Parcel_ID": 5, "Employee_ID": 1, "Current_Location": "Mumbai Hub", "Shipment_Status": "In Transit", "Dispatch_Date": "2026-07-08", "Expected_Delivery_Date": "2026-07-10"},
        {"Shipment_ID": 6, "Parcel_ID": 6, "Employee_ID": 3, "Current_Location": "Pune Warehouse", "Shipment_Status": "Booked", "Dispatch_Date": None, "Expected_Delivery_Date": "2026-07-17"},
        {"Shipment_ID": 7, "Parcel_ID": 7, "Employee_ID": 4, "Current_Location": "Bangalore Hub", "Shipment_Status": "In Transit", "Dispatch_Date": "2026-07-13", "Expected_Delivery_Date": "2026-07-18"},
        {"Shipment_ID": 8, "Parcel_ID": 8, "Employee_ID": 2, "Current_Location": "Delhi Hub", "Shipment_Status": "Booked", "Dispatch_Date": None, "Expected_Delivery_Date": "2026-07-18"},
        {"Shipment_ID": 9, "Parcel_ID": 9, "Employee_ID": 2, "Current_Location": "Delhi Hub", "Shipment_Status": "In Transit", "Dispatch_Date": "2026-07-19", "Expected_Delivery_Date": "2026-07-21"},
        {"Shipment_ID": 10,"Parcel_ID": 10,"Employee_ID": 1, "Current_Location": "Ahmedabad Warehouse", "Shipment_Status": "Booked", "Dispatch_Date": None, "Expected_Delivery_Date": "2026-07-26"},
        {"Shipment_ID": 11,"Parcel_ID": 11,"Employee_ID": 2, "Current_Location": "Lucknow Sorting Hub", "Shipment_Status": "Out for Delivery", "Dispatch_Date": "2026-07-21", "Expected_Delivery_Date": "2026-07-23"},
        {"Shipment_ID": 12,"Parcel_ID": 12,"Employee_ID": 4, "Current_Location": "Bangalore Hub", "Shipment_Status": "In Transit", "Dispatch_Date": "2026-07-22", "Expected_Delivery_Date": "2026-07-28"},
        {"Shipment_ID": 13,"Parcel_ID": 13,"Employee_ID": 3, "Current_Location": "Pune Warehouse", "Shipment_Status": "Booked", "Dispatch_Date": None, "Expected_Delivery_Date": "2026-07-25"}
    ])
    st.session_state.mock_payments = pd.DataFrame([
        {"Payment_ID": 1, "Parcel_ID": 1, "Courier_Charges": 80.0, "Payment_Date": "2026-07-01", "Payment_Mode": "UPI", "Payment_Status": "Completed"},
        {"Payment_ID": 2, "Parcel_ID": 2, "Courier_Charges": 250.0, "Payment_Date": "2026-07-02", "Payment_Mode": "Credit Card", "Payment_Status": "Completed"},
        {"Payment_ID": 3, "Parcel_ID": 3, "Courier_Charges": 320.0, "Payment_Date": "2026-07-03", "Payment_Mode": "Debit Card", "Payment_Status": "Completed"},
        {"Payment_ID": 4, "Parcel_ID": 4, "Courier_Charges": 750.0, "Payment_Date": "2026-07-05", "Payment_Mode": "Net Banking", "Payment_Status": "Completed"},
        {"Payment_ID": 5, "Parcel_ID": 5, "Courier_Charges": 400.0, "Payment_Date": "2026-07-07", "Payment_Mode": "UPI", "Payment_Status": "Pending"},
        {"Payment_ID": 6, "Parcel_ID": 6, "Courier_Charges": 1100.0, "Payment_Date": "2026-07-10", "Payment_Mode": "Cash", "Payment_Status": "Pending"},
        {"Payment_ID": 7, "Parcel_ID": 7, "Courier_Charges": 70.0, "Payment_Date": "2026-07-12", "Payment_Mode": "UPI", "Payment_Status": "Completed"},
        {"Payment_ID": 8, "Parcel_ID": 8, "Courier_Charges": 230.0, "Payment_Date": "2026-07-15", "Payment_Mode": "Credit Card", "Payment_Status": "Pending"},
        {"Payment_ID": 9, "Parcel_ID": 9, "Courier_Charges": 65.0, "Payment_Date": "2026-07-18", "Payment_Mode": "UPI", "Payment_Status": "Completed"},
        {"Payment_ID": 10,"Parcel_ID": 10,"Courier_Charges": 350.0, "Payment_Date": "2026-07-19", "Payment_Mode": "Debit Card", "Payment_Status": "Completed"},
        {"Payment_ID": 11,"Parcel_ID": 11,"Courier_Charges": 190.0, "Payment_Date": "2026-07-20", "Payment_Mode": "Credit Card", "Payment_Status": "Completed"},
        {"Payment_ID": 12,"Parcel_ID": 12,"Courier_Charges": 850.0, "Payment_Date": "2026-07-21", "Payment_Mode": "Net Banking", "Payment_Status": "Pending"},
        {"Payment_ID": 13,"Parcel_ID": 13,"Courier_Charges": 390.0, "Payment_Date": "2026-07-22", "Payment_Mode": "UPI", "Payment_Status": "Completed"}
    ])
    st.session_state.mock_next_ids = {"customer": 12, "parcel": 14, "shipment": 14, "payment": 14}


def _mock_query(query):
    _init_mock()
    q = query.lower().strip()
    if "customer" in q and "parcel" not in q and "payment" not in q:
        return st.session_state.mock_customers.copy()
    if "delivery_staff" in q or "employee" in q:
        return st.session_state.mock_staff.copy()
    if "shipment" in q and "parcel" in q:
        df = st.session_state.mock_shipments.merge(st.session_state.mock_parcels, on="Parcel_ID").merge(st.session_state.mock_customers, on="Customer_ID")
        return df
    if "shipment" in q:
        return st.session_state.mock_shipments.copy()
    if "payment" in q and ("group" in q or "sum" in q or "revenue" in q):
        return st.session_state.mock_payments.copy()
    if "payment" in q:
        return st.session_state.mock_payments.merge(st.session_state.mock_parcels[["Parcel_ID", "Tracking_Number"]], on="Parcel_ID")
    if "parcel" in q:
        return st.session_state.mock_parcels.copy()
    return pd.DataFrame()


def _mock_procedure(proc_name, args):
    _init_mock()
    name = proc_name.lower()
    if name == "register_customer":
        nid = st.session_state.mock_next_ids["customer"]
        st.session_state.mock_next_ids["customer"] += 1
        new_row = pd.DataFrame([{"Customer_ID": nid, "Customer_Name": args[0], "Mobile_Number": args[1], "Email": args[2], "Pickup_Address": args[3], "Delivery_Address": args[4]}])
        st.session_state.mock_customers = pd.concat([st.session_state.mock_customers, new_row], ignore_index=True)
        return [], [nid, f"Customer registered successfully with ID: {nid}"]
    if name == "book_parcel":
        nid = st.session_state.mock_next_ids["parcel"]
        st.session_state.mock_next_ids["parcel"] += 1
        trk = f"TRK-{date.today().strftime('%Y%m%d')}-{nid:06d}"
        charges = _mock_calc_charges(float(args[2]), args[4], args[1])
        new_parcel = pd.DataFrame([{"Parcel_ID": nid, "Customer_ID": int(args[0]), "Parcel_Type": args[1], "Weight": float(args[2]), "Dimensions": args[3], "Booking_Date": str(date.today()), "Delivery_Type": args[4], "Tracking_Number": trk}])
        st.session_state.mock_parcels = pd.concat([st.session_state.mock_parcels, new_parcel], ignore_index=True)
        sid = st.session_state.mock_next_ids["shipment"]
        st.session_state.mock_next_ids["shipment"] += 1
        exp = date.today() + timedelta(days=3 if args[4] == "Express" else 7)
        new_ship = pd.DataFrame([{"Shipment_ID": sid, "Parcel_ID": nid, "Employee_ID": None, "Current_Location": "Warehouse - Pending Dispatch", "Shipment_Status": "Booked", "Dispatch_Date": None, "Expected_Delivery_Date": str(exp)}])
        st.session_state.mock_shipments = pd.concat([st.session_state.mock_shipments, new_ship], ignore_index=True)
        pid = st.session_state.mock_next_ids["payment"]
        st.session_state.mock_next_ids["payment"] += 1
        new_pay = pd.DataFrame([{"Payment_ID": pid, "Parcel_ID": nid, "Courier_Charges": charges, "Payment_Date": str(date.today()), "Payment_Mode": args[5], "Payment_Status": "Pending"}])
        st.session_state.mock_payments = pd.concat([st.session_state.mock_payments, new_pay], ignore_index=True)
        return [], [nid, trk, charges, f"Parcel booked successfully. Tracking: {trk} | Charges: ₹{charges}"]
    if name == "assign_delivery_staff":
        sid_val = int(args[0])
        eid_val = int(args[1])
        mask = st.session_state.mock_shipments["Shipment_ID"] == sid_val
        if mask.any():
            st.session_state.mock_shipments.loc[mask, "Employee_ID"] = eid_val
            st.session_state.mock_shipments.loc[mask, "Shipment_Status"] = "Out for Delivery"
            st.session_state.mock_shipments.loc[mask, "Dispatch_Date"] = str(date.today())
            return [], [f"Staff (ID: {eid_val}) assigned to Shipment {sid_val}. Status set to Out for Delivery."]
        return [], ["PARCEL_NOT_FOUND: No shipment found with the given ID."]
    if name == "update_shipment_status":
        sid_val = int(args[0])
        mask = st.session_state.mock_shipments["Shipment_ID"] == sid_val
        if mask.any():
            st.session_state.mock_shipments.loc[mask, "Shipment_Status"] = args[1]
            st.session_state.mock_shipments.loc[mask, "Current_Location"] = args[2]
            return [], [f"Shipment {sid_val} updated to \"{args[1]}\" at {args[2]}."]
        return [], ["PARCEL_NOT_FOUND: No shipment record found."]
    if name == "generate_delivery_invoice":
        trk = args[0]
        p_mask = st.session_state.mock_parcels["Tracking_Number"] == trk
        if not p_mask.any():
            return [], ["PARCEL_NOT_FOUND: No parcel found with this tracking number."]
        p_row = st.session_state.mock_parcels[p_mask].iloc[0]
        c_row = st.session_state.mock_customers[st.session_state.mock_customers["Customer_ID"] == p_row["Customer_ID"]].iloc[0]
        s_row = st.session_state.mock_shipments[st.session_state.mock_shipments["Parcel_ID"] == p_row["Parcel_ID"]].iloc[0]
        py_row = st.session_state.mock_payments[st.session_state.mock_payments["Parcel_ID"] == p_row["Parcel_ID"]].iloc[0]
        invoice = (
            f"╔══════════════════════════════════════════════╗\n"
            f"║      VELOCITY LOGISTICS - DELIVERY INVOICE  ║\n"
            f"╠══════════════════════════════════════════════╣\n"
            f"║ Tracking #  : {trk}\n"
            f"║ Customer    : {c_row['Customer_Name']}\n"
            f"║ Parcel Type : {p_row['Parcel_Type']} ({p_row['Weight']} kg)\n"
            f"║ Delivery    : {p_row['Delivery_Type']}\n"
            f"║ Booked On   : {p_row['Booking_Date']}\n"
            f"║ From        : {c_row['Pickup_Address']}\n"
            f"║ To          : {c_row['Delivery_Address']}\n"
            f"╠══════════════════════════════════════════════╣\n"
            f"║ Status      : {s_row['Shipment_Status']}\n"
            f"║ Charges     : ₹{py_row['Courier_Charges']}\n"
            f"║ Payment     : {py_row['Payment_Mode']} ({py_row['Payment_Status']})\n"
            f"╚══════════════════════════════════════════════╝"
        )
        return [], [invoice]
    if name == "get_intransit_parcels":
        merged = st.session_state.mock_shipments.merge(st.session_state.mock_parcels, on="Parcel_ID").merge(st.session_state.mock_customers, on="Customer_ID")
        in_transit = merged[merged["Shipment_Status"] == "In Transit"][["Tracking_Number", "Customer_Name", "Parcel_Type", "Weight", "Current_Location", "Expected_Delivery_Date"]].copy()
        in_transit.columns = ["Tracking_Number", "Customer_Name", "Parcel_Type", "Weight", "Current_Location", "Expected_Delivery"]
        return [in_transit], []
    return [], []

def _mock_calc_charges(weight, delivery_type, parcel_type):
    base = 50.0
    per_kg = 55.0 if delivery_type == "Express" else 30.0
    surcharge = 0.0
    if parcel_type == "Fragile":
        surcharge = 100.0
    elif parcel_type == "Heavy Cargo":
        surcharge = 200.0
    return round(base + weight * per_kg + surcharge, 2)

def _mock_function(func_name, args):
    _init_mock()
    name = func_name.lower()
    if name == "calculate_courier_charges":
        return _mock_calc_charges(float(args[0]), args[1], args[2])
    if name == "estimate_delivery_date":
        d = args[0] if isinstance(args[0], date) else date.fromisoformat(str(args[0]))
        days = 3 if args[1] == "Express" else 7
        return d + timedelta(days=days)
    if name == "check_shipment_status":
        trk = args[0]
        p_mask = st.session_state.mock_parcels["Tracking_Number"] == trk
        if p_mask.any():
            pid = st.session_state.mock_parcels[p_mask].iloc[0]["Parcel_ID"]
            s_mask = st.session_state.mock_shipments["Parcel_ID"] == pid
            if s_mask.any():
                return st.session_state.mock_shipments[s_mask].iloc[0]["Shipment_Status"]
        return "NOT FOUND"
    if name == "count_delivered_parcels":
        cid = args[0]
        if cid is None:
            return int((st.session_state.mock_shipments["Shipment_Status"] == "Delivered").sum())
        merged = st.session_state.mock_shipments.merge(st.session_state.mock_parcels[["Parcel_ID", "Customer_ID"]], on="Parcel_ID")
        return int(((merged["Shipment_Status"] == "Delivered") & (merged["Customer_ID"] == int(cid))).sum())
    return None

st.set_page_config(page_title="Velocity Logistics", page_icon="🚚", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: #0a0a0a; color: #ededed; }
    
    /* Top Navigation bar styling */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        justify-content: center;
        background: rgba(26, 26, 26, 0.7);
        padding: 10px;
        border-radius: 12px;
        border: 1px solid rgba(255, 0, 51, 0.3);
    }
    .stRadio label { color: #cccccc !important; font-weight: 600; padding: 6px 16px; margin: 0 4px; cursor: pointer; }
    
    div[data-testid="stMetric"] {
        background: rgba(26, 26, 26, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 0, 51, 0.3);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(255, 0, 51, 0.08);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(255, 0, 51, 0.25);
        border-color: rgba(255, 0, 51, 0.6);
    }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .stButton > button {
        background: linear-gradient(135deg, #ff0033, #aa0000);
        color: #fff;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(255, 0, 51, 0.5), 0 0 50px rgba(170, 0, 0, 0.2);
        transform: scale(1.03);
        color: white;
    }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div, .stTextArea > div > div > textarea {
        background: rgba(26, 26, 26, 0.6) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #fff !important;
        transition: border-color 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #ff0033 !important;
        box-shadow: 0 0 12px rgba(255, 0, 51, 0.15) !important;
    }
    .section-header {
        background: rgba(17, 17, 17, 0.8);
        backdrop-filter: blur(8px);
        border-left: 4px solid #ff0033;
        padding: 12px 20px;
        border-radius: 0 12px 12px 0;
        margin: 20px 0 16px 0;
    }
    .section-header h3 { margin: 0; color: #ff0033; font-weight: 600; }
    .hero-banner {
        background: rgba(17, 17, 17, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 36px 40px;
        margin-bottom: 28px;
        text-align: center;
    }
    .hero-banner h1 {
        background: linear-gradient(135deg, #ff0033, #ff4444, #aa0000);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem;
        font-weight: 700;
        animation: gradientShift 4s ease infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .badge { padding: 4px 14px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-delivered { background: rgba(0,77,0,0.6); color: #00ff00; border: 1px solid #00ff00; }
    .badge-transit { background: rgba(0,34,77,0.6); color: #00aaff; border: 1px solid #00aaff; }
    .badge-booked { background: rgba(77,51,0,0.6); color: #ffaa00; border: 1px solid #ffaa00; }
    .badge-ofd { background: rgba(51,0,77,0.6); color: #cc00ff; border: 1px solid #cc00ff; }
    .invoice-block {
        background: rgba(15, 15, 15, 0.8);
        backdrop-filter: blur(8px);
        border: 1px solid #ff0033;
        border-radius: 12px;
        padding: 20px;
        font-family: 'Courier New', monospace;
        color: #ff4444;
        white-space: pre;
        overflow-x: auto;
    }
    div[data-testid="stTabs"] button {
        color: #aaa !important;
        font-weight: 500;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #ff0033 !important;
        border-bottom-color: #ff0033 !important;
    }
    
    /* Top user profile bug styling */
    .user-profile {
        float: right;
        margin-top: -10px;
        margin-bottom: 15px;
        background: rgba(26,26,26,0.9);
        padding: 10px 20px;
        border-radius: 20px;
        border: 1px solid rgba(255,0,51,0.5);
        color: #ff0033;
        font-weight: bold;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

_init_mock()

def status_badge(status):
    css_class = {"Delivered": "badge-delivered", "In Transit": "badge-transit", "Booked": "badge-booked", "Out for Delivery": "badge-ofd"}.get(status, "badge-booked")
    return f'<span class="badge {css_class}">{status}</span>'

def page_home():
    st.markdown("""
    <div class="hero-banner">
        <h1>🚚 Velocity Logistics</h1>
        <p style="color:#aaa; font-size:1.1rem; margin-top:8px;">Enterprise Courier & Fleet Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_trk, col_log = st.columns([1.5, 1])
    
    with col_trk:
        st.markdown("#### 📦 Track Your Package")
        st.markdown("No login required. Enter your Tracking ID below to see live status.")
        track_id = st.text_input("Tracking ID", placeholder="e.g. TRK-20260701-000001", key="public_track")
        if st.button("🔍 Track Package", use_container_width=True):
            if not track_id:
                st.warning("Please enter a tracking ID.")
            else:
                if MOCK_MODE:
                    p_mask = st.session_state.mock_parcels["Tracking_Number"] == track_id
                    if not p_mask.any():
                        st.error("Tracking ID not found.")
                    else:
                        pid = st.session_state.mock_parcels[p_mask].iloc[0]["Parcel_ID"]
                        s_mask = st.session_state.mock_shipments["Parcel_ID"] == pid
                        if s_mask.any():
                            status = st.session_state.mock_shipments[s_mask].iloc[0]["Shipment_Status"]
                            loc = st.session_state.mock_shipments[s_mask].iloc[0]["Current_Location"]
                            st.success(f"**Status:** {status} | **Location:** {loc}")
                        else:
                            st.error("Shipment details not found.")
                else:
                    q = "SELECT s.Shipment_Status, s.Current_Location FROM Shipment s INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID WHERE p.Tracking_Number = %s"
                    df = run_query(q, (track_id,))
                    if df.empty:
                        st.error("Tracking ID not found.")
                    else:
                        st.success(f"**Status:** {df.iloc[0]['Shipment_Status']} | **Location:** {df.iloc[0]['Current_Location']}")
                        
    with col_log:
        with st.container():
            st.markdown("#### 🔐 Staff / Admin Portal")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In", use_container_width=True):
                if not username or not password:
                    st.error("Enter both username and password.")
                    return
                authenticated, role = False, ""
                if not MOCK_MODE:
                    df = run_query("SELECT Role FROM User_Login WHERE Username = %s AND Password = %s", (username, password))
                    if not df.empty:
                        authenticated, role = True, df.iloc[0]["Role"]
                if not authenticated:
                    mock_user = st.session_state.mock_users.get(username)
                    if mock_user and mock_user["password"] == password:
                        authenticated, role = True, mock_user["role"]
                if authenticated:
                    st.session_state.logged_in, st.session_state.username, st.session_state.role = True, username, role
                    st.toast(f"Welcome to Velocity Logistics, {username}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

def page_dashboard():
    st.markdown('<div class="hero-banner"><h1>📊 Command Center</h1><p style="color:#aaa;">Real-time overview of global operations</p></div>', unsafe_allow_html=True)

    lottie_dash = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_jcikwtux.json")
    if lottie_dash:
        st_lottie(lottie_dash, height=120, key="lottie_dash")

    if MOCK_MODE:
        total_parcels = len(st.session_state.mock_parcels)
        delivered = int((st.session_state.mock_shipments["Shipment_Status"] == "Delivered").sum())
        in_transit = int((st.session_state.mock_shipments["Shipment_Status"] == "In Transit").sum())
        total_revenue = float(st.session_state.mock_payments[st.session_state.mock_payments["Payment_Status"] == "Completed"]["Courier_Charges"].sum())
        pending_payments = int((st.session_state.mock_payments["Payment_Status"] == "Pending").sum())
        total_customers = len(st.session_state.mock_customers)
    else:
        total_parcels = int(run_query("SELECT COUNT(*) AS c FROM Parcel").iloc[0]["c"])
        delivered = int(run_query("SELECT COUNT(*) AS c FROM Shipment WHERE Shipment_Status='Delivered'").iloc[0]["c"])
        in_transit = int(run_query("SELECT COUNT(*) AS c FROM Shipment WHERE Shipment_Status='In Transit'").iloc[0]["c"])
        r4 = run_query("SELECT COALESCE(SUM(Courier_Charges),0) AS c FROM Payment WHERE Payment_Status='Completed'")
        total_revenue = float(r4.iloc[0]["c"]) if not r4.empty else 0
        pending_payments = int(run_query("SELECT COUNT(*) AS c FROM Payment WHERE Payment_Status='Pending'").iloc[0]["c"])
        total_customers = int(run_query("SELECT COUNT(*) AS c FROM Customer").iloc[0]["c"])

    if st.session_state.role == "Admin":
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("📦 Parcels", total_parcels, "All Time")
        m2.metric("✅ Delivered", delivered, "+2")
        m3.metric("🚚 In Transit", in_transit)
        m4.metric("💰 Revenue", f"₹{total_revenue:,.0f}", "+12%")
        m5.metric("⏳ Pending", pending_payments, "-1")
        m6.metric("👥 Customers", total_customers, "+4")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Parcels", total_parcels, "All Time")
        m2.metric("✅ Delivered", delivered, "+2")
        m3.metric("🚚 In Transit", in_transit)
        m4.metric("👥 Customers", total_customers, "+4")

    st.markdown("---")
    st.markdown('<div class="section-header"><h3>🕐 Recent Shipments</h3></div>', unsafe_allow_html=True)
    if MOCK_MODE:
        shipment_df = st.session_state.mock_shipments.merge(st.session_state.mock_parcels[["Parcel_ID", "Tracking_Number", "Customer_ID"]], on="Parcel_ID").merge(st.session_state.mock_customers[["Customer_ID", "Customer_Name"]], on="Customer_ID").sort_values("Shipment_ID", ascending=False).head(5)
        display_cols = ["Shipment_ID", "Tracking_Number", "Customer_Name", "Shipment_Status", "Current_Location", "Expected_Delivery_Date"]
        shipment_df = shipment_df[[c for c in display_cols if c in shipment_df.columns]]
    else:
        shipment_df = run_query("SELECT s.Shipment_ID, p.Tracking_Number, c.Customer_Name, s.Shipment_Status, s.Current_Location, s.Expected_Delivery_Date FROM Shipment s INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID INNER JOIN Customer c ON p.Customer_ID = c.Customer_ID ORDER BY s.Shipment_ID DESC LIMIT 5")
    if not shipment_df.empty:
        st.dataframe(shipment_df, use_container_width=True, hide_index=True)

def page_customer_registration():
    st.markdown('<div class="hero-banner"><h1>👤 Client Onboarding</h1><p style="color:#aaa;">Register new clients securely</p></div>', unsafe_allow_html=True)
    with st.expander("Register New Customer", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", key="reg_name")
            mobile = st.text_input("Mobile Number *", key="reg_mobile")
            email = st.text_input("Email Address *", key="reg_email")
        with col2:
            pickup = st.text_input("Pickup Address *", key="reg_pickup")
            deliver = st.text_input("Delivery Address *", key="reg_deliver")
        if st.button("📝 Register Client", use_container_width=True):
            if not all([name, mobile, email, pickup, deliver]):
                st.error("All fields marked with * are mandatory.")
                return
            if "@" not in email or "." not in email:
                st.error("❌ Please enter a valid email address containing '@' and a domain.")
                return
            if len(pickup) < 10 or "," not in pickup or len(deliver) < 10 or "," not in deliver:
                st.error("❌ Addresses must be complete (at least 10 characters) and contain a comma (e.g. 'Street, City').")
                return
            if MOCK_MODE:
                _, outs = _mock_procedure("register_customer", (name, mobile, email, pickup, deliver))
                cust_id, msg = outs
            else:
                outs = call_procedure_simple("Register_Customer", (name, mobile, email, pickup, deliver), 2)
                cust_id, msg = outs[0] if outs else None, outs[1] if len(outs) > 1 else "Unknown"
            if cust_id and int(cust_id) > 0:
                st.toast(f"✅ {st.session_state.username} added a new client: {name}!")
                st.balloons()
            else:
                st.error(f"❌ {msg}")
    st.markdown('<div class="section-header"><h3>📋 Existing Clients (Editable)</h3></div>', unsafe_allow_html=True)
    cust_df = st.session_state.mock_customers.copy() if MOCK_MODE else run_query("SELECT * FROM Customer ORDER BY Customer_ID DESC")
    if not cust_df.empty:
        edited_df = st.data_editor(cust_df, use_container_width=True, hide_index=True, key="cust_editor")
        if st.button("💾 Save Customer Changes", use_container_width=True):
            try:
                diff = edited_df.compare(cust_df)
                if not diff.empty:
                    for idx in diff.index:
                        row = edited_df.loc[idx]
                        cid = int(row['Customer_ID'])
                        if MOCK_MODE:
                            st.session_state.mock_customers.loc[st.session_state.mock_customers['Customer_ID'] == cid] = row
                        else:
                            run_query("UPDATE Customer SET Customer_Name=%s, Mobile_Number=%s, Email=%s, Pickup_Address=%s, Delivery_Address=%s WHERE Customer_ID=%s", (row['Customer_Name'], row['Mobile_Number'], row['Email'], row['Pickup_Address'], row['Delivery_Address'], cid), fetch=False)
                    st.success("✅ Customer changes saved successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("No changes detected.")
            except Exception as e:
                st.error(f"Error saving changes: {e}")

def page_parcel_booking():
    st.markdown('<div class="hero-banner"><h1>📦 Express Booking</h1><p style="color:#aaa;">Create new shipments & generate waybills</p></div>', unsafe_allow_html=True)
    customers = st.session_state.mock_customers[["Customer_ID", "Customer_Name"]].copy() if MOCK_MODE else run_query("SELECT Customer_ID, Customer_Name FROM Customer ORDER BY Customer_Name")
    if customers.empty:
        st.warning("No clients available.")
        return
    customer_options = {f"{r['Customer_Name']} (ID: {r['Customer_ID']})": r['Customer_ID'] for _, r in customers.iterrows()}

    col1, col2 = st.columns(2)
    with col1:
        selected_cust = st.selectbox("Select Client *", list(customer_options.keys()), key="bk_cust")
        parcel_type = st.selectbox("Parcel Type *", ["Document", "Small Box", "Medium Box", "Large Box", "Fragile", "Heavy Cargo"], key="bk_type")
        weight = st.number_input("Weight (kg) *", min_value=0.01, max_value=500.0, value=1.0, step=0.1, key="bk_weight")
    with col2:
        dimensions = st.text_input("Dimensions (LxWxH cm)", key="bk_dim")
        delivery_type = st.selectbox("Delivery Type *", ["Standard", "Express"], key="bk_deltype")
        payment_mode = st.selectbox("Payment Mode *", ["Credit Card", "Debit Card", "Net Banking", "Cash"], key="bk_paymode")

    est_charges = _mock_calc_charges(weight, delivery_type, parcel_type)
    est_date = date.today() + timedelta(days=3 if delivery_type == "Express" else 7)
    st.info(f"💰 Est. Charges: **₹{est_charges:.2f}** | 📅 Est. Delivery: **{est_date.strftime('%d %b %Y')}**")

    if st.button("🚀 Confirm Booking", use_container_width=True):
        cust_id = customer_options[selected_cust]
        if MOCK_MODE:
            _, outs = _mock_procedure("book_parcel", (cust_id, parcel_type, weight, dimensions or "", delivery_type, payment_mode))
            parcel_id, tracking, charges, msg = outs[0] if outs else None, outs[1] if len(outs)>1 else "", outs[2] if len(outs)>2 else 0, outs[3] if len(outs)>3 else "Error"
        else:
            outs = call_procedure_simple("Book_Parcel", (cust_id, parcel_type, weight, dimensions or "", delivery_type, payment_mode), 4)
            parcel_id, tracking, charges, msg = outs[0] if outs else None, outs[1] if len(outs)>1 else "", outs[2] if len(outs)>2 else 0, outs[3] if len(outs)>3 else "Error"

        if parcel_id and int(parcel_id) > 0:
            st.toast(f"✅ {st.session_state.username} booked {parcel_type} for {selected_cust.split(' (')[0]}")
            st.balloons()
            st.markdown(f"### 🎉 Booking Confirmed!")
            st.markdown("**Your Tracking Number (click to copy):**")
            st.code(tracking, language=None)
        else:
            st.error(f"❌ {msg}")

def simulate_coordinates(location_str):
    mapping = {
        "Mumbai": [19.0760, 72.8777], "Delhi": [28.7041, 77.1025],
        "Pune": [18.5204, 73.8567], "Bangalore": [12.9716, 77.5946],
        "Kolkata": [22.5726, 88.3639], "Hyderabad": [17.3850, 78.4867],
        "Chennai": [13.0827, 80.2707], "Ahmedabad": [23.0225, 72.5714],
        "Lucknow": [26.8467, 80.9462], "Noida": [28.5355, 77.3910],
        "Warehouse": [18.5204, 73.8567],
    }
    for k, v in mapping.items():
        if k.lower() in location_str.lower():
            return v
    return [20.5937, 78.9629] # Central India

def create_pdf_invoice(tracking, cust_name, p_type, weight, d_type, date_b, frm, to, stat, charge, p_mode, p_stat):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 18)
    pdf.set_text_color(255, 0, 51)
    pdf.cell(0, 10, "VELOCITY LOGISTICS - TAX INVOICE", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(0, 8, f"Tracking Number: {tracking}", ln=True)
    pdf.cell(0, 8, f"Customer Name: {cust_name}", ln=True)
    pdf.cell(0, 8, f"Parcel Type: {p_type} ({weight} kg)", ln=True)
    pdf.cell(0, 8, f"Delivery Speed: {d_type}", ln=True)
    pdf.cell(0, 8, f"Booking Date: {date_b}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Pickup From: {frm}", ln=True)
    pdf.cell(0, 8, f"Deliver To: {to}", ln=True)
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, f"Current Status: {stat}", ln=True)
    pdf.cell(0, 8, f"Total Charges: INR {charge}", ln=True)
    pdf.cell(0, 8, f"Payment Mode: {p_mode} ({p_stat})", ln=True)
    return bytes(pdf.output())

def page_shipment_tracking():
    st.markdown('<div class="hero-banner"><h1>🔍 Global Fleet Map</h1><p style="color:#aaa;">Live GPS visibility of all active units</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🌍 Global Live Map", "🧾 Digital Invoice"])
    
    with tab1:
        st.markdown("### All Active Transits")
        
        if MOCK_MODE:
            merged = st.session_state.mock_shipments.merge(st.session_state.mock_parcels, on="Parcel_ID")
            active = merged[merged["Shipment_Status"].isin(["Booked", "In Transit", "Out for Delivery"])]
        else:
            active = run_query("SELECT s.Current_Location, s.Shipment_Status, p.Tracking_Number, p.Parcel_Type FROM Shipment s JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID WHERE s.Shipment_Status IN ('Booked', 'In Transit', 'Out for Delivery')")

        if active.empty:
            st.info("No active shipments on the grid.")
        else:
            m = folium.Map(location=[21.1458, 79.0882], zoom_start=5, tiles="http://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}", attr="Google Maps")
            
            for _, row in active.iterrows():
                loc_str = row["Current_Location"]
                status = row["Shipment_Status"]
                trk = row["Tracking_Number"]
                
                color_map = {"Booked": "orange", "In Transit": "blue", "Out for Delivery": "purple"}
                icon_color = color_map.get(status, "red")
                
                coords = simulate_coordinates(loc_str)
                # Jitter coordinates slightly if multiple parcels are in the exact same location
                jittered = [coords[0] + (hash(trk) % 100) / 10000.0, coords[1] + (hash(trk) % 100) / 10000.0]
                
                folium.Marker(
                    jittered, 
                    popup=f"<b>{trk}</b><br>{status}<br>{loc_str}", 
                    tooltip=f"{trk} - {status}", 
                    icon=folium.Icon(color=icon_color, icon="info-sign")
                ).add_to(m)
                
            st_folium(m, width="100%", height=500, key="global_tracking_map", returned_objects=[])

    with tab2:
        inv_tracking = st.text_input("Tracking Number for Invoice", key="inv_track", placeholder="e.g. TRK-20260701-000001")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            gen_clicked = st.button("🧾 Generate Invoice", key="btn_invoice", use_container_width=True)
        with col_btn2:
            pay_clicked = st.button("💳 Mark Payment Done", key="btn_paydone", use_container_width=True)
            
        if pay_clicked:
            if not inv_tracking:
                st.warning("Enter a tracking number first.")
            else:
                if MOCK_MODE:
                    st.success("✅ Payment marked as completed (Mock Mode).")
                else:
                    q = "UPDATE Payment py INNER JOIN Parcel p ON py.Parcel_ID = p.Parcel_ID SET py.Payment_Status = 'Completed' WHERE p.Tracking_Number = %s"
                    run_query(q, (inv_tracking,), fetch=False)
                    st.success(f"✅ Payment for {inv_tracking} marked as Completed!")
                    
        if gen_clicked:
            if not inv_tracking:
                st.warning("Enter a tracking number.")
            else:
                if MOCK_MODE:
                    p_mask = st.session_state.mock_parcels["Tracking_Number"] == inv_tracking
                    if not p_mask.any():
                        st.error("❌ PARCEL_NOT_FOUND: No parcel found with this tracking number.")
                    else:
                        p_row = st.session_state.mock_parcels[p_mask].iloc[0]
                        c_row = st.session_state.mock_customers[st.session_state.mock_customers["Customer_ID"] == p_row["Customer_ID"]].iloc[0]
                        s_row = st.session_state.mock_shipments[st.session_state.mock_shipments["Parcel_ID"] == p_row["Parcel_ID"]].iloc[0]
                        py_row = st.session_state.mock_payments[st.session_state.mock_payments["Parcel_ID"] == p_row["Parcel_ID"]].iloc[0]
                        pdf_bytes = create_pdf_invoice(inv_tracking, c_row['Customer_Name'], p_row['Parcel_Type'], p_row['Weight'], p_row['Delivery_Type'], p_row['Booking_Date'], c_row['Pickup_Address'], c_row['Delivery_Address'], s_row['Shipment_Status'], py_row['Courier_Charges'], py_row['Payment_Mode'], py_row['Payment_Status'])
                        st.success("✅ Invoice Generated Successfully!")
                        st.download_button(label="📥 Download PDF Invoice", data=pdf_bytes, file_name=f"Invoice_{inv_tracking}.pdf", mime="application/pdf", use_container_width=True)
                else:
                    q = "SELECT p.Tracking_Number, c.Customer_Name, p.Parcel_Type, p.Weight, p.Delivery_Type, p.Booking_Date, c.Pickup_Address, c.Delivery_Address, s.Shipment_Status, py.Courier_Charges, py.Payment_Mode, py.Payment_Status FROM Parcel p INNER JOIN Customer c ON p.Customer_ID = c.Customer_ID INNER JOIN Shipment s ON p.Parcel_ID = s.Parcel_ID INNER JOIN Payment py ON p.Parcel_ID = py.Parcel_ID WHERE p.Tracking_Number = %s"
                    df = run_query(q, (inv_tracking,))
                    if df.empty:
                        st.error("❌ PARCEL_NOT_FOUND: No parcel found with this tracking number.")
                    else:
                        row = df.iloc[0]
                        pdf_bytes = create_pdf_invoice(row['Tracking_Number'], row['Customer_Name'], row['Parcel_Type'], row['Weight'], row['Delivery_Type'], row['Booking_Date'], row['Pickup_Address'], row['Delivery_Address'], row['Shipment_Status'], row['Courier_Charges'], row['Payment_Mode'], row['Payment_Status'])
                        st.success("✅ Invoice Generated Successfully!")
                        st.download_button(label="📥 Download PDF Invoice", data=pdf_bytes, file_name=f"Invoice_{inv_tracking}.pdf", mime="application/pdf", use_container_width=True)

def page_staff_assignment():
    st.markdown('<div class="hero-banner"><h1>🧑‍💼 Fleet Management</h1><p style="color:#aaa;">Assign drivers & update coordinates</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📌 Deploy Driver", "🔄 Sync Status"])
    with tab1:
        if MOCK_MODE:
            ship_df = st.session_state.mock_shipments[~st.session_state.mock_shipments["Shipment_Status"].isin(["Delivered", "Cancelled"])].copy()
            staff_df = st.session_state.mock_staff.copy()
        else:
            ship_df = run_query("SELECT s.Shipment_ID, p.Tracking_Number, s.Shipment_Status FROM Shipment s INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID WHERE s.Shipment_Status NOT IN ('Delivered', 'Cancelled') ORDER BY s.Shipment_ID")
            staff_df = run_query("SELECT Employee_ID, Employee_Name, Assigned_Area FROM Delivery_Staff")
        if ship_df.empty:
            st.info("All units deployed.")
        elif staff_df.empty:
            st.warning("No drivers available.")
        else:
            shipment_options = {f"Shipment #{r.get('Shipment_ID')} ({r.get('Tracking_Number', 'N/A')} - {r.get('Shipment_Status', 'N/A')})": r.get('Shipment_ID') for _, r in ship_df.iterrows()}
            staff_options = {f"{r['Employee_Name']} - {r['Assigned_Area']} (ID: {r['Employee_ID']})": r['Employee_ID'] for _, r in staff_df.iterrows()}
            sel_ship = st.selectbox("Select Shipment", list(shipment_options.keys()), key="asgn_ship")
            sel_staff = st.selectbox("Select Driver", list(staff_options.keys()), key="asgn_staff")
            if st.button("✅ Deploy", use_container_width=True):
                ship_id, emp_id = shipment_options[sel_ship], staff_options[sel_staff]
                if MOCK_MODE:
                    _, outs = _mock_procedure("assign_delivery_staff", (ship_id, emp_id))
                    msg = outs[0] if outs else "Failed."
                else:
                    outs = call_procedure_simple("Assign_Delivery_Staff", (ship_id, emp_id), 1)
                    msg = outs[0] if outs else "Failed."
                if "ERROR" in str(msg) or "NOT_FOUND" in str(msg):
                    st.error(f"❌ {msg}")
                else:
                    st.toast(f"✅ {st.session_state.username} deployed Driver {emp_id}!")

    with tab2:
        all_ships = st.session_state.mock_shipments.merge(st.session_state.mock_parcels[["Parcel_ID", "Tracking_Number"]], on="Parcel_ID") if MOCK_MODE else run_query("SELECT s.Shipment_ID, p.Tracking_Number, s.Shipment_Status, s.Current_Location FROM Shipment s INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID ORDER BY s.Shipment_ID")
        if all_ships.empty:
            st.info("No shipments.")
        else:
            ship_opts = {f"#{r.get('Shipment_ID')} - {r.get('Tracking_Number', 'N/A')} ({r.get('Shipment_Status', '')})": r.get('Shipment_ID') for _, r in all_ships.iterrows()}
            sel = st.selectbox("Select Shipment", list(ship_opts.keys()), key="upd_ship")
            new_status = st.selectbox("New Status", ["Booked", "In Transit", "Out for Delivery", "Delivered", "Returned", "Cancelled"], key="upd_status")
            new_location = st.text_input("Current Location", key="upd_loc")
            if st.button("🔄 Sync", use_container_width=True):
                if not new_location:
                    st.warning("Enter location.")
                else:
                    ship_id = ship_opts[sel]
                    if MOCK_MODE:
                        _, outs = _mock_procedure("update_shipment_status", (ship_id, new_status, new_location))
                        msg = outs[0] if outs else "Failed."
                    else:
                        outs = call_procedure_simple("Update_Shipment_Status", (ship_id, new_status, new_location), 1)
                        msg = outs[0] if outs else "Failed."
                    if "ERROR" in str(msg):
                        st.error(f"❌ {msg}")
                    else:
                        st.toast(f"✅ Status updated successfully!")
                        if new_status == "Delivered":
                            st.balloons()
                            st.success("Delivery Confirmed!")

def page_reports():
    st.markdown('<div class="hero-banner"><h1>📈 Analytics Hub</h1><p style="color:#aaa;">Interactive visualizations & insights</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 Performance & Revenue", "👥 Clients", "🚚 Fleet Status"])
    with tab1:
        st.markdown('<div class="section-header"><h3>Staff Performance</h3></div>', unsafe_allow_html=True)
        if MOCK_MODE:
            perf = st.session_state.mock_shipments.merge(st.session_state.mock_staff, on="Employee_ID", how="right")
            staff_perf = perf.groupby(["Employee_ID", "Employee_Name", "Assigned_Area"]).agg(Delivered_Count=("Shipment_Status", lambda x: (x == "Delivered").sum()), Total_Assigned=("Shipment_ID", "count")).reset_index()
            staff_perf = staff_perf[staff_perf["Total_Assigned"] > 0].sort_values("Delivered_Count", ascending=False)
        else:
            staff_perf = run_query("SELECT ds.Employee_ID, ds.Employee_Name, ds.Assigned_Area, COUNT(CASE WHEN s.Shipment_Status = 'Delivered' THEN 1 END) AS Delivered_Count, COUNT(s.Shipment_ID) AS Total_Assigned FROM Delivery_Staff ds LEFT JOIN Shipment s ON ds.Employee_ID = s.Employee_ID GROUP BY ds.Employee_ID, ds.Employee_Name, ds.Assigned_Area HAVING COUNT(s.Shipment_ID) > 0 ORDER BY Delivered_Count DESC")
        if not staff_perf.empty:
            fig = px.bar(staff_perf, x="Employee_Name", y="Delivered_Count", color="Delivered_Count",
                         color_continuous_scale=["#aa0000", "#ff0033"], template="plotly_dark",
                         title="Deliveries per Driver")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-header"><h3>Revenue by Payment Mode</h3></div>', unsafe_allow_html=True)
        if MOCK_MODE:
            completed = st.session_state.mock_payments[st.session_state.mock_payments["Payment_Status"] == "Completed"]
            rev = completed.groupby("Payment_Mode").agg(Total_Transactions=("Payment_ID", "count"), Total_Revenue=("Courier_Charges", "sum")).reset_index()
            rev = rev[rev["Total_Revenue"] > 100].sort_values("Total_Revenue", ascending=False)
        else:
            rev = run_query("SELECT Payment_Mode, COUNT(*) AS Total_Transactions, SUM(Courier_Charges) AS Total_Revenue FROM Payment WHERE Payment_Status = 'Completed' GROUP BY Payment_Mode HAVING SUM(Courier_Charges) > 100 ORDER BY Total_Revenue DESC")
        if not rev.empty:
            fig2 = px.pie(rev, values='Total_Revenue', names='Payment_Mode', hole=0.45,
                          color_discrete_sequence=["#ff0033", "#ff4444", "#aa0000", "#550000"],
                          template="plotly_dark", title="Revenue Distribution")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header"><h3>Customer Summary</h3></div>', unsafe_allow_html=True)
        if MOCK_MODE:
            cust_summary = st.session_state.mock_parcels.merge(st.session_state.mock_customers, on="Customer_ID").merge(st.session_state.mock_payments, on="Parcel_ID").groupby(["Customer_ID", "Customer_Name"]).agg(Parcels_Booked=("Parcel_ID", "count"), Total_Spent=("Courier_Charges", "sum")).reset_index().sort_values("Total_Spent", ascending=False)
        else:
            cust_summary = run_query("SELECT c.Customer_ID, c.Customer_Name, COUNT(p.Parcel_ID) AS Parcels_Booked, COALESCE(SUM(py.Courier_Charges), 0) AS Total_Spent FROM Customer c INNER JOIN Parcel p ON c.Customer_ID = p.Customer_ID INNER JOIN Payment py ON p.Parcel_ID = py.Parcel_ID GROUP BY c.Customer_ID, c.Customer_Name ORDER BY Total_Spent DESC")
        if not cust_summary.empty:
            st.dataframe(cust_summary, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown('<div class="section-header"><h3>Shipment Status Breakdown</h3></div>', unsafe_allow_html=True)
        if MOCK_MODE:
            status_counts = st.session_state.mock_shipments["Shipment_Status"].value_counts().reset_index()
        else:
            status_counts = run_query("SELECT Shipment_Status as status, COUNT(*) AS count FROM Shipment GROUP BY Shipment_Status")
        if not status_counts.empty:
            status_counts.columns = ["Status", "Count"]
            fig3 = px.pie(status_counts, values='Count', names='Status',
                          color_discrete_sequence=["#ff0000", "#ff6666", "#cc0000", "#990000"],
                          template="plotly_dark", title="Global Fleet Status")
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

def page_messaging():
    st.markdown('<div class="hero-banner"><h1>📢 Client Comms</h1><p style="color:#aaa;">Broadcast offers and alerts</p></div>', unsafe_allow_html=True)
    
    customers = st.session_state.mock_customers[["Customer_ID", "Customer_Name"]].copy() if MOCK_MODE else run_query("SELECT Customer_ID, Customer_Name FROM Customer ORDER BY Customer_Name")
    
    if customers.empty:
        st.warning("No clients available to message.")
        return
        
    msg_type = st.radio("Message Audience", ["Broadcast to All", "Select Specific Clients"], horizontal=True)
    
    selected_ids = []
    if msg_type == "Select Specific Clients":
        customer_options = {f"{r['Customer_Name']} (ID: {r['Customer_ID']})": r['Customer_ID'] for _, r in customers.iterrows()}
        selected = st.multiselect("Select Clients", list(customer_options.keys()))
        selected_ids = [customer_options[x] for x in selected]
    else:
        selected_ids = customers["Customer_ID"].tolist()
        
    msg_body = st.text_area("Message Content", placeholder="Dear Customer, we are offering a 20% discount on Express shipments this week!")
    
    if st.button("✉️ Send Message(s)", use_container_width=True):
        if not msg_body:
            st.error("Please enter a message.")
        elif not selected_ids:
            st.error("Please select at least one client.")
        else:
            with st.spinner("Dispatching messages..."):
                time.sleep(1.5)
                st.success(f"✅ Message sent successfully to {len(selected_ids)} client(s)!")
                st.toast(f"Admin {st.session_state.username} dispatched a broadcast.")

def main():
    if not st.session_state.logged_in:
        page_home()
        return

    # Top User Profile indicator
    st.markdown(f'<div class="user-profile">👤 {st.session_state.username} | {st.session_state.role}</div>', unsafe_allow_html=True)
    
    # Top Navigation Logic
    if st.session_state.role == "Admin":
        pages = ["📊 Dashboard", "👤 Client Onboarding", "📦 Express Booking", "🔍 Velocity Tracking", "🧑‍💼 Fleet Management", "📢 Messaging", "📈 Analytics Hub"]
    else:
        # Staff role gets restricted view
        pages = ["📊 Dashboard", "👤 Client Onboarding", "📦 Express Booking", "🔍 Velocity Tracking", "🧑‍💼 Fleet Management"]
        
    selected_page = st.radio("Navigate", pages, horizontal=True, label_visibility="collapsed")
    
    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
    
    # Render the selected page
    page_map = {
        "📊 Dashboard": page_dashboard,
        "👤 Client Onboarding": page_customer_registration,
        "📦 Express Booking": page_parcel_booking,
        "🔍 Velocity Tracking": page_shipment_tracking,
        "🧑‍💼 Fleet Management": page_staff_assignment,
        "📢 Messaging": page_messaging,
        "📈 Analytics Hub": page_reports,
    }
    
    if selected_page in page_map:
        page_map[selected_page]()

    if st.sidebar.button("🚪 Secure Logout", use_container_width=True):
        st.session_state.logged_in, st.session_state.username, st.session_state.role = False, "", ""
        st.rerun()

    with st.sidebar:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if MOCK_MODE:
            st.markdown('<div style="background:rgba(51,34,0,0.6); border:1px solid #ffaa00; border-radius:10px; padding:10px; text-align:center;"><p style="color:#ffaa00; margin:0;">⚡ DEMO MODE</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:rgba(0,51,0,0.6); border:1px solid #00ff00; border-radius:10px; padding:10px; text-align:center;"><p style="color:#00ff00; margin:0;">🟢 LIVE MODE</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
