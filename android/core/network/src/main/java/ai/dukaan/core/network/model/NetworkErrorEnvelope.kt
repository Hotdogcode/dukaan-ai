package ai.dukaan.core.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

/**
 * Standard error response DTO matching DukaanAI FastAPI backend error envelopes.
 */
@Serializable
data class NetworkErrorEnvelope(
    val code: String,
    val message: String,
    val details: JsonObject? = null,
    @SerialName("request_id")
    val requestId: String? = null,
)
