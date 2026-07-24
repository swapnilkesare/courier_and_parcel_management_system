DROP DATABASE IF EXISTS courier_management;
CREATE DATABASE courier_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE courier_management;

CREATE TABLE User_Login (
    Username        VARCHAR(50)     PRIMARY KEY,
    Password        VARCHAR(255)    NOT NULL,
    Role            ENUM('Admin', 'Staff', 'Customer')
                                    NOT NULL DEFAULT 'Customer'
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

-- Added more users for robust testing
INSERT INTO User_Login (Username, Password, Role) VALUES
    ('admin',       'Admin@2026',   'Admin'),
    ('staff_raj',   'Raj$taff1',    'Staff'),
    ('staff_neha',  'Neha$taff2',   'Staff'),
    ('staff_amit',  'Amit$taff3',   'Staff'),
    ('cust_amit',   'Amit#123',     'Customer'),
    ('cust_priya',  'Priya#456',    'Customer'),
    ('cust_rahul',  'Rahul#789',    'Customer'),
    ('cust_sneha',  'Sneha#012',    'Customer');

-- Expanded customer base
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
        '22 Anna Nagar, Chennai',      '44 Koramangala, Bangalore'),
    ('Neha Sharma',   '9811223344', 'neha.s@email.com', 
        '12 Janpath, Delhi',           '45 MG Road, Bangalore'),
    ('Karan Patel',   '9822334455', 'karan.p@email.com', 
        '78 SG Highway, Ahmedabad',    '34 Nariman Point, Mumbai'),
    ('Pooja Singh',   '9833445566', 'pooja.s@email.com', 
        '56 Hazratganj, Lucknow',      '90 Sector 18, Noida'),
    ('Rahul Dravid',  '9844556677', 'rahul.d@email.com', 
        '100 Indiranagar, Bangalore',  '22 T Nagar, Chennai'),
    ('Aditi Rao',     '9855667788', 'aditi.r@email.com', 
        '11 Koregaon Park, Pune',      '33 Banjara Hills, Hyderabad');

INSERT INTO Delivery_Staff (Employee_Name, Mobile_Number, Assigned_Area) VALUES
    ('Rajesh Kumar',    '9800011122', 'Mumbai - Western'),
    ('Neha Gupta',      '9800033344', 'Delhi - Central'),
    ('Sanjay Pawar',    '9800055566', 'Pune - East'),
    ('Meera Nair',      '9800077788', 'Bangalore - South'),
    ('Arjun Singh',     '9800099900', 'Kolkata - North'),
    ('Deepa Rao',       '9800012345', 'Hyderabad - West');

DELIMITER $$

DROP TRIGGER IF EXISTS trg_auto_tracking$$
CREATE TRIGGER trg_auto_tracking
BEFORE INSERT ON Parcel
FOR EACH ROW
BEGIN
    IF NEW.Tracking_Number IS NULL OR NEW.Tracking_Number = '' THEN
        SET NEW.Tracking_Number = CONCAT(
            'TRK-',
            DATE_FORMAT(COALESCE(NEW.Booking_Date, CURDATE()), '%Y%m%d'),
            '-',
            LPAD(FLOOR(RAND() * 999999), 6, '0')
        );
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_check_customer_info$$
CREATE TRIGGER trg_check_customer_info
BEFORE INSERT ON Customer
FOR EACH ROW
BEGIN
    IF NEW.Customer_Name IS NULL OR TRIM(NEW.Customer_Name) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: Customer_Name is mandatory.';
    END IF;

    IF NEW.Mobile_Number IS NULL OR TRIM(NEW.Mobile_Number) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: Mobile_Number is mandatory.';
    END IF;

    IF NEW.Email IS NULL OR TRIM(NEW.Email) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: Email is mandatory.';
    END IF;

    IF NEW.Pickup_Address IS NULL OR TRIM(NEW.Pickup_Address) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: Pickup_Address is mandatory.';
    END IF;

    IF NEW.Delivery_Address IS NULL OR TRIM(NEW.Delivery_Address) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: Delivery_Address is mandatory.';
    END IF;
END$$

DELIMITER ;

-- Added more parcels
INSERT INTO Parcel (Customer_ID, Parcel_Type, Weight, Dimensions, Booking_Date, Delivery_Type, Tracking_Number) VALUES
    (1, 'Document',    0.50, '30x22x2',    '2026-07-01', 'Standard', 'TRK-20260701-000001'),
    (2, 'Small Box',   2.00, '25x20x15',   '2026-07-02', 'Express',  'TRK-20260702-000002'),
    (3, 'Medium Box',  5.50, '40x30x25',   '2026-07-03', 'Standard', 'TRK-20260703-000003'),
    (4, 'Large Box',  12.00, '60x45x40',   '2026-07-05', 'Express',  'TRK-20260705-000004'),
    (1, 'Fragile',     3.20, '35x25x20',   '2026-07-07', 'Express',  'TRK-20260707-000005'),
    (5, 'Heavy Cargo',25.00, '80x60x50',   '2026-07-10', 'Standard', 'TRK-20260710-000006'),
    (6, 'Document',    0.30, '28x21x1',    '2026-07-12', 'Standard', 'TRK-20260712-000007'),
    (3, 'Small Box',   1.80, '22x18x12',   '2026-07-15', 'Express',  'TRK-20260715-000008'),
    (7, 'Document',    0.20, '25x15x1',    '2026-07-18', 'Express',  'TRK-20260718-000009'),
    (8, 'Medium Box',  6.00, '30x30x30',   '2026-07-19', 'Standard', 'TRK-20260719-000010'),
    (9, 'Small Box',   2.50, '20x20x10',   '2026-07-20', 'Express',  'TRK-20260720-000011'),
    (10, 'Large Box', 15.00, '70x50x40',   '2026-07-21', 'Standard', 'TRK-20260721-000012'),
    (11, 'Fragile',    4.50, '40x30x20',   '2026-07-22', 'Express',  'TRK-20260722-000013');

-- Added more shipments
INSERT INTO Shipment (Parcel_ID, Employee_ID, Current_Location, Shipment_Status, Dispatch_Date, Expected_Delivery_Date) VALUES
    (1, 1, 'Mumbai Hub',           'Delivered',          '2026-07-02', '2026-07-06'),
    (2, 2, 'Delhi Sorting Centre', 'Delivered',          '2026-07-03', '2026-07-05'),
    (3, 5, 'Kolkata Hub',          'Out for Delivery',   '2026-07-04', '2026-07-09'),
    (4, 6, 'Hyderabad Hub',        'In Transit',         '2026-07-06', '2026-07-08'),
    (5, 1, 'Mumbai Hub',           'In Transit',         '2026-07-08', '2026-07-10'),
    (6, 3, 'Pune Warehouse',       'Booked',             NULL,         '2026-07-17'),
    (7, 4, 'Bangalore Hub',        'In Transit',         '2026-07-13', '2026-07-18'),
    (8, 2, 'Delhi Hub',            'Booked',             NULL,         '2026-07-18'),
    (9, 2, 'Delhi Hub',            'In Transit',         '2026-07-19', '2026-07-21'),
    (10, 1, 'Ahmedabad Warehouse', 'Booked',             NULL,         '2026-07-26'),
    (11, 2, 'Lucknow Sorting Hub', 'Out for Delivery',   '2026-07-21', '2026-07-23'),
    (12, 4, 'Bangalore Hub',       'In Transit',         '2026-07-22', '2026-07-28'),
    (13, 3, 'Pune Warehouse',      'Booked',             NULL,         '2026-07-25');

-- Added more payments
INSERT INTO Payment (Parcel_ID, Courier_Charges, Payment_Date, Payment_Mode, Payment_Status) VALUES
    (1,   80.00, '2026-07-01', 'UPI',          'Completed'),
    (2,  250.00, '2026-07-02', 'Credit Card',  'Completed'),
    (3,  320.00, '2026-07-03', 'Debit Card',   'Completed'),
    (4,  750.00, '2026-07-05', 'Net Banking',  'Completed'),
    (5,  400.00, '2026-07-07', 'UPI',          'Pending'),
    (6, 1100.00, '2026-07-10', 'Cash',         'Pending'),
    (7,   70.00, '2026-07-12', 'UPI',          'Completed'),
    (8,  230.00, '2026-07-15', 'Credit Card',  'Pending'),
    (9,   65.00, '2026-07-18', 'UPI',          'Completed'),
    (10, 350.00, '2026-07-19', 'Debit Card',   'Completed'),
    (11, 190.00, '2026-07-20', 'Credit Card',  'Completed'),
    (12, 850.00, '2026-07-21', 'Net Banking',  'Pending'),
    (13, 390.00, '2026-07-22', 'UPI',          'Completed');

DELIMITER $$

DROP FUNCTION IF EXISTS Calculate_Courier_Charges$$
CREATE FUNCTION Calculate_Courier_Charges(
    p_weight        DECIMAL(8,2),
    p_delivery_type VARCHAR(10),
    p_parcel_type   VARCHAR(20)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_base_rate     DECIMAL(10,2) DEFAULT 50.00;
    DECLARE v_per_kg_rate   DECIMAL(10,2);
    DECLARE v_surcharge     DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_total         DECIMAL(10,2);

    IF p_delivery_type = 'Express' THEN
        SET v_per_kg_rate = 55.00;
    ELSE
        SET v_per_kg_rate = 30.00;
    END IF;

    IF p_parcel_type = 'Fragile' THEN
        SET v_surcharge = 100.00;
    ELSEIF p_parcel_type = 'Heavy Cargo' THEN
        SET v_surcharge = 200.00;
    END IF;

    SET v_total = v_base_rate + (p_weight * v_per_kg_rate) + v_surcharge;
    RETURN v_total;
END$$

DROP FUNCTION IF EXISTS Estimate_Delivery_Date$$
CREATE FUNCTION Estimate_Delivery_Date(
    p_booking_date  DATE,
    p_delivery_type VARCHAR(10)
)
RETURNS DATE
DETERMINISTIC
BEGIN
    IF p_delivery_type = 'Express' THEN
        RETURN DATE_ADD(p_booking_date, INTERVAL 3 DAY);
    ELSE
        RETURN DATE_ADD(p_booking_date, INTERVAL 7 DAY);
    END IF;
END$$

DROP FUNCTION IF EXISTS Check_Shipment_Status$$
CREATE FUNCTION Check_Shipment_Status(
    p_tracking_number VARCHAR(30)
)
RETURNS VARCHAR(50)
READS SQL DATA
BEGIN
    DECLARE v_status VARCHAR(50) DEFAULT 'NOT FOUND';

    SELECT s.Shipment_Status INTO v_status
    FROM Shipment s
    INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID
    WHERE p.Tracking_Number = p_tracking_number
    LIMIT 1;

    RETURN v_status;
END$$

DROP FUNCTION IF EXISTS Count_Delivered_Parcels$$
CREATE FUNCTION Count_Delivered_Parcels(
    p_customer_id INT
)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_count INT DEFAULT 0;

    IF p_customer_id IS NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM Shipment
        WHERE Shipment_Status = 'Delivered';
    ELSE
        SELECT COUNT(*) INTO v_count
        FROM Shipment s
        INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID
        WHERE s.Shipment_Status = 'Delivered'
          AND p.Customer_ID = p_customer_id;
    END IF;

    RETURN v_count;
END$$

DELIMITER ;

DELIMITER $$

DROP TRIGGER IF EXISTS trg_status_out_for_delivery$$
CREATE TRIGGER trg_status_out_for_delivery
AFTER UPDATE ON Shipment
FOR EACH ROW
BEGIN
    IF OLD.Employee_ID IS NULL AND NEW.Employee_ID IS NOT NULL
       AND NEW.Shipment_Status NOT IN ('Delivered', 'Returned', 'Cancelled') THEN
        BEGIN
        END;
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_status_delivered$$
CREATE TRIGGER trg_status_delivered
BEFORE UPDATE ON Shipment
FOR EACH ROW
BEGIN
    IF NEW.Current_Location LIKE '%Delivered to Customer%' THEN
        SET NEW.Shipment_Status = 'Delivered';
    END IF;
END$$

DELIMITER ;

DELIMITER $$

DROP PROCEDURE IF EXISTS Register_Customer$$
CREATE PROCEDURE Register_Customer(
    IN  p_name      VARCHAR(100),
    IN  p_mobile    VARCHAR(15),
    IN  p_email     VARCHAR(100),
    IN  p_pickup    VARCHAR(255),
    IN  p_delivery  VARCHAR(255),
    OUT p_cust_id   INT,
    OUT p_message   VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        SET p_cust_id = -1;
        SET p_message = 'ERROR: Duplicate email address. Customer already exists.';
    END;

    DECLARE EXIT HANDLER FOR SQLSTATE '45000'
    BEGIN
        GET DIAGNOSTICS CONDITION 1 p_message = MESSAGE_TEXT;
        SET p_cust_id = -1;
    END;

    INSERT INTO Customer (Customer_Name, Mobile_Number, Email, Pickup_Address, Delivery_Address)
    VALUES (p_name, p_mobile, p_email, p_pickup, p_delivery);

    SET p_cust_id = LAST_INSERT_ID();
    SET p_message = CONCAT('Customer registered successfully with ID: ', p_cust_id);
END$$

DROP PROCEDURE IF EXISTS Book_Parcel$$
CREATE PROCEDURE Book_Parcel(
    IN  p_customer_id   INT,
    IN  p_parcel_type   VARCHAR(20),
    IN  p_weight        DECIMAL(8,2),
    IN  p_dimensions    VARCHAR(50),
    IN  p_delivery_type VARCHAR(10),
    IN  p_payment_mode  VARCHAR(20),
    OUT p_parcel_id     INT,
    OUT p_tracking      VARCHAR(30),
    OUT p_charges       DECIMAL(10,2),
    OUT p_message       VARCHAR(255)
)
BEGIN
    DECLARE v_cust_exists INT DEFAULT 0;
    DECLARE v_booking_date DATE;
    DECLARE v_expected_date DATE;

    DECLARE EXIT HANDLER FOR SQLSTATE '45000'
    BEGIN
        GET DIAGNOSTICS CONDITION 1 p_message = MESSAGE_TEXT;
        SET p_parcel_id = -1;
    END;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_parcel_id = -1;
        SET p_message = 'ERROR: An unexpected database error occurred during booking.';
        ROLLBACK;
    END;

    SELECT COUNT(*) INTO v_cust_exists FROM Customer WHERE Customer_ID = p_customer_id;
    IF v_cust_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: No customer found with the given ID.';
    END IF;

    START TRANSACTION;

    SET v_booking_date = CURDATE();

    SET p_charges = Calculate_Courier_Charges(p_weight, p_delivery_type, p_parcel_type);

    SET v_expected_date = Estimate_Delivery_Date(v_booking_date, p_delivery_type);

    INSERT INTO Parcel (Customer_ID, Parcel_Type, Weight, Dimensions, Booking_Date, Delivery_Type)
    VALUES (p_customer_id, p_parcel_type, p_weight, p_dimensions, v_booking_date, p_delivery_type);

    SET p_parcel_id = LAST_INSERT_ID();

    SELECT Tracking_Number INTO p_tracking FROM Parcel WHERE Parcel_ID = p_parcel_id;

    INSERT INTO Shipment (Parcel_ID, Current_Location, Shipment_Status, Expected_Delivery_Date)
    VALUES (p_parcel_id, 'Warehouse - Pending Dispatch', 'Booked', v_expected_date);

    INSERT INTO Payment (Parcel_ID, Courier_Charges, Payment_Date, Payment_Mode, Payment_Status)
    VALUES (p_parcel_id, p_charges, v_booking_date, p_payment_mode, 'Pending');

    COMMIT;

    SET p_message = CONCAT('Parcel booked successfully. Tracking: ', p_tracking,
                           ' | Charges: ₹', p_charges);
END$$

DROP PROCEDURE IF EXISTS Assign_Delivery_Staff$$
CREATE PROCEDURE Assign_Delivery_Staff(
    IN  p_shipment_id   INT,
    IN  p_employee_id   INT,
    OUT p_message       VARCHAR(255)
)
BEGIN
    DECLARE v_ship_exists INT DEFAULT 0;
    DECLARE v_emp_exists  INT DEFAULT 0;
    DECLARE v_current_status VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_message = 'ERROR: Failed to assign delivery staff.';
    END;

    SELECT COUNT(*), MAX(Shipment_Status) INTO v_ship_exists, v_current_status
    FROM Shipment WHERE Shipment_ID = p_shipment_id;

    IF v_ship_exists = 0 THEN
        SET p_message = 'PARCEL_NOT_FOUND: No shipment found with the given ID.';
    ELSEIF v_current_status IN ('Delivered', 'Returned', 'Cancelled') THEN
        SET p_message = CONCAT('ERROR: Cannot assign staff. Shipment is already ', v_current_status, '.');
    ELSE
        SELECT COUNT(*) INTO v_emp_exists FROM Delivery_Staff WHERE Employee_ID = p_employee_id;
        IF v_emp_exists = 0 THEN
            SET p_message = 'ERROR: No delivery staff found with the given Employee ID.';
        ELSE
            UPDATE Shipment
            SET Employee_ID     = p_employee_id,
                Shipment_Status = 'Out for Delivery',
                Dispatch_Date   = COALESCE(Dispatch_Date, CURDATE())
            WHERE Shipment_ID = p_shipment_id;

            SET p_message = CONCAT('Staff (ID: ', p_employee_id,
                                   ') assigned to Shipment ', p_shipment_id,
                                   '. Status set to Out for Delivery.');
        END IF;
    END IF;
END$$

DROP PROCEDURE IF EXISTS Update_Shipment_Status$$
CREATE PROCEDURE Update_Shipment_Status(
    IN  p_shipment_id   INT,
    IN  p_new_status    VARCHAR(20),
    IN  p_new_location  VARCHAR(150),
    OUT p_message       VARCHAR(255)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_message = 'ERROR: Failed to update shipment status.';
    END;

    SELECT COUNT(*) INTO v_exists FROM Shipment WHERE Shipment_ID = p_shipment_id;

    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'PARCEL_NOT_FOUND: No shipment record found.';
    END IF;

    UPDATE Shipment
    SET Shipment_Status  = p_new_status,
        Current_Location = p_new_location
    WHERE Shipment_ID = p_shipment_id;

    SET p_message = CONCAT('Shipment ', p_shipment_id,
                           ' updated to "', p_new_status,
                           '" at ', p_new_location, '.');
END$$

DROP PROCEDURE IF EXISTS Generate_Delivery_Invoice$$
CREATE PROCEDURE Generate_Delivery_Invoice(
    IN  p_tracking_number VARCHAR(30),
    OUT p_invoice_text    TEXT
)
BEGIN
    DECLARE v_parcel_id     INT;
    DECLARE v_cust_name     VARCHAR(100);
    DECLARE v_parcel_type   VARCHAR(20);
    DECLARE v_weight        DECIMAL(8,2);
    DECLARE v_delivery_type VARCHAR(10);
    DECLARE v_tracking      VARCHAR(30);
    DECLARE v_booking_date  DATE;
    DECLARE v_status        VARCHAR(20);
    DECLARE v_charges       DECIMAL(10,2);
    DECLARE v_pay_mode      VARCHAR(20);
    DECLARE v_pay_status    VARCHAR(20);
    DECLARE v_pickup        VARCHAR(255);
    DECLARE v_delivery_addr VARCHAR(255);

    DECLARE EXIT HANDLER FOR SQLSTATE '45000'
    BEGIN
        GET DIAGNOSTICS CONDITION 1 p_invoice_text = MESSAGE_TEXT;
    END;

    SELECT p.Parcel_ID, c.Customer_Name, p.Parcel_Type, p.Weight,
           p.Delivery_Type, p.Tracking_Number, p.Booking_Date,
           s.Shipment_Status, py.Courier_Charges, py.Payment_Mode,
           py.Payment_Status, c.Pickup_Address, c.Delivery_Address
    INTO   v_parcel_id, v_cust_name, v_parcel_type, v_weight,
           v_delivery_type, v_tracking, v_booking_date,
           v_status, v_charges, v_pay_mode, v_pay_status,
           v_pickup, v_delivery_addr
    FROM Parcel p
    INNER JOIN Customer c  ON p.Customer_ID = c.Customer_ID
    INNER JOIN Shipment s  ON p.Parcel_ID   = s.Parcel_ID
    INNER JOIN Payment  py ON p.Parcel_ID   = py.Parcel_ID
    WHERE p.Tracking_Number = p_tracking_number
    LIMIT 1;

    IF v_parcel_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'PARCEL_NOT_FOUND: No parcel found with this tracking number.';
    END IF;

    SET p_invoice_text = CONCAT(
        '╔══════════════════════════════════════════════╗\n',
        '║      VELOCITY LOGISTICS - DELIVERY INVOICE  ║\n',
        '╠══════════════════════════════════════════════╣\n',
        '║ Tracking #  : ', v_tracking, '\n',
        '║ Customer    : ', v_cust_name, '\n',
        '║ Parcel Type : ', v_parcel_type, ' (', v_weight, ' kg)\n',
        '║ Delivery    : ', v_delivery_type, '\n',
        '║ Booked On   : ', v_booking_date, '\n',
        '║ From        : ', v_pickup, '\n',
        '║ To          : ', v_delivery_addr, '\n',
        '╠══════════════════════════════════════════════╣\n',
        '║ Status      : ', v_status, '\n',
        '║ Charges     : ₹', v_charges, '\n',
        '║ Payment     : ', v_pay_mode, ' (', v_pay_status, ')\n',
        '╚══════════════════════════════════════════════╝'
    );
END$$

DROP PROCEDURE IF EXISTS Get_InTransit_Parcels$$
CREATE PROCEDURE Get_InTransit_Parcels()
BEGIN
    DECLARE v_tracking      VARCHAR(30);
    DECLARE v_cust_name     VARCHAR(100);
    DECLARE v_parcel_type   VARCHAR(20);
    DECLARE v_weight        DECIMAL(8,2);
    DECLARE v_location      VARCHAR(150);
    DECLARE v_expected_date DATE;
    DECLARE v_done          INT DEFAULT 0;

    DECLARE cur_in_transit CURSOR FOR
        SELECT p.Tracking_Number,
               c.Customer_Name,
               p.Parcel_Type,
               p.Weight,
               s.Current_Location,
               s.Expected_Delivery_Date
        FROM Shipment s
        INNER JOIN Parcel   p ON s.Parcel_ID   = p.Parcel_ID
        INNER JOIN Customer c ON p.Customer_ID = c.Customer_ID
        WHERE s.Shipment_Status = 'In Transit';

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET v_done = 1;

    DROP TEMPORARY TABLE IF EXISTS tmp_in_transit;
    CREATE TEMPORARY TABLE tmp_in_transit (
        Tracking_Number     VARCHAR(30),
        Customer_Name       VARCHAR(100),
        Parcel_Type         VARCHAR(20),
        Weight              DECIMAL(8,2),
        Current_Location    VARCHAR(150),
        Expected_Delivery   DATE
    );

    OPEN cur_in_transit;

    fetch_loop: LOOP
        FETCH cur_in_transit INTO v_tracking, v_cust_name, v_parcel_type,
                                  v_weight, v_location, v_expected_date;
        IF v_done = 1 THEN
            LEAVE fetch_loop;
        END IF;

        INSERT INTO tmp_in_transit VALUES
            (v_tracking, v_cust_name, v_parcel_type,
             v_weight, v_location, v_expected_date);
    END LOOP;

    CLOSE cur_in_transit;

    SELECT * FROM tmp_in_transit;
END$$

DROP PROCEDURE IF EXISTS Safe_Track_Parcel$$
CREATE PROCEDURE Safe_Track_Parcel(
    IN  p_tracking_number VARCHAR(30),
    IN  p_customer_id     INT,
    OUT p_status          VARCHAR(50),
    OUT p_message         VARCHAR(255)
)
BEGIN
    DECLARE v_cust_exists   INT DEFAULT 0;
    DECLARE v_parcel_exists INT DEFAULT 0;
    DECLARE v_dup_count     INT DEFAULT 0;
    DECLARE v_found_status  VARCHAR(50);

    DECLARE CONTINUE HANDLER FOR SQLWARNING
    BEGIN
        SET p_message = 'WARNING: A non-critical issue occurred.';
    END;

    SELECT COUNT(*) INTO v_cust_exists FROM Customer WHERE Customer_ID = p_customer_id;
    IF v_cust_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'INVALID_CUSTOMER: The provided Customer ID does not exist.';
    END IF;

    SELECT COUNT(*) INTO v_dup_count
    FROM Parcel WHERE Tracking_Number = p_tracking_number;

    IF v_dup_count > 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DUP_TRACKING_NO: Multiple parcels share this tracking number. Contact support.';
    END IF;

    SELECT s.Shipment_Status INTO v_found_status
    FROM Shipment s
    INNER JOIN Parcel p ON s.Parcel_ID = p.Parcel_ID
    WHERE p.Tracking_Number = p_tracking_number
      AND p.Customer_ID = p_customer_id
    LIMIT 1;

    IF v_found_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'PARCEL_NOT_FOUND: No parcel matches this tracking number for the given customer.';
    END IF;

    SET p_status  = v_found_status;
    SET p_message = CONCAT('Parcel ', p_tracking_number, ' is currently: ', v_found_status);
END$$

DELIMITER ;

SELECT 'Velocity Logistics Database Setup Complete!' AS status;
