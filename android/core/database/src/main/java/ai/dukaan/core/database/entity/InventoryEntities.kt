package ai.dukaan.core.database.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID

@Entity(
    tableName = "stock_balances",
    indices = [
        Index(value = ["business_id", "store_id", "variant_id"], unique = true),
        Index(value = ["store_id"]),
        Index(value = ["variant_id"])
    ]
)
data class StockBalanceEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "store_id")
    val storeId: UUID,
    @ColumnInfo(name = "product_id")
    val productId: UUID,
    @ColumnInfo(name = "variant_id")
    val variantId: UUID,
    @ColumnInfo(name = "current_quantity")
    val currentQuantity: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "moving_average_cost")
    val movingAverageCost: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "min_stock_level")
    val minStockLevel: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "reorder_quantity")
    val reorderQuantity: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "last_movement_id")
    val lastMovementId: UUID? = null,
    val version: Int = 1,
    @ColumnInfo(name = "updated_at")
    val updatedAt: Instant = Instant.now(),
)

@Entity(
    tableName = "stock_movements",
    indices = [
        Index(value = ["business_id", "store_id", "variant_id", "occurred_at"]),
        Index(value = ["store_id"]),
        Index(value = ["variant_id"])
    ]
)
data class StockMovementEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "store_id")
    val storeId: UUID,
    @ColumnInfo(name = "product_id")
    val productId: UUID,
    @ColumnInfo(name = "variant_id")
    val variantId: UUID,
    @ColumnInfo(name = "movement_type")
    val movementType: String,
    @ColumnInfo(name = "quantity_delta")
    val quantityDelta: BigDecimal,
    @ColumnInfo(name = "base_quantity_delta")
    val baseQuantityDelta: BigDecimal? = null,
    @ColumnInfo(name = "unit_cost_at_movement")
    val unitCostAtMovement: BigDecimal? = null,
    @ColumnInfo(name = "balance_after_movement")
    val balanceAfterMovement: BigDecimal,
    @ColumnInfo(name = "reference_type")
    val referenceType: String,
    @ColumnInfo(name = "reference_id")
    val referenceId: UUID,
    val reason: String? = null,
    val notes: String? = null,
    @ColumnInfo(name = "created_by_user_id")
    val createdByUserId: UUID? = null,
    @ColumnInfo(name = "occurred_at")
    val occurredAt: Instant = Instant.now(),
    @ColumnInfo(name = "created_at")
    val createdAt: Instant = Instant.now(),
)

@Entity(
    tableName = "inventory_count_sessions",
    indices = [
        Index(value = ["business_id", "store_id"]),
        Index(value = ["store_id"])
    ]
)
data class InventoryCountSessionEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "store_id")
    val storeId: UUID,
    @ColumnInfo(name = "conducted_by_user_id")
    val conductedByUserId: UUID,
    val status: String = "OPEN",
    val notes: String? = null,
    @ColumnInfo(name = "started_at")
    val startedAt: Instant = Instant.now(),
    @ColumnInfo(name = "completed_at")
    val completedAt: Instant? = null,
)

@Entity(
    tableName = "inventory_count_items",
    indices = [
        Index(value = ["session_id", "variant_id"], unique = true),
        Index(value = ["session_id"])
    ]
)
data class InventoryCountItemEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "store_id")
    val storeId: UUID,
    @ColumnInfo(name = "session_id")
    val sessionId: UUID,
    @ColumnInfo(name = "product_id")
    val productId: UUID,
    @ColumnInfo(name = "variant_id")
    val variantId: UUID,
    @ColumnInfo(name = "expected_quantity")
    val expectedQuantity: BigDecimal,
    @ColumnInfo(name = "counted_quantity")
    val countedQuantity: BigDecimal,
    @ColumnInfo(name = "variance_quantity")
    val varianceQuantity: BigDecimal,
    val notes: String? = null,
)

@Entity(
    tableName = "inventory_outbox",
    indices = [
        Index(value = ["business_id", "store_id"]),
        Index(value = ["synced_at"])
    ]
)
data class InventoryOutboxEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "store_id")
    val storeId: UUID,
    @ColumnInfo(name = "operation_type")
    val operationType: String, // OPENING_STOCK, ADJUSTMENT, COUNT_ITEM, COUNT_COMPLETE, RECONCILIATION
    @ColumnInfo(name = "payload_json")
    val payloadJson: String,
    @ColumnInfo(name = "created_at")
    val createdAt: Instant = Instant.now(),
    @ColumnInfo(name = "synced_at")
    val syncedAt: Instant? = null,
    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0,
    @ColumnInfo(name = "error_message")
    val errorMessage: String? = null,
)
