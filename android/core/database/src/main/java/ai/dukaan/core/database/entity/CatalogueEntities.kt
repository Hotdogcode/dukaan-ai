package ai.dukaan.core.database.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID

@Entity(
    tableName = "units_of_measure",
    indices = [
        Index(value = ["code"], unique = true)
    ]
)
data class UnitOfMeasureEntity(
    @PrimaryKey
    val id: UUID,
    val code: String,
    val name: String,
    val category: String,
    @ColumnInfo(name = "is_fractional_allowed")
    val isFractionalAllowed: Boolean,
)

@Entity(
    tableName = "categories",
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["parent_id"]),
        Index(value = ["business_id", "name"], unique = true)
    ]
)
data class CategoryEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    val name: String,
    @ColumnInfo(name = "parent_id")
    val parentId: UUID? = null,
    @ColumnInfo(name = "display_order")
    val displayOrder: Int = 0,
    @ColumnInfo(name = "is_system")
    val isSystem: Boolean = false,
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,
)

@Entity(
    tableName = "brands",
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["business_id", "name"], unique = true)
    ]
)
data class BrandEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    val name: String,
    val description: String? = null,
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,
)

@Entity(
    tableName = "products",
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["category_id"]),
        Index(value = ["brand_id"]),
        Index(value = ["business_id", "sku"], unique = true),
        Index(value = ["name"])
    ]
)
data class ProductEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    val name: String,
    @ColumnInfo(name = "brand_id")
    val brandId: UUID? = null,
    @ColumnInfo(name = "category_id")
    val categoryId: UUID? = null,
    val description: String? = null,
    @ColumnInfo(name = "image_url")
    val imageUrl: String? = null,
    @ColumnInfo(name = "base_uom_id")
    val baseUomId: UUID,
    val sku: String? = null,
    @ColumnInfo(name = "purchase_price")
    val purchasePrice: BigDecimal? = null,
    @ColumnInfo(name = "selling_price")
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal? = null,
    @ColumnInfo(name = "tax_rate_percent")
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "has_variants")
    val hasVariants: Boolean = false,
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,
    @ColumnInfo(name = "created_at")
    val createdAt: Instant = Instant.now(),
    @ColumnInfo(name = "updated_at")
    val updatedAt: Instant = Instant.now(),
    @ColumnInfo(name = "sync_status")
    val syncStatus: String = "SYNCED", // SYNCED, PENDING_SYNC, FAILED
)

@Entity(
    tableName = "product_variants",
    foreignKeys = [
        ForeignKey(
            entity = ProductEntity::class,
            parentColumns = ["id"],
            childColumns = ["product_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["product_id"]),
        Index(value = ["business_id", "sku"], unique = true)
    ]
)
data class ProductVariantEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "product_id")
    val productId: UUID,
    @ColumnInfo(name = "variant_name")
    val variantName: String,
    val sku: String? = null,
    @ColumnInfo(name = "base_uom_id")
    val baseUomId: UUID,
    @ColumnInfo(name = "purchase_price")
    val purchasePrice: BigDecimal? = null,
    @ColumnInfo(name = "selling_price")
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal? = null,
    @ColumnInfo(name = "tax_rate_percent")
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,
    @ColumnInfo(name = "sync_status")
    val syncStatus: String = "SYNCED",
)

@Entity(
    tableName = "product_barcodes",
    foreignKeys = [
        ForeignKey(
            entity = ProductEntity::class,
            parentColumns = ["id"],
            childColumns = ["product_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["product_id"]),
        Index(value = ["variant_id"]),
        Index(value = ["business_id", "barcode"], unique = true)
    ]
)
data class ProductBarcodeEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "product_id")
    val productId: UUID,
    @ColumnInfo(name = "variant_id")
    val variantId: UUID? = null,
    val barcode: String,
    @ColumnInfo(name = "barcode_type")
    val barcodeType: String = "EAN_13",
    @ColumnInfo(name = "is_primary")
    val isPrimary: Boolean = true,
)

@Entity(
    tableName = "catalogue_outbox",
    indices = [
        Index(value = ["business_id"]),
        Index(value = ["synced_at"])
    ]
)
data class CatalogueOutboxEntity(
    @PrimaryKey
    val id: UUID,
    @ColumnInfo(name = "business_id")
    val businessId: UUID,
    @ColumnInfo(name = "entity_type")
    val entityType: String, // PRODUCT, VARIANT, CATEGORY, BRAND, BARCODE
    @ColumnInfo(name = "entity_id")
    val entityId: UUID,
    val operation: String, // INSERT, UPDATE, DELETE
    @ColumnInfo(name = "payload_json")
    val payloadJson: String,
    @ColumnInfo(name = "created_at")
    val createdAt: Instant = Instant.now(),
    @ColumnInfo(name = "synced_at")
    val syncedAt: Instant? = null,
    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0,
    @ColumnInfo(name = "error_message")
    val errorMessage: String? = null,
)
