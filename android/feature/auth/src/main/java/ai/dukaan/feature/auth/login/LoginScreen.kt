package ai.dukaan.feature.auth.login

import ai.dukaan.core.designsystem.R as DesignR
import ai.dukaan.core.designsystem.component.DukaanPrimaryButton
import ai.dukaan.core.designsystem.component.DukaanScaffold
import ai.dukaan.core.designsystem.component.DukaanTextField
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
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
fun LoginRoute(
    onNavigateToOtp: (phoneNumber: String, requestId: String?) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: LoginViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LoginScreen(
        uiState = uiState,
        onPhoneNumberChanged = viewModel::onPhoneNumberChanged,
        onRequestOtp = {
            viewModel.requestOtp(onSuccess = onNavigateToOtp)
        },
        modifier = modifier,
    )
}

@Composable
fun LoginScreen(
    uiState: LoginUiState,
    onPhoneNumberChanged: (String) -> Unit,
    onRequestOtp: () -> Unit,
    modifier: Modifier = Modifier,
) {
    DukaanScaffold(
        modifier = modifier,
        title = { Text(stringResource(DesignR.string.login_screen_title)) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = stringResource(DesignR.string.login_title),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = stringResource(DesignR.string.login_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(modifier = Modifier.height(24.dp))
            DukaanTextField(
                value = uiState.phoneNumber,
                onValueChange = onPhoneNumberChanged,
                label = stringResource(DesignR.string.phone_number_label),
                placeholder = stringResource(DesignR.string.phone_number_placeholder),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                isError = uiState.errorMessage != null,
                errorMessage = uiState.errorMessage,
            )
            Spacer(modifier = Modifier.height(24.dp))
            DukaanPrimaryButton(
                text = stringResource(DesignR.string.get_otp_button),
                onClick = onRequestOtp,
                enabled = uiState.phoneNumber.length == 10,
                isLoading = uiState.isLoading,
            )
        }
    }
}
