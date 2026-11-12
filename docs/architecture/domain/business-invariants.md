# DukaanAI: Business Invariants Specification

This document details the mandatory, testable business invariants of DukaanAI. Any operation that would violate an invariant must fail fast and abort within the domain layer before persistence.

---

## 1. Sales & Invoicing Invariants

- **INV-SALE-001 (Line Item Determinism)**:
  $$\text{LineTotal} = (\text{Quantity} \times \text{UnitPrice}) - \text{LineDiscount}$$
  Calculated with exact decimal arithmetic. Floating-point types are prohibited.
- **INV-SALE-002 (Invoice Total Exactness)**:
  $$\text{SaleTotalAmount} = \sum (\text{LineTotals}) - \text{OrderDiscount} + \text{Taxes}$$
- **INV-SALE-003 (Tender Balance Equality)**:
  $$\text{SaleTotalAmount} = \sum (\text{CashPayments}) + \sum (\text{UpiPayments}) + \text{CreditAmountAllocated}$$
  The sum of all payment allocations plus deferred customer credit must equal `SaleTotalAmount`.
- **INV-SALE-004 (Completed Sale Immutability)**:
  Once a `Sale` reaches the `Completed` state, its items, quantities, prices, discounts, and customer associations become permanently immutable. It cannot be edited.
- **INV-SALE-005 (Auditable Reversals & Voids)**:
  A sale can only be voided or reversed by appending an explicit compensating transaction with a non-empty `VoidReason` and an authorized staff identifier.
- **INV-SALE-006 (Tenant Integrity of Products)**:
  Every product line item in a sale must belong to the exact same `businessId` as the store where the sale is being performed.
- **INV-SALE-007 (Pricing Ceilings)**:
  Effective selling unit price cannot exceed the product's Maximum Retail Price (`MRP`) under Indian Legal Metrology regulations:
  $$\text{EffectiveUnitPrice} \le \text{MRP}$$

---

## 2. Inventory Invariants

- **INV-INV-001 (Fundamental Stock Equation)**:
  $$\text{CurrentStockBalance} = \text{InitialCheckpointBalance} + \sum_{i=1}^{n} \text{QuantityDelta}_i$$
  Stock is never set via an arbitrary assignment (`stock = X`). It is always derived from the sum of immutable journal movements.
- **INV-INV-002 (Mandatory Movement Pairing)**:
  Every finalized sale must produce an outward stock deduction movement (`SALE_DEDUCTION`). A sale cannot exist without corresponding stock movements.
- **INV-INV-003 (Procurement Inward Movement)**:
  Every received purchase bill must produce an inward stock addition movement (`PURCHASE_RECEIPT`).
- **INV-INV-004 (Movement Idempotency)**:
  Every stock movement requires a unique client-generated `idempotencyKey: UUID`. Duplicate submission of the same key must result in a no-op and return the existing movement record without modifying stock balance.
- **INV-INV-005 (Auditable Stock Adjustment)**:
  Physical stock variance discovered during audits must be recorded as an `AUDIT_ADJUSTMENT` movement containing the counted quantity, variance, reason, and auditor ID.
- **INV-INV-006 (Unit Conversion Exactness)**:
  Stock movements must convert secondary transaction units (e.g., kg, sack, packet) into the product's immutable `BaseUnit` (e.g., gram, piece) before committing to the ledger.
- **INV-INV-007 (Allowable Temporary Negative Stock)**:
  In fast-paced kirana retail, physical goods are often handed to customers before the distributor's inward bill has been keyed into the software. The inventory engine **must allow negative stock balances** while flagging them with a warning, rather than blocking the cash register checkout. When the purchase bill is entered later, the balance reconciles automatically.

---

## 3. Customer Khata (Credit Ledger) Invariants

- **INV-KHATA-001 (Credit Sale Debit)**:
  A credit sale (*Udhar*) increases the customer's outstanding balance:
  $$\text{OutstandingBalance}_{\text{new}} = \text{OutstandingBalance}_{\text{old}} + \text{CreditSaleAmount}$$
- **INV-KHATA-002 (Customer Repayment Credit)**:
  A customer repayment (*Jama*) strictly decreases the customer's outstanding balance:
  $$\text{OutstandingBalance}_{\text{new}} = \text{OutstandingBalance}_{\text{old}} - \text{RepaymentAmount}$$
- **INV-KHATA-003 (Zero Sales Revenue on Repayment)**:
  A customer repayment (*Jama*) **must never create or increase sales revenue**. Revenue was already recognized when the original sale occurred. Customer repayment is strictly an asset reallocation: Cash Drawer / Bank increases; Accounts Receivable decreases.
- **INV-KHATA-004 (Customer Advance Balance)**:
  If a customer deposits money exceeding their current outstanding, the resulting balance becomes negative, representing an advance deposit (*Peshgi*) owed by the merchant to the customer.
- **INV-KHATA-005 (Credit Limit Guardrail)**:
  If a customer profile specifies a non-null `creditLimit`, any credit sale that would push the outstanding balance past the limit must trigger an explicit confirmation warning or manager override.

---

## 4. Supplier Management Invariants

- **INV-SUP-001 (Purchase Liability Recognition)**:
  Receiving an unpaid or partially paid purchase bill increases the supplier's payable liability:
  $$\text{PayableBalance}_{\text{new}} = \text{PayableBalance}_{\text{old}} + \text{UnpaidPurchaseAmount}$$
- **INV-SUP-002 (Supplier Settlement Reduction)**:
  A payout made to a supplier strictly decreases the payable liability.
- **INV-SUP-003 (Debit Note on Purchase Return)**:
  Returning damaged or rejected goods to a supplier creates a debit note entry that reduces the outstanding payable balance owed to that supplier.

---

## 5. Financial Management Invariants

- **INV-FIN-001 (Decimal Precision Standard)**:
  All financial computations use fixed-point decimal arithmetic (minimum 4 decimal places internally, rounded using Banker's Rounding / `HALF_EVEN` to 2 decimal places for Rupee display). Floating-point math is strictly forbidden.
- **INV-FIN-002 (Distinction Between Cash Flow & Profit)**:
  Cash collections (*Galla*) must never be conflated with operating profit:
  - $\text{Cash Flow} = \text{Total Cash Inward} - \text{Total Cash Outward}$
  - $\text{Gross Profit} = \text{Net Sales Revenue} - \text{Cost of Goods Sold (COGS)}$
  - $\text{Operating Profit} = \text{Gross Profit} - \text{Operating Expenses}$
- **INV-FIN-003 (Cash Drawer Session Reconciliation)**:
  At the close of a cash register session:
  $$\text{ExpectedClosingCash} = \text{OpeningFloat} + \text{CashCollections} - \text{CashExpensesRecorded}$$
  $$\text{Variance} = \text{ActualCountedCash} - \text{ExpectedClosingCash}$$
  Any non-zero variance must be flagged with an auditable discrepancy note.
- **INV-FIN-004 (Expense Positive Magnitude)**:
  Recorded expense amounts must be strictly greater than zero ($> 0.0000$). Negative expenses are prohibited; expense reversals must be recorded as explicit refund adjustments.

---

## 6. AI Assistant Guardrail Invariants

- **INV-AI-001 (No Direct Mutation)**:
  The AI Assistant engine possesses **zero direct write access** to domain database tables. All mutating actions must pass through strongly typed application services.
- **INV-AI-002 (Untrusted Input Boundary)**:
  Data extracted from natural-language Hinglish utterances is considered an unvalidated draft until confirmed by the merchant.
- **INV-AI-003 (Deterministic Price Protection)**:
  The AI prompt is never permitted to calculate subtotal prices, taxes, or change due. The AI extracts tokens (`item="Atta"`, `qty=5`, `unit="kg"`); the deterministic calculation engine computes all financial numbers.
