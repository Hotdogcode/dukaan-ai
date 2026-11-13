# Stock Adjustments Workflow

## 1. Overview
Stock adjustments account for inventory variations outside regular sales and procurement cycles.

## 2. Adjustment Types & Ledger Impact
- `DAMAGED`: Stock spoilage, package tearing, pest infestation (`delta = -quantity`).
- `THEFT`: Pilferage or shoplifting loss (`delta = -quantity`).
- `FOUND`: Items discovered on shelves previously unrecorded (`delta = +quantity`).
- `MANUAL_IN`: Positive stock corrections (`delta = +quantity`).
- `MANUAL_OUT`: Negative stock write-offs (`delta = -quantity`).

## 3. Mandatory Audit Reason
All adjustments require a non-blank audit `reason` string to ensure accountability.
Staff user identification (`created_by_user_id`) is permanently stamped on the movement.
