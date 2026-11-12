package ai.dukaan.feature.catalogue

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.domain.repository.ProductDraft
import ai.dukaan.core.domain.repository.ProductUpdateDraft
import ai.dukaan.core.domain.repository.VariantDraft
import ai.dukaan.core.model.Brand
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.UnitOfMeasure
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.math.BigDecimal
import java.util.UUID
import javax.inject.Inject

data class VariantFormState(
    val id: String = UUID.randomUUID().toString(),
    val name: String = "",
    val sku: String = "",
    val costPrice: String = "0",
    val sellingPrice: String = "",
    val mrp: String = "",
    val barcode: String = "",
)

data class AddEditProductUiState(
    val productId: String? = null,
    val isEditMode: Boolean = false,
    val name: String = "",
    val sku: String = "",
    val description: String = "",
    val selectedCategoryId: UUID? = null,
    val selectedBrandId: UUID? = null,
    val selectedUomId: UUID? = null,
    val costPrice: String = "0",
    val sellingPrice: String = "",
    val mrp: String = "",
    val taxRatePercent: String = "0",
    val isTaxInclusive: Boolean = true,
    val hasVariants: Boolean = false,
    val barcodes: List<String> = emptyList(),
    val variants: List<VariantFormState> = emptyList(),
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val saveSuccess: Boolean = false,
    val errorMessage: String? = null,
)

@HiltViewModel
class AddEditProductViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val appConfigRepository: AppConfigRepository,
    private val catalogueRepository: CatalogueRepository,
) : ViewModel() {

    private val productId: String? = savedStateHandle["productId"]
    private val prefilledBarcode: String? = savedStateHandle["prefilledBarcode"]

    private val _uiState = MutableStateFlow(
        AddEditProductUiState(
            productId = productId,
            isEditMode = productId != null,
            barcodes = if (!prefilledBarcode.isNullOrBlank()) listOf(prefilledBarcode) else emptyList(),
        )
    )
    val uiState: StateFlow<AddEditProductUiState> = _uiState.asStateFlow()

    val businessId: StateFlow<UUID?> = appConfigRepository.appConfig
        .map { it.selectedBusinessId }
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val categories: StateFlow<List<Category>> = businessId
        .flatMapLatest { bId ->
            if (bId == null) flowOf(emptyList())
            else catalogueRepository.getCategories(bId, activeOnly = true)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val brands: StateFlow<List<Brand>> = businessId
        .flatMapLatest { bId ->
            if (bId == null) flowOf(emptyList())
            else catalogueRepository.getBrands(bId)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val unitsOfMeasure: StateFlow<List<UnitOfMeasure>> = catalogueRepository.getUnitsOfMeasure()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    init {
        if (productId != null) {
            loadExistingProduct(UUID.fromString(productId))
        } else {
            // Default UOM to PCS if available
            viewModelScope.launch {
                val uoms = unitsOfMeasure.filterNotNull().first { it.isNotEmpty() }
                val defaultUom = uoms.find { it.code == "PCS" } ?: uoms.firstOrNull()
                defaultUom?.let { u ->
                    _uiState.update { it.copy(selectedUomId = u.id) }
                }
            }
        }
    }

    private fun loadExistingProduct(pId: UUID) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val product = catalogueRepository.getProductById(pId).first()
            if (product != null) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        name = product.name,
                        sku = product.sku ?: "",
                        description = product.description ?: "",
                        selectedCategoryId = product.categoryId,
                        selectedBrandId = product.brandId,
                        selectedUomId = product.baseUomId,
                        costPrice = product.purchasePrice?.toPlainString() ?: "0",
                        sellingPrice = product.sellingPrice.toPlainString(),
                        mrp = product.mrp?.toPlainString() ?: "",
                        taxRatePercent = product.taxRatePercent.toPlainString(),
                        hasVariants = product.hasVariants,
                        barcodes = product.barcodes.map { b -> b.barcode },
                        variants = product.variants.map { v ->
                            VariantFormState(
                                id = v.id.toString(),
                                name = v.variantName,
                                sku = v.sku ?: "",
                                costPrice = v.purchasePrice?.toPlainString() ?: "0",
                                sellingPrice = v.sellingPrice.toPlainString(),
                                mrp = v.mrp?.toPlainString() ?: "",
                                barcode = v.barcodes.firstOrNull()?.barcode ?: "",
                            )
                        },
                    )
                }
            } else {
                _uiState.update { it.copy(isLoading = false, errorMessage = "Product not found") }
            }
        }
    }

    fun onNameChanged(name: String) = _uiState.update { it.copy(name = name) }
    fun onSkuChanged(sku: String) = _uiState.update { it.copy(sku = sku) }
    fun onDescriptionChanged(desc: String) = _uiState.update { it.copy(description = desc) }
    fun onCategorySelected(id: UUID?) = _uiState.update { it.copy(selectedCategoryId = id) }
    fun onBrandSelected(id: UUID?) = _uiState.update { it.copy(selectedBrandId = id) }
    fun onUomSelected(id: UUID?) = _uiState.update { it.copy(selectedUomId = id) }
    fun onCostPriceChanged(price: String) = _uiState.update { it.copy(costPrice = price) }
    fun onSellingPriceChanged(price: String) = _uiState.update { it.copy(sellingPrice = price) }
    fun onMrpChanged(mrp: String) = _uiState.update { it.copy(mrp = mrp) }
    fun onTaxRateChanged(rate: String) = _uiState.update { it.copy(taxRatePercent = rate) }
    fun onToggleHasVariants(enabled: Boolean) = _uiState.update { it.copy(hasVariants = enabled) }

    fun addBarcode(barcode: String) {
        val clean = barcode.trim()
        if (clean.isNotBlank() && !_uiState.value.barcodes.contains(clean)) {
            _uiState.update { it.copy(barcodes = it.barcodes + clean) }
        }
    }

    fun removeBarcode(barcode: String) {
        _uiState.update { it.copy(barcodes = it.barcodes - barcode) }
    }

    fun addVariant() {
        val count = _uiState.value.variants.size + 1
        val newVariant = VariantFormState(
            name = "Variant $count",
            sku = "${_uiState.value.sku}-V$count",
            sellingPrice = _uiState.value.sellingPrice,
            mrp = _uiState.value.mrp,
        )
        _uiState.update { it.copy(variants = it.variants + newVariant) }
    }

    fun updateVariant(index: Int, updated: VariantFormState) {
        _uiState.update { state ->
            val list = state.variants.toMutableList()
            if (index in list.indices) {
                list[index] = updated
            }
            state.copy(variants = list)
        }
    }

    fun removeVariant(index: Int) {
        _uiState.update { state ->
            val list = state.variants.toMutableList()
            if (index in list.indices) {
                list.removeAt(index)
            }
            state.copy(variants = list)
        }
    }

    fun saveProduct() {
        val state = _uiState.value
        val bId = businessId.value ?: run {
            _uiState.update { it.copy(errorMessage = "Business context missing") }
            return
        }

        if (state.name.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Product name cannot be empty") }
            return
        }
        if (state.sku.isBlank()) {
            _uiState.update { it.copy(errorMessage = "SKU cannot be empty") }
            return
        }
        val uomId = state.selectedUomId ?: run {
            _uiState.update { it.copy(errorMessage = "Please select a Base Unit of Measure") }
            return
        }

        val sp = state.sellingPrice.toBigDecimalOrNull() ?: run {
            _uiState.update { it.copy(errorMessage = "Valid selling price is required") }
            return
        }
        val mrp = state.mrp.toBigDecimalOrNull() ?: sp

        if (sp > mrp) {
            _uiState.update { it.copy(errorMessage = "Selling price (₹$sp) cannot exceed MRP (₹$mrp)") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, errorMessage = null) }

            if (state.isEditMode && state.productId != null) {
                val updateDraft = ProductUpdateDraft(
                    name = state.name.trim(),
                    sku = state.sku.trim(),
                    categoryId = state.selectedCategoryId,
                    brandId = state.selectedBrandId,
                    description = state.description.ifBlank { null },
                    baseUomId = uomId,
                    sellingPrice = sp,
                    mrp = mrp,
                    costPrice = state.costPrice.toBigDecimalOrNull() ?: BigDecimal.ZERO,
                    taxRatePercent = state.taxRatePercent.toBigDecimalOrNull() ?: BigDecimal.ZERO,
                )
                val result = catalogueRepository.updateProduct(bId, UUID.fromString(state.productId), updateDraft)
                if (result.isSuccess) {
                    _uiState.update { it.copy(isSaving = false, saveSuccess = true) }
                } else {
                    _uiState.update {
                        it.copy(isSaving = false, errorMessage = result.exceptionOrNull()?.message ?: "Update failed")
                    }
                }
            } else {
                val variantsDraft = if (state.hasVariants) {
                    state.variants.map { v ->
                        val vSp = v.sellingPrice.toBigDecimalOrNull() ?: sp
                        val vMrp = v.mrp.toBigDecimalOrNull() ?: vSp
                        if (vSp > vMrp) {
                            _uiState.update {
                                it.copy(isSaving = false, errorMessage = "Variant ${v.name}: Selling price cannot exceed MRP")
                            }
                            return@launch
                        }
                        VariantDraft(
                            variantName = v.name.ifBlank { "Default" },
                            sku = v.sku.ifBlank { "${state.sku}-${UUID.randomUUID().toString().take(4)}" },
                            baseUomId = uomId,
                            costPrice = v.costPrice.toBigDecimalOrNull() ?: BigDecimal.ZERO,
                            sellingPrice = vSp,
                            mrp = vMrp,
                            barcodes = if (v.barcode.isNotBlank()) listOf(v.barcode.trim()) else emptyList(),
                        )
                    }
                } else emptyList()

                val draft = ProductDraft(
                    name = state.name.trim(),
                    sku = state.sku.trim(),
                    categoryId = state.selectedCategoryId,
                    brandId = state.selectedBrandId,
                    description = state.description.ifBlank { null },
                    baseUomId = uomId,
                    sellingPrice = sp,
                    mrp = mrp,
                    costPrice = state.costPrice.toBigDecimalOrNull() ?: BigDecimal.ZERO,
                    taxRatePercent = state.taxRatePercent.toBigDecimalOrNull() ?: BigDecimal.ZERO,
                    barcodes = state.barcodes,
                    variants = variantsDraft,
                )

                val result = catalogueRepository.createProduct(bId, draft)
                if (result.isSuccess) {
                    _uiState.update { it.copy(isSaving = false, saveSuccess = true) }
                } else {
                    _uiState.update {
                        it.copy(isSaving = false, errorMessage = result.exceptionOrNull()?.message ?: "Creation failed")
                    }
                }
            }
        }
    }

    fun clearError() = _uiState.update { it.copy(errorMessage = null) }
}
