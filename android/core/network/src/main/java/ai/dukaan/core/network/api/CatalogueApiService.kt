package ai.dukaan.core.network.api

import ai.dukaan.core.network.model.BarcodeLookupNetwork
import ai.dukaan.core.network.model.BrandCreateNetwork
import ai.dukaan.core.network.model.BrandNetwork
import ai.dukaan.core.network.model.CategoryCreateNetwork
import ai.dukaan.core.network.model.CategoryNetwork
import ai.dukaan.core.network.model.ProductBarcodeCreateNetwork
import ai.dukaan.core.network.model.ProductBarcodeNetwork
import ai.dukaan.core.network.model.ProductCreateNetwork
import ai.dukaan.core.network.model.ProductListNetwork
import ai.dukaan.core.network.model.ProductNetwork
import ai.dukaan.core.network.model.ProductUpdateNetwork
import ai.dukaan.core.network.model.ProductVariantCreateNetwork
import ai.dukaan.core.network.model.ProductVariantNetwork
import ai.dukaan.core.network.model.StandardUnitConversionNetwork
import ai.dukaan.core.network.model.UnitOfMeasureNetwork
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface CatalogueApiService {

    // Units and Conversions
    @GET("api/v1/catalogue/units")
    suspend fun getUnitsOfMeasure(): Response<List<UnitOfMeasureNetwork>>

    @GET("api/v1/catalogue/conversions")
    suspend fun getStandardUnitConversions(): Response<List<StandardUnitConversionNetwork>>

    // Brands
    @GET("api/v1/catalogue/brands")
    suspend fun getBrands(
        @Query("business_id") businessId: String,
        @Query("active_only") activeOnly: Boolean = true,
    ): Response<List<BrandNetwork>>

    @POST("api/v1/catalogue/brands")
    suspend fun createBrand(
        @Query("business_id") businessId: String,
        @Body payload: BrandCreateNetwork,
    ): Response<BrandNetwork>

    // Categories
    @GET("api/v1/catalogue/categories")
    suspend fun getCategories(
        @Query("business_id") businessId: String,
        @Query("active_only") activeOnly: Boolean = true,
    ): Response<List<CategoryNetwork>>

    @POST("api/v1/catalogue/categories")
    suspend fun createCategory(
        @Query("business_id") businessId: String,
        @Body payload: CategoryCreateNetwork,
    ): Response<CategoryNetwork>

    // Products
    @GET("api/v1/catalogue/products")
    suspend fun listProducts(
        @Query("business_id") businessId: String,
        @Query("query") query: String? = null,
        @Query("category_id") categoryId: String? = null,
        @Query("brand_id") brandId: String? = null,
        @Query("active_only") activeOnly: Boolean = true,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 50,
    ): Response<ProductListNetwork>

    @POST("api/v1/catalogue/products")
    suspend fun createProduct(
        @Query("business_id") businessId: String,
        @Body payload: ProductCreateNetwork,
    ): Response<ProductNetwork>

    @GET("api/v1/catalogue/products/{product_id}")
    suspend fun getProduct(
        @Path("product_id") productId: String,
        @Query("business_id") businessId: String,
    ): Response<ProductNetwork>

    @PUT("api/v1/catalogue/products/{product_id}")
    suspend fun updateProduct(
        @Path("product_id") productId: String,
        @Query("business_id") businessId: String,
        @Body payload: ProductUpdateNetwork,
    ): Response<ProductNetwork>

    @DELETE("api/v1/catalogue/products/{product_id}")
    suspend fun deleteProduct(
        @Path("product_id") productId: String,
        @Query("business_id") businessId: String,
    ): Response<ProductNetwork>

    // Variants
    @POST("api/v1/catalogue/products/{product_id}/variants")
    suspend fun createVariant(
        @Path("product_id") productId: String,
        @Query("business_id") businessId: String,
        @Body payload: ProductVariantCreateNetwork,
    ): Response<ProductVariantNetwork>

    // Barcodes
    @GET("api/v1/catalogue/barcodes/lookup")
    suspend fun lookupBarcode(
        @Query("barcode") barcode: String,
        @Query("business_id") businessId: String,
    ): Response<BarcodeLookupNetwork>

    @POST("api/v1/catalogue/barcodes")
    suspend fun registerBarcode(
        @Query("business_id") businessId: String,
        @Body payload: ProductBarcodeCreateNetwork,
    ): Response<ProductBarcodeNetwork>
}
