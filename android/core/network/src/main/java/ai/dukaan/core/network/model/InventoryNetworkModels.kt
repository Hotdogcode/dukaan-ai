package ai.dukaan.core.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import java.math.BigDecimal

@Serializable
data class OpeningStockRequestNetwork(
    @SerialName("variant_id") val variantId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("quantity") val quantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("unit_cost") val unitCost: BigDecimal,
    @SerialName("notes") val notes: String? = null,
)

@Serializable
data class OpeningStockResponseNetwork(
    @SerialName("movement_id") val movementId: String,
    @SerialName("variant_id") val variantId: String,
    @SerialName("store_id") val storeId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("quantity") val quantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("unit_cost") val unitCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("current_quantity") val currentQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("moving_average_cost") val movingAverageCost: BigDecimal,
    @SerialName("recorded_at") val recordedAt: String,
)

@Serializable
data class StockAdjustmentRequestNetwork(
    @SerialName("variant_id") val variantId: String,
    @SerialName("adjustment_type") val adjustmentType: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("quantity") val quantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("unit_cost") val unitCost: BigDecimal? = null,
    @SerialName("reason") val reason: String,
    @SerialName("notes") val notes: String? = null,
)

@Serializable
data class StockAdjustmentResponseNetwork(
    @SerialName("adjustment_id") val adjustmentId: String,
    @SerialName("movement_id") val movementId: String,
    @SerialName("variant_id") val variantId: String,
    @SerialName("adjustment_type") val adjustmentType: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("quantity") val quantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("previous_quantity") val previousQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("new_quantity") val newQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("moving_average_cost") val movingAverageCost: BigDecimal,
    @SerialName("recorded_at") val recordedAt: String,
)

@Serializable
data class InventoryCountSessionCreateNetwork(
    @SerialName("notes") val notes: String? = null,
)

@Serializable
data class InventoryCountItemCreateNetwork(
    @SerialName("variant_id") val variantId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("counted_quantity") val countedQuantity: BigDecimal,
    @SerialName("notes") val notes: String? = null,
)

@Serializable
data class InventoryCountItemResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("product_id") val productId: String,
    @SerialName("variant_id") val variantId: String,
    @SerialName("product_name") val productName: String? = null,
    @SerialName("variant_name") val variantName: String? = null,
    @SerialName("sku") val sku: String? = null,
    @SerialName("barcode") val barcode: String? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("expected_quantity") val expectedQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("counted_quantity") val countedQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("variance_quantity") val varianceQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("unit_cost") val unitCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("variance_value") val varianceValue: BigDecimal,
    @SerialName("notes") val notes: String? = null,
)

@Serializable
data class InventoryCountSessionResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("store_id") val storeId: String,
    @SerialName("session_number") val sessionNumber: String,
    @SerialName("status") val status: String,
    @SerialName("total_variants_counted") val totalVariantsCounted: Int,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("total_variance_quantity") val totalVarianceQuantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("total_variance_value") val totalVarianceValue: BigDecimal,
    @SerialName("notes") val notes: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("completed_at") val completedAt: String? = null,
    @SerialName("items") val items: List<InventoryCountItemResponseNetwork> = emptyList(),
)

@Serializable
data class CompleteCountSessionResponseNetwork(
    @SerialName("session_id") val sessionId: String,
    @SerialName("status") val status: String,
    @SerialName("items_adjusted") val itemsAdjusted: Int,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("total_variance_value") val totalVarianceValue: BigDecimal,
    @SerialName("completed_at") val completedAt: String,
)

@Serializable
data class InventorySummaryItemNetwork(
    @SerialName("variant_id") val variantId: String,
    @SerialName("product_id") val productId: String,
    @SerialName("product_name") val productName: String,
    @SerialName("variant_name") val variantName: String,
    @SerialName("sku") val sku: String? = null,
    @SerialName("barcode") val barcode: String? = null,
    @SerialName("category_name") val categoryName: String? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("current_quantity") val currentQuantity: BigDecimal,
    @SerialName("uom_name") val uomName: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("moving_average_cost") val movingAverageCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("inventory_valuation") val inventoryValuation: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("min_stock_level") val minStockLevel: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("reorder_quantity") val reorderQuantity: BigDecimal,
    @SerialName("stock_status") val stockStatus: String,
    @SerialName("last_movement_at") val lastMovementAt: String? = null,
)

@Serializable
data class InventorySummaryResponseNetwork(
    @SerialName("total_items") val totalItems: Int,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("total_valuation") val totalValuation: BigDecimal,
    @SerialName("low_stock_count") val lowStockCount: Int,
    @SerialName("out_of_stock_count") val outOfStockCount: Int,
    @SerialName("items") val items: List<InventorySummaryItemNetwork>,
    @SerialName("page") val page: Int,
    @SerialName("limit") val limit: Int,
    @SerialName("total_pages") val totalPages: Int,
)

@Serializable
data class StockDetailsResponseNetwork(
    @SerialName("variant_id") val variantId: String,
    @SerialName("product_id") val productId: String,
    @SerialName("product_name") val productName: String,
    @SerialName("variant_name") val variantName: String,
    @SerialName("sku") val sku: String? = null,
    @SerialName("barcode") val barcode: String? = null,
    @SerialName("category_name") val categoryName: String? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("current_quantity") val currentQuantity: BigDecimal,
    @SerialName("uom_name") val uomName: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("moving_average_cost") val movingAverageCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("inventory_valuation") val inventoryValuation: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("min_stock_level") val minStockLevel: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("reorder_quantity") val reorderQuantity: BigDecimal,
    @SerialName("stock_status") val stockStatus: String,
    @SerialName("has_opening_stock") val hasOpeningStock: Boolean,
)

@Serializable
data class StockMovementResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("store_id") val storeId: String,
    @SerialName("variant_id") val variantId: String,
    @SerialName("movement_type") val movementType: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("quantity") val quantity: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("unit_cost") val unitCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("total_cost") val totalCost: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("balance_after") val balanceAfter: BigDecimal,
    @SerialName("reference_type") val referenceType: String? = null,
    @SerialName("reference_id") val referenceId: String? = null,
    @SerialName("reason") val reason: String? = null,
    @SerialName("notes") val notes: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("created_by_user_id") val createdByUserId: String? = null,
)

@Serializable
data class PaginatedStockMovementsResponseNetwork(
    @SerialName("items") val items: List<StockMovementResponseNetwork>,
    @SerialName("total") val total: Int,
    @SerialName("page") val page: Int,
    @SerialName("limit") val limit: Int,
    @SerialName("total_pages") val totalPages: Int,
)

@Serializable
data class ReconciliationReportResponseNetwork(
    @SerialName("store_id") val storeId: String,
    @SerialName("total_variants_checked") val totalVariantsChecked: Int,
    @SerialName("variants_reconciled") val variantsReconciled: Int,
    @SerialName("discrepancies_repaired") val discrepanciesRepaired: Int,
    @SerialName("discrepancy_details") val discrepancyDetails: List<Map<String, String>>,
    @SerialName("reconciled_at") val reconciledAt: String,
)
