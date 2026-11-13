package ai.dukaan.core.model

import java.math.BigDecimal
import java.time.Instant
import java.util.UUID

enum class StockMovementType {
    OPENING_STOCK,
    PURCHASE_RECEIVED,
    SALE,
    SALE_RETURN,
    PURCHASE_RETURN,
    MANUAL_ADJUSTMENT_IN,
    MANUAL_ADJUSTMENT_OUT,
    DAMAGE,
    EXPIRY,
    TRANSFER_IN,
    TRANSFER_OUT,
    REVERSAL,
    AUDIT_ADJUSTMENT,
}

enum class StockAdjustmentType {
    MANUAL_IN,
    MANUAL_OUT,
    DAMAGE,
    EXPIRY,
    COUNT_CORRECTION,
}

enum class StockStatus {
    OUT_OF_STOCK,
    LOW_STOCK,
    IN_STOCK,
    OVERSTOCKED,
}

enum class NegativeStockPolicy {
    DISALLOW_NEGATIVE_STOCK,
    ALLOW_NEGATIVE_STOCK,
}

/**
 * Domain representation of a product variant's stock standing at a specific retail store.
 */
data class InventoryItem(
    val variantId: UUID,
    val productId: UUID,
    val productName: String,
    val variantName: String,
    val sku: String? = null,
    val barcode: String? = null,
    val categoryName: String? = null,
    val currentQuantity: BigDecimal,
    val uomName: String,
    val movingAverageCost: BigDecimal,
    val sellingPrice: BigDecimal,
    val inventoryValuation: BigDecimal,
    val minStockLevel: BigDecimal,
    val reorderQuantity: BigDecimal,
    val stockStatus: StockStatus,
    val lastMovementAt: Instant? = null,
)

/**
 * Paginated store inventory summary and aggregate valuation KPIs.
 */
data class InventorySummary(
    val totalItems: Int,
    val totalValuation: BigDecimal,
    val lowStockCount: Int,
    val outOfStockCount: Int,
    val items: List<InventoryItem>,
    val page: Int,
    val limit: Int,
    val totalPages: Int,
)

/**
 * Detailed stock, valuation, and status metrics for a single variant.
 */
data class VariantStockDetails(
    val variantId: UUID,
    val productId: UUID,
    val productName: String,
    val variantName: String,
    val sku: String? = null,
    val barcode: String? = null,
    val categoryName: String? = null,
    val currentQuantity: BigDecimal,
    val uomName: String,
    val movingAverageCost: BigDecimal,
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal,
    val inventoryValuation: BigDecimal,
    val minStockLevel: BigDecimal,
    val reorderQuantity: BigDecimal,
    val stockStatus: StockStatus,
    val hasOpeningStock: Boolean,
)

/**
 * Immutable stock ledger movement entry.
 */
data class StockMovementRecord(
    val id: UUID,
    val businessId: UUID,
    val storeId: UUID,
    val variantId: UUID,
    val movementType: String,
    val quantity: BigDecimal,
    val unitCost: BigDecimal,
    val totalCost: BigDecimal,
    val balanceAfter: BigDecimal,
    val referenceType: String? = null,
    val referenceId: UUID? = null,
    val reason: String? = null,
    val notes: String? = null,
    val createdAt: Instant,
    val createdByUserId: UUID? = null,
)

/**
 * Physical stock counting audit session.
 */
data class InventoryCountSession(
    val id: UUID,
    val businessId: UUID,
    val storeId: UUID,
    val sessionNumber: String,
    val status: String, // OPEN, COMPLETED, CANCELLED
    val totalVariantsCounted: Int,
    val totalVarianceQuantity: BigDecimal,
    val totalVarianceValue: BigDecimal,
    val notes: String? = null,
    val createdAt: Instant,
    val completedAt: Instant? = null,
    val items: List<InventoryCountItem> = emptyList(),
)

/**
 * Line item within a physical inventory count audit session.
 */
data class InventoryCountItem(
    val id: UUID,
    val sessionId: UUID,
    val productId: UUID,
    val variantId: UUID,
    val productName: String? = null,
    val variantName: String? = null,
    val sku: String? = null,
    val barcode: String? = null,
    val expectedQuantity: BigDecimal,
    val countedQuantity: BigDecimal,
    val varianceQuantity: BigDecimal,
    val unitCost: BigDecimal,
    val varianceValue: BigDecimal,
    val notes: String? = null,
)

/**
 * Domain payload for recording opening stock.
 */
data class OpeningStockRequestModel(
    val variantId: UUID,
    val quantity: BigDecimal,
    val unitCost: BigDecimal,
    val notes: String? = null,
)

/**
 * Domain payload for stock adjustments.
 */
data class StockAdjustmentRequestModel(
    val variantId: UUID,
    val adjustmentType: StockAdjustmentType,
    val quantity: BigDecimal,
    val unitCost: BigDecimal? = null,
    val reason: String,
    val notes: String? = null,
)

/**
 * Store stock projection reconciliation report.
 */
data class ReconciliationReport(
    val storeId: UUID,
    val totalVariantsChecked: Int,
    val variantsReconciled: Int,
    val discrepanciesRepaired: Int,
    val discrepancyDetails: List<Map<String, String>>,
    val reconciledAt: Instant,
)
