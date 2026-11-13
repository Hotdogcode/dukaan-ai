package ai.dukaan.core.data

import ai.dukaan.core.data.repository.InventoryRepositoryImpl
import ai.dukaan.core.database.dao.InventoryCountDao
import ai.dukaan.core.database.dao.InventoryOutboxDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.StockBalanceDao
import ai.dukaan.core.database.dao.StockMovementDao
import ai.dukaan.core.database.entity.InventoryOutboxEntity
import ai.dukaan.core.database.entity.StockBalanceEntity
import ai.dukaan.core.model.OpeningStockRequestModel
import ai.dukaan.core.model.StockAdjustmentRequestModel
import ai.dukaan.core.model.StockAdjustmentType
import ai.dukaan.core.network.api.InventoryApiService
import ai.dukaan.core.network.model.OpeningStockResponseNetwork
import ai.dukaan.core.network.model.StockAdjustmentResponseNetwork
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.slot
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.Response
import java.io.IOException
import java.math.BigDecimal
import java.math.RoundingMode
import java.util.UUID

class InventoryRepositoryTest {

    private val stockBalanceDao: StockBalanceDao = mockk(relaxed = true)
    private val stockMovementDao: StockMovementDao = mockk(relaxed = true)
    private val inventoryCountDao: InventoryCountDao = mockk(relaxed = true)
    private val inventoryOutboxDao: InventoryOutboxDao = mockk(relaxed = true)
    private val productDao: ProductDao = mockk(relaxed = true)
    private val apiService: InventoryApiService = mockk(relaxed = true)

    private val repository = InventoryRepositoryImpl(
        stockBalanceDao = stockBalanceDao,
        stockMovementDao = stockMovementDao,
        inventoryCountDao = inventoryCountDao,
        inventoryOutboxDao = inventoryOutboxDao,
        productDao = productDao,
        apiService = apiService,
    )

    @Test
    fun recordOpeningStock_success_updatesLocalBalance() = runTest {
        val businessId = UUID.randomUUID()
        val storeId = UUID.randomUUID()
        val variantId = UUID.randomUUID()

        val responseNetwork = OpeningStockResponseNetwork(
            movementId = UUID.randomUUID().toString(),
            variantId = variantId.toString(),
            storeId = storeId.toString(),
            quantity = BigDecimal("100.0000"),
            unitCost = BigDecimal("12.5000"),
            currentQuantity = BigDecimal("100.0000"),
            movingAverageCost = BigDecimal("12.5000"),
            recordedAt = "2026-11-13T10:00:00Z",
        )

        coEvery {
            apiService.recordOpeningStock(businessId.toString(), storeId.toString(), any())
        } returns Response.success(responseNetwork)

        val request = OpeningStockRequestModel(
            variantId = variantId,
            quantity = BigDecimal("100.0000"),
            unitCost = BigDecimal("12.5000"),
            notes = "Initial opening stock",
        )

        val result = repository.recordOpeningStock(businessId, storeId, request)
        assertTrue(result.isSuccess)

        val balanceSlot = slot<StockBalanceEntity>()
        coVerify { stockBalanceDao.insertBalance(capture(balanceSlot)) }
        assertEquals(variantId, balanceSlot.captured.variantId)
        assertEquals(BigDecimal("100.0000"), balanceSlot.captured.currentQuantity)
        assertEquals(BigDecimal("12.5000"), balanceSlot.captured.movingAverageCost)
    }

    @Test
    fun recordOpeningStock_networkFailure_queuesInOutbox() = runTest {
        val businessId = UUID.randomUUID()
        val storeId = UUID.randomUUID()
        val variantId = UUID.randomUUID()

        coEvery {
            apiService.recordOpeningStock(businessId.toString(), storeId.toString(), any())
        } throws IOException("Network unavailable")

        val request = OpeningStockRequestModel(
            variantId = variantId,
            quantity = BigDecimal("50.0000"),
            unitCost = BigDecimal("15.0000"),
            notes = "Offline opening stock",
        )

        val result = repository.recordOpeningStock(businessId, storeId, request)
        assertTrue(result.isSuccess) // Graceful offline queueing

        val outboxSlot = slot<InventoryOutboxEntity>()
        coVerify { inventoryOutboxDao.insert(capture(outboxSlot)) }
        assertEquals("OPENING_STOCK", outboxSlot.captured.operationType)
        assertEquals(businessId, outboxSlot.captured.businessId)
        assertEquals(storeId, outboxSlot.captured.storeId)
    }

    @Test
    fun recordAdjustment_success_updatesLocalBalance() = runTest {
        val businessId = UUID.randomUUID()
        val storeId = UUID.randomUUID()
        val variantId = UUID.randomUUID()

        val responseNetwork = StockAdjustmentResponseNetwork(
            adjustmentId = UUID.randomUUID().toString(),
            movementId = UUID.randomUUID().toString(),
            variantId = variantId.toString(),
            adjustmentType = "DAMAGE",
            quantity = BigDecimal("5.0000"),
            previousQuantity = BigDecimal("100.0000"),
            newQuantity = BigDecimal("95.0000"),
            movingAverageCost = BigDecimal("12.5000"),
            recordedAt = "2026-11-13T10:00:00Z",
        )

        coEvery {
            apiService.recordStockAdjustment(businessId.toString(), storeId.toString(), any())
        } returns Response.success(responseNetwork)

        val request = StockAdjustmentRequestModel(
            variantId = variantId,
            adjustmentType = StockAdjustmentType.DAMAGE,
            quantity = BigDecimal("5.0000"),
            unitCost = null,
            reason = "Rats damaged 5 packets",
            notes = null,
        )

        val result = repository.recordAdjustment(businessId, storeId, request)
        assertTrue(result.isSuccess)

        val balanceSlot = slot<StockBalanceEntity>()
        coVerify { stockBalanceDao.insertBalance(capture(balanceSlot)) }
        assertEquals(variantId, balanceSlot.captured.variantId)
        assertEquals(BigDecimal("95.0000"), balanceSlot.captured.currentQuantity)
    }

    @Test
    fun weightedAverageCost_arithmeticVerification() {
        // Formula: New WAC = (Existing Qty * Existing WAC + Inflow Qty * Inflow Unit Cost) / (Existing Qty + Inflow Qty)
        val existingQty = BigDecimal("10.0000")
        val existingWac = BigDecimal("100.0000") // total cost = 1000.00
        val incomingQty = BigDecimal("5.0000")
        val incomingCost = BigDecimal("130.0000") // total incoming = 650.00

        val totalValue = (existingQty * existingWac) + (incomingQty * incomingCost) // 1650.00
        val totalQty = existingQty + incomingQty // 15.0000
        val expectedWac = totalValue.divide(totalQty, 4, RoundingMode.HALF_UP) // 110.0000

        assertEquals(BigDecimal("110.0000"), expectedWac)
    }
}
