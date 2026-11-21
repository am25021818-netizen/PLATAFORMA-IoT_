-- ============================================================
-- BOVINOS IoT - Valle del Mezquital, Hidalgo
-- Datos Semilla con Roles, Hashes y Multi-Ranchos por Propietario
-- ============================================================

-- 1. USUARIOS (Contraseñas Hasheadas con scrypt)
-- admin@mezquital.mx      -> admin123
-- dueno@mezquital.mx      -> dueno123  (Don Aurelio: Propietario con 3 ranchos en Huichapan, Tecozautla e Ixmiquilpan)
-- operador@mezquital.mx   -> operador123 (Juan Hernández: Encargado de campo)
-- tecnico@mezquital.mx    -> tecnico123  (Ing. Roberto: Soporte hardware LoRa / Gateway)
INSERT OR IGNORE INTO usuarios (id, nombre, correo, password_hash, rol, telefono)
VALUES
  (1, 'Administrador Central', 'admin@mezquital.mx',
   'scrypt:32768:8:1$lCZ1l52o6tqnf4RT$9e225613d81e7e2db9814886b949b241be9395da55929f97a344d972cda9f4484a24b2dae53b3d3531073a0cf1a45c0963842b9699e5f5589eba85398ec85ea0',
   'administrador', '7731002233'),

  (2, 'Don Aurelio Trejo (Propietario)', 'dueno@mezquital.mx',
   'scrypt:32768:8:1$VE72leyTV4chyBFh$3a9c8a0a657ea2377e85721fbe88e62019bec508337b397100e22167bedbe5615001c2b5329b0d85aaf2784f23b22c006244577339fd83c5c5ec4c7b4a2f3fce',
   'propietario', '7611029384'),

  (3, 'Juan Hernández (Encargado de Campo)', 'operador@mezquital.mx',
   'scrypt:32768:8:1$HMGxtoGfOyRWZ73t$d8d543779eac6ec18c536c87febae3fef66248804a0f8e7b324761180e5a8fb3d1b2823b9d8d6937f3d52aab7c0979007c3ea107abad5edbd37c6bc47a67cf06',
   'operador_campo', '7735928172'),

  (4, 'Ing. Roberto Silva (Técnico Mantenimiento)', 'tecnico@mezquital.mx',
   'scrypt:32768:8:1$ROx6afoYJE7p2qtE$be91a254000c4ad2352cd8fc5b06b1329275199f30d2013726506e7248fddae2ba92abe212d616d0e9c3165261542024dc06cd90abad7e70955666eb4dd84be2',
   'tecnico_mantenimiento', '7719876543');

-- 2. RANCHOS: Don Aurelio (ID 2) es dueño de 3 ranchos en distintas locaciones del Valle del Mezquital
INSERT OR IGNORE INTO ranchos (id, propietario_id, nombre, municipio, estado, lat_centro, lon_centro, superficie_ha)
VALUES
  (1, 2, 'Rancho El Mezquital (Huichapan)',   'Huichapan',    'Hidalgo', 20.37542, -99.65431, 120.5),
  (2, 2, 'Rancho San Clemente (Tecozautla)',  'Tecozautla',   'Hidalgo', 20.52118, -99.63005, 185.0),
  (3, 2, 'Rancho Los Nopales (Ixmiquilpan)',  'Ixmiquilpan',  'Hidalgo', 20.48620, -99.21780, 95.0);

-- 3. ASIGNACIÓN DE OPERADORES A RANCHOS
INSERT OR IGNORE INTO usuarios_ranchos (usuario_id, rancho_id)
VALUES
  (3, 1), -- Juan Hernández atiende Rancho El Mezquital
  (3, 2); -- y Rancho San Clemente

-- 4. POTREROS
INSERT OR IGNORE INTO potreros (id, rancho_id, nombre, lat_centro, lon_centro, radio_m, superficie_ha)
VALUES
  (1, 1, 'La Cantera',    20.37800, -99.65100, 420, 55.0),
  (2, 1, 'El Mezquite',   20.36950, -99.66200, 380, 45.0),
  (3, 2, 'Sabino Grande', 20.52400, -99.62800, 500, 70.0),
  (4, 3, 'Los Cardos',    20.48900, -99.21400, 350, 38.0);

-- 5. DISPOSITIVOS (Collares Heltec LoRa ESP32 y Gateways)
INSERT OR IGNORE INTO dispositivos (id, mac_id, tipo, nombre, rancho_id, firmware_ver, bateria_pct, ultima_conexion)
VALUES
  (1, 'HELTEC-COL-001', 'collar',  'Collar El Barón',     1, '1.2.0', 87, datetime('now','-5 minutes','localtime')),
  (2, 'HELTEC-COL-002', 'collar',  'Collar La Paloma',    1, '1.2.0', 72, datetime('now','-8 minutes','localtime')),
  (3, 'HELTEC-COL-003', 'collar',  'Collar El Pinto',     1, '1.2.0', 95, datetime('now','-3 minutes','localtime')),
  (4, 'HELTEC-COL-004', 'collar',  'Collar La Gitana',    2, '1.2.0', 61, datetime('now','-12 minutes','localtime')),
  (5, 'HELTEC-COL-005', 'collar',  'Collar El Huasteco',  2, '1.2.0', 44, datetime('now','-45 minutes','localtime')),
  (6, 'HELTEC-COL-006', 'collar',  'Collar La Canela',    3, '1.2.0', 83, datetime('now','-6 minutes','localtime')),
  (7, 'HELTEC-GTW-01',  'gateway', 'Gateway Huichapan',   1, '1.1.0', NULL, datetime('now','-1 minutes','localtime')),
  (8, 'HELTEC-GTW-02',  'gateway', 'Gateway Tecozautla',  2, '1.1.0', NULL, datetime('now','-2 minutes','localtime')),
  (9, 'HELTEC-GTW-03',  'gateway', 'Gateway Ixmiquilpan', 3, '1.1.0', NULL, datetime('now','-3 minutes','localtime'));

-- 6. BOVINOS (Pertenecen a Don Aurelio [propietario_id = 2] en sus diferentes ranchos)
INSERT OR IGNORE INTO animales (id, arete, nombre, raza, sexo, peso_kg, propietario_id, rancho_id, potrero_id, collar_id, color_pelaje, fecha_nacimiento)
VALUES
  (1, 'MX-HGO-001', 'El Barón',     'Simental',  'Macho',  620, 2, 1, 1, 1, 'Rojo y blanco',  '2020-03-15'),
  (2, 'MX-HGO-002', 'La Paloma',    'Charolais', 'Hembra', 480, 2, 1, 1, 2, 'Blanco crema',   '2021-06-20'),
  (3, 'MX-HGO-003', 'El Pinto',     'Suizo',     'Macho',  540, 2, 1, 2, 3, 'Gris manchado',  '2021-01-10'),
  (4, 'MX-HGO-004', 'La Gitana',    'Angus',     'Hembra', 420, 2, 2, 3, 4, 'Negro brillante','2022-04-05'),
  (5, 'MX-HGO-005', 'El Huasteco',  'Brahman',   'Macho',  710, 2, 2, 3, 5, 'Gris perla',     '2019-11-30'),
  (6, 'MX-HGO-006', 'La Canela',    'Simbrah',   'Hembra', 390, 2, 3, 4, 6, 'Canela rojiza',  '2023-02-14');

-- 7. LECTURAS GPS HISTÓRICAS
INSERT OR IGNORE INTO lecturas_gps (animal_id, dispositivo_id, lat, lon, altitud_m, velocidad_kmh, hdop, satelites, bateria_pct, rssi_lora, timestamp_utc)
VALUES
  (1,1, 20.37812, -99.65089, 1812, 0.5, 1.2, 8, 90, -85, datetime('now','-60 minutes','localtime')),
  (1,1, 20.37834, -99.65102, 1813, 1.2, 1.1, 9, 89, -84, datetime('now','-30 minutes','localtime')),
  (1,1, 20.37859, -99.65118, 1814, 0.8, 1.0, 9, 87, -83, datetime('now','-5 minutes','localtime')),
  (2,2, 20.37780, -99.65075, 1810, 0.3, 1.3, 7, 74, -88, datetime('now','-50 minutes','localtime')),
  (2,2, 20.37795, -99.65091, 1811, 0.6, 1.2, 8, 73, -87, datetime('now','-20 minutes','localtime')),
  (2,2, 20.37810, -99.65110, 1812, 0.4, 1.1, 8, 72, -86, datetime('now','-8 minutes','localtime')),
  (3,3, 20.36960, -99.66188, 1820, 1.5, 1.0, 10, 96, -80, datetime('now','-40 minutes','localtime')),
  (3,3, 20.36982, -99.66215, 1821, 2.1, 0.9, 10, 95, -79, datetime('now','-10 minutes','localtime')),
  (3,3, 20.37010, -99.66230, 1822, 1.8, 0.9, 10, 95, -78, datetime('now','-3 minutes','localtime')),
  (4,4, 20.52388, -99.62812, 1900, 0.2, 1.4, 7, 63, -92, datetime('now','-55 minutes','localtime')),
  (4,4, 20.52405, -99.62830, 1901, 0.5, 1.3, 8, 62, -91, datetime('now','-12 minutes','localtime')),
  (5,5, 20.52420, -99.62845, 1902, 0.0, 2.1, 5, 46, -98, datetime('now','-45 minutes','localtime')),
  (6,6, 20.48912, -99.21388, 1750, 1.0, 1.1, 9, 85, -82, datetime('now','-30 minutes','localtime')),
  (6,6, 20.48930, -99.21410, 1751, 1.3, 1.0, 9, 83, -81, datetime('now','-6 minutes','localtime'));

-- 8. ALERTAS
INSERT OR IGNORE INTO alertas (id, animal_id, dispositivo_id, tipo, mensaje, lat, lon, atendida, creada_en)
VALUES
  (1, 5, 5, 'sin_comunicacion',
   'El Huasteco no ha reportado posición en más de 30 minutos. Última ubicación: Rancho San Clemente (Tecozautla).',
   20.52420, -99.62845, 0, datetime('now','-40 minutes','localtime')),
  (2, 5, 5, 'bateria_baja',
   'Batería del collar de El Huasteco al 44%. Requiere revisión por técnico.',
   20.52420, -99.62845, 0, datetime('now','-40 minutes','localtime')),
  (3, 4, 4, 'bateria_baja',
   'Batería del collar de La Gitana al 61%. Programar mantenimiento preventivo.',
   20.52405, -99.62830, 0, datetime('now','-10 minutes','localtime'));
