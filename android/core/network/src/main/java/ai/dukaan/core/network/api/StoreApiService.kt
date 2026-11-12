package ai.dukaan.core.network.api

import ai.dukaan.core.network.model.StoreCreateNetwork
import ai.dukaan.core.network.model.StoreResponseNetwork
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface StoreApiService {
    @POST("api/v1/businesses/{business_id}/stores")
    suspend fun createStore(
        @Path("business_id") businessId: String,
        @Body payload: StoreCreateNetwork,
    ): Response<StoreResponseNetwork>

    @GET("api/v1/businesses/{business_id}/stores")
    suspend fun listStores(@Path("business_id") businessId: String): Response<List<StoreResponseNetwork>>

    @GET("api/v1/businesses/{business_id}/stores/{store_id}")
    suspend fun getStore(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
    ): Response<StoreResponseNetwork>
}
