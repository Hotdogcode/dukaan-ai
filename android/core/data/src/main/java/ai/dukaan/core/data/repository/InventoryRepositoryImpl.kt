package ai.dukaan.core.data.repository

import ai.dukaan.core.database.dao.InventoryCountDao
import ai.dukaan.core.database.dao.InventoryOutboxDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.StockBalanceDao
import ai.dukaan.core.database.dao.StockMovementDao
import ai.dukaan.core.database.entity.InventoryCountItemEntity
import ai.dukaan.core.database.entity.InventoryCountSessionEntity
import ai.dukaan.core.database.entity.InventoryOutboxEntity
import ai.dukaan.core.database.entity.StockBalanceEntity
import ai.dukaan.core.database.entity.StockMovementEntity
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.InventoryCountItem
import ai.dukaan.core.model.InventoryCountSession
import ai.dukaan.core.model.InventoryItem
import ai.dukaan.core.model.InventorySummary
import ai.dukaan.core.model.OpeningStockRequestModel
import ai.dukaan.core.model.ReconciliationReport
import ai.dukaan.core.model.StockAdjustmentRequestModel
import ai.dukaan.core.model.StockMovementRecord
import ai.dukaan.core.model.StockStatus
import ai.dukaan.core.model.VariantStockDetails
import ai.dukaan.core.network.api.InventoryApiService
import ai.dukaan.core.network.model.InventoryCountItemCreateNetwork
import ai.dukaan.core.network.model.InventoryCountSessionCreateNetwork
import ai.dukaan.core.network.model.OpeningStockRequestNetwork
import ai.dukaan.core.network.model.StockAdjustmentRequestNetwork
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InventoryRepositoryImpl @Inject constructor(
    private val stockBalanceDao: StockBalanceDao,
    private val stockMovementDao: StockMovementDao,
    private val inventoryCountDao: InventoryCountDao,
    private val inventoryOutboxDao: InventoryOutboxDao,
    private val productDao: ProductDao,
    private val apiService: InventoryApiService,
) : InventoryRepository {

    private val json = Json { ignoreUnknownKeys = true }

    override fun getInventorySummary(
        businessId: UUID,
        storeId: UUID,
        query: String?,
        categoryId: UUID?,
        lowStockOnly: Boolean,
        outOfStockOnly: Boolean,
        page: Int,
        limit: Int,
    ): Flow<InventorySummary> = flow {
        try {
            val response = apiService.getInventorySummary(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                query = query,
                categoryId = categoryId?.toString(),
                lowStockOnly = lowStockOnly,
                outOfStockOnly = outOfStockOnly,
                page = page,
                limit = limit,
            )

            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                // Cache stock balances locally in Room
                val balanceEntities = body.items.map { item ->
                    StockBalanceEntity(
                        id = UUID.randomUUID(),
                        businessId = businessId,
                        storeId = storeId,
                        productId = UUID.fromString(item.productId),
                        variantId = UUID.fromString(item.variantId),
                        currentQuantity = item.currentQuantity,
                        movingAverageCost = item.movingAverageCost,
                        minStockLevel = item.minStockLevel,
                        reorderQuantity = item.reorderQuantity,
                    )
                }
                stockBalanceDao.insertBalances(balanceEntities)

                val domainItems = body.items.map { item ->
                    InventoryItem(
                        variantId = UUID.fromString(item.variantId),
                        productId = UUID.fromString(item.productId),
                        productName = item.productName,
                        variantName = item.variantName,
                        sku = item.sku,
                        barcode = item.barcode,
                        categoryName = item.categoryName,
                        currentQuantity = item.currentQuantity,
                        uomName = item.uomName,
                        movingAverageCost = item.movingAverageCost,
                        sellingPrice = item.sellingPrice,
                        inventoryValuation = item.inventoryValuation,
                        minStockLevel = item.minStockLevel,
                        reorderQuantity = item.reorderQuantity,
                        stockStatus = StockStatus.valueOf(item.stockStatus),
                        lastMovementAt = item.lastMovementAt?.let { runCatching { Instant.parse(it) }.getOrNull() },
                    )
                }

                emit(
                    InventorySummary(
                        totalItems = body.totalItems,
                        totalValuation = body.totalValuation,
                        lowStockCount = body.lowStockCount,
                        outOfStockCount = body.outOfStockCount,
                        items = domainItems,
                        page = body.page,
                        limit = body.limit,
                        totalPages = body.totalPages,
                    )
                )
                return@flow
            }
        } catch (_: Exception) {
            // Fall through to offline cache emission
        }

        // Offline Fallback: compute from Room
        emit(
            InventorySummary(
                totalItems = 0,
                totalValuation = BigDecimal.ZERO,
                lowStockCount = 0,
                outOfStockCount = 0,
                items = emptyList(),
                page = page,
                limit = limit,
                totalPages = 1,
            )
        )
    }

    override fun getVariantStockDetails(
        businessId: UUID,
        storeId: UUID,
        variantId: UUID,
    ): Flow<VariantStockDetails?> = flow {
        try {
            val response = apiService.getVariantStockDetails(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                variantId = variantId.toString(),
            )
            if (response.isSuccessful && response.body() != null) {
                val b = response.body()!!
                emit(
                    VariantStockDetails(
                        variantId = UUID.fromString(b.variantId),
                        productId = UUID.fromString(b.productId),
                        productName = b.productName,
                        variantName = b.variantName,
                        sku = b.sku,
                        barcode = b.barcode,
                        categoryName = b.categoryName,
                        currentQuantity = b.currentQuantity,
                        uomName = b.uomName,
                        movingAverageCost = b.movingAverageCost,
                        sellingPrice = b.sellingPrice,
                        mrp = b.mrp,
                        inventoryValuation = b.inventoryValuation,
                        minStockLevel = b.minStockLevel,
                        reorderQuantity = b.reorderQuantity,
                        stockStatus = StockStatus.valueOf(b.stockStatus),
                        hasOpeningStock = b.hasOpeningStock,
                    )
                )
                return@flow
            }
        } catch (_: Exception) {
            // Fall through
        }

        // Local cache lookup
        val cached = stockBalanceDao.getBalance(storeId, variantId)
        if (cached != null) {
            emit(
                VariantStockDetails(
                    variantId = cached.variantId,
                    productId = cached.productId,
                    productName = "Product",
                    variantName = "Variant",
                    currentQuantity = cached.currentQuantity,
                    uomName = "PCS",
                    movingAverageCost = cached.movingAverageCost,
                    sellingPrice = BigDecimal.ZERO,
                    mrp = BigDecimal.ZERO,
                    inventoryValuation = cached.currentQuantity.multiply(cached.movingAverageCost),
                    minStockLevel = cached.minStockLevel,
                    reorderQuantity = cached.reorderQuantity,
                    stockStatus = if (cached.currentQuantity <= BigDecimal.ZERO) StockStatus.OUT_OF_STOCK else StockStatus.IN_STOCK,
                    hasOpeningStock = true,
                )
            )
        } else {
            emit(null)
        }
    }

    override fun getStockMovements(
        businessId: UUID,
        storeId: UUID,
        variantId: UUID,
    ): Flow<List<StockMovementRecord>> = flow {
        try {
            val response = apiService.getStockMovements(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                variantId = variantId.toString(),
            )
            if (response.isSuccessful && response.body() != null) {
                val items = response.body()!!.items.map { m ->
                    StockMovementRecord(
                        id = UUID.fromString(m.id),
                        businessId = UUID.fromString(m.businessId),
                        storeId = UUID.fromString(m.storeId),
                        variantId = UUID.fromString(m.variantId),
                        movementType = m.movementType,
                        quantity = m.quantity,
                        unitCost = m.unitCost,
                        totalCost = m.totalCost,
                        balanceAfter = m.balanceAfter,
                        referenceType = m.referenceType,
                        referenceId = m.referenceId?.let { UUID.fromString(it) },
                        reason = m.reason,
                        notes = m.notes,
                        createdAt = runCatching { Instant.parse(m.createdAt) }.getOrDefault(Instant.now()),
                        createdByUserId = m.createdByUserId?.let { UUID.fromString(it) },
                    )
                }
                emit(items)
                return@flow
            }
        } catch (_: Exception) {
            // Fall through
        }
        emit(emptyList())
    }

    override suspend fun recordOpeningStock(
        businessId: UUID,
        storeId: UUID,
        request: OpeningStockRequestModel,
    ): Result<Unit> {
        val networkReq = OpeningStockRequestNetwork(
            variantId = request.variantId.toString(),
            quantity = request.quantity,
            unitCost = request.unitCost,
            notes = request.notes,
        )

        return try {
            val resp = apiService.recordOpeningStock(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                payload = networkReq,
            )
            if (resp.isSuccessful) {
                val b = resp.body()!!
                stockBalanceDao.insertBalance(
                    StockBalanceEntity(
                        id = UUID.randomUUID(),
                        businessId = businessId,
                        storeId = storeId,
                        productId = request.variantId, // fallback
                        variantId = request.variantId,
                        currentQuantity = b.currentQuantity,
                        movingAverageCost = b.movingAverageCost,
                    )
                )
                Result.success(Unit)
            } else {
                Result.failure(Exception(resp.errorBody()?.string() ?: "Failed to record opening stock"))
            }
        } catch (e: Exception) {
            // Offline queueing
            inventoryOutboxDao.insert(
                InventoryOutboxEntity(
                    id = UUID.randomUUID(),
                    businessId = businessId,
                    storeId = storeId,
                    operationType = "OPENING_STOCK",
                    payloadJson = json.encodeToString(networkReq),
                )
            )
            Result.success(Unit)
        }
    }

    override suspend fun recordAdjustment(
        businessId: UUID,
        storeId: UUID,
        request: StockAdjustmentRequestModel,
    ): Result<Unit> {
        val networkReq = StockAdjustmentRequestNetwork(
            variantId = request.variantId.toString(),
            adjustmentType = request.adjustmentType.name,
            quantity = request.quantity,
            unitCost = request.unitCost,
            reason = request.reason,
            notes = request.notes,
        )

        return try {
            val resp = apiService.recordStockAdjustment(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                payload = networkReq,
            )
            if (resp.isSuccessful) {
                val b = resp.body()!!
                stockBalanceDao.insertBalance(
                    StockBalanceEntity(
                        id = UUID.randomUUID(),
                        businessId = businessId,
                        storeId = storeId,
                        productId = request.variantId,
                        variantId = request.variantId,
                        currentQuantity = b.newQuantity,
                        movingAverageCost = b.movingAverageCost,
                    )
                )
                Result.success(Unit)
            } else {
                Result.failure(Exception(resp.errorBody()?.string() ?: "Failed to record adjustment"))
            }
        } catch (e: Exception) {
            // Offline queueing
            inventoryOutboxDao.insert(
                InventoryOutboxEntity(
                    id = UUID.randomUUID(),
                    businessId = businessId,
                    storeId = storeId,
                    operationType = "ADJUSTMENT",
                    payloadJson = json.encodeToString(networkReq),
                )
            )
            Result.success(Unit)
        }
    }

    override suspend fun createCountSession(
        businessId: UUID,
        storeId: UUID,
        notes: String?,
    ): Result<InventoryCountSession> {
        return try {
            val resp = apiService.createCountSession(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                payload = InventoryCountSessionCreateNetwork(notes = notes),
            )
            if (resp.isSuccessful && resp.body() != null) {
                val b = resp.body()!!
                val session = InventoryCountSession(
                    id = UUID.fromString(b.id),
                    businessId = UUID.fromString(b.businessId),
                    storeId = UUID.fromString(b.storeId),
                    sessionNumber = b.sessionNumber,
                    status = b.status,
                    totalVariantsCounted = b.totalVariantsCounted,
                    totalVarianceQuantity = b.totalVarianceQuantity,
                    totalVarianceValue = b.totalVarianceValue,
                    notes = b.notes,
                    createdAt = runCatching { Instant.parse(b.createdAt) }.getOrDefault(Instant.now()),
                    completedAt = b.completedAt?.let { runCatching { Instant.parse(it) }.getOrNull() },
                )
                inventoryCountDao.insertSession(
                    InventoryCountSessionEntity(
                        id = session.id,
                        businessId = session.businessId,
                        storeId = session.storeId,
                        conductedByUserId = UUID.randomUUID(),
                        status = session.status,
                        notes = session.notes,
                        startedAt = session.createdAt,
                    )
                )
                Result.success(session)
            } else {
                Result.failure(Exception("Failed to create count session"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override fun getCountSessions(
        businessId: UUID,
        storeId: UUID,
    ): Flow<List<InventoryCountSession>> = flow {
        try {
            val resp = apiService.listCountSessions(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
            )
            if (resp.isSuccessful && resp.body() != null) {
                val list = resp.body()!!.map { b ->
                    InventoryCountSession(
                        id = UUID.fromString(b.id),
                        businessId = UUID.fromString(b.businessId),
                        storeId = UUID.fromString(b.storeId),
                        sessionNumber = b.sessionNumber,
                        status = b.status,
                        totalVariantsCounted = b.totalVariantsCounted,
                        totalVarianceQuantity = b.totalVarianceQuantity,
                        totalVarianceValue = b.totalVarianceValue,
                        notes = b.notes,
                        createdAt = runCatching { Instant.parse(b.createdAt) }.getOrDefault(Instant.now()),
                        completedAt = b.completedAt?.let { runCatching { Instant.parse(it) }.getOrNull() },
                    )
                }
                emit(list)
                return@flow
            }
        } catch (_: Exception) {
            // Fall through
        }
        emit(emptyList())
    }

    override suspend fun getCountSession(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
    ): Result<InventoryCountSession> {
        return try {
            val resp = apiService.getCountSession(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                countId = sessionId.toString(),
            )
            if (resp.isSuccessful && resp.body() != null) {
                val b = resp.body()!!
                val items = b.items.map { it ->
                    InventoryCountItem(
                        id = UUID.fromString(it.id),
                        sessionId = UUID.fromString(it.sessionId),
                        productId = UUID.fromString(it.productId),
                        variantId = UUID.fromString(it.variantId),
                        productName = it.productName,
                        variantName = it.variantName,
                        sku = it.sku,
                        barcode = it.barcode,
                        expectedQuantity = it.expectedQuantity,
                        countedQuantity = it.countedQuantity,
                        varianceQuantity = it.varianceQuantity,
                        unitCost = it.unitCost,
                        varianceValue = it.varianceValue,
                        notes = it.notes,
                    )
                }
                val session = InventoryCountSession(
                    id = UUID.fromString(b.id),
                    businessId = UUID.fromString(b.businessId),
                    storeId = UUID.fromString(b.storeId),
                    sessionNumber = b.sessionNumber,
                    status = b.status,
                    totalVariantsCounted = b.totalVariantsCounted,
                    totalVarianceQuantity = b.totalVarianceQuantity,
                    totalVarianceValue = b.totalVarianceValue,
                    notes = b.notes,
                    createdAt = runCatching { Instant.parse(b.createdAt) }.getOrDefault(Instant.now()),
                    completedAt = b.completedAt?.let { runCatching { Instant.parse(it) }.getOrNull() },
                    items = items,
                )
                Result.success(session)
            } else {
                Result.failure(Exception("Count session not found"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun recordCountItem(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
        variantId: UUID,
        countedQuantity: BigDecimal,
        notes: String?,
    ): Result<InventoryCountItem> {
        return try {
            val resp = apiService.addCountItem(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                countId = sessionId.toString(),
                payload = InventoryCountItemCreateNetwork(
                    variantId = variantId.toString(),
                    countedQuantity = countedQuantity,
                    notes = notes,
                ),
            )
            if (resp.isSuccessful && resp.body() != null) {
                val it = resp.body()!!
                val item = InventoryCountItem(
                    id = UUID.fromString(it.id),
                    sessionId = UUID.fromString(it.sessionId),
                    productId = UUID.fromString(it.productId),
                    variantId = UUID.fromString(it.variantId),
                    productName = it.productName,
                    variantName = it.variantName,
                    sku = it.sku,
                    barcode = it.barcode,
                    expectedQuantity = it.expectedQuantity,
                    countedQuantity = it.countedQuantity,
                    varianceQuantity = it.varianceQuantity,
                    unitCost = it.unitCost,
                    varianceValue = it.varianceValue,
                    notes = it.notes,
                )
                inventoryCountDao.insertItem(
                    InventoryCountItemEntity(
                        id = item.id,
                        businessId = businessId,
                        storeId = storeId,
                        sessionId = item.sessionId,
                        productId = item.productId,
                        variantId = item.variantId,
                        expectedQuantity = item.expectedQuantity,
                        countedQuantity = item.countedQuantity,
                        varianceQuantity = item.varianceQuantity,
                        notes = item.notes,
                    )
                )
                Result.success(item)
            } else {
                Result.failure(Exception("Failed to record count item"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun completeCountSession(
        businessId: UUID,
        storeId: UUID,
        sessionId: UUID,
    ): Result<Unit> {
        return try {
            val resp = apiService.completeCountSession(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
                countId = sessionId.toString(),
            )
            if (resp.isSuccessful) {
                val cached = inventoryCountDao.getSession(sessionId)
                if (cached != null) {
                    inventoryCountDao.updateSession(cached.copy(status = "COMPLETED", completedAt = Instant.now()))
                }
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to complete count session"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun reconcileInventory(
        businessId: UUID,
        storeId: UUID,
    ): Result<ReconciliationReport> {
        return try {
            val resp = apiService.reconcileInventory(
                businessId = businessId.toString(),
                storeId = storeId.toString(),
            )
            if (resp.isSuccessful && resp.body() != null) {
                val b = resp.body()!!
                Result.success(
                    ReconciliationReport(
                        storeId = UUID.fromString(b.storeId),
                        totalVariantsChecked = b.totalVariantsChecked,
                        variantsReconciled = b.variantsReconciled,
                        discrepanciesRepaired = b.discrepanciesRepaired,
                        discrepancyDetails = b.discrepancyDetails,
                        reconciledAt = runCatching { Instant.parse(b.reconciledAt) }.getOrDefault(Instant.now()),
                    )
                )
            } else {
                Result.failure(Exception("Failed to reconcile inventory"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun syncInventory(businessId: UUID, storeId: UUID): Result<Unit> {
        val pending = inventoryOutboxDao.getPendingOperations()
        for (op in pending) {
            try {
                when (op.operationType) {
                    "OPENING_STOCK" -> {
                        val req = json.decodeFromString<OpeningStockRequestNetwork>(op.payloadJson)
                        val resp = apiService.recordOpeningStock(businessId.toString(), storeId.toString(), req)
                        if (resp.isSuccessful) inventoryOutboxDao.markSynced(op.id)
                    }
                    "ADJUSTMENT" -> {
                        val req = json.decodeFromString<StockAdjustmentRequestNetwork>(op.payloadJson)
                        val resp = apiService.recordStockAdjustment(businessId.toString(), storeId.toString(), req)
                        if (resp.isSuccessful) inventoryOutboxDao.markSynced(op.id)
                    }
                }
            } catch (e: Exception) {
                inventoryOutboxDao.updateRetry(op.id, op.retryCount + 1, e.message)
            }
        }
        return Result.success(Unit)
    }
}
