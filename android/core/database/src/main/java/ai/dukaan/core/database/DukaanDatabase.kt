package ai.dukaan.core.database

import ai.dukaan.core.database.converter.BigDecimalConverter
import ai.dukaan.core.database.converter.InstantConverter
import ai.dukaan.core.database.converter.UuidConverter
import ai.dukaan.core.database.dao.AppMetadataDao
import ai.dukaan.core.database.dao.BrandDao
import ai.dukaan.core.database.dao.CatalogueOutboxDao
import ai.dukaan.core.database.dao.CategoryDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.UnitOfMeasureDao
import ai.dukaan.core.database.entity.AppMetadataEntity
import ai.dukaan.core.database.entity.BrandEntity
import ai.dukaan.core.database.entity.CatalogueOutboxEntity
import ai.dukaan.core.database.entity.CategoryEntity
import ai.dukaan.core.database.entity.ProductBarcodeEntity
import ai.dukaan.core.database.entity.ProductEntity
import ai.dukaan.core.database.entity.ProductVariantEntity
import ai.dukaan.core.database.entity.UnitOfMeasureEntity
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters

@Database(
    entities = [
        AppMetadataEntity::class,
        UnitOfMeasureEntity::class,
        CategoryEntity::class,
        BrandEntity::class,
        ProductEntity::class,
        ProductVariantEntity::class,
        ProductBarcodeEntity::class,
        CatalogueOutboxEntity::class,
    ],
    version = 2,
    exportSchema = false,
)
@TypeConverters(
    BigDecimalConverter::class,
    InstantConverter::class,
    UuidConverter::class,
)
abstract class DukaanDatabase : RoomDatabase() {
    abstract fun appMetadataDao(): AppMetadataDao
    abstract fun productDao(): ProductDao
    abstract fun categoryDao(): CategoryDao
    abstract fun brandDao(): BrandDao
    abstract fun unitOfMeasureDao(): UnitOfMeasureDao
    abstract fun catalogueOutboxDao(): CatalogueOutboxDao

    companion object {
        const val DATABASE_NAME = "dukaanai.db"
    }
}
