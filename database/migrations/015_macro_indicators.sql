CREATE TABLE macro_indicators (
    id TEXT PRIMARY KEY,
    indicator_type TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_macro_indicators_type_date ON macro_indicators(indicator_type, date);
