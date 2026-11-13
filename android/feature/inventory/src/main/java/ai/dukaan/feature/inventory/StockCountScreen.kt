package ai.dukaan.feature.inventory

import ai.dukaan.core.model.InventoryCountItem
import ai.dukaan.core.model.InventoryCountSession
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Assessment
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.math.BigDecimal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StockCountScreen(
    onNavigateBack: () -> Unit,
    viewModel: StockCountViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val sessions by viewModel.countSessions.collectAsStateWithLifecycle()
    val variants by viewModel.variants.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    var showConfirmDialog by remember { mutableStateOf(false) }
    var variantDropdownExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearMessages()
        }
    }

    LaunchedEffect(uiState.successMessage) {
        uiState.successMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearMessages()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (uiState.activeSession != null) uiState.activeSession!!.sessionNumber else "Stock Count Audits") },
                navigationIcon = {
                    IconButton(onClick = {
                        if (uiState.activeSession != null) viewModel.closeActiveSession() else onNavigateBack()
                    }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { innerPadding ->
        if (uiState.activeSession == null) {
            // Sessions List View
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Button(
                    onClick = viewModel::createSession,
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.isSubmitting
                ) {
                    Icon(Icons.Default.Add, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Start New Stock Audit Session")
                }

                Text(
                    text = "Previous Audit Sessions",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                )

                if (sessions.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("No count sessions recorded.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        items(sessions, key = { it.id }) { s ->
                            CountSessionCard(session = s, onClick = { viewModel.openSession(s.id) })
                        }
                    }
                }
            }
        } else {
            // Active Session Counting View
            val session = uiState.activeSession!!
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Session Status Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f)),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = session.sessionNumber, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            val statusColor = if (session.status == "OPEN") Color(0xFF2E7D32) else MaterialTheme.colorScheme.onSurfaceVariant
                            Text(text = session.status, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = statusColor)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Items Counted: ${session.items.size} | Net Variance: ${session.totalVarianceQuantity.toPlainString()} units",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                if (session.status == "OPEN") {
                    Text("Record Physical Count", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)

                    // Variant Dropdown Picker
                    Box {
                        OutlinedTextField(
                            value = uiState.selectedVariantName.ifEmpty { "Select Variant to Count" },
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Product Variant") },
                            trailingIcon = { Icon(Icons.Default.ArrowDropDown, contentDescription = null) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { variantDropdownExpanded = true },
                            enabled = false,
                            colors = androidx.compose.material3.TextFieldDefaults.colors(
                                disabledTextColor = MaterialTheme.colorScheme.onSurface,
                                disabledLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                disabledTrailingIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                disabledContainerColor = Color.Transparent,
                            )
                        )
                        Box(
                            modifier = Modifier
                                .matchParentSize()
                                .clickable { variantDropdownExpanded = true }
                        )
                        DropdownMenu(
                            expanded = variantDropdownExpanded,
                            onDismissRequest = { variantDropdownExpanded = false }
                        ) {
                            variants.forEach { v ->
                                DropdownMenuItem(
                                    text = { Text("${v.productName} — ${v.variantName} (Expected: ${v.currentQuantity})") },
                                    onClick = {
                                        viewModel.onSelectVariant(v.variantId, "${v.productName} — ${v.variantName}", v.currentQuantity)
                                        variantDropdownExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    if (uiState.selectedVariantId != null) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(text = "System Expected Stock:", style = MaterialTheme.typography.bodyMedium)
                                Text(text = "${uiState.expectedQuantity.toPlainString()} units", fontWeight = FontWeight.Bold)
                            }
                        }

                        OutlinedTextField(
                            value = uiState.countedQuantityText,
                            onValueChange = viewModel::onCountedQuantityChange,
                            label = { Text("Physical Counted Quantity") },
                            modifier = Modifier.fillMaxWidth(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                            singleLine = true,
                        )

                        if (uiState.countedQuantity != null) {
                            val varColor = if (uiState.variance < BigDecimal.ZERO) MaterialTheme.colorScheme.error else Color(0xFF2E7D32)
                            Text(
                                text = "Computed Variance: ${uiState.variance.toPlainString()} units",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = varColor
                            )
                        }

                        Button(
                            onClick = viewModel::recordCountItem,
                            modifier = Modifier.fillMaxWidth(),
                            enabled = uiState.countedQuantity != null && !uiState.isSubmitting
                        ) {
                            Icon(Icons.Default.Check, contentDescription = null)
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Save Counted Line Item")
                        }
                    }

                    HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                }

                // Counted Items Table
                Text("Counted Line Items (${session.items.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)

                session.items.forEach { item ->
                    CountItemRow(item = item)
                }

                if (session.status == "OPEN" && session.items.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { showConfirmDialog = true },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Icon(Icons.Default.Check, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Finalize & Post Audit Adjustments")
                    }
                }
            }
        }
    }

    if (showConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showConfirmDialog = false },
            title = { Text("Complete Stock Audit?") },
            text = { Text("This will finalize the session and post AUDIT_ADJUSTMENT ledger movements for all line items with non-zero variance. This action cannot be reversed.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        showConfirmDialog = false
                        viewModel.completeSession()
                    }
                ) {
                    Text("Finalize & Post")
                }
            },
            dismissButton = {
                TextButton(onClick = { showConfirmDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun CountSessionCard(
    session: InventoryCountSession,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Default.Assessment, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(32.dp))
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(text = session.sessionNumber, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text(text = "Variants Counted: ${session.totalVariantsCounted}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(text = session.createdAt.toString(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f))
            }
            val statusColor = if (session.status == "OPEN") Color(0xFF2E7D32) else MaterialTheme.colorScheme.onSurfaceVariant
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(6.dp))
                    .background(statusColor.copy(alpha = 0.12f))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Text(text = session.status, style = MaterialTheme.typography.labelSmall, color = statusColor, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun CountItemRow(item: InventoryCountItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "${item.productName ?: "Item"} — ${item.variantName ?: "Variant"}",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Expected: ${item.expectedQuantity.toPlainString()} | Counted: ${item.countedQuantity.toPlainString()}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            val varColor = if (item.varianceQuantity < BigDecimal.ZERO) MaterialTheme.colorScheme.error else Color(0xFF2E7D32)
            val sign = if (item.varianceQuantity > BigDecimal.ZERO) "+" else ""
            Text(
                text = "$sign${item.varianceQuantity.toPlainString()} units",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = varColor
            )
        }
    }
}
