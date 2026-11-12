package ai.dukaan.core.common.format

import java.math.BigDecimal
import java.text.NumberFormat
import java.util.Locale

object CurrencyFormatter {
    private val indianLocale = Locale("en", "IN")

    /**
     * Formats a BigDecimal monetary amount to Indian Rupee representation (e.g. ₹ 1,23,456.00).
     */
    fun formatInr(amount: BigDecimal, showSymbol: Boolean = true): String {
        val format = NumberFormat.getCurrencyInstance(indianLocale)
        val formatted = format.format(amount)
        return if (showSymbol) {
            formatted
        } else {
            formatted.replace("₹", "").trim()
        }
    }
}
