package ai.dukaan.feature.auth.otp

import ai.dukaan.core.designsystem.R as DesignR
import ai.dukaan.core.designsystem.component.DukaanOutlinedButton
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
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun OtpVerifyRoute(
    phoneNumber: String,
    requestId: String?,
    onNavigateToOnboarding: () -> Unit,
    onNavigateToDashboard: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: OtpVerifyViewModel = hiltViewModel(),
) {
    LaunchedEffect(phoneNumber, requestId) {
        viewModel.initialize(phoneNumber, requestId)
    }

    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    OtpVerifyScreen(
        uiState = uiState,
        onOtpChanged = viewModel::onOtpCodeChanged,
        onVerify = {
            viewModel.verifyOtp(
                onNavigateToOnboarding = onNavigateToOnboarding,
                onNavigateToDashboard = onNavigateToDashboard,
            )
        },
        onResend = viewModel::resendOtp,
        modifier = modifier,
    )
}

@Composable
fun OtpVerifyScreen(
    uiState: OtpVerifyUiState,
    onOtpChanged: (String) -> Unit,
    onVerify: () -> Unit,
    onResend: () -> Unit,
    modifier: Modifier = Modifier,
) {
    DukaanScaffold(
        modifier = modifier,
        title = { Text(stringResource(DesignR.string.otp_screen_title)) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = stringResource(DesignR.string.otp_title),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = stringResource(DesignR.string.otp_subtitle, "+91 ${uiState.phoneNumber}"),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(modifier = Modifier.height(24.dp))
            DukaanTextField(
                value = uiState.otpCode,
                onValueChange = onOtpChanged,
                label = stringResource(DesignR.string.otp_label),
                placeholder = "123456",
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                isError = uiState.errorMessage != null,
                errorMessage = uiState.errorMessage,
            )
            Spacer(modifier = Modifier.height(16.dp))

            // Resend OTP / Countdown Timer
            if (uiState.canResend) {
                TextButton(
                    onClick = onResend,
                    enabled = !uiState.isResending && !uiState.isLoading,
                    modifier = Modifier.align(Alignment.End),
                ) {
                    Text(
                        text = stringResource(DesignR.string.resend_otp),
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            } else {
                Text(
                    text = stringResource(DesignR.string.resend_in_seconds, uiState.countdownSeconds),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.align(Alignment.End).padding(end = 8.dp),
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
            DukaanPrimaryButton(
                text = stringResource(DesignR.string.verify_button),
                onClick = onVerify,
                enabled = uiState.otpCode.length == 6,
                isLoading = uiState.isLoading,
            )
        }
    }
}
