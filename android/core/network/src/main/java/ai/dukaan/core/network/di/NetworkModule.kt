package ai.dukaan.core.network.di

import ai.dukaan.core.network.api.AuthApiService
import ai.dukaan.core.network.api.BusinessApiService
import ai.dukaan.core.network.api.StoreApiService
import ai.dukaan.core.network.authenticator.TokenAuthenticator
import ai.dukaan.core.network.connectivity.ConnectivityObserver
import ai.dukaan.core.network.connectivity.NetworkConnectivityObserver
import ai.dukaan.core.network.interceptor.AuthInterceptor
import ai.dukaan.core.network.interceptor.AuthTokenProvider
import ai.dukaan.core.network.interceptor.DefaultAuthTokenProvider
import ai.dukaan.core.network.interceptor.RequestIdInterceptor
import ai.dukaan.core.network.interceptor.SafeLoggingInterceptor
import ai.dukaan.core.network.token.AndroidKeystoreTokenStorage
import ai.dukaan.core.network.token.SecureTokenStorage
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class NetworkBindingModule {

    @Binds
    @Singleton
    abstract fun bindConnectivityObserver(
        networkConnectivityObserver: NetworkConnectivityObserver,
    ): ConnectivityObserver

    @Binds
    @Singleton
    abstract fun bindSecureTokenStorage(
        storage: AndroidKeystoreTokenStorage,
    ): SecureTokenStorage

    @Binds
    @Singleton
    abstract fun bindAuthTokenProvider(
        provider: DefaultAuthTokenProvider,
    ): AuthTokenProvider
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private const val DEFAULT_BASE_URL = "https://dukaanai-backend-yx5b.onrender.com/"

    @Provides
    @Singleton
    fun providesNetworkJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    @Provides
    @Singleton
    fun providesOkHttpClient(
        requestIdInterceptor: RequestIdInterceptor,
        authInterceptor: AuthInterceptor,
        safeLoggingInterceptor: SafeLoggingInterceptor,
        tokenAuthenticator: TokenAuthenticator,
    ): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(requestIdInterceptor)
        .addInterceptor(authInterceptor)
        .addInterceptor(safeLoggingInterceptor)
        .authenticator(tokenAuthenticator)
        .build()

    @Provides
    @Singleton
    fun providesRetrofit(
        okHttpClient: OkHttpClient,
        networkJson: Json,
    ): Retrofit {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(DEFAULT_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(networkJson.asConverterFactory(contentType))
            .build()
    }

    @Provides
    @Singleton
    fun providesAuthApiService(retrofit: Retrofit): AuthApiService =
        retrofit.create(AuthApiService::class.java)

    @Provides
    @Singleton
    fun providesBusinessApiService(retrofit: Retrofit): BusinessApiService =
        retrofit.create(BusinessApiService::class.java)

    @Provides
    @Singleton
    fun providesStoreApiService(retrofit: Retrofit): StoreApiService =
        retrofit.create(StoreApiService::class.java)

    @Provides
    @Singleton
    fun providesCatalogueApiService(retrofit: Retrofit): ai.dukaan.core.network.api.CatalogueApiService =
        retrofit.create(ai.dukaan.core.network.api.CatalogueApiService::class.java)
}
