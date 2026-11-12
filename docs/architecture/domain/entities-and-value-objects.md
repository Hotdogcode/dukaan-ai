# DukaanAI: Entities and Value Objects Specification

This document provides the formal structural and semantic specification of all Value Objects and Core Entities across the DukaanAI business domain.

---

## 1. Reusable Immutable Value Objects

Value objects possess **no conceptual identity**. They are defined solely by their attributes, are **strictly immutable**, validate their own internal invariants upon instantiation, and utilize **structural equality** (two instances with identical attributes are completely interchangeable).

### 1.1 Money
Represents an exact monetary value in a specific currency.
- **Internal Fields**:
  - `amount: Decimal` (Precision: 15 digits, Scale: 4 decimal places, e.g., `1250.5000`)
  - `currency: CurrencyCode` (ISO-4217, default: `INR`)
- **Validation Rules**:
  - `amount` must be a valid fixed-point number.
  - Operations between instances with differing currencies are strictly prohibited and throw `CurrencyMismatchException`.
- **Equality Semantics**: Structural equality: `amount.stripTrailingZeros() == other.amount.stripTrailingZeros() && currency == other.currency`.
- **Allowed Operations**:
  - `plus(other: Money): Money`
  - `minus(other: Money): Money`
  - `times(factor: Decimal): Money`
  - `times(percentage: Percentage): Money`
  - `dividedBy(divisor: Decimal, roundingMode: RoundingMode): Money`
  - `isPositive(): Boolean`, `isNegative(): Boolean`, `isZero(): Boolean`
  - `roundToDisplay(roundingMode = HALF_EVEN): Money` (Rounds to 2 decimal places for Indian Rupee paise display)
- **Invariant**: Floating-point types (`float`, `double`) are strictly prohibited in the constructor.

### 1.2 Quantity
Represents a physical count, weight, or volume of merchandise.
- **Internal Fields**:
  - `amount: Decimal` (Scale: 4 decimal places, e.g., `1.5000` kg or `500.0000` g)
  - `unit: UnitOfMeasure`
- **Validation Rules**:
  - `amount` must be non-negative for physical stock measurements.
  - Discrete units (`PIECE`, `PACKET`, `DOZEN`) must enforce whole integer numbers where fractional sale is disallowed, or validate allowable increments (e.g., half-piece).
- **Equality Semantics**: Structural equality taking unit conversion into account (e.g., `Quantity(1, KG) == Quantity(1000, GRAM)`).
- **Allowed Operations**:
  - `plus(other: Quantity, converter: UnitConverter): Quantity`
  - `minus(other: Quantity, converter: UnitConverter): Quantity`
  - `times(scalar: Decimal): Quantity`
  - `convertTo(targetUnit: UnitOfMeasure, multiplier: Decimal): Quantity`

### 1.3 UnitOfMeasure (UOM)
Defines the measurement dimension of products.
- **Fields**:
  - `code: String` (e.g., `KG`, `GRAM`, `LITRE`, `ML`, `PIECE`, `PACKET`, `DOZEN`)
  - `category: UomCategory` (`MASS`, `VOLUME`, `COUNT`)
  - `isFractionalAllowed: Boolean` (True for kg/litre; False for piece/packet)
- **Validation Rules**: Conversions are strictly permitted only between units of the same `UomCategory` (e.g., grams to kilograms is valid; grams to packets is invalid without product-specific packaging definitions).

### 1.4 ProductPrice
Encapsulates retail pricing rules for a product.
- **Internal Fields**:
  - `mrp: Money` (Maximum Retail Price mandated by Indian Legal Metrology)
  - `sellingPrice: Money` (The store's current active shelf price)
  - `costPrice: Money` (Latest acquisition or average cost price)
- **Validation Rules**:
  - `sellingPrice <= mrp` (In Indian retail, selling above MRP is a statutory offense).
  - All amounts must have identical currency (`INR`).

### 1.5 TaxRate & TaxConfiguration
Represents Indian Goods and Services Tax (GST) slabs.
- **Internal Fields**:
  - `slab: GstSlab` (`EXEMPT_0`, `GST_5`, `GST_12`, `GST_18`, `GST_28`)
  - `percentage: Percentage` (0%, 5%, 12%, 18%, 28%)
  - `isInclusive: Boolean` (Whether shelf price includes tax, common in Indian FMCG)
- **Calculated Properties**:
  - `cgstRate: Percentage` (Half of total GST rate for intra-state sales)
  - `sgstRate: Percentage` (Half of total GST rate for intra-state sales)
  - `igstRate: Percentage` (Full GST rate for inter-state sales)
- **Allowed Operations**:
  - `calculateTax(baseAmount: Money): TaxBreakdown`
  - `extractBaseAmount(grossAmount: Money): Money` (For price-inclusive items: $\text{Base} = \frac{\text{Gross}}{1 + \text{TaxRate}}$)

### 1.6 Percentage
Represents fractions or discount ratios.
- **Fields**: `value: Decimal` (Scale: 4, e.g., `10.5000` for 10.5%)
- **Validation**: $0.0000 \le \text{value} \le 100.0000$ (except markup calculations).

### 1.7 PhoneNumber (Indian Standard)
- **Fields**: `raw: String`, `countryCode: String` (`+91`), `nationalNumber: String` (10 digits)
- **Validation Rules**: Must match standard Indian cellular numbering scheme (`^[6-9]\d{9}$`).

### 1.8 DateRange
- **Fields**: `startInstant: Instant`, `endInstant: Instant`
- **Validation**: `startInstant <= endInstant`.
- **Operations**: `contains(instant: Instant): Boolean`, `duration(): Duration`.

### 1.9 Domain Identifiers (Typed Value Objects)
To prevent "primitive obsession" where arbitrary strings or integers are passed incorrectly, every aggregate identifier is a strongly typed value object wrapping a UUID v4:
- `BusinessId(val value: UUID)`
- `StoreId(val value: UUID)`
- `ProductId(val value: UUID)`
- `SaleId(val value: UUID)`
- `PurchaseId(val value: UUID)`
- `CustomerId(val value: UUID)`
- `SupplierId(val value: UUID)`
- `StockMovementId(val value: UUID)`
- `ExpenseId(val value: UUID)`
- `IdempotencyKey(val value: UUID)`

### 1.10 PaymentMethod
Enumeration with metadata:
- `CASH`: Settled to physical cash drawer (*Galla*).
- `UPI_DIRECT`: Dynamic QR / soundbox payment direct to merchant bank.
- `CUSTOMER_CREDIT`: Deferred payment posted to Customer Khata ledger.
- `BANK_TRANSFER`: NEFT/RTGS/IMPS for distributor settlements.
- `SPLIT`: Composite payment split across multiple tenders.

---

## 2. Core Entities Specification

Entities possess unique identities that persist through time and state transformations.

### 2.1 Product Entity
- **Identity**: `ProductId: ProductId`
- **Attributes**:
  - `businessId: BusinessId`
  - `name: ProductName` (e.g., "Aashirvaad Shudh Chakki Atta")
  - `category: CategoryName` (e.g., "Flours & Grains")
  - `sku: SKU` (Unique product code)
  - `barcode: Barcode?` (EAN-13, UPC, or custom store barcode)
  - `baseUnit: UnitOfMeasure` (The indivisible unit for physical stock tracking, e.g., `GRAM` or `PIECE`)
  - `pricing: ProductPrice`
  - `taxConfig: TaxConfiguration`
  - `reorderThreshold: Quantity` (Alert point for low stock warnings)
  - `status: ProductStatus` (`ACTIVE`, `DISCONTINUED`, `ARCHIVED`)
  - `conversionRules: List<UnitConversionRule>`
- **Separation of Concerns**: The `Product` entity contains **no stock quantity attribute**. Product definition belongs to the Catalogue context, while physical quantity belongs strictly to the `StockItem` aggregate in the Inventory context.

### 2.2 Store Entity
- **Identity**: `StoreId: StoreId`
- **Attributes**:
  - `businessId: BusinessId`
  - `storeName: String` (e.g., "Main Road Branch")
  - `address: Address`
  - `contactNumber: PhoneNumber`
  - `isActive: Boolean`
  - `registeredAt: Instant`

### 2.3 Customer Entity
- **Identity**: `CustomerId: CustomerId`
- **Attributes**:
  - `businessId: BusinessId`
  - `fullName: String`
  - `phoneNumber: PhoneNumber`
  - `creditLimit: Money?` (Optional maximum allowable credit balance)
  - `isActive: Boolean`
  - `createdAt: Instant`

### 2.4 Supplier Entity
- **Identity**: `SupplierId: SupplierId`
- **Attributes**:
  - `businessId: BusinessId`
  - `companyName: String`
  - `contactPerson: String?`
  - `phoneNumber: PhoneNumber`
  - `gstin: TaxIdentificationNumber?`
  - `paymentTermsDays: Int` (e.g., 7, 15, 30 days credit)
  - `isActive: Boolean`

---

## 3. Unit Conversion & Loose Items Architecture

Kirana stores constantly purchase in bulk packaging units and sell in variable retail fractions.

### 3.1 The Canonical Base Unit Principle
To avoid precision loss and rounding drift, **all inventory balances are internally accounted for in the product's defined `BaseUnit`**:
- Loose Rice: `BaseUnit = GRAM`
- Cooking Oil: `BaseUnit = MILLILITRE`
- Packaged Biscuits: `BaseUnit = PIECE`

### 3.2 Unit Conversion Rules
A `UnitConversionRule` defines a deterministic conversion factor between a secondary transaction unit and the base unit:
$$\text{BaseQuantity} = \text{TransactionQuantity} \times \text{ConversionMultiplier}$$

```
Example 1: Loose Sugar
- Base Unit: GRAM
- Rule 1: 1 KG = 1000 GRAMS (Multiplier = 1000.0000)
- Rule 2: 1 QUINTAL = 100,000 GRAMS (Multiplier = 100000.0000)

If merchant purchases 2 Quintal sacks:
Purchase input: 2 Quintal -> Inward Stock Movement: +200,000 Grams

If customer purchases 750 grams:
POS Sale input: 750 Gram -> Outward Stock Movement: -750 Grams

If customer purchases 2.5 kg:
POS Sale input: 2.5 Kg -> Outward Stock Movement: -2,500 Grams
New Stock Balance = 200,000 - 750 - 2,500 = 196,750 Grams (or 196.75 kg)
```

```
Example 2: Packaged Soap (Carton vs Piece)
- Base Unit: PIECE
- Rule 1: 1 CASE = 48 PIECES (Multiplier = 48.0000)
- Rule 2: 1 PACK_OF_4 = 4 PIECES (Multiplier = 4.0000)

Purchase: 5 Cases received -> +240 Pieces in stock
Sale: 2 Pack-of-4 sold -> -8 Pieces in stock
Sale: 3 Individual Pieces sold -> -3 Pieces in stock
Balance = 240 - 8 - 3 = 229 Pieces
```

### 3.3 Conversion Invariant Rules
1. Multipliers must be positive non-zero decimals.
2. Inward or outward movements are computed to 4 decimal places before committing to the ledger.
3. Unit conversions between incompatible physical categories (e.g., mass to volume) are rejected unless an explicit density factor is defined.
