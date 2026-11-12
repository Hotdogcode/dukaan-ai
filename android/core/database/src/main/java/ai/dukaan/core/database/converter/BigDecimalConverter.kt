package ai.dukaan.core.database.converter

import androidx.room.TypeConverter
import java.math.BigDecimal

class BigDecimalConverter {
    @TypeConverter
    fun fromString(value: String?): BigDecimal? = value?.let { BigDecimal(it) }

    @TypeConverter
    fun toString(amount: BigDecimal?): String? = amount?.toPlainString()
}
