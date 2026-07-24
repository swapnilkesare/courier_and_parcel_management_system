# Velocity Logistics - Enterprise Courier & Fleet Management System

Velocity Logistics is a comprehensive database management system (DBMS) micro-project built to handle courier, parcel, and fleet management operations efficiently. The application provides an intuitive interface for both customers and administrative staff to track, book, and manage parcel deliveries globally.

## 🚀 Key Features

- **Public Tracking Portal**: Customers can track their packages in real-time without needing to log in, using their unique Tracking ID.
- **Admin/Staff Dashboard**: Secure portal for staff to view metrics, manage parcels, and oversee operations.
- **Client Onboarding**: Easy registration process for new customers with validation for details like email and addresses.
- **Express Booking System**: Calculate estimated charges based on weight, parcel type, and delivery speed. Book shipments and instantly generate tracking numbers.
- **Global Fleet Map**: Live GPS visibility simulation of all active transport units.
- **Digital Invoicing**: Generate and download professional PDF invoices for booked parcels.

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python) with custom CSS for a modern, responsive UI.
- **Backend**: Python with Pandas for data manipulation.
- **Database**: MySQL (using `mysql-connector-python`) for persistent storage.
  - *Note*: The application includes a mock mode that activates automatically if the database connection fails, allowing the app to run seamlessly for demonstration purposes.
- **Visualization**: Plotly Express for charts, Folium & `streamlit-folium` for interactive maps.
- **Other Utilities**: `fpdf` for generating PDF invoices, `streamlit-lottie` for animations.

## 📦 Getting Started

### Prerequisites

Ensure you have Python installed, along with the required dependencies:

```bash
pip install -r requirements.txt
```

### Database Setup (Optional)

1. Open MySQL Workbench (or any MySQL client).
2. Execute the provided SQL scripts in the following order:
   - `setup.sql` - Creates the database schema, tables, and relationships.
   - `phase1_schema_and_data.sql` - Inserts mock data into the tables.
   - `phase2_procedures_triggers.sql` - Sets up stored procedures and triggers.
3. Update the database connection credentials in `app.py` if necessary (default is `root`/`root` on `localhost`).

### Running the Application

To start the Velocity Logistics application, run:

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your web browser to view the app.

---
*This project was developed as a DBMS Micro Project.*
