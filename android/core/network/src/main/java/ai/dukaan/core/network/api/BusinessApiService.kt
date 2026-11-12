package ai.dukaan.core.network.api

import ai.dukaan.core.network.model.BusinessCreateNetwork
import ai.dukaan.core.network.model.BusinessMembershipResponseNetwork
import ai.dukaan.core.network.model.BusinessResponseNetwork
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface BusinessApiService {
    @POST("api/v1/businesses")
    suspend fun createBusiness(@Body payload: BusinessCreateNetwork): Response<BusinessMembershipResponseNetwork>

    @GET("api/v1/businesses")
    suspend fun listMyBusinesses(): Response<List<BusinessMembershipResponseNetwork>>

    @GET("api/v1/businesses/{business_id}")
    suspend fun getBusiness(@Path("business_id") businessId: String): Response<BusinessResponseNetwork>
}
