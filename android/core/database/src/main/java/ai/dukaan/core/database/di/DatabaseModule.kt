package ai.dukaan.core.database.di

import ai.dukaan.core.database.DukaanDatabase
import ai.dukaan.core.database.dao.AppMetadataDao
import ai.dukaan.core.database.dao.BrandDao
import ai.dukaan.core.database.dao.CatalogueOutboxDao
import ai.dukaan.core.database.dao.CategoryDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.UnitOfMeasureDao
import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun providesDukaanDatabase(
        @ApplicationContext context: Context,
    ): DukaanDatabase = Room.databaseBuilder(
        context,
        DukaanDatabase::class.java,
        DukaanDatabase.DATABASE_NAME,
    )
        .fallbackToDestructiveMigration()
        .build()

    @Provides
    @Singleton
    fun providesAppMetadataDao(
        database: DukaanDatabase,
    ): AppMetadataDao = database.appMetadataDao()

    @Provides
    @Singleton
    fun providesProductDao(
        database: DukaanDatabase,
    ): ProductDao = database.productDao()

    @Provides
    @Singleton
    fun providesCategoryDao(
        database: DukaanDatabase,
    ): CategoryDao = database.categoryDao()

    @Provides
    @Singleton
    fun providesBrandDao(
        database: DukaanDatabase,
    ): BrandDao = database.brandDao()

    @Provides
    @Singleton
    fun providesUnitOfMeasureDao(
        database: DukaanDatabase,
    ): UnitOfMeasureDao = database.unitOfMeasureDao()

    @Provides
    @Singleton
    fun providesCatalogueOutboxDao(
        database: DukaanDatabase,
    ): CatalogueOutboxDao = database.catalogueOutboxDao()
}
