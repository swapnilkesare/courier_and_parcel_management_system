USE courier_management;


DELIMITER //

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
END //

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
END //

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
END //

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
END //



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
END //

CREATE TRIGGER trg_status_out_for_delivery
AFTER UPDATE ON Shipment
FOR EACH ROW
BEGIN
    IF OLD.Employee_ID IS NULL AND NEW.Employee_ID IS NOT NULL
       AND NEW.Shipment_Status NOT IN ('Delivered', 'Returned', 'Cancelled') THEN
        BEGIN
        END;
    END IF;
END //

CREATE TRIGGER trg_status_delivered
BEFORE UPDATE ON Shipment
FOR EACH ROW
BEGIN
    IF NEW.Current_Location LIKE '%Delivered to Customer%' THEN
        SET NEW.Shipment_Status = 'Delivered';
    END IF;
END //

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
END //



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
END //

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
END //

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
END //

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
END //

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
        '║        COURIER DELIVERY INVOICE              ║\n',
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
END //



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
END //



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
END //

DELIMITER ;

