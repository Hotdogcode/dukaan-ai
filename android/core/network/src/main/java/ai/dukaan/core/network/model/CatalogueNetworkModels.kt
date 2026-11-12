package ai.dukaan.core.network.model

import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive
import java.math.BigDecimal

object BigDecimalSerializer : KSerializer<BigDecimal> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("BigDecimal", PrimitiveKind.STRING)

    override fun deserialize(decoder: Decoder): BigDecimal {
        return if (decoder is JsonDecoder) {
            val element = decoder.decodeJsonElement()
            BigDecimal(element.jsonPrimitive.content)
        } else {
            BigDecimal(decoder.decodeString())
        }
    }

    override fun serialize(encoder: Encoder, value: BigDecimal) {
        if (encoder is JsonEncoder) {
            encoder.encodeJsonElement(JsonPrimitive(value.toPlainString()))
        } else {
            encoder.encodeString(value.toPlainString())
        }
    }
}

@Serializable
data class UnitOfMeasureNetwork(
    @SerialName("id") val id: String,
    @SerialName("code") val code: String,
    @SerialName("name") val name: String,
    @SerialName("category") val category: String,
    @SerialName("is_fractional_allowed") val isFractionalAllowed: Boolean,
)

@Serializable
data class StandardUnitConversionNetwork(
    @SerialName("id") val id: String,
    @SerialName("from_uom_id") val fromUomId: String,
    @SerialName("to_uom_id") val toUomId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("multiplier") val multiplier: BigDecimal,
    @SerialName("dimension") val dimension: String,
    @SerialName("from_uom_code") val fromUomCode: String? = null,
    @SerialName("to_uom_code") val toUomCode: String? = null,
)

@Serializable
data class BrandCreateNetwork(
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
)

@Serializable
data class BrandNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class CategoryCreateNetwork(
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
    @SerialName("parent_id") val parentId: String? = null,
)

@Serializable
data class CategoryNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
    @SerialName("parent_id") val parentId: String? = null,
    @SerialName("is_system") val isSystem: Boolean = false,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class ProductBarcodeNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("product_id") val productId: String,
    @SerialName("variant_id") val variantId: String? = null,
    @SerialName("barcode") val barcode: String,
    @SerialName("barcode_type") val barcodeType: String = "EAN_13",
    @SerialName("is_primary") val isPrimary: Boolean = true,
)

@Serializable
data class ProductBarcodeCreateNetwork(
    @SerialName("barcode") val barcode: String,
    @SerialName("barcode_type") val barcodeType: String = "EAN_13",
    @SerialName("is_primary") val isPrimary: Boolean = true,
    @SerialName("product_id") val productId: String? = null,
    @SerialName("variant_id") val variantId: String? = null,
)

@Serializable
data class ProductVariantCreateNetwork(
    @SerialName("variant_name") val variantName: String,
    @SerialName("sku") val sku: String,
    @SerialName("base_uom_id") val baseUomId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("cost_price") val costPrice: BigDecimal = BigDecimal.ZERO,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("tax_rate_percent") val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @SerialName("is_tax_inclusive") val isTaxInclusive: Boolean = true,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("barcodes") val barcodes: List<String> = emptyList(),
)

@Serializable
data class ProductVariantNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("product_id") val productId: String,
    @SerialName("variant_name") val variantName: String,
    @SerialName("sku") val sku: String,
    @SerialName("base_uom_id") val baseUomId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("cost_price") val costPrice: BigDecimal = BigDecimal.ZERO,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("tax_rate_percent") val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @SerialName("is_tax_inclusive") val isTaxInclusive: Boolean = true,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("barcodes") val barcodes: List<ProductBarcodeNetwork> = emptyList(),
    @SerialName("base_uom") val baseUom: UnitOfMeasureNetwork? = null,
)

@Serializable
data class ProductCreateNetwork(
    @SerialName("name") val name: String,
    @SerialName("sku") val sku: String,
    @SerialName("category_id") val categoryId: String? = null,
    @SerialName("brand_id") val brandId: String? = null,
    @SerialName("description") val description: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("hsn_code") val hsn_code: String? = null,
    @SerialName("base_uom_id") val baseUomId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("cost_price") val costPrice: BigDecimal = BigDecimal.ZERO,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("tax_rate_percent") val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @SerialName("is_tax_inclusive") val isTaxInclusive: Boolean = true,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("reorder_threshold") val reorderThreshold: BigDecimal = BigDecimal.ZERO,
    @SerialName("is_loose_item") val isLooseItem: Boolean = false,
    @SerialName("barcodes") val barcodes: List<String> = emptyList(),
    @SerialName("variants") val variants: List<ProductVariantCreateNetwork> = emptyList(),
)

@Serializable
data class ProductUpdateNetwork(
    @SerialName("name") val name: String? = null,
    @SerialName("sku") val sku: String? = null,
    @SerialName("category_id") val categoryId: String? = null,
    @SerialName("brand_id") val brandId: String? = null,
    @SerialName("description") val description: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("hsn_code") val hsnCode: String? = null,
    @SerialName("base_uom_id") val baseUomId: String? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("cost_price") val costPrice: BigDecimal? = null,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("tax_rate_percent") val taxRatePercent: BigDecimal? = null,
    @SerialName("is_tax_inclusive") val isTaxInclusive: Boolean? = null,
    @SerialName("is_loose_item") val isLooseItem: Boolean? = null,
    @SerialName("is_active") val isActive: Boolean? = null,
)

@Serializable
data class ProductNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("category_id") val categoryId: String? = null,
    @SerialName("brand_id") val brandId: String? = null,
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("sku") val sku: String,
    @SerialName("hsn_code") val hsnCode: String? = null,
    @SerialName("base_uom_id") val baseUomId: String,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("selling_price") val sellingPrice: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("mrp") val mrp: BigDecimal,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("cost_price") val costPrice: BigDecimal = BigDecimal.ZERO,
    @Serializable(with = BigDecimalSerializer::class)
    @SerialName("tax_rate_percent") val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @SerialName("is_tax_inclusive") val isTaxInclusive: Boolean = true,
    @SerialName("has_variants") val hasVariants: Boolean = false,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
    @SerialName("category") val category: CategoryNetwork? = null,
    @SerialName("brand") val brand: BrandNetwork? = null,
    @SerialName("base_uom") val baseUom: UnitOfMeasureNetwork? = null,
    @SerialName("barcodes") val barcodes: List<ProductBarcodeNetwork> = emptyList(),
    @SerialName("variants") val variants: List<ProductVariantNetwork> = emptyList(),
)

@Serializable
data class ProductListNetwork(
    @SerialName("items") val items: List<ProductNetwork>,
    @SerialName("total") val total: Int,
    @SerialName("page") val page: Int,
    @SerialName("page_size") val pageSize: Int,
    @SerialName("pages") val pages: Int,
)

@Serializable
data class BarcodeLookupNetwork(
    @SerialName("barcode") val barcode: String,
    @SerialName("barcode_type") val barcodeType: String,
    @SerialName("product") val product: ProductNetwork,
    @SerialName("variant") val variant: ProductVariantNetwork? = null,
)
