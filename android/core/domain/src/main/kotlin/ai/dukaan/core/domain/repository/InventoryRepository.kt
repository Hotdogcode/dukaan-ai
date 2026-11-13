package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.InventoryCountItem
import ai.dukaan.core.model.InventoryCountSession
import ai.dukaan.core.model.InventoryItem
import ai.dukaan.core.model.InventorySummary
import ai.dukaan.core.model.OpeningStockRequestModel
import ai.dukaan.core.model.ReconciliationReport
import ai.dukaan.core.model.StockAdjustmentRequestModel
import ai.dukaan.core.model.StockMovementRecord
import ai.dukaan.core.model.VariantStockDetails
import kotlinx.coroutines.flow.Flow
import java.math.BigDecimal
import java.util.UUID

interface InventoryRepository {
    fun getInventorySummary(
        businessId: UUID,
        storeId: UUID,
        query: String? = null,
        categoryId: UUID? = null,
        lowStockOnly: Boolean = false,
        outOfStockOnly: Boolean = false,
        page: Int = 1,
        limit: Int = 50,
    ): Flow<InventorySummary>

    fun getVariantStockDetails(
        businessId: UUID,
        storeId: UUID,
        variantId: UUID,
    ): Flow<VariantStockDetails?>

    fun getStockMovements(
        businessId: UUID,
        storeId: UUID,
        variantId: UUID,
    ): Flow<List<StockMovementRecord>>

    suspend fun recordOpeningStock(
        businessId: UUID,
        storeId: UUID,
        request: OpeningStockRequestModel,
    ): Result<Unit>

    suspend fun recordAdjustment(
        businessId: UUID,
        storeId: UUID,
        request: StockAdjustmentRequestModel,
    ): Result<Unit>

    suspend fun createCountSession(
        businessId: UUID,
        storeId: UUID,
        notes: String? = null,
    ): Result<InventoryCountSession>

    fun getCountSessions(
        businessId: UUID,
        storeId: UUID,
    ): Flow<List<InventoryCountSession>>

    suspend fun getCountSession(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
    ): Result<InventoryCountSession>

    suspend fun recordCountItem(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
        variantId: UUID,
        countedQuantity: BigDecimal,
        notes: String? = null,
    ): Result<InventoryCountItem>

    suspend fun completeCountSession(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
    ): Result<Unit>

    suspend fun reconcileInventory(
        businessId: UUID,
        storeId: UUID,
    ): Result<ReconciliationReport>

    suspend fun syncInventory(businessId: UUID, storeId: UUID): Result<Unit>
}
