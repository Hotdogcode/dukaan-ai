package ai.dukaan.core.database.di

import ai.dukaan.core.database.DukaanDatabase
import ai.dukaan.core.database.dao.AppMetadataDao
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
    ).build()

    @Provides
    @Singleton
    fun providesAppMetadataDao(
        database: DukaanDatabase,
    ): AppMetadataDao = database.appMetadataDao()
}
