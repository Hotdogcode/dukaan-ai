package ai.dukaan.feature.catalogue

import ai.dukaan.core.model.Brand
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.UnitOfMeasure
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.InputChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun AddEditProductScreen(
    viewModel: AddEditProductViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onNavigateToScanBarcode: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val categories by viewModel.categories.collectAsStateWithLifecycle()
    val brands by viewModel.brands.collectAsStateWithLifecycle()
    val uoms by viewModel.unitsOfMeasure.collectAsStateWithLifecycle()

    val snackbarHostState = remember { SnackbarHostState() }
    var barcodeInput by remember { mutableStateOf("") }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) {
            onNavigateBack()
        }
    }

    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.clearError()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (uiState.isEditMode) "Edit Product" else "Add New Product",
                        fontWeight = FontWeight.Bold,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                        )
                    }
                },
                actions = {
                    if (uiState.isSaving) {
                        CircularProgressIndicator(
                            modifier = Modifier
                                .size(24.dp)
                                .padding(end = 12.dp)
                        )
                    } else {
                        Button(
                            onClick = { viewModel.saveProduct() },
                            modifier = Modifier.padding(end = 8.dp),
                            shape = RoundedCornerShape(8.dp),
                        ) {
                            Text("Save")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        modifier = modifier,
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // Section 1: Basic Information
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Text(
                            text = "Basic Information",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                        )

                        OutlinedTextField(
                            value = uiState.name,
                            onValueChange = { viewModel.onNameChanged(it) },
                            label = { Text("Product Name *") },
                            placeholder = { Text("e.g. Parle-G Biscuits") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                        )

                        OutlinedTextField(
                            value = uiState.sku,
                            onValueChange = { viewModel.onSkuChanged(it) },
                            label = { Text("SKU / Item Code *") },
                            placeholder = { Text("e.g. PARLE-G-100G") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                        )

                        OutlinedTextField(
                            value = uiState.description,
                            onValueChange = { viewModel.onDescriptionChanged(it) },
                            label = { Text("Description (Optional)") },
                            modifier = Modifier.fillMaxWidth(),
                            maxLines = 3,
                        )
                    }
                }

                // Section 2: Classification (Category, Brand, Base UOM)
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Text(
                            text = "Category & Unit",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                        )

                        // Category Dropdown
                        CategoryDropdownSelector(
                            categories = categories,
                            selectedId = uiState.selectedCategoryId,
                            onSelected = { viewModel.onCategorySelected(it) },
                        )

                        // Brand Dropdown
                        BrandDropdownSelector(
                            brands = brands,
                            selectedId = uiState.selectedBrandId,
                            onSelected = { viewModel.onBrandSelected(it) },
                        )

                        // Base UOM Dropdown
                        UomDropdownSelector(
                            uoms = uoms,
                            selectedId = uiState.selectedUomId,
                            onSelected = { viewModel.onUomSelected(it) },
                        )
                    }
                }

                // Section 3: Pricing (MRP, Selling Price, Cost Price, Tax)
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Text(
                            text = "Pricing & Taxes",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            OutlinedTextField(
                                value = uiState.sellingPrice,
                                onValueChange = { viewModel.onSellingPriceChanged(it) },
                                label = { Text("Selling Price (₹) *") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                            )

                            OutlinedTextField(
                                value = uiState.mrp,
                                onValueChange = { viewModel.onMrpChanged(it) },
                                label = { Text("MRP (₹) *") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                            )
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            OutlinedTextField(
                                value = uiState.costPrice,
                                onValueChange = { viewModel.onCostPriceChanged(it) },
                                label = { Text("Purchase Cost (₹)") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                            )

                            OutlinedTextField(
                                value = uiState.taxRatePercent,
                                onValueChange = { viewModel.onTaxRateChanged(it) },
                                label = { Text("GST Tax %") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                            )
                        }
                    }
                }

                // Section 4: Barcodes
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                text = "Barcodes",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                            )

                            OutlinedButton(
                                onClick = onNavigateToScanBarcode,
                                shape = RoundedCornerShape(8.dp),
                            ) {
                                Icon(
                                    imageVector = Icons.Default.QrCodeScanner,
                                    contentDescription = null,
                                    modifier = Modifier.size(16.dp),
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Scan")
                            }
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            OutlinedTextField(
                                value = barcodeInput,
                                onValueChange = { barcodeInput = it },
                                placeholder = { Text("Enter barcode number") },
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                            )
                            Button(
                                onClick = {
                                    if (barcodeInput.isNotBlank()) {
                                        viewModel.addBarcode(barcodeInput)
                                        barcodeInput = ""
                                    }
                                },
                                shape = RoundedCornerShape(8.dp),
                            ) {
                                Text("Add")
                            }
                        }

                        if (uiState.barcodes.isNotEmpty()) {
                            FlowRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                uiState.barcodes.forEach { code ->
                                    InputChip(
                                        selected = true,
                                        onClick = { viewModel.removeBarcode(code) },
                                        label = { Text(code) },
                                        trailingIcon = {
                                            Icon(
                                                imageVector = Icons.Default.Close,
                                                contentDescription = "Remove",
                                                modifier = Modifier.size(16.dp),
                                            )
                                        },
                                    )
                                }
                            }
                        }
                    }
                }

                // Section 5: Variants Configuration
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Column {
                                Text(
                                    text = "Product Variants",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                )
                                Text(
                                    text = "Multiple sizes, weights, or packs",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                            Switch(
                                checked = uiState.hasVariants,
                                onCheckedChange = { viewModel.onToggleHasVariants(it) },
                            )
                        }

                        AnimatedVisibility(visible = uiState.hasVariants) {
                            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                uiState.variants.forEachIndexed { index, variant ->
                                    VariantItemEditor(
                                        variant = variant,
                                        onUpdate = { updated -> viewModel.updateVariant(index, updated) },
                                        onRemove = { viewModel.removeVariant(index) },
                                    )
                                }

                                OutlinedButton(
                                    onClick = { viewModel.addVariant() },
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(8.dp),
                                ) {
                                    Icon(imageVector = Icons.Default.Add, contentDescription = null)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Add Variant")
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
private fun VariantItemEditor(
    variant: VariantFormState,
    onUpdate: (VariantFormState) -> Unit,
    onRemove: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = variant.name.ifBlank { "New Variant" },
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                )
                IconButton(onClick = onRemove, modifier = Modifier.size(24.dp)) {
                    Icon(
                        imageVector = Icons.Default.Delete,
                        contentDescription = "Remove Variant",
                        tint = MaterialTheme.colorScheme.error,
                        modifier = Modifier.size(18.dp),
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedTextField(
                    value = variant.name,
                    onValueChange = { onUpdate(variant.copy(name = it)) },
                    label = { Text("Name (e.g. 200g)") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = variant.sku,
                    onValueChange = { onUpdate(variant.copy(sku = it)) },
                    label = { Text("SKU") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedTextField(
                    value = variant.sellingPrice,
                    onValueChange = { onUpdate(variant.copy(sellingPrice = it)) },
                    label = { Text("Price (₹)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = variant.mrp,
                    onValueChange = { onUpdate(variant.copy(mrp = it)) },
                    label = { Text("MRP (₹)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
            }

            OutlinedTextField(
                value = variant.barcode,
                onValueChange = { onUpdate(variant.copy(barcode = it)) },
                label = { Text("Barcode (Optional)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CategoryDropdownSelector(
    categories: List<Category>,
    selectedId: java.util.UUID?,
    onSelected: (java.util.UUID?) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedCategory = categories.find { it.id == selectedId }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
        modifier = Modifier.fillMaxWidth(),
    ) {
        OutlinedTextField(
            value = selectedCategory?.name ?: "None (Uncategorized)",
            onValueChange = {},
            readOnly = true,
            label = { Text("Category") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            DropdownMenuItem(
                text = { Text("None (Uncategorized)") },
                onClick = {
                    onSelected(null)
                    expanded = false
                },
            )
            categories.forEach { cat ->
                DropdownMenuItem(
                    text = { Text(cat.name) },
                    onClick = {
                        onSelected(cat.id)
                        expanded = false
                    },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BrandDropdownSelector(
    brands: List<Brand>,
    selectedId: java.util.UUID?,
    onSelected: (java.util.UUID?) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedBrand = brands.find { it.id == selectedId }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
        modifier = Modifier.fillMaxWidth(),
    ) {
        OutlinedTextField(
            value = selectedBrand?.name ?: "None (Generic / Unbranded)",
            onValueChange = {},
            readOnly = true,
            label = { Text("Brand") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            DropdownMenuItem(
                text = { Text("None (Generic / Unbranded)") },
                onClick = {
                    onSelected(null)
                    expanded = false
                },
            )
            brands.forEach { b ->
                DropdownMenuItem(
                    text = { Text(b.name) },
                    onClick = {
                        onSelected(b.id)
                        expanded = false
                    },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun UomDropdownSelector(
    uoms: List<UnitOfMeasure>,
    selectedId: java.util.UUID?,
    onSelected: (java.util.UUID?) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedUom = uoms.find { it.id == selectedId }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
        modifier = Modifier.fillMaxWidth(),
    ) {
        OutlinedTextField(
            value = selectedUom?.let { "${it.code} (${it.name})" } ?: "Select Base Unit *",
            onValueChange = {},
            readOnly = true,
            label = { Text("Base Unit *") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            uoms.forEach { u ->
                DropdownMenuItem(
                    text = { Text("${u.code} - ${u.name}") },
                    onClick = {
                        onSelected(u.id)
                        expanded = false
                    },
                )
            }
        }
    }
}
