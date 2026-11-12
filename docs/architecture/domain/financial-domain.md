# DukaanAI: Financial Domain & Ledger Specification

This document details the financial transaction architecture, revenue recognition rules, profit equations, cash drawer reconciliation, and ledger invariants for DukaanAI.

---

## 1. Architectural Scope & Positioning

DukaanAI provides a **purpose-built retail operational finance engine** tailored for Indian shopkeepers. 

> [!NOTE]
> **Boundary Statement**: DukaanAI is **not** a general-ledger enterprise accounting software (such as Tally ERP or SAP). It does not maintain complex multi-tier balance sheets, depreciation schedules, or corporate tax filings. Instead, it delivers a **tamper-proof, double-entry operational ledger** governing counter sales, customer credit (*Udhar*), distributor liabilities, cash flow (*Galla*), and true gross/operating profit margins.

---

## 2. Fundamental Financial Distinctions

A widespread failure in low-end retail software is conflating **Cash Flow** with **Profit**, leading shopkeepers to falsely believe they are profitable simply because cash is present in their till.

DukaanAI enforces strict architectural separation between three financial pillars:

```
+-----------------------------------------------------------------------------------+
| 1. Sales & Revenue Plane        (Accrual Revenue Recognized at Point of Sale)     |
|    - Net Sales Revenue = Gross Sales - Discounts - Returns                        |
|    - Recognized immediately when goods leave the counter, regardless of payment.  |
+-----------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------+
| 2. Cash & Collection Plane      (Actual Liquidity Movements in Galla / Bank)      |
|    - Cash Inward: Immediate cash sales + Customer Khata repayments (Jama).        |
|    - Cash Outward: Supplier payments + Petty shop expenses + Cash refunds.        |
|    - Cash Flow = Inward - Outward.                                                |
+-----------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------+
| 3. Profitability Plane          (Economic Surplus Created by Retail Operations)   |
|    - Gross Profit = Net Sales Revenue - Cost of Goods Sold (COGS).                |
|    - Operating Profit = Gross Profit - Operating Shop Expenses.                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Financial Equations & Calculation Rules

All calculations are executed using `Money` value objects backed by fixed-point decimal arithmetic.

### 3.1 Revenue Equations
$$\text{GrossSales} = \sum (\text{LineItemQuantity} \times \text{SellingPrice})$$
$$\text{NetSalesRevenue} = \text{GrossSales} - \text{OrderDiscounts} - \text{SalesReturns}$$

### 3.2 Cost of Goods Sold (COGS)
When products are sold, COGS is determined using the product's moving weighted average cost ($C_{\text{wac}}$) at the time of sale:
$$\text{COGS} = \sum_{i=1}^{m} (\text{QuantitySold}_i \times C_{\text{wac}, i})$$

### 3.3 Profit Equations
$$\text{GrossProfit} = \text{NetSalesRevenue} - \text{COGS}$$
$$\text{GrossMarginPercentage} = \left(\frac{\text{GrossProfit}}{\text{NetSalesRevenue}}\right) \times 100$$
$$\text{OperatingProfit} = \text{GrossProfit} - \sum \text{OperatingExpenses}$$

> [!IMPORTANT]
> **Financial Invariant**: Customer repayments (*Jama*) and loan infusions are **strictly excluded** from Gross and Operating Profit calculations.

---

## 4. Customer Khata & Double-Entry Mechanics

Customer credit represents accounts receivable. Every interaction is recorded as a double-entry journal:

### Scenario A: Customer purchases ₹1,000 worth of groceries on Credit (*Udhar*)
1. **Debit**: Customer Khata Account (Accounts Receivable) increases by `+₹1,000.00`.
2. **Credit**: Sales Revenue recognized as `+₹1,000.00`.
3. **Inventory**: Stock deducted for goods sold; COGS recognized.
4. **Cash Impact**: `₹0.00` (Cash till is unaffected).

### Scenario B: Customer pays ₹600 toward their credit balance (*Jama*)
1. **Debit**: Cash Drawer / Bank Account increases by `+₹600.00`.
2. **Credit**: Customer Khata Account (Accounts Receivable) decreases by `-₹600.00`.
3. **Sales Revenue Impact**: `₹0.00` (**Zero revenue recognized!** Revenue was already accounted for in Scenario A).
4. **Profit Impact**: `₹0.00` (Liquidity transfer only).

### Scenario C: Customer pays ₹1,200 when only ₹1,000 was owed
1. Outstanding balance reduces to `₹0.00`.
2. Remaining `₹200.00` is credited to the customer account as an **Advance Deposit (*Peshgi*)**.
3. Customer balance displays as `-₹200.00` (Merchant liability to customer).
4. On their next purchase, the ₹200 advance is automatically applied before generating new credit.

---

## 5. Refunds, Reversals & Audit Adjustments

Historical financial entries are **never silently overwritten**. Compensating entries preserve full auditability.

### 5.1 Counter Sale Return
When a customer returns a ₹150 item with original cash tender:
1. `SaleReturn` record appended referencing original `SaleId`.
2. Stock Movement appended: `+1` unit added back to inventory (`SALE_RETURN`).
3. COGS is reversed by `1 * CostPrice`.
4. Net Sales Revenue reduced by `₹150.00`.
5. Cash Drawer credited: `-₹150.00` paid out to customer.

### 5.2 Counter Sale Void (Same-Day Cancellation)
If a sale was punched by mistake:
1. Status transitions to `VOIDED`.
2. A compensating reversal transaction is appended to the ledger.
3. Inventory deduction is restored via `AUDIT_ADJUSTMENT`.
4. If payment was cash, physical cash in drawer is reconciled.
5. If payment was customer credit, customer balance debit is cancelled.

---

## 6. Cash Drawer (*Galla*) Session Reconciliation

At the cash counter, cash physically moves through the drawer. DukaanAI models drawer sessions using an explicit opening and closing lifecycle:

$$\text{ExpectedClosingCash} = \text{OpeningFloat} + \text{CashSales} + \text{CustomerCashRepayments} - \text{CashExpenses} - \text{SupplierCashPayouts} - \text{CashRefunds}$$

$$\text{Variance} = \text{ActualCountedCash} - \text{ExpectedClosingCash}$$

- **Variance = 0**: Perfect reconciliation (*Galla barabar*).
- **Variance > 0**: Cash Surplus (*Galla zyada*).
- **Variance < 0**: Cash Shortage (*Galla kam*).

Every variance requires an explicit audit notation before closing the register session.
