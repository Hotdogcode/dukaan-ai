package ai.dukaan.core.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class BusinessCreateNetwork(
    @SerialName("name") val name: String,
    @SerialName("business_type") val businessType: String? = "GROCERY",
    @SerialName("owner_name") val ownerName: String? = null,
    @SerialName("primary_language") val primaryLanguage: String = "hi",
    @SerialName("initial_store_name") val initialStoreName: String? = null,
)

@Serializable
data class BusinessResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("name") val name: String,
    @SerialName("business_type") val businessType: String? = null,
    @SerialName("owner_name") val ownerName: String? = null,
    @SerialName("legal_name") val legalName: String? = null,
    @SerialName("gstin") val gstin: String? = null,
    @SerialName("currency") val currency: String = "INR",
    @SerialName("timezone") val timezone: String = "Asia/Kolkata",
    @SerialName("primary_language") val primaryLanguage: String = "hi",
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class BusinessMembershipResponseNetwork(
    @SerialName("business") val business: BusinessResponseNetwork,
    @SerialName("role") val role: String,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("permissions") val permissions: List<String> = emptyList(),
)
