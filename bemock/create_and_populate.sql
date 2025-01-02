CREATE TYPE MEMBERSHIP_TYPE AS ENUM ('Standard', 'Premium', 'VIP');
CREATE TYPE USER_STATUS as ENUM ('Active', 'Inactive');
CREATE TYPE BIKE_STATUS as ENUM ('In_Use', 'Available', 'Maintenance', 'Retired');
CREATE TYPE CURRENCY as ENUM ('EURO', 'USD', 'RON');
CREATE TYPE PAYMENT_METHOD as ENUM ('Card', 'Account');

-- Crearea tabelelor
CREATE TABLE Users (
    UserID INT PRIMARY KEY,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Email VARCHAR(100),
    PhoneNumber VARCHAR(15),
    RegistrationDate DATE,
    MembershipType MEMBERSHIP_TYPE,
    Status USER_STATUS
);

CREATE TABLE Bikes (
    BikeID INT PRIMARY KEY,
    BikeType VARCHAR(20),
    PurchaseDate DATE,
    BikeProducer VARCHAR(50),
    BikeDefaultTarif DECIMAL(5, 2)
);

CREATE TABLE Inventory (
    InventoryID INT PRIMARY KEY,
    BikeID INT,
    CheckDate TIMESTAMP,
    Status BIKE_STATUS,
    Notes TEXT,
    FOREIGN KEY (BikeID) REFERENCES Bikes(BikeID)
);

CREATE TABLE Rentals (
    RentalID INT PRIMARY KEY,
    UserID INT,
    BikeID INT,
    StartTime TIMESTAMP,
    EndTime TIMESTAMP,
    StartLocation VARCHAR(100),
    EndLocation VARCHAR(100),
    Status VARCHAR(20),
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (BikeID) REFERENCES Bikes(BikeID)
);

CREATE TABLE Payments (
    PaymentID INT PRIMARY KEY,
    RentalID INT,
    PaymentDate TIMESTAMP,
    Amount DECIMAL(10, 2),
    PaymentMethod PAYMENT_METHOD,
    Currency CURRENCY,
    CardNumberHint VARCHAR(4), --last 4 digits of card
    FOREIGN KEY (RentalID) REFERENCES Rentals(RentalID)
);

CREATE TABLE MaintenanceLogs (
    LogID INT PRIMARY KEY,
    BikeID INT,
    MaintenanceDate DATE,
    Description TEXT,
    Cost DECIMAL(10, 2),
    TechnicianName VARCHAR(50),
    FOREIGN KEY (BikeID) REFERENCES Bikes(BikeID)
);

-- Populare Users
INSERT INTO Users (UserID, FirstName, LastName, Email, PhoneNumber, RegistrationDate, MembershipType, Status)
SELECT LEVEL,
       'User' || LEVEL,
       'Last' || LEVEL,
       'user' || LEVEL || '@example.com',
       '+4074' || LPAD(TO_CHAR(LEVEL), 6, '0'),
       TRUNC(SYSDATE - DBMS_RANDOM.VALUE(1000, 2000)),
       CASE MOD(LEVEL, 3) WHEN 0 THEN 'Standard' WHEN 1 THEN 'Premium' ELSE 'VIP' END::MEMBERSHIP_TYPE,
       CASE MOD(LEVEL, 2) WHEN 0 THEN 'Active' ELSE 'Inactive' END::USER_STATUS
FROM DUAL CONNECT BY LEVEL <= 50;

-- Populare Bikes
INSERT INTO Bikes (BikeID, BikeType, PurchaseDate, BikeProducer, BikeDefaultTarif)
SELECT LEVEL,
       CASE MOD(LEVEL, 4) WHEN 0 THEN 'Mountain' WHEN 1 THEN 'Road' WHEN 2 THEN 'Electric' ELSE 'Hybrid' END,
       TRUNC(SYSDATE - DBMS_RANDOM.VALUE(1000, 1500)),
       CASE MOD(LEVEL, 3) WHEN 0 THEN 'Giant' WHEN 1 THEN 'Trek' ELSE 'Specialized' END,
       ROUND(DBMS_RANDOM.VALUE(0.2, 2), 2)
FROM DUAL CONNECT BY LEVEL <= 30;

-- Generare intrări pentru tabela Inventory (cu available)
DECLARE
    v_inventory_id INT := 1;
    v_available_date DATE;
BEGIN
    FOR bike_rec IN (
        SELECT BikeID, PurchaseDate 
        FROM Bikes
    ) LOOP
        -- Generăm o dată random pentru "Available", la cel puțin 1 zi după PurchaseDate
        v_available_date := bike_rec.PurchaseDate + INTERVAL '1 day' * FLOOR(DBMS_RANDOM.VALUE(1, 365));

        -- Adăugăm înregistrarea în Inventory
        INSERT INTO Inventory (InventoryID, BikeID, CheckDate, Status, Notes)
        VALUES (
            v_inventory_id,
            bike_rec.BikeID,
            v_available_date,
            'Available'::BIKE_STATUS,
            'Initial availability after purchase'
        );

        -- Incrementăm InventoryID
        v_inventory_id := v_inventory_id + 1;
    END LOOP;
    COMMIT;
END;
/

-- Generare rentaluri si inventory asociat + payments
DECLARE
    v_rental_id INT := 1;
    v_payment_id INT := 1;
    v_inventory_id INT := 1;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
BEGIN
    FOR user_rec IN (
        SELECT UserID, RegistrationDate FROM Users WHERE Status = 'Active'::USER_STATUS
    ) LOOP
        FOR bike_rec IN (
            SELECT BikeID, PurchaseDate 
            FROM Bikes
        ) LOOP
            -- Găsirea celei mai apropiate date disponibile pentru bicicletă plecand de la ultima data disponibila
            FOR inventory_rec IN (
                SELECT CheckDate 
                FROM Inventory 
                WHERE BikeID = bike_rec.BikeID AND Status = 'Available'::BIKE_STATUS
                ORDER BY CheckDate
                LIMIT 1
            ) LOOP
                v_start_time := GREATEST(
                    user_rec.RegistrationDate + INTERVAL '1 day',
                    bike_rec.PurchaseDate + INTERVAL '1 day', --date + interval -> timestamp
                    inventory_rec.CheckDate
                ) + INTERVAL '1 hour' * FLOOR(DBMS_RANDOM.VALUE(9, 21)); -- Start între 9:00 și 21:00
                
                v_end_time := v_start_time + INTERVAL '1 minute' * FLOOR(DBMS_RANDOM.VALUE(10, 60)); -- Durează 15-60 min

                -- Adăugăm închirieri și actualizăm inventarul
                INSERT INTO Rentals (RentalID, UserID, BikeID, StartTime, EndTime, StartLocation, EndLocation, Status)
                VALUES (
                    v_rental_id,
                    user_rec.UserID,
                    bike_rec.BikeID,
                    v_start_time,
                    v_end_time,
                    'Location ' || DBMS_RANDOM.VALUE(1, 10),
                    'Location ' || DBMS_RANDOM.VALUE(1, 10),
                    'Success'
                );

                -- Adăugăm Inventory pentru începutul închirierii
                INSERT INTO Inventory (InventoryID, BikeID, CheckDate, Status, Notes)
                VALUES (
                    v_inventory_id,
                    bike_rec.BikeID,
                    v_start_time,
                    'In_Use'::BIKE_STATUS,
                    'Bike in use for rental ' || v_rental_id
                );
                v_inventory_id := v_inventory_id + 1;

                -- Adăugăm Inventory pentru sfârșitul închirierii
                INSERT INTO Inventory (InventoryID, BikeID, CheckDate, Status, Notes)
                VALUES (
                    v_inventory_id,
                    bike_rec.BikeID,
                    v_end_time,
                    'Available'::BIKE_STATUS,
                    'Bike available after rental ' || v_rental_id
                );
                v_inventory_id := v_inventory_id + 1;

                SELECT bike_rate, start_time, end_time 
                INTO v_bike_rate, v_start_time, v_end_time
                FROM Rentals
                WHERE RentalID = v_rental_id;

                -- Adăugăm Payment pentru închiriere
                INSERT INTO Payments (PaymentID, RentalID, PaymentDate, Amount, PaymentMethod, Currency, CardNumberHint)
                VALUES (
                    v_payment_id,
                    v_rental_id,
                    v_end_time,
                    ROUND(
                        v_bike_rate * 
                        (CASE 
                            WHEN user_rec.UserType = 'Premium' THEN 0.9 
                            WHEN user_rec.UserType = 'VIP' THEN 0.8 
                            ELSE 1 
                        END) * 
                        (EXTRACT(MINUTE FROM (v_end_time - v_start_time)) + 
                        EXTRACT(HOUR FROM (v_end_time - v_start_time)) * 60), 
                    2),
                    CASE MOD(v_payment_id, 2) WHEN 0 THEN 'Card' ELSE 'Account' END::PAYMENT_METHOD,
                    CASE MOD(v_payment_id, 3) WHEN 0 THEN 'RON' WHEN 1 THEN 'EURO' ELSE 'USD' END::CURRENCY,
                    SUBSTR(v_card_number, -4)
                );
                v_payment_id := v_payment_id + 1;

                -- Incrementăm ID-ul închirierii
                v_rental_id := v_rental_id + 1;

                -- Ieșim din bucla de Inventory pentru a evita suprapunerea închirierilor
                EXIT;
            END LOOP;
        END LOOP;
    END LOOP;
    COMMIT;
END;
/

-- Populare cu cateva maintenance
DECLARE
    v_maintenance_id INT := 1;
    v_inventory_id INT := (SELECT MAX(InventoryID) FROM Inventory) + 1;
    maintenance_date DATE;
BEGIN
    FOR bike_rec IN (
        SELECT BikeID, PurchaseDate 
        FROM Bikes
        LIMIT 5
    ) LOOP
        -- Găsirea celei mai apropiate date disponibile pentru bicicletă plecand de la ultima data disponibila
        FOR inventory_rec IN (
            SELECT CheckDate 
            FROM Inventory 
            WHERE BikeID = bike_rec.BikeID AND Status = 'Available'::BIKE_STATUS
            ORDER BY CheckDate
            LIMIT 1
        ) LOOP
            maintenance_date := CAST(inventory_rec.CheckDate AS DATE) + INTERVAL '1 day';             
            maintenance_date_end := v_start_time + INTERVAL '1 day';

            -- Adăugăm Inventory pentru începutul închirierii
            INSERT INTO Inventory (InventoryID, BikeID, CheckDate, Status, Notes)
            VALUES (
                v_inventory_id,
                bike_rec.BikeID,
                maintenance_date,
                'Maintenance'::BIKE_STATUS,
                'Bike in use for maintenance '
            );
            v_inventory_id := v_inventory_id + 1;

            -- Adăugăm Inventory pentru sfârșitul închirierii
            INSERT INTO Inventory (InventoryID, BikeID, CheckDate, Status, Notes)
            VALUES (
                v_inventory_id,
                bike_rec.BikeID,
                maintenance_date_end,
                'Available'::BIKE_STATUS,
                'Bike available after maintenance'
            );
            v_inventory_id := v_inventory_id + 1;

            INSERT INTO MaintenanceLogs (LogID, BikeID, MaintenanceDate, Description, Cost, TechnicianName)
            VALUES (
                v_maintenance_id,
                bike_rec.BikeID,
                maintenance_date_end,
                'General maintenance',
                ROUND(DBMS_RANDOM.VALUE(10, 100), 2),
                'Technician ' || DBMS_RANDOM.VALUE(1, 10)
            );
            v_maintenance_id := v_maintenance_id + 1;

            EXIT;
        END LOOP;
    END LOOP;
    COMMIT;
END;
/

COMMIT;
