-- SupplyGuard AI — Seed Data
-- 10 synthetic suppliers, 15 parts, AVL entries, and test events
-- All data is fully synthetic per competition rules

-- ═══════════════════════════════════════════════
-- SUPPLIERS (10 total — mix of GREEN/YELLOW/RED)
-- ═══════════════════════════════════════════════
INSERT INTO suppliers (supplier_id, supplier_name, country, tier, financial_health, lead_time_days, unit_cost, is_active, quality_cert_type, quality_cert_expiry) VALUES
('a1000000-0000-0000-0000-000000000001', 'AlphaForge Industries',   'Mexico',     1, 'RED',    12, 85.50,  TRUE,  'ISO 9001',   '2025-06-15'),
('a1000000-0000-0000-0000-000000000002', 'BetaSteel Corporation',   'USA',        1, 'GREEN',   5, 92.00,  TRUE,  'ISO 9001',   '2027-12-31'),
('a1000000-0000-0000-0000-000000000003', 'GammaCast Manufacturing', 'Germany',    1, 'GREEN',   7, 110.00, TRUE,  'IATF 16949', '2027-08-20'),
('a1000000-0000-0000-0000-000000000004', 'DeltaSteel Corp',         'Brazil',     2, 'YELLOW',  9, 78.00,  TRUE,  'ISO 9001',   '2026-03-01'),
('a1000000-0000-0000-0000-000000000005', 'EpsilonCast Systems',     'India',      2, 'GREEN',   8, 65.00,  TRUE,  'ISO 14001',  '2027-05-10'),
('a1000000-0000-0000-0000-000000000006', 'ZetaAlloy Solutions',     'USA',        1, 'GREEN',   4, 98.00,  TRUE,  'IATF 16949', '2028-01-15'),
('a1000000-0000-0000-0000-000000000007', 'EtaPrecision Parts',      'Japan',      1, 'GREEN',   6, 120.00, TRUE,  'ISO 9001',   '2027-11-30'),
('a1000000-0000-0000-0000-000000000008', 'ThetaForge Ltd',          'China',      2, 'YELLOW', 10, 55.00,  TRUE,  'ISO 9001',   '2025-12-01'),
('a1000000-0000-0000-0000-000000000009', 'IotaMetals Inc',          'South Korea',1, 'GREEN',   5, 105.00, TRUE,  'IATF 16949', '2027-09-15'),
('a1000000-0000-0000-0000-000000000010', 'KappaComponents Global',  'Turkey',     3, 'RED',    14, 48.00,  TRUE,  'ISO 9001',   '2024-08-01');

-- ═══════════════════════════════════════════════
-- PARTS (15 total — mix of engine, turbo, exhaust, etc.)
-- ═══════════════════════════════════════════════
INSERT INTO parts (part_id, part_number, part_name, category, primary_supplier_id, factory, min_order_qty) VALUES
('b2000000-0000-0000-0000-000000000001', 'PT-ENG-001',   'Engine Block Assembly',       'Engine',     'a1000000-0000-0000-0000-000000000001', 'Columbus Plant',   50),
('b2000000-0000-0000-0000-000000000002', 'PT-ENG-002',   'Cylinder Head',               'Engine',     'a1000000-0000-0000-0000-000000000002', 'Columbus Plant',   100),
('b2000000-0000-0000-0000-000000000003', 'PT-TURBO-001', 'Turbocharger Assembly',       'Turbo',      'a1000000-0000-0000-0000-000000000003', 'Jamestown Plant',  75),
('b2000000-0000-0000-0000-000000000004', 'PT-TURBO-002', 'Turbo Wastegate Actuator',    'Turbo',      'a1000000-0000-0000-0000-000000000004', 'Jamestown Plant',  200),
('b2000000-0000-0000-0000-000000000005', 'PT-EXH-001',   'Exhaust Manifold',            'Exhaust',    'a1000000-0000-0000-0000-000000000005', 'Rocky Mount Plant',150),
('b2000000-0000-0000-0000-000000000006', 'PT-EXH-002',   'DPF Assembly',                'Exhaust',    'a1000000-0000-0000-0000-000000000006', 'Rocky Mount Plant',80),
('b2000000-0000-0000-0000-000000000007', 'PT-FUEL-001',  'Fuel Injector Set',           'Fuel System','a1000000-0000-0000-0000-000000000007', 'Columbus Plant',   120),
('b2000000-0000-0000-0000-000000000008', 'PT-FUEL-002',  'High Pressure Fuel Pump',     'Fuel System','a1000000-0000-0000-0000-000000000008', 'Jamestown Plant',  60),
('b2000000-0000-0000-0000-000000000009', 'PT-COOL-001',  'Radiator Assembly',           'Cooling',    'a1000000-0000-0000-0000-000000000009', 'Columbus Plant',   90),
('b2000000-0000-0000-0000-000000000010', 'PT-COOL-002',  'Water Pump',                  'Cooling',    'a1000000-0000-0000-0000-000000000010', 'Rocky Mount Plant',200),
('b2000000-0000-0000-0000-000000000011', 'PT-ENG-003',   'Crankshaft',                  'Engine',     'a1000000-0000-0000-0000-000000000002', 'Columbus Plant',   40),
('b2000000-0000-0000-0000-000000000012', 'PT-TURBO-003', 'Intercooler',                 'Turbo',      'a1000000-0000-0000-0000-000000000005', 'Jamestown Plant',  100),
('b2000000-0000-0000-0000-000000000013', 'PT-EXH-003',   'SCR Catalyst',                'Exhaust',    'a1000000-0000-0000-0000-000000000003', 'Rocky Mount Plant',70),
('b2000000-0000-0000-0000-000000000014', 'PT-FUEL-003',  'Fuel Filter Module',          'Fuel System','a1000000-0000-0000-0000-000000000009', 'Columbus Plant',   250),
('b2000000-0000-0000-0000-000000000015', 'PT-COOL-003',  'Thermostat Housing Assembly', 'Cooling',    'a1000000-0000-0000-0000-000000000006', 'Jamestown Plant',  180);

-- ═══════════════════════════════════════════════
-- AVL (Approved Vendor List) — multiple suppliers per part
-- ═══════════════════════════════════════════════
INSERT INTO approved_vendor_list (part_id, supplier_id, lead_time_days, unit_cost, quality_cert_expiry, geographic_risk, is_approved) VALUES
-- Engine Block: AlphaForge (primary), BetaSteel, GammaCast
('b2000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 12, 85.50,  '2025-06-15', 0.40, TRUE),
('b2000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000002',  5, 95.00,  '2027-12-31', 0.10, TRUE),
('b2000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000003',  7, 112.00, '2027-08-20', 0.20, TRUE),
-- Cylinder Head: BetaSteel (primary), EtaPrecision
('b2000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002',  5, 92.00,  '2027-12-31', 0.10, TRUE),
('b2000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000007',  6, 125.00, '2027-11-30', 0.15, TRUE),
-- Turbocharger: GammaCast (primary), IotaMetals, EpsilonCast
('b2000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003',  7, 110.00, '2027-08-20', 0.20, TRUE),
('b2000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000009',  5, 115.00, '2027-09-15', 0.20, TRUE),
('b2000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000005',  8, 70.00,  '2027-05-10', 0.55, TRUE),
-- Turbo Wastegate: DeltaSteel (primary), ThetaForge
('b2000000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000004',  9, 78.00,  '2026-03-01', 0.45, TRUE),
('b2000000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000008', 10, 58.00,  '2025-12-01', 0.60, TRUE),
-- Exhaust Manifold: EpsilonCast (primary), ZetaAlloy
('b2000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005',  8, 65.00,  '2027-05-10', 0.55, TRUE),
('b2000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000006',  4, 102.00, '2028-01-15', 0.10, TRUE),
-- DPF Assembly: ZetaAlloy (primary), EtaPrecision
('b2000000-0000-0000-0000-000000000006', 'a1000000-0000-0000-0000-000000000006',  4, 98.00,  '2028-01-15', 0.10, TRUE),
('b2000000-0000-0000-0000-000000000006', 'a1000000-0000-0000-0000-000000000007',  6, 130.00, '2027-11-30', 0.15, TRUE),
-- Fuel Injector: EtaPrecision (primary), IotaMetals
('b2000000-0000-0000-0000-000000000007', 'a1000000-0000-0000-0000-000000000007',  6, 120.00, '2027-11-30', 0.15, TRUE),
('b2000000-0000-0000-0000-000000000007', 'a1000000-0000-0000-0000-000000000009',  5, 108.00, '2027-09-15', 0.20, TRUE),
-- Fuel Pump: ThetaForge (primary), KappaComponents
('b2000000-0000-0000-0000-000000000008', 'a1000000-0000-0000-0000-000000000008', 10, 55.00,  '2025-12-01', 0.60, TRUE),
('b2000000-0000-0000-0000-000000000008', 'a1000000-0000-0000-0000-000000000010', 14, 50.00,  '2024-08-01', 0.70, TRUE),
-- Radiator: IotaMetals (primary), BetaSteel
('b2000000-0000-0000-0000-000000000009', 'a1000000-0000-0000-0000-000000000009',  5, 105.00, '2027-09-15', 0.20, TRUE),
('b2000000-0000-0000-0000-000000000009', 'a1000000-0000-0000-0000-000000000002',  5, 99.00,  '2027-12-31', 0.10, TRUE),
-- Water Pump: KappaComponents (primary), EpsilonCast
('b2000000-0000-0000-0000-000000000010', 'a1000000-0000-0000-0000-000000000010', 14, 48.00,  '2024-08-01', 0.70, TRUE),
('b2000000-0000-0000-0000-000000000010', 'a1000000-0000-0000-0000-000000000005',  8, 68.00,  '2027-05-10', 0.55, TRUE);

-- ═══════════════════════════════════════════════
-- SUPPLIER EVENTS (test scenarios)
-- ═══════════════════════════════════════════════
INSERT INTO supplier_events (event_id, supplier_id, event_type, delay_days, description, severity) VALUES
-- RED: AlphaForge critical disruption
('c3000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'DELIVERY_MISS', 9, 'Facility fire at AlphaForge Monterrey plant. 9-day delivery delay confirmed.', 'CRITICAL'),
-- GREEN: ZetaAlloy minor
('c3000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000006', 'DELIVERY_MISS', 1, 'Minor 1-day delay within SLA buffer. No factory impact.', 'LOW'),
-- YELLOW: DeltaSteel financial flag
('c3000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000004', 'FINANCIAL_FLAG', 4, 'DeltaSteel flagged for Q3 cash flow concerns. Delivery delay possible.', 'HIGH'),
-- KappaComponents expired cert + financial RED
('c3000000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000010', 'QUALITY_HOLD', 6, 'KappaComponents quality cert expired. Multiple defect reports received.', 'CRITICAL'),
-- ThetaForge delivery miss
('c3000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000008', 'DELIVERY_MISS', 5, 'ThetaForge production line down for 5 days. Partial shipment only.', 'HIGH'),
-- BetaSteel low-risk
('c3000000-0000-0000-0000-000000000006', 'a1000000-0000-0000-0000-000000000002', 'DELIVERY_MISS', 1, 'Weather delay, 1-day impact. Full recovery expected.', 'LOW'),
-- GammaCast medium
('c3000000-0000-0000-0000-000000000007', 'a1000000-0000-0000-0000-000000000003', 'QUALITY_HOLD', 3, 'GammaCast batch #4421 held for dimensional tolerance review.', 'MEDIUM'),
-- EpsilonCast medium
('c3000000-0000-0000-0000-000000000008', 'a1000000-0000-0000-0000-000000000005', 'DELIVERY_MISS', 3, 'Port congestion in Mumbai causing 3-day delay on EpsilonCast shipment.', 'MEDIUM'),
-- EtaPrecision low
('c3000000-0000-0000-0000-000000000009', 'a1000000-0000-0000-0000-000000000007', 'DELIVERY_MISS', 1, 'Customs clearance delay, 1-day impact. Documentation resolved.', 'LOW'),
-- IotaMetals medium
('c3000000-0000-0000-0000-000000000010', 'a1000000-0000-0000-0000-000000000009', 'FINANCIAL_FLAG', 2, 'IotaMetals credit rating downgrade flagged by monitoring service.', 'MEDIUM');
