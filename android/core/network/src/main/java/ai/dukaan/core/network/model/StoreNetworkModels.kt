package ai.dukaan.core.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class StoreCreateNetwork(
    @SerialName("name") val name: String,
    @SerialName("code") val code: String? = null,
    @SerialName("address_line1") val addressLine1: String = "",
    @SerialName("city") val city: String = "",
    @SerialName("state") val state: String = "",
    @SerialName("pincode") val pincode: String = "",
    @SerialName("phone_number") val phoneNumber: String? = null,
    @SerialName("is_primary") val isPrimary: Boolean = false,
    @SerialName("timezone") val timezone: String = "Asia/Kolkata",
)

@Serializable
data class StoreResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("business_id") val businessId: String,
    @SerialName("name") val name: String,
    @SerialName("code") val code: String? = null,
    @SerialName("address_line1") val addressLine1: String = "",
    @SerialName("address_line2") val addressLine2: String? = null,
    @SerialName("city") val city: String = "",
    @SerialName("state") val state: String = "",
    @SerialName("pincode") val pincode: String = "",
    @SerialName("phone_number") val phoneNumber: String? = null,
    @SerialName("is_primary") val isPrimary: Boolean = false,
    @SerialName("timezone") val timezone: String = "Asia/Kolkata",
    @SerialName("is_active") val isActive: Boolean = true,
)
