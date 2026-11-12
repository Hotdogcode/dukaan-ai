# Unit of Measurement & Conversions

## 1. Indian Retail Units of Measure
Indian grocery stores handle diverse measurement paradigms:
- **Mass / Weight:**
  - `kg` (Kilogram) - Base unit
  - `g` (Gram) - Conversion: `1000 g = 1 kg`
  - `quintal` (Quintal) - Conversion: `1 quintal = 100 kg`
- **Volume / Liquid:**
  - `L` / `ltr` (Litre) - Base unit
  - `ml` (Millilitre) - Conversion: `1000 ml = 1 L`
- **Count / Discrete Units:**
  - `pc` (Piece) - Base unit
  - `pack` (Pack) - Default discrete
  - `box` (Box) - Packaging unit
  - `dozen` (Dozen) - Conversion: `1 dozen = 12 pc`
- **Length / Area:**
  - `m` (Metre) - Base unit
  - `cm` (Centimetre) - Conversion: `100 cm = 1 m`

## 2. Standard Unit Conversion Schema
Conversions are modeled globally to prevent calculation errors across shops:
```sql
CREATE TABLE standard_unit_conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_unit_id UUID NOT NULL REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    to_unit_id UUID NOT NULL REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    conversion_factor NUMERIC(16, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_conversion_pair UNIQUE (from_unit_id, to_unit_id)
);
```

## 3. Precision Rules
All unit conversions and quantity calculations employ high-precision decimal arithmetic (`NUMERIC(16, 8)` in PostgreSQL, `BigDecimal` in Kotlin and Python). Floating-point arithmetic (`float`, `Double`) is strictly prohibited to avoid fractional unit loss during bulk sales and inventory tallying.
