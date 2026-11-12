package ai.dukaan.core.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.math.BigDecimal

class MonetaryAmountTest {

    @Test
    fun addition_isDeterministicAndPreservesPrecision() {
        val a = MonetaryAmount.from("100.50")
        val b = MonetaryAmount.from("50.25")
        val result = a + b
        assertEquals(BigDecimal("150.75"), result.amount)
    }

    @Test
    fun subtraction_isDeterministic() {
        val a = MonetaryAmount.from("100.00")
        val b = MonetaryAmount.from("45.50")
        val result = a - b
        assertEquals(BigDecimal("54.50"), result.amount)
    }

    @Test
    fun multiplication_appliesHalfUpRounding() {
        val amount = MonetaryAmount.from("10.55")
        val multiplier = BigDecimal("2.5")
        val result = amount * multiplier
        // 10.55 * 2.5 = 26.375 -> rounded HALF_UP = 26.38
        assertEquals(BigDecimal("26.38"), result.amount)
    }

    @Test
    fun scaleExceedingTwoDecimalPlaces_throwsException() {
        assertThrows(IllegalArgumentException::class.java) {
            MonetaryAmount(BigDecimal("10.555"))
        }
    }
}
