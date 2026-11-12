package ai.dukaan.core.model

import java.math.BigDecimal
import java.time.Instant
import java.util.UUID

/**
 * Standard Unit of Measure (e.g. PCS, KG, GM, L, ML, PKT, BOX, BTL, DOZ).
 */
data class UnitOfMeasure(
    val id: UUID,
    val code: String,
    val name: String,
    val category: String, // MASS, VOLUME, COUNT, LENGTH
    val isFractionalAllowed: Boolean,
)

/**
 * Standard mathematical unit conversion rule across identical dimensions (e.g. 1 KG = 1000 GM).
 */
data class StandardUnitConversion(
    val id: UUID,
    val fromUomId: UUID,
    val fromUomCode: String,
    val toUomId: UUID,
    val toUomCode: String,
    val conversionFactor: BigDecimal,
)

/**
 * Hierarchical product category (e.g. Grocery -> Staples -> Atta).
 */
data class Category(
    val id: UUID,
    val businessId: UUID,
    val name: String,
    val parentId: UUID? = null,
    val parentName: String? = null,
    val displayOrder: Int = 0,
    val isSystem: Boolean = false,
    val isActive: Boolean = true,
)

/**
 * Brand classification (e.g. Parle, Amul, Tata).
 */
data class Brand(
    val id: UUID,
    val businessId: UUID,
    val name: String,
    val description: String? = null,
    val isActive: Boolean = true,
)

/**
 * Physical or global barcode (e.g. EAN-13, UPC-A, Code-128, Custom QR).
 */
data class ProductBarcode(
    val id: UUID,
    val businessId: UUID,
    val productId: UUID,
    val variantId: UUID? = null,
    val barcode: String,
    val barcodeType: String = "EAN_13",
    val isPrimary: Boolean = true,
)

/**
 * Sellable variation of a multi-variant product (e.g. Parle-G 100g vs 200g).
 */
data class ProductVariant(
    val id: UUID,
    val businessId: UUID,
    val productId: UUID,
    val variantName: String,
    val sku: String? = null,
    val baseUomId: UUID,
    val baseUomCode: String? = null,
    val purchasePrice: BigDecimal? = null,
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal? = null,
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    val isActive: Boolean = true,
    val barcodes: List<ProductBarcode> = emptyList(),
)

/**
 * Core product aggregate representing a catalogued item.
 */
data class Product(
    val id: UUID,
    val businessId: UUID,
    val name: String,
    val brandId: UUID? = null,
    val brandName: String? = null,
    val categoryId: UUID? = null,
    val categoryName: String? = null,
    val description: String? = null,
    val imageUrl: String? = null,
    val baseUomId: UUID,
    val baseUomCode: String? = null,
    val sku: String? = null,
    val purchasePrice: BigDecimal? = null,
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal? = null,
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    val hasVariants: Boolean = false,
    val isActive: Boolean = true,
    val variants: List<ProductVariant> = emptyList(),
    val barcodes: List<ProductBarcode> = emptyList(),
    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now(),
)

/**
 * Fast barcode lookup scan result matching either a product or a specific variant.
 */
data class BarcodeLookupResult(
    val barcode: String,
    val barcodeType: String,
    val product: Product,
    val variant: ProductVariant? = null,
)
