package ai.dukaan.core.database.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.Instant

@Entity(tableName = "app_metadata")
data class AppMetadataEntity(
    @PrimaryKey
    @ColumnInfo(name = "key")
    val key: String,
    @ColumnInfo(name = "value")
    val value: String,
    @ColumnInfo(name = "updated_at")
    val updatedAt: Instant = Instant.now(),
)
