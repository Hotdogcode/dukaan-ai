package ai.dukaan.core.ui

/**
 * Marker interface for immutable screen UI states.
 */
interface UiState

/**
 * Marker interface for user actions dispatched from Compose UI to ViewModel.
 */
interface UiEvent

/**
 * Marker interface for one-shot UI side-effects (e.g. navigation events, toasts, snackbars).
 */
interface UiEffect
