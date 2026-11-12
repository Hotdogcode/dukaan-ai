package ai.dukaan.feature.onboarding

import ai.dukaan.core.designsystem.R as DesignR
import ai.dukaan.core.designsystem.component.DukaanPrimaryButton
import ai.dukaan.core.designsystem.component.DukaanScaffold
import ai.dukaan.core.designsystem.component.DukaanTextField
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun BusinessOnboardingRoute(
    onNavigateToDashboard: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: BusinessOnboardingViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    BusinessOnboardingScreen(
        uiState = uiState,
        onBusinessNameChanged = viewModel::onBusinessNameChanged,
        onBusinessTypeChanged = viewModel::onBusinessTypeChanged,
        onOwnerNameChanged = viewModel::onOwnerNameChanged,
        onLanguageChanged = viewModel::onLanguageChanged,
        onStoreNameChanged = viewModel::onStoreNameChanged,
        onCityChanged = viewModel::onCityChanged,
        onStateChanged = viewModel::onStateChanged,
        onPincodeChanged = viewModel::onPincodeChanged,
        onSubmit = {
            viewModel.submitOnboarding(onSuccess = onNavigateToDashboard)
        },
        modifier = modifier,
    )
}

@Composable
fun BusinessOnboardingScreen(
    uiState: BusinessOnboardingUiState,
    onBusinessNameChanged: (String) -> Unit,
    onBusinessTypeChanged: (String) -> Unit,
    onOwnerNameChanged: (String) -> Unit,
    onLanguageChanged: (String) -> Unit,
    onStoreNameChanged: (String) -> Unit,
    onCityChanged: (String) -> Unit,
    onStateChanged: (String) -> Unit,
    onPincodeChanged: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val scrollState = rememberScrollState()

    DukaanScaffold(
        modifier = modifier,
        title = { Text(stringResource(DesignR.string.onboarding_screen_title)) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(scrollState)
                .padding(24.dp),
            verticalArrangement = Arrangement.Top,
        ) {
            Text(
                text = stringResource(DesignR.string.onboarding_title),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = stringResource(DesignR.string.onboarding_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(modifier = Modifier.height(20.dp))

            // Business Name
            DukaanTextField(
                value = uiState.businessName,
                onValueChange = onBusinessNameChanged,
                label = stringResource(DesignR.string.business_name_label),
                placeholder = stringResource(DesignR.string.business_name_placeholder),
                isError = uiState.errorMessage != null,
                errorMessage = uiState.errorMessage,
            )
            Spacer(modifier = Modifier.height(16.dp))

            // Business Category / Type
            Text(
                text = stringResource(DesignR.string.business_type_label),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                listOf(
                    "GROCERY" to "Kirana • किराना",
                    "GENERAL" to "General • जनरल",
                    "DAIRY" to "Dairy • डेयरी",
                ).forEach { (typeKey, label) ->
                    FilterChip(
                        selected = uiState.businessType == typeKey,
                        onClick = { onBusinessTypeChanged(typeKey) },
                        label = { Text(label) },
                    )
                }
            }
            Spacer(modifier = Modifier.height(16.dp))

            // Owner Name
            DukaanTextField(
                value = uiState.ownerName,
                onValueChange = onOwnerNameChanged,
                label = stringResource(DesignR.string.owner_name_label),
                placeholder = stringResource(DesignR.string.owner_name_placeholder),
            )
            Spacer(modifier = Modifier.height(16.dp))

            // Preferred Language
            Text(
                text = stringResource(DesignR.string.language_label),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                listOf("hi" to "हिन्दी (Hindi)", "en" to "English").forEach { (code, name) ->
                    FilterChip(
                        selected = uiState.preferredLanguage == code,
                        onClick = { onLanguageChanged(code) },
                        label = { Text(name) },
                    )
                }
            }
            Spacer(modifier = Modifier.height(16.dp))

            // Store Name & Location
            DukaanTextField(
                value = uiState.storeName,
                onValueChange = onStoreNameChanged,
                label = stringResource(DesignR.string.store_name_label),
                placeholder = stringResource(DesignR.string.store_name_placeholder),
            )
            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    DukaanTextField(
                        value = uiState.city,
                        onValueChange = onCityChanged,
                        label = stringResource(DesignR.string.city_label),
                        placeholder = stringResource(DesignR.string.city_placeholder),
                    )
                }
                Column(modifier = Modifier.weight(1f)) {
                    DukaanTextField(
                        value = uiState.pincode,
                        onValueChange = onPincodeChanged,
                        label = stringResource(DesignR.string.pincode_label),
                        placeholder = stringResource(DesignR.string.pincode_placeholder),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    )
                }
            }

            Spacer(modifier = Modifier.height(28.dp))
            DukaanPrimaryButton(
                text = stringResource(DesignR.string.launch_dukaan_button),
                onClick = onSubmit,
                enabled = uiState.businessName.trim().length >= 2,
                isLoading = uiState.isLoading,
            )
        }
    }
}
