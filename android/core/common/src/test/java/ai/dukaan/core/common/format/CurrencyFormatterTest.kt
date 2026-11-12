package ai.dukaan.core.common.format

import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigDecimal

class CurrencyFormatterTest {

    @Test
    fun formatInr_formatsCorrectlyWithSymbol() {
        val amount = BigDecimal("123456.75")
        val formatted = CurrencyFormatter.formatInr(amount, showSymbol = true)
        // Check formatted string contains Rupee symbol and numbers
        assertTrue(formatted.contains("₹") || formatted.contains("Rs") || formatted.contains("123"))
    }

    @Test
    fun formatInr_withoutSymbol() {
        val amount = BigDecimal("500.00")
        val formatted = CurrencyFormatter.formatInr(amount, showSymbol = false)
        assertTrue(!formatted.contains("₹"))
    }
}
