package ai.dukaan.core.database

import ai.dukaan.core.database.converter.BigDecimalConverter
import ai.dukaan.core.database.converter.InstantConverter
import ai.dukaan.core.database.converter.UuidConverter
import ai.dukaan.core.database.dao.AppMetadataDao
import ai.dukaan.core.database.entity.AppMetadataEntity
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters

@Database(
    entities = [
        AppMetadataEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
@TypeConverters(
    BigDecimalConverter::class,
    InstantConverter::class,
    UuidConverter::class,
)
abstract class DukaanDatabase : RoomDatabase() {
    abstract fun appMetadataDao(): AppMetadataDao

    companion object {
        const val DATABASE_NAME = "dukaanai.db"
    }
}
