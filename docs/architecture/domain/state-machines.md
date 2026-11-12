# DukaanAI: State Machines & Lifecycle Transitions

This document defines the formal state machines, transition rules, preconditions, and invariants governing key domain entity lifecycles in DukaanAI.

---

## 1. Sale Lifecycle State Machine

A counter sale progresses from drafting to completion and potential reversal.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : CreateDraftSale()
    
    DRAFT --> DRAFT : AddItem() / RemoveItem() / ApplyDiscount()
    DRAFT --> CANCELLED : CancelDraft()
    
    DRAFT --> COMPLETED : FinalizeSale() [Full Immediate Tender Paid]
    DRAFT --> PARTIALLY_PAID : FinalizeSale() [Tender < Total, No Credit Configured]
    DRAFT --> COMPLETED : FinalizeSale() [Split Paid + Valid Customer Credit]
    
    PARTIALLY_PAID --> COMPLETED : RecordDeferredPayment() [Balance == 0]
    
    COMPLETED --> PARTIALLY_RETURNED : InitiateSaleReturn() [Partial Items Returned]
    COMPLETED --> RETURNED : InitiateSaleReturn() [All Items Returned]
    PARTIALLY_RETURNED --> RETURNED : InitiateSaleReturn() [Remaining Items Returned]
    
    COMPLETED --> VOIDED : VoidSale() [Same Day / Prior to Day Close]
    
    CANCELLED --> [*]
    RETURNED --> [*]
    VOIDED --> [*]
```

### Transition Specifications:

| Initial State | Command | Preconditions | Resulting State | Events Emitted | Rejected Transitions & Reason |
|---|---|---|---|---|---|
| `[*]"` | `CreateDraftSale` | Valid `storeId` & `cashierId`. | `DRAFT` | `SaleDraftCreated` | Cannot create for deactivated store. |
| `DRAFT` | `FinalizeSale` | At least 1 valid line item; Payments + Credit == TotalAmount. | `COMPLETED` | `SaleCompleted`, `StockDeductionRequested`, `CustomerCreditDebited?` | Rejected if total != allocated tenders. |
| `DRAFT` | `CancelDraft` | None. | `CANCELLED` | `SaleDraftCancelled` | No stock or financial impact. |
| `COMPLETED` | `InitiateSaleReturn` | Return quantity $\le$ original sold quantity; return window active. | `PARTIALLY_RETURNED` or `RETURNED` | `SaleReturned`, `StockReturnRestored`, `RefundIssued` | Rejected if returning more than sold. |
| `COMPLETED` | `VoidSale` | Register session not yet locked; explicit void reason provided. | `VOIDED` | `SaleVoided`, `StockDeductionReversed` | Cannot void an already returned sale. |
| `VOIDED` / `RETURNED` | Any Mutating Command | None (Terminal States). | Rejected | None | **Terminal states are permanently locked.** |

---

## 2. Purchase Lifecycle State Machine

Governs distributor procurement from billing to inward receipt and payment settlement.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : RecordPurchaseBill()
    
    DRAFT --> DRAFT : AddPurchaseItem() / EditCost()
    DRAFT --> CANCELLED : CancelBill()
    
    DRAFT --> RECEIVED : ReceivePurchaseInventory()
    
    RECEIVED --> PARTIALLY_PAID : RecordSupplierPayment() [Paid < TotalCost]
    RECEIVED --> SETTLED : RecordSupplierPayment() [Paid == TotalCost]
    
    PARTIALLY_PAID --> SETTLED : RecordSupplierPayment() [Remaining Balance Cleared]
    
    RECEIVED --> PARTIALLY_RETURNED : RecordPurchaseReturn() [Debit Note Issued]
    RECEIVED --> RETURNED : RecordPurchaseReturn() [Full Bill Rejected]
    
    CANCELLED --> [*]
    SETTLED --> [*]
    RETURNED --> [*]
```

### Transition Specifications:

| Initial State | Command | Preconditions | Resulting State | Events Emitted | Invariants & Notes |
|---|---|---|---|---|---|
| `[*]"` | `RecordPurchaseBill` | Valid `supplierId`, invoice number, and store. | `DRAFT` | `PurchaseDraftRecorded` | Line items can be adjusted before receipt. |
| `DRAFT` | `ReceivePurchaseInventory` | At least 1 item; unit costs $\ge 0$. | `RECEIVED` | `PurchaseReceived`, `StockAdditionRequested`, `SupplierLiabilityPosted` | **Inventory additions trigger only upon transitioning to `RECEIVED`.** |
| `RECEIVED` | `RecordSupplierPayment` | Payment amount $\le$ unpaid bill balance. | `PARTIALLY_PAID` or `SETTLED` | `PurchasePaymentRecorded`, `SupplierLiabilityReduced` | Cash / Bank account balance reduces accordingly. |
| `RECEIVED` | `RecordPurchaseReturn` | Returned quantity $\le$ received quantity; debit note generated. | `PARTIALLY_RETURNED` or `RETURNED` | `PurchaseReturned`, `StockOutwardRecorded`, `DebitNoteCreated` | Reduces inventory and decreases supplier payable liability. |

---

## 3. Payment Lifecycle State Machine

Models individual monetary tender flows across Cash, UPI, and Digital Khata.

```mermaid
stateDiagram-v2
    [*] --> INITIATED : InitiatePayment(tenderType, amount)
    
    INITIATED --> AUTHORIZED : PaymentAuthorized() [e.g. UPI soundbox tone / dynamic QR]
    INITIATED --> SETTLED : RecordCashTender() [Immediate physical cash in galla]
    INITIATED --> SETTLED : PostCreditLedger() [Immediate customer khata debit]
    
    AUTHORIZED --> SETTLED : ConfirmSettlement() [Webhook / Soundbox ack]
    AUTHORIZED --> FAILED : TimeoutOrDeclined()
    
    INITIATED --> FAILED : PaymentFailed()
    
    SETTLED --> REFUNDED : IssueRefund() [Sale Return]
    SETTLED --> REVERSED : ReversePayment() [Discrepancy / Chargeback]
    
    FAILED --> [*]
    REFUNDED --> [*]
    REVERSED --> [*]
```

### Transition Specifications:
- `SETTLED`: Monetary value is recognized in the financial register.
- `REFUNDED`: Compensating reversal tender issued with identical payment method where possible.
- `REVERSED`: Audit correction voiding a fraudulent or duplicated transaction.

---

## 4. Inventory Adjustment Lifecycle State Machine

Controls physical stock reconciliation, damage write-offs, and audit corrections.

```mermaid
stateDiagram-v2
    [*] --> PROPOSED : ProposeStockAdjustment(storeId, productId, countedQty)
    
    PROPOSED --> REJECTED : RejectAdjustment(reason)
    PROPOSED --> COMMITTED : ApproveAdjustment(authorizedBy)
    
    COMMITTED --> AUDITED : ReconcileDiscrepancy()
    
    REJECTED --> [*]
    AUDITED --> [*]
```

### Transition Specifications:
- `PROPOSED`: Draft adjustment created during count. System computes variance: $\Delta = \text{Counted} - \text{SystemBalance}$. No stock balance change occurs.
- `COMMITTED`: Authorized by store owner/manager. Generates an `AUDIT_ADJUSTMENT` movement entry in `StockMovementJournal`.
- `AUDITED`: Finalized reconciliation report archived for tax and inventory accounting.

---

## 5. AI Action Approval & Execution Lifecycle

Enforces human-in-the-loop safety for voice and conversational transactions.

```mermaid
stateDiagram-v2
    [*] --> EXTRACTED : ParseUtterance(audio/text)
    
    EXTRACTED --> PROPOSED_TO_HUMAN : ValidateSchemaAndDisambiguate()
    EXTRACTED --> REJECTED_BY_SYSTEM : ExtractionConfidenceBelowThreshold()
    
    PROPOSED_TO_HUMAN --> APPROVED : ShopkeeperTapsConfirm()
    PROPOSED_TO_HUMAN --> REJECTED : ShopkeeperTapsCancel()
    PROPOSED_TO_HUMAN --> EXPIRED : ConfirmationTimeout(120s)
    
    APPROVED --> EXECUTED : DispatchToApplicationService()
    APPROVED --> EXECUTION_FAILED : DomainInvariantViolation()
    
    REJECTED_BY_SYSTEM --> [*]
    REJECTED --> [*]
    EXPIRED --> [*]
    EXECUTED --> [*]
    EXECUTION_FAILED --> [*]
```

### Transition Specifications:
- `EXTRACTED`: LLM parses Hinglish voice utterance into candidate JSON tokens.
- `PROPOSED_TO_HUMAN`: Application layer verifies product/customer disambiguation and presents a high-contrast confirmation card on screen.
- `APPROVED`: Shopkeeper explicitly taps "Confirm".
- `EXECUTED`: Target domain application service (`RecordSale`, `RecordExpense`, `RecordCredit`) executes with deterministic business rules.
- `EXECUTION_FAILED`: If the domain rejects the command (e.g., negative money, missing mandatory field), the failure is reported to the user with a specific business explanation.
