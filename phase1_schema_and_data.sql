
DROP DATABASE IF EXISTS courier_management;
CREATE DATABASE courier_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE courier_management;

CREATE TABLE User_Login (
    Username        VARCHAR(50)     PRIMARY KEY,
    Password        VARCHAR(255)    NOT NULL,
    Role            ENUM('Admin', 'Staff')
                                    NOT NULL DEFAULT 'Staff'
) ENGINE=InnoDB;

CREATE TABLE Customer (
    Customer_ID         INT             AUTO_INCREMENT PRIMARY KEY,
    Customer_Name       VARCHAR(100)    NOT NULL,
    Mobile_Number       VARCHAR(15)     NOT NULL,
    Email               VARCHAR(100)    NOT NULL UNIQUE,
    Pickup_Address      VARCHAR(255)    NOT NULL,
    Delivery_Address    VARCHAR(255)    NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Parcel (
    Parcel_ID           INT             AUTO_INCREMENT PRIMARY KEY,
    Customer_ID         INT             NOT NULL,
    Parcel_Type         ENUM('Document', 'Small Box', 'Medium Box',
                             'Large Box', 'Fragile', 'Heavy Cargo')
                                        NOT NULL,
    Weight              DECIMAL(8,2)    NOT NULL CHECK (Weight > 0),
    Dimensions          VARCHAR(50)     DEFAULT NULL
                                        COMMENT 'LxWxH in cm',
    Booking_Date        DATE            NOT NULL DEFAULT (CURRENT_DATE),
    Delivery_Type       ENUM('Standard', 'Express')
                                        NOT NULL DEFAULT 'Standard',
    Tracking_Number     VARCHAR(30)     UNIQUE,

    CONSTRAINT fk_parcel_customer
        FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE Delivery_Staff (
    Employee_ID         INT             AUTO_INCREMENT PRIMARY KEY,
    Employee_Name       VARCHAR(100)    NOT NULL,
    Mobile_Number       VARCHAR(15)     NOT NULL,
    Assigned_Area       VARCHAR(100)    NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Shipment (
    Shipment_ID             INT             AUTO_INCREMENT PRIMARY KEY,
    Parcel_ID               INT             NOT NULL,
    Employee_ID             INT             DEFAULT NULL,
    Current_Location        VARCHAR(150)    NOT NULL DEFAULT 'Warehouse',
    Shipment_Status         ENUM('Booked', 'In Transit', 'Out for Delivery',
                                 'Delivered', 'Returned', 'Cancelled')
                                            NOT NULL DEFAULT 'Booked',
    Dispatch_Date           DATE            DEFAULT NULL,
    Expected_Delivery_Date  DATE            DEFAULT NULL,

    CONSTRAINT fk_shipment_parcel
        FOREIGN KEY (Parcel_ID) REFERENCES Parcel(Parcel_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_shipment_staff
        FOREIGN KEY (Employee_ID) REFERENCES Delivery_Staff(Employee_ID)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE Payment (
    Payment_ID          INT             AUTO_INCREMENT PRIMARY KEY,
    Parcel_ID           INT             NOT NULL,
    Courier_Charges     DECIMAL(10,2)   NOT NULL CHECK (Courier_Charges >= 0),
    Payment_Date        DATE            NOT NULL DEFAULT (CURRENT_DATE),
    Payment_Mode        ENUM('Cash', 'Credit Card', 'Debit Card',
                             'UPI', 'Net Banking')
                                        NOT NULL DEFAULT 'UPI',
    Payment_Status      ENUM('Pending', 'Completed', 'Refunded', 'Failed')
                                        NOT NULL DEFAULT 'Pending',

    CONSTRAINT fk_payment_parcel
        FOREIGN KEY (Parcel_ID) REFERENCES Parcel(Parcel_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;



INSERT INTO User_Login (Username, Password, Role) VALUES
    ('admin',       'Admin@2026',   'Admin'),
    ('staff_raj',   'Raj$taff1',    'Staff'),
    ('staff_neha',  'Neha$taff2',   'Staff');

INSERT INTO Customer (Customer_Name, Mobile_Number, Email, Pickup_Address, Delivery_Address) VALUES
    ('Amit Sharma',   '9876543210', 'amit.sharma@email.com',
        '12 MG Road, Pune',            '45 Park Street, Mumbai'),
    ('Priya Desai',   '9123456780', 'priya.desai@email.com',
        '78 FC Road, Pune',            '23 Lajpat Nagar, Delhi'),
    ('Rahul Verma',   '9988776655', 'rahul.verma@email.com',
        '34 Brigade Road, Bangalore',  '11 Salt Lake, Kolkata'),
    ('Sneha Patil',   '9871234560', 'sneha.patil@email.com',
        '56 JM Road, Pune',            '89 Banjara Hills, Hyderabad'),
    ('Vikram Joshi',  '9765432100', 'vikram.joshi@email.com',
        '90 Connaught Place, Delhi',   '67 Boat Club Road, Pune'),
    ('Ananya Iyer',   '9654321098', 'ananya.iyer@email.com',
        '22 Anna Nagar, Chennai',      '44 Koramangala, Bangalore');

INSERT INTO Parcel (Customer_ID, Parcel_Type, Weight, Dimensions, Booking_Date, Delivery_Type, Tracking_Number) VALUES
    (1, 'Document',    0.50, '30x22x2',    '2026-07-01', 'Standard', 'TRK-20260701-000001'),
    (2, 'Small Box',   2.00, '25x20x15',   '2026-07-02', 'Express',  'TRK-20260702-000002'),
    (3, 'Medium Box',  5.50, '40x30x25',   '2026-07-03', 'Standard', 'TRK-20260703-000003'),
    (4, 'Large Box',  12.00, '60x45x40',   '2026-07-05', 'Express',  'TRK-20260705-000004'),
    (1, 'Fragile',     3.20, '35x25x20',   '2026-07-07', 'Express',  'TRK-20260707-000005'),
    (5, 'Heavy Cargo',25.00, '80x60x50',   '2026-07-10', 'Standard', 'TRK-20260710-000006'),
    (6, 'Document',    0.30, '28x21x1',    '2026-07-12', 'Standard', 'TRK-20260712-000007'),
    (3, 'Small Box',   1.80, '22x18x12',   '2026-07-15', 'Express',  'TRK-20260715-000008');

INSERT INTO Delivery_Staff (Employee_Name, Mobile_Number, Assigned_Area) VALUES
    ('Rajesh Kumar',    '9800011122', 'Mumbai - Western'),
    ('Neha Gupta',      '9800033344', 'Delhi - Central'),
    ('Sanjay Pawar',    '9800055566', 'Pune - East'),
    ('Meera Nair',      '9800077788', 'Bangalore - South'),
    ('Arjun Singh',     '9800099900', 'Kolkata - North'),
    ('Deepa Rao',       '9800012345', 'Hyderabad - West');

INSERT INTO Shipment (Parcel_ID, Employee_ID, Current_Location, Shipment_Status, Dispatch_Date, Expected_Delivery_Date) VALUES
    (1, 1, 'Mumbai Hub',           'Delivered',          '2026-07-02', '2026-07-06'),
    (2, 2, 'Delhi Sorting Centre', 'Delivered',          '2026-07-03', '2026-07-05'),
    (3, 5, 'Kolkata Hub',          'Out for Delivery',   '2026-07-04', '2026-07-09'),
    (4, 6, 'Hyderabad Hub',        'In Transit',         '2026-07-06', '2026-07-08'),
    (5, 1, 'Mumbai Hub',           'In Transit',         '2026-07-08', '2026-07-10'),
    (6, 3, 'Pune Warehouse',       'Booked',             NULL,         '2026-07-17'),
    (7, 4, 'Bangalore Hub',        'In Transit',         '2026-07-13', '2026-07-18'),
    (8, 2, 'Delhi Hub',            'Booked',             NULL,         '2026-07-18');

INSERT INTO Payment (Parcel_ID, Courier_Charges, Payment_Date, Payment_Mode, Payment_Status) VALUES
    (1,   80.00, '2026-07-01', 'UPI',          'Completed'),
    (2,  250.00, '2026-07-02', 'Credit Card',  'Completed'),
    (3,  320.00, '2026-07-03', 'Debit Card',   'Completed'),
    (4,  750.00, '2026-07-05', 'Net Banking',  'Completed'),
    (5,  400.00, '2026-07-07', 'UPI',          'Pending'),
    (6, 1100.00, '2026-07-10', 'Cash',         'Pending'),
    (7,   70.00, '2026-07-12', 'UPI',          'Completed'),
    (8,  230.00, '2026-07-15', 'Credit Card',  'Pending');



SELECT
    py.Payment_Mode,
    COUNT(*)                AS Total_Transactions,
    SUM(py.Courier_Charges) AS Total_Revenue
FROM Payment py
WHERE py.Payment_Status = 'Completed'
GROUP BY py.Payment_Mode
HAVING SUM(py.Courier_Charges) > 100
ORDER BY Total_Revenue DESC;

SELECT
    c.Customer_ID,
    c.Customer_Name,
    COUNT(p.Parcel_ID)      AS Parcels_Booked,
    COALESCE(SUM(py.Courier_Charges), 0) AS Total_Spent
FROM Customer c
INNER JOIN Parcel  p  ON c.Customer_ID = p.Customer_ID
INNER JOIN Payment py ON p.Parcel_ID   = py.Parcel_ID
GROUP BY c.Customer_ID, c.Customer_Name
ORDER BY Total_Spent DESC;

SELECT
    s.Shipment_ID,
    p.Tracking_Number,
    c.Customer_Name,
    s.Shipment_Status,
    s.Current_Location,
    COALESCE(ds.Employee_Name, 'Unassigned') AS Assigned_To,
    s.Expected_Delivery_Date
FROM Shipment s
INNER JOIN Parcel         p  ON s.Parcel_ID   = p.Parcel_ID
INNER JOIN Customer       c  ON p.Customer_ID = c.Customer_ID
LEFT  JOIN Delivery_Staff ds ON s.Employee_ID = ds.Employee_ID
ORDER BY s.Expected_Delivery_Date;

SELECT
    p.Parcel_ID,
    p.Tracking_Number,
    c.Customer_Name,
    py.Courier_Charges,
    p.Delivery_Type
FROM Parcel p
INNER JOIN Customer c  ON p.Customer_ID = c.Customer_ID
INNER JOIN Payment  py ON p.Parcel_ID   = py.Parcel_ID
WHERE py.Courier_Charges > (
    SELECT AVG(Courier_Charges) FROM Payment
)
ORDER BY py.Courier_Charges DESC;

SELECT
    ds.Employee_ID,
    ds.Employee_Name,
    ds.Assigned_Area,
    COUNT(CASE WHEN s.Shipment_Status = 'Delivered' THEN 1 END) AS Delivered_Count,
    COUNT(s.Shipment_ID)                                         AS Total_Assigned
FROM Delivery_Staff ds
LEFT JOIN Shipment s ON ds.Employee_ID = s.Employee_ID
GROUP BY ds.Employee_ID, ds.Employee_Name, ds.Assigned_Area
HAVING COUNT(s.Shipment_ID) > 0
ORDER BY Delivered_Count DESC;