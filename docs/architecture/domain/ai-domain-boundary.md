# DukaanAI: AI Domain Boundary & 20 Validation Scenarios

This document defines the strict Clean Architecture boundary separating the AI Assistant from core business domains, details the 10 domain-facing AI capabilities, and validates the entire business domain through 20 end-to-end retail scenarios.

---

## 1. The Clean Architecture AI Boundary

The Artificial Intelligence layer (speech-to-text, LLM parsing, conversational agent) is strictly categorized as an **Infrastructure / Interface Adapter**. 

```
+-----------------------------------------------------------------------------------+
|                        AI Interaction Plane (Untrusted)                           |
|  [Voice Mic Audio] / [Hinglish Text] -> ASR -> Phonetic Normalizer -> LLM        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                   Anti-Corruption Layer (ACL) & Schema Parser                     |
|  - Validates tokens into typed Command/Query DTOs                                 |
|  - Disambiguates customer names ("Ramesh Ji") & vernacular SKUs ("Maggi 70g")     |
+-----------------------------------------------------------------------------------+
                                         |
                        +----------------+----------------+
                        |                                 |
                        v                                 v
        [Mutating Actions (Confirmation Card)]   [Read-Only Analytical Queries]
                        |                                 |
                        v                                 v
+-----------------------------------------------------------------------------------+
|                         Application Services Layer                                |
|  - Enforces authorization, permissions, and validation preconditions              |
|  - Calls Domain Aggregates (Sale, StockItem, CustomerAccount, Expense)            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         Pure Domain Aggregates & Ledgers                          |
|  - Executes deterministic arithmetic and emits immutable Domain Events            |
+-----------------------------------------------------------------------------------+
```

---

## 2. Specification of the 10 AI Domain Capabilities

### 2.1 Capability 1: `RecordSale`
- **Purpose**: Creates a counter sale from voice commands (e.g., *"Do kilo atta aur ek packet namak ka bill banao"*).
- **Input Contract**:
  ```json
  {
    "store_id": "UUID",
    "customer_id": "UUID?",
    "items": [
      { "product_id": "UUID", "quantity": 2.0, "unit": "KG", "override_unit_price": null }
    ],
    "tender": { "type": "CASH", "amount": 110.0 }
  }
  ```
- **Validation Rules**: Product must exist in store catalog; quantity $> 0$; unit compatible with product category; tenders match total.
- **Authorization**: Cashier or Store Owner role.
- **User Confirmation Required?**: **YES** (Presents a high-contrast confirmation card with itemized prices and total before committing).
- **Output Contract**: `SaleConfirmationDraftDTO` returning `invoice_number`, `line_totals`, and `grand_total`.

### 2.2 Capability 2: `RecordExpense`
- **Purpose**: Logs shop operational expenses (e.g., *"Dukan ka bijli bill 1200 rupaye cash bhara"*).
- **Input Contract**: `store_id: UUID`, `category: ExpenseCategory`, `amount: Decimal`, `payment_method: PaymentMethod`, `recipient: String?`, `notes: String?`.
- **Validation Rules**: Amount $> 0$; recognized category.
- **Authorization**: Cashier (up to ₹500 petty cash) or Store Owner (unlimited).
- **User Confirmation Required?**: **YES** (1-tap confirmation card).
- **Output Contract**: `ExpenseRecordDTO` with assigned `expense_id` and timestamp.

### 2.3 Capability 3: `RecordPurchase`
- **Purpose**: Ingests distributor inward supplies from voice or bill photo OCR.
- **Input Contract**: `store_id: UUID`, `supplier_id: UUID`, `supplier_invoice_no: String`, `items: List<InwardItemDTO>`, `total_amount: Decimal`.
- **Validation Rules**: Items must map to valid SKUs; unit purchase cost $\ge 0$.
- **Authorization**: Store Owner or Inventory Manager.
- **User Confirmation Required?**: **YES** (Mandatory review before updating stock levels).
- **Output Contract**: `PurchaseDraftDTO`.

### 2.4 Capability 4: `GetDailySales`
- **Purpose**: Answers query *"Aaj ki total bikri kitni hui?"*
- **Input Contract**: `store_id: UUID`, `date: LocalDate` (default: today).
- **Validation Rules**: Valid store access.
- **Authorization**: Cashier (own till) or Owner (all store tills).
- **User Confirmation Required?**: **NO** (Read-only query).
- **Output Contract**: Total gross sales, total discounts, net sales revenue, cash vs digital split.

### 2.5 Capability 5: `GetSalesSummary`
- **Purpose**: Answers query *"Iss hafte ya iss mahine ka sales summary batao"*.
- **Input Contract**: `store_id: UUID`, `date_range: DateRange`.
- **User Confirmation Required?**: **NO**.
- **Output Contract**: Aggregated turnover, invoice count, average basket size, peak transaction hours.

### 2.6 Capability 6: `GetProductStock`
- **Purpose**: Answers query *"Basmati chawal ka stock kitna bacha hai?"*
- **Input Contract**: `store_id: UUID`, `product_id: UUID`.
- **User Confirmation Required?**: **NO**.
- **Output Contract**: Product name, current physical balance in display units (e.g., "45.5 kg"), reorder status.

### 2.7 Capability 7: `GetLowStockProducts`
- **Purpose**: Answers query *"Kaun sa maal khatam hone wala hai?"*
- **Input Contract**: `store_id: UUID`, `limit: Int = 10`.
- **User Confirmation Required?**: **NO**.
- **Output Contract**: List of products where `current_stock <= reorder_threshold`, with estimated days of inventory remaining.

### 2.8 Capability 8: `GetCustomerOutstanding`
- **Purpose**: Answers query *"Ramesh ji ka kitna udhar baaki hai?"*
- **Input Contract**: `business_id: UUID`, `customer_id: UUID`.
- **User Confirmation Required?**: **NO**.
- **Output Contract**: Customer name, phone, running outstanding balance, last payment date, days since last payment.

### 2.9 Capability 9: `GetGrossProfit`
- **Purpose**: Answers query *"Iss hafte kitna munaafa (gross profit) hua?"*
- **Input Contract**: `store_id: UUID`, `date_range: DateRange`.
- **Authorization**: Store Owner only.
- **User Confirmation Required?**: **NO**.
- **Output Contract**: Net sales revenue, Cost of Goods Sold (COGS), gross profit amount, gross margin percentage.

### 2.10 Capability 10: `SuggestReorder`
- **Purpose**: Proactively recommends wholesale restock quantities based on sales velocity.
- **Input Contract**: `store_id: UUID`, `lead_time_days: Int = 3`.
- **User Confirmation Required?**: **NO** (Produces recommendations; placing actual purchase order requires explicit confirmation).
- **Output Contract**: Recommended SKUs, suggested purchase quantities, preferred supplier IDs.

---

## 3. Comprehensive Domain Validation: 20 Retail Scenarios

The following 20 scenarios validate all core business invariants, unit conversions, state machine transitions, and financial equations.

---

### Scenario 1: Standard Cash Counter Checkout
- **Given**: Store has 50 kg of Loose Sugar in stock (BaseUnit = Gram, balance = 50,000 g, selling price = ₹44/kg).
- **When**: Cashier sells 2 kg of Sugar for cash; customer pays ₹88.00.
- **Then**: `Sale` completes with status `COMPLETED`.
- **Expected Domain Events**: `sales.sale.completed.v1`, `inventory.stock.movement_recorded.v1`.
- **Expected Inventory Impact**: Stock movement `-2,000.0000` grams (`SALE_DEDUCTION`); new balance = `48,000.0000` grams (48 kg).
- **Expected Financial Impact**: Net Sales Revenue increases by `+₹88.00`; Cash Drawer (*Galla*) increases by `+₹88.00`; Customer balance unaffected (`₹0.00`).

---

### Scenario 2: Credit Sale to Khata Customer (*Udhar Bikri*)
- **Given**: Customer "Ramesh Bhai" has an existing outstanding balance of `₹350.00`.
- **When**: Cashier bills 5 kg of Aashirvaad Atta (₹210.00); tender is allocated entirely to `CUSTOMER_CREDIT`.
- **Then**: `Sale` completes with status `COMPLETED`.
- **Expected Domain Events**: `sales.sale.completed.v1`, `customer.credit.debited.v1`, `inventory.stock.movement_recorded.v1`.
- **Expected Inventory Impact**: Atta stock decreases by `5.0000` units.
- **Expected Financial Impact**: Net Sales Revenue increases by `+₹210.00`; Cash Drawer increases by `₹0.00`; Customer outstanding balance increases to `₹560.00` ($350 + 210$).

---

### Scenario 3: Customer Credit Repayment (*Jama*)
- **Given**: Customer "Ramesh Bhai" owes `₹560.00`.
- **When**: Ramesh Bhai pays `₹500.00` in cash at the counter to settle his debt.
- **Then**: Repayment is recorded against `CustomerAccount`.
- **Expected Domain Events**: `customer.payment.received.v1`.
- **Expected Inventory Impact**: **Zero impact** on inventory.
- **Expected Financial Impact**: Net Sales Revenue is `₹0.00` (**Zero revenue recognized!**); Cash Drawer increases by `+₹500.00`; Customer outstanding balance decreases to `₹60.00` ($560 - 500$).

---

### Scenario 4: Overpayment Resulting in Customer Advance (*Peshgi*)
- **Given**: Customer "Sunil Ji" owes `₹150.00`.
- **When**: Sunil Ji hands over a `₹500.00` currency note and asks the merchant to keep the change as advance.
- **Then**: Repayment of ₹500 is applied.
- **Expected Domain Events**: `customer.payment.received.v1`.
- **Expected Financial Impact**: Outstanding balance becomes `-₹350.00` (Negative balance represents a ₹350 advance deposit in Sunil's favor); Cash Drawer increases by `+₹500.00`.

---

### Scenario 5: Subsequent Purchase Consuming Customer Advance
- **Given**: Sunil Ji has a credit balance of `-₹350.00` (advance).
- **When**: Sunil Ji purchases goods worth `₹200.00`.
- **Then**: Sale total is automatically satisfied by the available advance.
- **Expected Domain Events**: `sales.sale.completed.v1`, `customer.credit.debited.v1`.
- **Expected Financial Impact**: Net Sales Revenue increases by `+₹200.00`; Cash Drawer increases by `₹0.00`; Sunil's customer balance updates from `-₹350.00` to `-₹150.00` (still has ₹150 advance remaining).

---

### Scenario 6: Split Payment (Cash + UPI)
- **Given**: Customer purchase total is `₹1,250.00`.
- **When**: Customer pays `₹250.00` in cash and `₹1,000.00` via UPI QR code.
- **Then**: `Sale` completes with two payment allocations.
- **Expected Domain Events**: `sales.sale.completed.v1`.
- **Expected Financial Impact**: Net Sales Revenue increases by `+₹1,250.00`; Cash Drawer increases by `+₹250.00`; Merchant Bank Account (UPI) increases by `+₹1,000.00`.

---

### Scenario 7: Inward Distributor Purchase Bill
- **Given**: Moving average cost for Fortune Sunflower Oil 1L is `₹110.00` with 20 packets in stock.
- **When**: Distributor delivers 50 packets at `₹105.00` per packet (Total Bill: ₹5,250.00). Bill is marked `RECEIVED` on 15 days credit.
- **Then**: `Purchase` transitions to `RECEIVED`.
- **Expected Domain Events**: `purchasing.purchase.received.v1`, `inventory.stock.movement_recorded.v1`, `supplier.liability.recorded.v1`.
- **Expected Inventory Impact**: Stock increases by `+50.0000` packets (new balance = 70 packets). Moving average cost updates to:
  $$\frac{(20 \times 110) + (50 \times 105)}{20 + 50} = \frac{2200 + 5250}{70} = ₹106.4285\text{/packet}$$
- **Expected Financial Impact**: Supplier Payable balance increases by `+₹5,250.00`; Cash Drawer unaffected (`₹0.00`).

---

### Scenario 8: Supplier Debt Settlement via Bank Transfer
- **Given**: Merchant owes Supplier "Patel Wholesalers" `₹15,000.00`.
- **When**: Merchant pays `₹10,000.00` via NEFT bank transfer.
- **Then**: Supplier payment is recorded.
- **Expected Domain Events**: `supplier.payment.settled.v1`.
- **Expected Financial Impact**: Supplier Payable balance decreases to `₹5,000.00`; Bank Account decreases by `₹10,000.00`; Profit/Loss statement is completely unaffected.

---

### Scenario 9: Full Counter Sale Return with Cash Refund
- **Given**: Sale #101 included a defective umbrella sold for `₹300.00` cash (COGS was `₹210.00`).
- **When**: Customer returns the umbrella on the same day with receipt; cashier refunds ₹300 cash.
- **Then**: Sale transitions to `RETURNED`.
- **Expected Domain Events**: `sales.sale.returned.v1`, `inventory.stock.movement_recorded.v1`.
- **Expected Inventory Impact**: Stock movement `+1.0000` unit (`SALE_RETURN`); inventory restored.
- **Expected Financial Impact**: Net Sales Revenue reduced by `-₹300.00`; COGS reduced by `-₹210.00`; Cash Drawer reduced by `-₹300.00` payout.

---

### Scenario 10: Counter Sale Void (Audit Cancellation)
- **Given**: Cashier accidentally billed 10 bags of rice instead of 1 bag for cash (Total ₹4,000). The mistake is caught immediately.
- **When**: Cashier invokes `VoidSale(reason="Cashier billing typo", authorizedBy=Owner)`.
- **Then**: Sale transitions to `VOIDED`.
- **Expected Domain Events**: `sales.sale.voided.v1`, `inventory.stock.movement_recorded.v1`.
- **Expected Inventory Impact**: Stock deduction of 9 extra bags restored via `AUDIT_ADJUSTMENT`.
- **Expected Financial Impact**: ₹4,000 erroneously recognized revenue is completely nullified; Cash drawer float is corrected.

---

### Scenario 11: Unit Conversion Loose Grain Purchase & Fractional Sale
- **Given**: Product "Basmati Rice Loose" has `BaseUnit = GRAM`. Conversion rule: `1 KG = 1000 GRAMS`, `1 BAG = 50,000 GRAMS`.
- **When**: Store receives 2 BAGS inward from distributor, and subsequently sells 750 GRAMS to a customer.
- **Then**: Movements are recorded in BaseUnit.
- **Expected Inventory Impact**:
  1. Purchase Receipt: $+100,000.0000$ Grams.
  2. Sale Deduction: $-750.0000$ Grams.
  3. Ending Balance: $+99,250.0000$ Grams (99.25 kg). Zero fractional precision drift.

---

### Scenario 12: Temporary Negative Stock & Subsequent Reconciliation
- **Given**: System shows 1 packet of Tata Salt in stock.
- **When**: Customer brings 3 packets to the counter (new delivery just arrived physically). Cashier bills 3 packets.
- **Then**: Sale completes successfully without blocking checkout.
- **Expected Inventory Impact**: Stock balance becomes `-2.0000` packets. UI flags `Negative Stock Alert`.
- **When (Later in the day)**: Store owner enters the distributor purchase bill (+24 packets).
- **Expected Final State**: Stock balance updates to $+22.0000$ packets ($-2 + 24$). Timeline and moving average cost reconcile cleanly.

---

### Scenario 13: Physical Stock Audit Discovery of Spoilage (Shrinkage)
- **Given**: System stock for loose potatoes is 40.0 kg.
- **When**: Daily physical weigh-in reveals only 37.2 kg (2.8 kg rotten / moisture loss).
- **Then**: Owner commits `AdjustStockAudit(countedQty=37.2, reason="Moisture loss and rotting")`.
- **Expected Domain Events**: `inventory.stock.audited.v1`, `inventory.stock.movement_recorded.v1`.
- **Expected Inventory Impact**: Movement `-2.8000` kg (`DAMAGE_SPOILAGE`); new balance = 37.2 kg.
- **Expected Financial Impact**: COGS write-off recognized for the 2.8 kg acquisition cost; Operating profit reflects spoilage loss.

---

### Scenario 14: Daily Cash Drawer (*Galla*) Reconciliation
- **Given**: Opening cash float was ₹2,000. During the day: Cash Sales = ₹8,500; Customer Khata Cash Repayments = ₹1,200; Cash Expenses = ₹400; Supplier Cash Payout = ₹1,000.
- **When**: Owner closes the till and counts ₹10,250 in physical cash.
- **Then**: Expected cash is calculated:
  $$\text{Expected} = 2000 + 8500 + 1200 - 400 - 1000 = ₹10,300.00$$
  $$\text{Variance} = 10250 - 10300 = -₹50.00\text{ (Cash Shortage)}$$
- **Expected Domain Events**: `finance.register.closed.v1`.
- **Expected Financial Impact**: Till closes with `Status = VARIANCE_FLAGGED` and note "₹50 shortage in drawer".

---

### Scenario 15: Recording Store Operating Expense
- **Given**: Owner pays ₹350 from cash drawer for electricity repair work.
- **When**: Action `RecordExpense(category=MAINTENANCE, amount=350, tender=CASH, recipient="Raju Electrician")` executes.
- **Then**: Expense aggregate committed.
- **Expected Domain Events**: `finance.expense.recorded.v1`.
- **Expected Financial Impact**: Operating Expenses increase by `+₹350.00`; Cash Drawer decreases by `-₹350.00`; Operating Profit decreases by `₹350.00`. Gross profit remains unaffected.

---

### Scenario 16: Offline Counter Sale with Subsequent Cloud Sync
- **Given**: Shop Wi-Fi is down; Android device is offline.
- **When**: Cashier punches a ₹420 sale.
- **Then**: Device writes sale to local Room DB and enqueues event with `idempotencyKey = UUID_X` in local Outbox. Receipt is printed in 45ms.
- **When (2 hours later)**: Network reconnects; WorkManager pushes batch.
- **Expected Server State**: Server ingests UUID_X, creates database rows, commits atomically, and replies HTTP 200. Client marks outbox entry synced. Zero duplicate risk.

---

### Scenario 17: Concurrent Offline Sales on Two Devices
- **Given**: Store has 10 units of Dettol Soap. Device 1 and Device 2 are both offline.
- **When**: Device 1 sells 4 units (`Movement: -4`); Device 2 sells 3 units (`Movement: -3`).
- **Then**: Both devices commit locally.
- **When**: Both reconnect and sync.
- **Expected Cloud State**: Server processes both commutative movements:
  $$\text{Total Stock} = 10 - 4 - 3 = 3\text{ units}$$
  Neither sale overwrites the other.

---

### Scenario 18: AI Voice Command Confirmation Flow
- **Given**: Cashier speaks into microphone: *"Ramesh ji ke khate me ek kilo ghee aur do packet bread likho"*.
- **When**: AI extracts tokens: `customer="Ramesh", items=[{Ghee, 1kg}, {Bread, 2pkts}]`.
- **Then**: AI **does not write to DB**. It displays a confirmation card on the Android screen: `Bill for Ramesh Bhai: Ghee 1kg (₹540) + Bread 2pkts (₹80) = ₹620. [CONFIRM] [CANCEL]`.
- **When**: Cashier taps `[CONFIRM]`.
- **Then**: Application service executes `RecordSale`; domain invariants validate prices; sale and credit commit to ledger.

---

### Scenario 19: AI Hallucination Guardrail & Precondition Rejection
- **Given**: Cashier speaks: *"Teen packet Parle-G becho minus pachas rupaye me"* (invalid negative price).
- **When**: AI attempts to construct draft with price `amount = -50.00`.
- **Then**: `Money` value object constructor rejects negative price with `InvalidMonetaryAmountException`.
- **Expected State**: Application service halts; screen alerts cashier: *"Invalid price detected. Sale cannot be recorded."* Database remains completely untouched.

---

### Scenario 20: Stale Offline Catalog Price Honor Roll
- **Given**: Owner updates master price of Amul Butter from ₹56 to ₹60 on the backend. Mobile counter device is offline with cached price of ₹56.
- **When**: Cashier sells Amul Butter offline for ₹56 cash.
- **Then**: Sale is billed and committed at ₹56.
- **When**: Device syncs with cloud.
- **Expected Server State**: Server accepts the transaction at ₹56 because that was the binding contract printed on the physical receipt. Server updates device's local catalog cache to ₹60 for future sales.
