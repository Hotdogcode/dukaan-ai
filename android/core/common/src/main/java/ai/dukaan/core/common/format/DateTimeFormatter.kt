package ai.dukaan.core.common.format

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

object DukaanDateTimeFormatter {
    private val istZone = ZoneId.of("Asia/Kolkata")
    private val displayDateFormatter = DateTimeFormatter.ofPattern("dd MMM yyyy", Locale.ENGLISH)
    private val displayTimeFormatter = DateTimeFormatter.ofPattern("hh:mm a", Locale.ENGLISH)
    private val displayDateTimeFormatter = DateTimeFormatter.ofPattern("dd MMM yyyy, hh:mm a", Locale.ENGLISH)

    fun formatDate(instant: Instant): String {
        return instant.atZone(istZone).format(displayDateFormatter)
    }

    fun formatTime(instant: Instant): String {
        return instant.atZone(istZone).format(displayTimeFormatter)
    }

    fun formatDateTime(instant: Instant): String {
        return instant.atZone(istZone).format(displayDateTimeFormatter)
    }
}
