package ai.dukaan.feature.dashboard

import ai.dukaan.core.designsystem.component.DukaanCard
import ai.dukaan.core.designsystem.component.DukaanLoadingWheel
import ai.dukaan.core.designsystem.component.DukaanScaffold
import ai.dukaan.core.model.ConnectivityStatus
import androidx.compose.foundation.background
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.clickable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ReceiptLong
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PointOfSale
import androidx.compose.material.icons.filled.Storefront
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun DashboardRoute(
    modifier: Modifier = Modifier,
    viewModel: DashboardViewModel = hiltViewModel(),
    onNavigateToCatalogue: () -> Unit = {},
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    DashboardScreen(
        uiState = uiState,
        onNavigateToCatalogue = onNavigateToCatalogue,
        modifier = modifier,
    )
}

@Composable
fun DashboardScreen(
    uiState: DashboardUiState,
    onNavigateToCatalogue: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    DukaanScaffold(
        modifier = modifier,
        title = {
            Column {
                Text(
                    text = "DukaanAI • दुकान AI",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = "Retail Business Assistant",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { /* Voice assistant connected in Phase 4 */ },
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
                shape = CircleShape,
            ) {
                Icon(
                    imageVector = Icons.Default.Mic,
                    contentDescription = "Voice Assistant",
                    modifier = Modifier.size(28.dp),
                )
            }
        },
    ) { innerPadding ->
        if (uiState.isLoading) {
            DukaanLoadingWheel()
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // Connectivity & Status Banner
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = if (uiState.connectivityStatus == ConnectivityStatus.AVAILABLE) {
                        MaterialTheme.colorScheme.secondaryContainer
                    } else {
                        MaterialTheme.colorScheme.errorContainer
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = if (uiState.connectivityStatus == ConnectivityStatus.AVAILABLE) {
                                Icons.Default.CheckCircle
                            } else {
                                Icons.Default.CloudOff
                            },
                            contentDescription = "Status",
                            tint = if (uiState.connectivityStatus == ConnectivityStatus.AVAILABLE) {
                                MaterialTheme.colorScheme.secondary
                            } else {
                                MaterialTheme.colorScheme.error
                            },
                            modifier = Modifier.size(24.dp),
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = if (uiState.connectivityStatus == ConnectivityStatus.AVAILABLE) {
                                    "Connected • Online Mode"
                                } else {
                                    "Offline • Local Mode Active"
                                },
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(
                                text = "Authoritative Room database enabled • Ready for sales",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }

                // Store Card
                DukaanCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(44.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(MaterialTheme.colorScheme.primaryContainer),
                                contentAlignment = Alignment.Center,
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Storefront,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                )
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                val bizName = uiState.appConfig?.selectedBusinessName ?: "Shri Ganesh Kirana Store"
                                val owner = uiState.appConfig?.userFullName ?: "Store Owner"
                                Text(
                                    text = bizName,
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                )
                                Text(
                                    text = "$owner (${uiState.appConfig?.userRole ?: "OWNER"})",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                }

                Text(
                    text = "Operational Modules",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )

                DashboardModuleCard(
                    title = "Product Catalogue & Items",
                    subtitle = "Products, variants, barcodes & categories",
                    icon = Icons.Default.Inventory2,
                    badge = "Stage 07",
                    onClick = onNavigateToCatalogue,
                )

                DashboardModuleCard(
                    title = "Point of Sale (Counter Billing)",
                    subtitle = "High-speed barcode scanning & receipts",
                    icon = Icons.Default.PointOfSale,
                    badge = "Stage 08",
                )

                DashboardModuleCard(
                    title = "Customer Credit Ledger (Khata)",
                    subtitle = "Auditable double-entry ledger & WhatsApp reminders",
                    icon = Icons.AutoMirrored.Filled.ReceiptLong,
                    badge = "Stage 09",
                )

                DashboardModuleCard(
                    title = "Hinglish Conversational AI",
                    subtitle = "Voice transaction parsing with user confirmation",
                    icon = Icons.Default.Mic,
                    badge = "Stage 10",
                )
            }
        }
    }
}

@Composable
private fun DashboardModuleCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    badge: String,
    onClick: (() -> Unit)? = null,
) {
    val cardModifier = if (onClick != null) {
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    } else {
        Modifier.fillMaxWidth()
    }

    DukaanCard(modifier = cardModifier) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(22.dp),
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium,
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = RoundedCornerShape(8.dp),
            ) {
                Text(
                    text = badge,
                    style = MaterialTheme.typography.labelSmall,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
