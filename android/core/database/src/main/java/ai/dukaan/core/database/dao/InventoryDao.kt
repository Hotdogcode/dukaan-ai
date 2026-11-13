package ai.dukaan.core.database.dao

import ai.dukaan.core.database.entity.InventoryCountItemEntity
import ai.dukaan.core.database.entity.InventoryCountSessionEntity
import ai.dukaan.core.database.entity.InventoryOutboxEntity
import ai.dukaan.core.database.entity.StockBalanceEntity
import ai.dukaan.core.database.entity.StockMovementEntity
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import java.time.Instant
import java.util.UUID

@Dao
interface StockBalanceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBalance(balance: StockBalanceEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBalances(balances: List<StockBalanceEntity>)

    @Query("SELECT * FROM stock_balances WHERE store_id = :storeId AND variant_id = :variantId LIMIT 1")
    suspend fun getBalance(storeId: UUID, variantId: UUID): StockBalanceEntity?

    @Query("SELECT * FROM stock_balances WHERE store_id = :storeId")
    fun getBalancesForStore(storeId: UUID): Flow<List<StockBalanceEntity>>

    @Query("DELETE FROM stock_balances WHERE store_id = :storeId")
    suspend fun clearBalancesForStore(storeId: UUID)
}

@Dao
interface StockMovementDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMovement(movement: StockMovementEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMovements(movements: List<StockMovementEntity>)

    @Query("SELECT * FROM stock_movements WHERE store_id = :storeId AND variant_id = :variantId ORDER BY occurred_at DESC")
    fun getMovementsForVariant(storeId: UUID, variantId: UUID): Flow<List<StockMovementEntity>>

    @Query("SELECT * FROM stock_movements WHERE store_id = :storeId ORDER BY occurred_at DESC")
    fun getMovementsForStore(storeId: UUID): Flow<List<StockMovementEntity>>
}

@Dao
interface InventoryCountDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: InventoryCountSessionEntity)

    @Update
    suspend fun updateSession(session: InventoryCountSessionEntity)

    @Query("SELECT * FROM inventory_count_sessions WHERE id = :sessionId LIMIT 1")
    suspend fun getSession(sessionId: UUID): InventoryCountSessionEntity?

    @Query("SELECT * FROM inventory_count_sessions WHERE store_id = :storeId ORDER BY started_at DESC")
    fun getSessionsForStore(storeId: UUID): Flow<List<InventoryCountSessionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItems(items: List<InventoryCountItemEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItem(item: InventoryCountItemEntity)

    @Query("SELECT * FROM inventory_count_items WHERE session_id = :sessionId")
    suspend fun getItemsForSession(sessionId: UUID): List<InventoryCountItemEntity>
}

@Dao
interface InventoryOutboxDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(operation: InventoryOutboxEntity)

    @Query("SELECT * FROM inventory_outbox WHERE synced_at IS NULL ORDER BY created_at ASC")
    suspend fun getPendingOperations(): List<InventoryOutboxEntity>

    @Query("UPDATE inventory_outbox SET synced_at = :syncedAt WHERE id = :id")
    suspend fun markSynced(id: UUID, syncedAt: Instant = Instant.now())

    @Query("UPDATE inventory_outbox SET retry_count = :retryCount, error_message = :errorMessage WHERE id = :id")
    suspend fun updateRetry(id: UUID, retryCount: Int, errorMessage: String?)

    @Query("DELETE FROM inventory_outbox WHERE synced_at IS NOT NULL")
    suspend fun pruneSynced()
}
