package ai.dukaan.core.database.dao

import ai.dukaan.core.database.entity.AppMetadataEntity
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface AppMetadataDao {
    @Query("SELECT * FROM app_metadata WHERE `key` = :key")
    suspend fun getByKey(key: String): AppMetadataEntity?

    @Query("SELECT * FROM app_metadata WHERE `key` = :key")
    fun observeByKey(key: String): Flow<AppMetadataEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(metadata: AppMetadataEntity)

    @Query("DELETE FROM app_metadata WHERE `key` = :key")
    suspend fun deleteByKey(key: String)
}
