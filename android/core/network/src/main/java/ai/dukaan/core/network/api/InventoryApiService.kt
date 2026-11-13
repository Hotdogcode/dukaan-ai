package ai.dukaan.core.network.api

import ai.dukaan.core.network.model.CompleteCountSessionResponseNetwork
import ai.dukaan.core.network.model.InventoryCountItemCreateNetwork
import ai.dukaan.core.network.model.InventoryCountItemResponseNetwork
import ai.dukaan.core.network.model.InventoryCountSessionCreateNetwork
import ai.dukaan.core.network.model.InventoryCountSessionResponseNetwork
import ai.dukaan.core.network.model.InventorySummaryResponseNetwork
import ai.dukaan.core.network.model.OpeningStockRequestNetwork
import ai.dukaan.core.network.model.OpeningStockResponseNetwork
import ai.dukaan.core.network.model.PaginatedStockMovementsResponseNetwork
import ai.dukaan.core.network.model.ReconciliationReportResponseNetwork
import ai.dukaan.core.network.model.StockAdjustmentRequestNetwork
import ai.dukaan.core.network.model.StockAdjustmentResponseNetwork
import ai.dukaan.core.network.model.StockDetailsResponseNetwork
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface InventoryApiService {

    @GET("api/v1/businesses/{business_id}/stores/{store_id}/inventory")
    suspend fun getInventorySummary(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Query("query") query: String? = null,
        @Query("category_id") categoryId: String? = null,
        @Query("low_stock_only") lowStockOnly: Boolean = false,
        @Query("out_of_stock_only") outOfStockOnly: Boolean = false,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 50,
    ): Response<InventorySummaryResponseNetwork>

    @GET("api/v1/businesses/{business_id}/stores/{store_id}/inventory/{variant_id}")
    suspend fun getVariantStockDetails(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Path("variant_id") variantId: String,
    ): Response<StockDetailsResponseNetwork>

    @GET("api/v1/businesses/{business_id}/stores/{store_id}/inventory/{variant_id}/movements")
    suspend fun getStockMovements(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Path("variant_id") variantId: String,
        @Query("movement_type") movementType: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 50,
    ): Response<PaginatedStockMovementsResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/opening-stock")
    suspend fun recordOpeningStock(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Body payload: OpeningStockRequestNetwork,
    ): Response<OpeningStockResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/adjustments")
    suspend fun recordStockAdjustment(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Body payload: StockAdjustmentRequestNetwork,
    ): Response<StockAdjustmentResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/counts")
    suspend fun createCountSession(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Body payload: InventoryCountSessionCreateNetwork,
    ): Response<InventoryCountSessionResponseNetwork>

    @GET("api/v1/businesses/{business_id}/stores/{store_id}/inventory/counts")
    suspend fun listCountSessions(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
    ): Response<List<InventoryCountSessionResponseNetwork>>

    @GET("api/v1/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}")
    suspend fun getCountSession(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Path("count_id") countId: String,
    ): Response<InventoryCountSessionResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}/items")
    suspend fun addCountItem(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Path("count_id") countId: String,
        @Body payload: InventoryCountItemCreateNetwork,
    ): Response<InventoryCountItemResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}/complete")
    suspend fun completeCountSession(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
        @Path("count_id") countId: String,
    ): Response<CompleteCountSessionResponseNetwork>

    @POST("api/v1/businesses/{business_id}/stores/{store_id}/inventory/reconciliation")
    suspend fun reconcileInventory(
        @Path("business_id") businessId: String,
        @Path("store_id") storeId: String,
    ): Response<ReconciliationReportResponseNetwork>
}
