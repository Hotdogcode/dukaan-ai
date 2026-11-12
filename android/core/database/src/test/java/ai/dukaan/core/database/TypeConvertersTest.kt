package ai.dukaan.core.database

import ai.dukaan.core.database.converter.BigDecimalConverter
import ai.dukaan.core.database.converter.InstantConverter
import ai.dukaan.core.database.converter.UuidConverter
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID

class TypeConvertersTest {

    private val bigDecimalConverter = BigDecimalConverter()
    private val instantConverter = InstantConverter()
    private val uuidConverter = UuidConverter()

    @Test
    fun bigDecimalConverter_preservesFullPrecision() {
        val original = BigDecimal("123456789.95")
        val stringVal = bigDecimalConverter.toString(original)
        val deserialized = bigDecimalConverter.fromString(stringVal)

        assertEquals("123456789.95", stringVal)
        assertEquals(original, deserialized)
    }

    @Test
    fun bigDecimalConverter_handlesNull() {
        assertNull(bigDecimalConverter.toString(null))
        assertNull(bigDecimalConverter.fromString(null))
    }

    @Test
    fun instantConverter_serializesAndDeserializes() {
        val now = Instant.ofEpochMilli(1700000000000L)
        val epoch = instantConverter.toTimestamp(now)
        val deserialized = instantConverter.fromTimestamp(epoch)

        assertEquals(1700000000000L, epoch)
        assertEquals(now, deserialized)
    }

    @Test
    fun uuidConverter_serializesAndDeserializes() {
        val uuid = UUID.randomUUID()
        val stringVal = uuidConverter.toString(uuid)
        val deserialized = uuidConverter.fromString(stringVal)

        assertEquals(uuid, deserialized)
    }
}
