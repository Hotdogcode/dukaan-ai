package ai.dukaan.core.data.di

import ai.dukaan.core.data.repository.AppConfigRepositoryImpl
import ai.dukaan.core.data.repository.AuthRepositoryImpl
import ai.dukaan.core.data.repository.BusinessRepositoryImpl
import ai.dukaan.core.data.repository.ConnectivityRepositoryImpl
import ai.dukaan.core.data.repository.StoreRepositoryImpl
import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.domain.repository.ConnectivityRepository
import ai.dukaan.core.domain.repository.StoreRepository
import ai.dukaan.core.domain.usecase.CreateBusinessUseCase
import ai.dukaan.core.domain.usecase.CreateStoreUseCase
import ai.dukaan.core.domain.usecase.GetAppConfigUseCase
import ai.dukaan.core.domain.usecase.GetMyBusinessesUseCase
import ai.dukaan.core.domain.usecase.GetStoresUseCase
import ai.dukaan.core.domain.usecase.LogoutUseCase
import ai.dukaan.core.domain.usecase.ObserveConnectivityUseCase
import ai.dukaan.core.domain.usecase.RefreshTokenUseCase
import ai.dukaan.core.domain.usecase.RequestOtpUseCase
import ai.dukaan.core.domain.usecase.SetOnboardingCompletedUseCase
import ai.dukaan.core.domain.usecase.VerifyOtpUseCase
import android.content.Context
import androidx.work.WorkManager
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class DataBindingsModule {

    @Binds
    @Singleton
    abstract fun bindAppConfigRepository(
        appConfigRepositoryImpl: AppConfigRepositoryImpl,
    ): AppConfigRepository

    @Binds
    @Singleton
    abstract fun bindConnectivityRepository(
        connectivityRepositoryImpl: ConnectivityRepositoryImpl,
    ): ConnectivityRepository

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        authRepositoryImpl: AuthRepositoryImpl,
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindBusinessRepository(
        businessRepositoryImpl: BusinessRepositoryImpl,
    ): BusinessRepository

    @Binds
    @Singleton
    abstract fun bindStoreRepository(
        storeRepositoryImpl: StoreRepositoryImpl,
    ): StoreRepository
}

@Module
@InstallIn(SingletonComponent::class)
object DataModule {

    @Provides
    @Singleton
    fun providesWorkManager(
        @ApplicationContext context: Context,
    ): WorkManager = WorkManager.getInstance(context)

    @Provides
    fun providesGetAppConfigUseCase(
        appConfigRepository: AppConfigRepository,
    ): GetAppConfigUseCase = GetAppConfigUseCase(appConfigRepository)

    @Provides
    fun providesSetOnboardingCompletedUseCase(
        appConfigRepository: AppConfigRepository,
    ): SetOnboardingCompletedUseCase = SetOnboardingCompletedUseCase(appConfigRepository)

    @Provides
    fun providesObserveConnectivityUseCase(
        connectivityRepository: ConnectivityRepository,
    ): ObserveConnectivityUseCase = ObserveConnectivityUseCase(connectivityRepository)

    @Provides
    fun providesRequestOtpUseCase(
        authRepository: AuthRepository,
    ): RequestOtpUseCase = RequestOtpUseCase(authRepository)

    @Provides
    fun providesVerifyOtpUseCase(
        authRepository: AuthRepository,
    ): VerifyOtpUseCase = VerifyOtpUseCase(authRepository)

    @Provides
    fun providesRefreshTokenUseCase(
        authRepository: AuthRepository,
    ): RefreshTokenUseCase = RefreshTokenUseCase(authRepository)

    @Provides
    fun providesLogoutUseCase(
        authRepository: AuthRepository,
    ): LogoutUseCase = LogoutUseCase(authRepository)

    @Provides
    fun providesGetMyBusinessesUseCase(
        businessRepository: BusinessRepository,
    ): GetMyBusinessesUseCase = GetMyBusinessesUseCase(businessRepository)

    @Provides
    fun providesCreateBusinessUseCase(
        businessRepository: BusinessRepository,
    ): CreateBusinessUseCase = CreateBusinessUseCase(businessRepository)

    @Provides
    fun providesGetStoresUseCase(
        storeRepository: StoreRepository,
    ): GetStoresUseCase = GetStoresUseCase(storeRepository)

    @Provides
    fun providesCreateStoreUseCase(
        storeRepository: StoreRepository,
    ): CreateStoreUseCase = CreateStoreUseCase(storeRepository)
}
