# DukaanAI: Bounded Contexts Specification

This document defines the 11 logical bounded contexts of DukaanAI. Each context encapsulates a distinct business responsibility, protects its own consistency boundaries, and exposes explicit command, query, and event contracts.

---

## 1. Context 1: Business Management

### 1.1 Responsibility
Manages legal entity tenancy, store physical locations, organizational settings, merchant staff memberships, user roles, permission grants, operating currencies, and localization preferences (Hinglish/Hindi/English).

### 1.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `Business` (Tenant root)
- **Child Entities**: `Store`, `BusinessMember`, `RolePermission`
- **Value Objects**: `BusinessId`, `StoreId`, `MemberId`, `BusinessSettings`, `TaxIdentificationNumber` (e.g., GSTIN), `Currency`, `Timezone`, `LanguagePreference`

### 1.3 Commands
- `RegisterBusiness(name, ownerId, currency, gstin, language)`
- `AddStore(businessId, storeName, address, contactNumber)`
- `UpdateStoreSettings(storeId, settings)`
- `InviteMember(businessId, userId, role, assignedStores)`
- `RevokeMember(businessId, memberId)`

### 1.4 Queries
- `GetBusinessDetails(businessId)`
- `ListStores(businessId)`
- `GetMemberPermissions(businessId, memberId)`

### 1.5 Domain Events
- `BusinessRegistered(businessId, name, ownerId, registeredAt)`
- `StoreAdded(businessId, storeId, storeName, addedAt)`
- `MemberAssignedToStore(businessId, memberId, storeId)`
- `BusinessSettingsUpdated(businessId, newSettings)`

### 1.6 Invariants
- A Business must have at least one primary Store upon registration.
- Store names must be unique within a single Business.
- A BusinessMember cannot possess permissions exceeding their assigned role boundary.
- Tenant ID (`businessId`) is immutable once provisioned.

### 1.7 Dependencies
- Upstream to all other contexts (provides identity and authorization context).

---

## 2. Context 2: Product Catalogue

### 2.1 Responsibility
Maintains master catalog definitions, SKU identifiers, barcode registries, categories, packaging units, loose commodity definitions, unit conversion rules, and tax rate classifications.

### 2.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `Product`
- **Child Entities**: `ProductVariant`, `UnitConversionRule`
- **Value Objects**: `ProductId`, `SKU`, `Barcode`, `ProductName`, `CategoryName`, `UnitOfMeasure` (kg, g, l, ml, piece, packet, dozen), `ProductPrice` (MRP, standard selling price), `TaxRate` (GST slab 0%, 5%, 12%, 18%, 28%), `ReorderThreshold`

### 2.3 Commands
- `CreateProduct(businessId, name, category, barcode, baseUnit, sellingPrice, taxRate, reorderThreshold)`
- `UpdateProductPrice(productId, newSellingPrice, reason)`
- `DefineUnitConversion(productId, fromUnit, toUnit, multiplier)`
- `AttachBarcode(productId, barcode)`
- `DeactivateProduct(productId, reason)`

### 2.4 Queries
- `GetProductById(productId)`
- `LookupProductByBarcode(businessId, barcode)`
- `SearchProducts(businessId, query, category)`
- `GetUnitConversion(productId, fromUnit, toUnit)`

### 2.5 Domain Events
- `ProductCreated(productId, businessId, name, sku, baseUnit, sellingPrice)`
- `ProductPriceChanged(productId, oldPrice, newPrice, changedAt)`
- `ProductBarcodeLinked(productId, barcode)`
- `ProductDeactivated(productId, reason)`

### 2.6 Invariants
- Product identity is strictly separated from physical stock levels (Catalogue does not track stock count).
- Every product must have an immutable `BaseUnit` (the atomic unit of inventory storage, e.g., Gram for loose grains).
- Barcode must be unique within a Business.
- Unit conversion multipliers must be strictly positive non-zero decimals ($> 0$).

### 2.7 Dependencies
- Upstream to Sales, Purchasing, and Inventory.

---

## 3. Context 3: Sales (Counter POS & Invoicing)

### 3.1 Responsibility
Orchestrates high-speed counter billing, line-item pricing, discounts, invoice numbering, tax breakdown, customer credit tagging, payment tenders, and customer sale returns.

### 3.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `Sale` (Invoice / Counter Bill)
- **Child Entities**: `SaleLineItem`, `SalePaymentAllocation`, `SaleAdjustment`
- **Value Objects**: `SaleId`, `InvoiceNumber`, `CustomerId`, `SaleStatus` (Draft, Completed, PartiallyPaid, Paid, Returned, Voided), `Discount`, `LineItemTotal`, `SaleTaxBreakdown`, `TenderType` (Cash, UPI, Credit/Udhar, Split)

### 3.3 Commands
- `CreateDraftSale(storeId, cashierId, customerId?)`
- `AddSaleItem(saleId, productId, quantity, unitOfMeasure, overridePrice?)`
- `ApplySaleDiscount(saleId, discount)`
- `FinalizeSale(saleId, payments: List<PaymentAllocation>)`
- `VoidSale(saleId, reason, authorizedBy)`
- `InitiateSaleReturn(saleId, returnedItems: List<ReturnItemRequest>, refundMethod)`

### 3.4 Queries
- `GetSaleById(saleId)`
- `GetSaleByInvoiceNumber(storeId, invoiceNumber)`
- `ListSalesByDateRange(storeId, fromDate, toDate, status?)`

### 3.5 Domain Events
- `SaleCompleted(saleId, storeId, businessId, invoiceNumber, customerId?, lineItems, totalAmount, paidAmount, creditAmount, completedAt)`
- `SalePaymentAllocated(saleId, paymentId, amount, tenderType)`
- `SaleVoided(saleId, reason, voidedAt)`
- `SaleReturned(saleId, returnId, returnedItems, refundAmount, returnedAt)`

### 3.6 Invariants
- A completed sale is immutable; items cannot be added, removed, or edited.
- $\text{TotalAmount} = \sum (\text{LineItemTotals}) - \text{Discount} + \text{ApplicableTaxes}$.
- Total payment allocations plus credit allocation must equal `TotalAmount`.
- A sale cannot complete without emitting corresponding inventory deduction requests and customer credit additions.

### 3.7 Dependencies
- Depends on Product Catalogue (for SKU/pricing/taxes) and Business Management (for store context).
- Produces events consumed by Inventory, Financial Management, and Customer Management.

---

## 4. Context 4: Purchasing

### 4.1 Responsibility
Manages supplier procurement bills, inward purchase deliveries, unit cost calculations, distributor tax invoices, and supplier purchase returns.

### 4.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `Purchase` (Inward Supply Bill)
- **Child Entities**: `PurchaseLineItem`, `PurchasePaymentRecord`
- **Value Objects**: `PurchaseId`, `SupplierInvoiceNumber`, `SupplierId`, `PurchaseStatus` (Draft, Received, PartiallyPaid, Settled, Cancelled), `PurchaseUnitCost`, `PurchaseTaxBreakdown`

### 4.3 Commands
- `RecordPurchaseBill(storeId, supplierId, supplierInvoiceNumber, purchaseDate)`
- `AddPurchaseItem(purchaseId, productId, quantityReceived, unitOfMeasure, unitCost, taxRate)`
- `ReceivePurchaseInventory(purchaseId)`
- `RecordSupplierPayment(purchaseId, amount, paymentMethod)`
- `RecordPurchaseReturn(purchaseId, items: List<ReturnItemRequest>, debitNoteNumber)`

### 4.4 Queries
- `GetPurchaseById(purchaseId)`
- `ListPurchasesBySupplier(supplierId, dateRange)`

### 4.5 Domain Events
- `PurchaseReceived(purchaseId, storeId, businessId, supplierId, items, totalCost, receivedAt)`
- `PurchasePaymentRecorded(purchaseId, amount, paymentMethod, recordedAt)`
- `PurchaseReturned(purchaseId, returnedItems, debitNoteAmount, returnedAt)`

### 4.6 Invariants
- Inward stock movements can only be triggered when a purchase transitions to `Received`.
- Unit purchase cost must be non-negative ($\ge 0$).
- Total received cost updates the product's moving valuation in the Inventory context.

### 4.7 Dependencies
- Depends on Product Catalogue and Supplier Management.
- Publishes events consumed by Inventory and Financial Management.

---

## 5. Context 5: Inventory (Stock Movements & Ledgers)

### 5.1 Responsibility
Serves as the authoritative, auditable source of truth for physical stock levels across all stores using an immutable movement journal. Manages real-time stock balances, stock adjustments, wastage, spoilage, shrinkage, and stock valuation.

### 5.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `StockItem` (Per Product, Per Store boundary)
- **Child Entities**: `StockMovementJournalEntry`
- **Value Objects**: `StockMovementId`, `StockMovementType` (PurchaseReceipt, SaleDeduction, SaleReturn, PurchaseReturn, DamageSpoilage, AuditAdjustment), `QuantityDelta`, `BaseQuantity`, `ValuationAmount`, `StockBatchReference`

### 5.3 Commands
- `RecordStockMovement(storeId, productId, movementType, quantityDelta, unitOfMeasure, unitCost?, referenceId, idempotencyKey)`
- `AdjustStockAudit(storeId, productId, countedPhysicalQuantity, reason, auditorId)`
- `RecordDamageOrLoss(storeId, productId, damagedQuantity, unitOfMeasure, reason)`

### 5.4 Queries
- `GetCurrentStock(storeId, productId)`
- `GetStockLedgerHistory(storeId, productId, dateRange)`
- `ListLowStockProducts(storeId)`
- `GetInventoryValuation(storeId)`

### 5.5 Domain Events
- `StockMovementRecorded(movementId, storeId, businessId, productId, movementType, quantityDelta, balanceAfter, timestamp)`
- `StockLowThresholdBreached(storeId, productId, currentStock, reorderThreshold)`
- `StockDiscrepancyReconciled(storeId, productId, varianceQuantity, reconciledAt)`

### 5.6 Invariants
- **Core Invariant**: Stock balance is an aggregate sum of all historical valid journal entries:
  $$\text{Balance} = \sum \text{QuantityDelta}_i$$
- Stock cannot be mutated directly through an arbitrary update command; every modification requires a typed `StockMovementJournalEntry`.
- Duplicate processing of an `idempotencyKey` must result in a no-op returning the existing movement record.

### 5.7 Dependencies
- Consumes events from Sales (`SaleCompleted`, `SaleReturned`) and Purchasing (`PurchaseReceived`, `PurchaseReturned`).
- Publishes events consumed by Business Intelligence and Financial Management.

---

## 6. Context 6: Customer Management & Khata

### 6.1 Responsibility
Maintains customer profiles, contact directories, customer credit accounts (*Khata*), payment collection recording (*Jama*), customer advance deposits, credit limits, and WhatsApp reminder schedules.

### 6.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `CustomerAccount`
- **Child Entities**: `CustomerLedgerEntry`, `PaymentReminderSchedule`
- **Value Objects**: `CustomerId`, `CustomerName`, `PhoneNumber`, `CreditLimit`, `CustomerBalance` (Current outstanding owed), `CustomerLedgerType` (CreditSaleDebit, PaymentReceivedCredit, AdjustmentCredit, AdvanceDeposit)

### 6.3 Commands
- `RegisterCustomer(businessId, name, phoneNumber, creditLimit?)`
- `RecordCustomerCreditSale(customerId, saleId, amount, transactionDate)`
- `RecordCustomerPayment(customerId, amount, paymentMethod, referenceNote?)`
- `AdjustCustomerCredit(customerId, amount, adjustmentType, reason, authorizedBy)`
- `SchedulePaymentReminder(customerId, scheduledDate, messageTemplate)`

### 6.4 Queries
- `GetCustomerAccount(customerId)`
- `GetCustomerLedger(customerId, dateRange)`
- `ListCustomersWithOutstanding(businessId, minBalance?)`

### 6.5 Domain Events
- `CustomerRegistered(customerId, businessId, name, phoneNumber)`
- `CustomerCreditIncreased(customerId, saleId, amount, newOutstanding, timestamp)`
- `CustomerPaymentReceived(customerId, paymentId, amount, newOutstanding, timestamp)`
- `CustomerCreditLimitExceeded(customerId, currentBalance, creditLimit)`

### 6.6 Invariants
- Customer payment recording (*Jama*) **never** increases sales revenue; it is strictly an Accounts Receivable asset reduction.
- Outstanding balance must mathematically equal:
  $$\text{Outstanding} = \sum \text{Debits (Credit Sales)} - \sum \text{Credits (Payments & Adjustments)}$$
- If customer balance is negative, it represents a Customer Advance (*Peshgi*).

### 6.7 Dependencies
- Consumes events from Sales (`SaleCompleted` with credit tender).
- Emits events consumed by Financial Management and AI Assistant.

---

## 7. Context 7: Supplier Management

### 7.1 Responsibility
Maintains wholesale vendor profiles, supplier contact channels, purchase liabilities, settlement histories, and vendor credit terms.

### 7.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `SupplierAccount`
- **Child Entities**: `SupplierLedgerEntry`
- **Value Objects**: `SupplierId`, `SupplierName`, `GSTIN`, `PaymentTermsDays`, `SupplierPayableBalance`

### 7.3 Commands
- `RegisterSupplier(businessId, name, contactPhone, gstin?, paymentTermsDays?)`
- `PostPurchaseLiability(supplierId, purchaseId, amount)`
- `RecordSupplierPaymentSettlement(supplierId, amount, paymentMethod, reference)`

### 7.4 Queries
- `GetSupplierAccount(supplierId)`
- `ListOutstandingSupplierPayables(businessId)`

### 7.5 Domain Events
- `SupplierRegistered(supplierId, businessId, name)`
- `SupplierLiabilityRecorded(supplierId, purchaseId, amount, newPayableBalance)`
- `SupplierPaymentSettled(supplierId, amount, newPayableBalance, settledAt)`

### 7.6 Invariants
- Supplier payable balance equals total inward purchase liabilities minus settlements and purchase return debit notes.

### 7.7 Dependencies
- Consumes events from Purchasing (`PurchaseReceived`, `PurchaseReturned`).

---

## 8. Context 8: Financial Management

### 8.1 Responsibility
Aggregates sales revenue, cash-drawer collections (*Galla* reconciliation), operational shop expenses, Cost of Goods Sold (COGS), gross margins, and operating net margins.

### 8.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `CashRegister` (Drawer / Galla session)
- **Aggregate Root**: `Expense`
- **Value Objects**: `ExpenseId`, `ExpenseCategory` (Rent, Electricity, StaffSalary, Logistics, Maintenance, Refreshments), `FinancialReportPeriod`, `GrossProfitSummary`, `OperatingProfitSummary`

### 8.3 Commands
- `OpenRegisterSession(storeId, openingFloat, cashierId)`
- `CloseRegisterSession(sessionId, closingCashCounted, discrepancyReason?)`
- `RecordExpense(storeId, category, amount, paymentMethod, recipientName, notes)`

### 8.4 Queries
- `GetDailyCashSummary(storeId, date)`
- `CalculateGrossProfit(storeId, dateRange)`
- `GetProfitAndLossStatement(storeId, dateRange)`

### 8.5 Domain Events
- `RegisterSessionOpened(sessionId, storeId, openingFloat, openedAt)`
- `RegisterSessionClosed(sessionId, closingCash, varianceAmount, closedAt)`
- `ExpenseRecorded(expenseId, storeId, category, amount, recordedAt)`

### 8.6 Invariants
- Operating Profit = Gross Profit - Operating Expenses.
- Gross Profit = Net Sales Revenue - COGS.
- Cash Drawer Variance = Actual Counted Cash - (Opening Float + Cash Collections - Cash Expenses).
- Financial math uses exact fixed-point decimal calculation; no estimated approximations in core finance.

### 8.7 Dependencies
- Consumes events from Sales, Purchasing, Customer Management, and Inventory.

---

## 9. Context 9: Business Intelligence (BI & Analytics)

### 9.1 Responsibility
Computes non-transactional projections, fast-moving vs dead stock analytics, customer churn predictions, margin heatmaps, and restock recommendation alerts.

### 9.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `StoreAnalyticsSnapshot`
- **Value Objects**: `DeadStockItem`, `ProductSalesVelocity`, `CustomerRepaymentVelocity`

### 9.3 Commands / Calculations
- `RecomputeDailySnapshot(storeId, date)`
- `GenerateReorderRecommendations(storeId)`

### 9.4 Queries
- `GetTopSellingProducts(storeId, dateRange, limit)`
- `GetDeadStockList(storeId, daysWithoutSale)`
- `GetCustomerRepaymentMetrics(businessId)`

### 9.5 Invariants
- BI models are read-only analytical projections; they never mutate operational transaction tables.

### 9.6 Dependencies
- Consumes integration events from Sales, Inventory, Customer Management, and Purchasing.

---

## 10. Context 10: AI Assistant & Orchestration

### 10.1 Responsibility
Acts as the natural-language conversational gateway. Interprets audio/text Hinglish utterances, maps customer vernacular to SKUs and Customer IDs, constructs proposed command drafts, and handles confirmation dialogues.

### 10.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `ConversationalSession`
- **Child Entities**: `ActionDraft`
- **Value Objects**: `SessionId`, `DraftActionId`, `Utterance`, `IntentType` (POS_SALE, KHATA_CREDIT, RECORD_EXPENSE, QUERY_STOCK, QUERY_SALES), `ExtractionConfidence`, `ActionStatus` (Drafted, UserConfirmed, Rejected, Executed)

### 10.3 Commands
- `ProcessUtterance(sessionId, utteranceText, audioBuffer?)`
- `ConfirmActionDraft(draftId, authorizedBy)`
- `CancelActionDraft(draftId, reason)`

### 10.4 Queries
- `GetPendingActionDrafts(sessionId)`

### 10.5 Invariants
- The AI context cannot directly execute mutating commands; every state-altering action requires human approval or an explicit confidence threshold bypass protocol.
- Domain rules are enforced by the target application service, not by the LLM prompt.

### 10.6 Dependencies
- Calls Application Services across Sales, Customer Management, Inventory, and Financial Management via strictly typed command ports.

---

## 11. Context 11: Subscription & Entitlements

### 11.1 Responsibility
Manages SaaS billing tiers (Free, Premium, Enterprise), feature flag gates, multi-device sync licenses, and AI request quotas.

### 11.2 Core Entities & Aggregate Roots
- **Aggregate Root**: `TenantSubscription`
- **Value Objects**: `PlanTier` (Free, ProMonthly, ProYearly), `FeatureFlag`, `QuotaLimit`, `QuotaUsage`

### 11.3 Commands
- `ProvisionSubscription(businessId, planTier)`
- `UpgradePlan(businessId, newPlanTier, paymentToken)`
- `IncrementQuotaUsage(businessId, quotaType, count)`

### 11.4 Invariants
- When an account exceeds its quota or lapses in subscription, data access remains read-only; historical records are never deleted.

### 11.5 Dependencies
- Upstream gatekeeper for Business Management and AI Assistant.
