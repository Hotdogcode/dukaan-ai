package ai.dukaan.core.network.api

import ai.dukaan.core.network.model.LogoutNetwork
import ai.dukaan.core.network.model.MessageResponseNetwork
import ai.dukaan.core.network.model.OtpRequestNetwork
import ai.dukaan.core.network.model.OtpResponseNetwork
import ai.dukaan.core.network.model.OtpVerifyNetwork
import ai.dukaan.core.network.model.RefreshTokenNetwork
import ai.dukaan.core.network.model.TokenResponseNetwork
import ai.dukaan.core.network.model.UserResponseNetwork
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApiService {
    @POST("api/v1/auth/otp/request")
    suspend fun requestOtp(@Body payload: OtpRequestNetwork): Response<OtpResponseNetwork>

    @POST("api/v1/auth/otp/verify")
    suspend fun verifyOtp(@Body payload: OtpVerifyNetwork): Response<TokenResponseNetwork>

    @POST("api/v1/auth/refresh")
    suspend fun refreshToken(@Body payload: RefreshTokenNetwork): Response<TokenResponseNetwork>

    @POST("api/v1/auth/logout")
    suspend fun logout(@Body payload: LogoutNetwork): Response<MessageResponseNetwork>

    @GET("api/v1/auth/me")
    suspend fun getMe(): Response<UserResponseNetwork>
}
