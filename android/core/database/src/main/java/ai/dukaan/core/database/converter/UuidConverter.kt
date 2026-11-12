package ai.dukaan.core.database.converter

import androidx.room.TypeConverter
import java.util.UUID

class UuidConverter {
    @TypeConverter
    fun fromString(value: String?): UUID? = value?.let { UUID.fromString(it) }

    @TypeConverter
    fun toString(uuid: UUID?): String? = uuid?.toString()
}
