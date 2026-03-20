CREATE TABLE IF NOT EXISTS clients (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  tier VARCHAR(20) DEFAULT 'standard'
);

CREATE TABLE IF NOT EXISTS sales (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  client_name VARCHAR(255) NOT NULL,
  product VARCHAR(255) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(50) DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS financial_summary (
  id SERIAL PRIMARY KEY,
  month DATE NOT NULL,
  revenue DECIMAL(12,2),
  expenses DECIMAL(12,2),
  profit DECIMAL(12,2),
  active_clients INTEGER
);

INSERT INTO clients (name, email, phone, created_at, tier) VALUES
('TechCorp Brasil', 'contato@techcorp.com.br', '+5511900001111', '2025-06-15', 'enterprise'),
('Innovate Solutions', 'hello@innovate.io', '+5511900002222', '2025-07-20', 'premium'),
('DataFlow Ltda', 'ops@dataflow.com.br', '+5511900003333', '2025-08-10', 'enterprise'),
('StartupXYZ', 'team@startupxyz.com', '+5511900004444', '2025-09-01', 'standard'),
('CloudNine Tech', 'info@cloudnine.tech', '+5511900005555', '2025-09-15', 'premium'),
('Agile Masters', 'contato@agilemasters.com.br', '+5511900006666', '2025-10-01', 'standard'),
('Digital Wave', 'hello@digitalwave.io', '+5511900007777', '2025-10-20', 'premium'),
('CodeBase Inc', 'dev@codebase.inc', '+5511900008888', '2025-11-05', 'enterprise'),
('SmartOps', 'support@smartops.com.br', '+5511900009999', '2025-11-20', 'standard'),
('Pixel Perfect', 'design@pixelperfect.com', '+5511900010000', '2025-12-01', 'standard'),
('NetSphere', 'admin@netsphere.com.br', '+5511900011111', '2025-12-15', 'premium'),
('ByteForge', 'forge@byteforge.dev', '+5511900012222', '2026-01-05', 'enterprise'),
('Quantum Labs', 'research@quantumlabs.ai', '+5511900013333', '2026-01-15', 'premium'),
('Apex Systems', 'sales@apexsystems.com.br', '+5511900014444', '2026-02-01', 'standard'),
('FutureStack', 'info@futurestack.io', '+5511900015555', '2026-02-10', 'standard'),
('NovaTech', 'contact@novatech.com.br', '+5511900016666', '2026-02-20', 'premium'),
('SkyBridge', 'ops@skybridge.tech', '+5511900017777', '2026-03-01', 'enterprise'),
('RapidDev', 'team@rapiddev.io', '+5511900018888', '2026-03-05', 'standard'),
('CoreLogic', 'info@corelogic.com.br', '+5511900019999', '2026-03-10', 'premium'),
('ZeroDay Security', 'sec@zeroday.com', '+5511900020000', '2026-03-15', 'enterprise');

INSERT INTO sales (date, client_name, product, amount, status) VALUES
('2026-02-17', 'TechCorp Brasil', 'Enterprise Platform License', 45000.00, 'completed'),
('2026-02-17', 'StartupXYZ', 'Starter Plan', 2500.00, 'completed'),
('2026-02-18', 'Innovate Solutions', 'API Integration Pack', 15000.00, 'completed'),
('2026-02-18', 'DataFlow Ltda', 'Data Pipeline Module', 32000.00, 'completed'),
('2026-02-19', 'CloudNine Tech', 'Cloud Migration Service', 28000.00, 'completed'),
('2026-02-19', 'Agile Masters', 'Consulting - Sprint', 8500.00, 'completed'),
('2026-02-20', 'Digital Wave', 'Design System License', 12000.00, 'completed'),
('2026-02-20', 'CodeBase Inc', 'Enterprise Platform License', 45000.00, 'completed'),
('2026-02-21', 'SmartOps', 'Monitoring Suite', 6800.00, 'completed'),
('2026-02-24', 'Pixel Perfect', 'Design System License', 12000.00, 'completed'),
('2026-02-24', 'NetSphere', 'API Integration Pack', 15000.00, 'completed'),
('2026-02-25', 'ByteForge', 'Enterprise Platform License', 45000.00, 'completed'),
('2026-02-25', 'Quantum Labs', 'AI Module Add-on', 22000.00, 'completed'),
('2026-02-26', 'TechCorp Brasil', 'Consulting - Sprint', 8500.00, 'completed'),
('2026-02-26', 'Apex Systems', 'Starter Plan', 2500.00, 'completed'),
('2026-02-27', 'FutureStack', 'Starter Plan', 2500.00, 'completed'),
('2026-02-27', 'NovaTech', 'Cloud Migration Service', 28000.00, 'completed'),
('2026-02-28', 'SkyBridge', 'Enterprise Platform License', 45000.00, 'pending'),
('2026-03-02', 'RapidDev', 'Starter Plan', 2500.00, 'completed'),
('2026-03-02', 'CoreLogic', 'API Integration Pack', 15000.00, 'completed'),
('2026-03-03', 'ZeroDay Security', 'Security Audit Package', 55000.00, 'completed'),
('2026-03-03', 'Innovate Solutions', 'AI Module Add-on', 22000.00, 'completed'),
('2026-03-04', 'DataFlow Ltda', 'Consulting - Sprint', 8500.00, 'completed'),
('2026-03-04', 'TechCorp Brasil', 'AI Module Add-on', 22000.00, 'completed'),
('2026-03-05', 'CloudNine Tech', 'Monitoring Suite', 6800.00, 'completed'),
('2026-03-05', 'Digital Wave', 'API Integration Pack', 15000.00, 'completed'),
('2026-03-09', 'ByteForge', 'Data Pipeline Module', 32000.00, 'completed'),
('2026-03-09', 'Quantum Labs', 'Consulting - Sprint', 8500.00, 'completed'),
('2026-03-10', 'Agile Masters', 'Starter Plan', 2500.00, 'completed'),
('2026-03-10', 'NetSphere', 'Cloud Migration Service', 28000.00, 'completed'),
('2026-03-11', 'SmartOps', 'API Integration Pack', 15000.00, 'completed'),
('2026-03-11', 'SkyBridge', 'Security Audit Package', 55000.00, 'completed'),
('2026-03-12', 'CodeBase Inc', 'Data Pipeline Module', 32000.00, 'completed'),
('2026-03-12', 'TechCorp Brasil', 'Monitoring Suite', 6800.00, 'completed'),
('2026-03-13', 'Pixel Perfect', 'Consulting - Sprint', 8500.00, 'completed'),
('2026-03-16', 'ZeroDay Security', 'AI Module Add-on', 22000.00, 'completed'),
('2026-03-16', 'NovaTech', 'API Integration Pack', 15000.00, 'completed'),
('2026-03-17', 'Innovate Solutions', 'Enterprise Platform License', 45000.00, 'completed'),
('2026-03-17', 'CoreLogic', 'Monitoring Suite', 6800.00, 'completed'),
('2026-03-18', 'DataFlow Ltda', 'AI Module Add-on', 22000.00, 'pending'),
('2026-03-18', 'StartupXYZ', 'API Integration Pack', 15000.00, 'completed'),
('2026-03-18', 'RapidDev', 'Design System License', 12000.00, 'pending');

INSERT INTO financial_summary (month, revenue, expenses, profit, active_clients) VALUES
('2025-10-01', 385000.00, 245000.00, 140000.00, 9),
('2025-11-01', 412000.00, 258000.00, 154000.00, 11),
('2025-12-01', 368000.00, 242000.00, 126000.00, 12),
('2026-01-01', 445000.00, 275000.00, 170000.00, 14),
('2026-02-01', 478000.00, 282000.00, 196000.00, 17),
('2026-03-01', 520000.00, 298000.00, 222000.00, 20);
