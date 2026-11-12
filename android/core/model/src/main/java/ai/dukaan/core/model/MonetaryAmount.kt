package ai.dukaan.core.model

import java.math.BigDecimal
import java.math.RoundingMode

@JvmInline
value class MonetaryAmount(val amount: BigDecimal) {
    init {
        require(amount.scale() <= 2) { "MonetaryAmount cannot have more than 2 decimal places, was: $amount" }
    }

    operator fun plus(other: MonetaryAmount): MonetaryAmount =
        MonetaryAmount(amount.add(other.amount).setScale(2, RoundingMode.HALF_UP))

    operator fun minus(other: MonetaryAmount): MonetaryAmount =
        MonetaryAmount(amount.subtract(other.amount).setScale(2, RoundingMode.HALF_UP))

    operator fun times(multiplier: BigDecimal): MonetaryAmount =
        MonetaryAmount(amount.multiply(multiplier).setScale(2, RoundingMode.HALF_UP))

    companion object {
        val ZERO = MonetaryAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP))

        fun from(value: String): MonetaryAmount =
            MonetaryAmount(BigDecimal(value).setScale(2, RoundingMode.HALF_UP))

        fun from(value: Double): MonetaryAmount =
            MonetaryAmount(BigDecimal.valueOf(value).setScale(2, RoundingMode.HALF_UP))
    }
}
