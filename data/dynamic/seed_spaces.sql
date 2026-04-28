---- SCHEMA DEFINITIONS ----

CREATE TABLE IF NOT EXISTS city (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    province   TEXT,
    population INTEGER
);

CREATE TABLE IF NOT EXISTS human_resources (
    id                    TEXT PRIMARY KEY,
    name                  TEXT NOT NULL,
    surname               TEXT NOT NULL,
    role                  TEXT,
    social_security_code  TEXT,
    disabilities          INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS docking_stations (
    id                        TEXT PRIMARY KEY,
    name                      TEXT NOT NULL,
    city_id                   TEXT NOT NULL REFERENCES city(id),
    shift_human_supervisor_id TEXT REFERENCES human_resources(id),
    total_spaces              INTEGER,
    free_spaces               INTEGER,
    occupied_spaces           INTEGER,
    off_peak_rate             REAL,
    peak_rate                 REAL,
    opening_hours             TEXT,
    closing_hours             TEXT,
    ai_supervision            INTEGER DEFAULT 1  -- 1 = true
);

CREATE TABLE IF NOT EXISTS prices (
    id                  TEXT PRIMARY KEY,
    docking_station_id  TEXT NOT NULL REFERENCES docking_stations(id),
    vehicle_class       TEXT NOT NULL,
    period              TEXT NOT NULL,
    rate_per_hour       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id                   TEXT PRIMARY KEY,
    docking_station_id   TEXT NOT NULL REFERENCES docking_stations(id),
    customer_name        TEXT NOT NULL,
    vehicle_class        TEXT NOT NULL,
    arrival_start        TEXT NOT NULL,
    arrival_end          TEXT NOT NULL,
    estimated_departure  TEXT NOT NULL,
    booking_channel      TEXT NOT NULL,
    payment_method       TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'booked',
    enhancements         TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);



---- DATA POPULATION ----

BEGIN TRANSACTION;

-- Cities
INSERT INTO city (id, name, province, population) VALUES
    ('CITY-NT', 'Neo-Terra Megacity', 'Helix District', 9870000),
    ('CITY-AX', 'Axios Canal Urban Zone', 'Reclaimer Province', 2100000);

-- Human resources
INSERT INTO human_resources (id, name, surname, role, social_security_code, disabilities) VALUES
    ('HR-001', 'Mira', 'Solace', 'Operations Supervisor', 'NT-8834-9921', 0),
    ('HR-002', 'Daxon', 'Wilde', 'Night Shift Coordinator', 'NT-5541-1884', 0),
    ('HR-003', 'Eli',   'Kale',  'Accessibility Liaison', 'NT-3377-0455', 1);

-- Docking stations
INSERT INTO docking_stations (
    id, name, city_id, shift_human_supervisor_id,
    total_spaces, free_spaces, occupied_spaces,
    off_peak_rate, peak_rate,
    opening_hours, closing_hours, ai_supervision
) VALUES
    ('DS-NEO-01', 'Neo-Terra Skyport Parking Complex', 'CITY-NT', 'HR-001',
     4800, 1320, 3480, 24.00, 36.00, '00:00', '23:59', 1),
    ('DS-AX-02', 'Axios Canal Freight Annex',          'CITY-AX', 'HR-002',
     1200,  410,  790, 32.00, 45.00, '05:00', '23:00', 1);

-- Pricing (baseline & add-ons)
INSERT INTO prices (id, docking_station_id, vehicle_class, period, rate_per_hour) VALUES
    ('PRC-NEO-G_STD-OFF', 'DS-NEO-01', 'Standard Groundcar (G1-G3)',         'off_peak',    24.00),
    ('PRC-NEO-G_STD-PEAK','DS-NEO-01', 'Standard Groundcar (G1-G3)',         'peak',        36.00),
    ('PRC-NEO-H2-OFF',    'DS-NEO-01', 'Hovercraft & Lev-Bike (H2)',         'off_peak',    32.00),
    ('PRC-NEO-H2-PEAK',   'DS-NEO-01', 'Hovercraft & Lev-Bike (H2)',         'peak',        45.00),
    ('PRC-NEO-FRT-FLAT',  'DS-NEO-01', 'Heavy Freight',                      'flat',        58.00),
    ('PRC-NEO-AUTO-STD',  'DS-NEO-01', 'Autonomous Shuttle Pod',             'standard',    40.00),
    ('PRC-NEO-FLEX-OFF',  'DS-NEO-01', 'Flex Bay',                           'off_peak',    28.00),
    ('PRC-NEO-FLEX-PEAK', 'DS-NEO-01', 'Flex Bay',                           'peak',        50.00),
    ('PRC-NEO-ADD-CHG',   'DS-NEO-01', 'Add-on: Charging Session',           'per_session',  6.00),
    ('PRC-NEO-ADD-VAL',   'DS-NEO-01', 'Add-on: Valet Drone',                'per_request', 12.00),
    ('PRC-NEO-ADD-SEC',   'DS-NEO-01', 'Add-on: Security Escort',            'per_request',  9.00),
    ('PRC-NEO-ADD-CLM',   'DS-NEO-01', 'Add-on: Climate Stabilization',      'per_hour',     5.00),
    ('PRC-AX-G_STD-OFF',  'DS-AX-02',  'Standard Groundcar (G1-G3)',         'off_peak',    22.00),
    ('PRC-AX-G_STD-PEAK', 'DS-AX-02',  'Standard Groundcar (G1-G3)',         'peak',        34.00),
    ('PRC-AX-FRT-FLAT',   'DS-AX-02',  'Heavy Freight',                      'flat',        55.00),
    ('PRC-AX-ADD-LOAD',   'DS-AX-02',  'Add-on: Loading Dock Priority',      'per_hour',     8.00);

-- Reservations
INSERT INTO reservations (
    id, docking_station_id, customer_name, vehicle_class,
    arrival_start, arrival_end, estimated_departure,
    booking_channel, payment_method, status, enhancements, created_at
) VALUES
    ('RES-0001', 'DS-NEO-01', 'Lyra Chen',                 'Standard Groundcar (G1-G3)',
     '2125-05-14 09:00', '2125-05-14 11:00', '2125-05-14 18:00',
     'Aegis Portal', 'CredChip',          'booked',     'charging,valet_drone',      '2125-05-10 08:45'),
    ('RES-0002', 'DS-NEO-01', 'Helix Dynamics Fleet',      'Autonomous Shuttle Pod',
     '2125-05-14 06:00', '2125-05-14 08:00', '2125-05-15 06:00',
     'Mesh Concierge', 'Corporate Ledger', 'checked_in', 'security_escort',          '2125-05-09 15:20'),
    ('RES-0003', 'DS-NEO-01', 'Juno & Pax Rover',          'Flex Bay',
     '2125-05-14 14:00', '2125-05-14 16:00', '2125-05-16 14:30',
     'Synapse Kiosk', 'MembranePay',       'booked',     'climate_control',          '2125-05-12 12:05'),
    ('RES-0004', 'DS-NEO-01', 'Major Aric Voss',           'Hovercraft & Lev-Bike (H2)',
     '2125-05-13 19:00', '2125-05-13 21:00', '2125-05-14 09:00',
     'Mesh Concierge', 'CredChip',         'completed',  'charging,security_escort', '2125-05-11 18:35'),
    ('RES-0005', 'DS-AX-02',  'Chrona Recycling Freight',  'Heavy Freight',
     '2125-05-14 03:30', '2125-05-14 05:30', '2125-05-14 20:00',
     'Aegis Portal', 'Corporate Ledger',   'booked',     'loading_dock_priority',    '2125-05-08 07:10');

COMMIT;