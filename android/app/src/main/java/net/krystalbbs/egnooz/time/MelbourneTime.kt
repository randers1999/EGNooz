package net.krystalbbs.egnooz.time

import java.time.Clock
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.time.format.TextStyle
import java.util.Locale

object MelbourneTime {
    val ZONE: ZoneId = ZoneId.of("Australia/Melbourne")
    val LOCALE: Locale = Locale.forLanguageTag("en-AU")

    fun clock(): Clock = Clock.system(ZONE)

    fun today(clock: Clock = clock()): LocalDate = LocalDate.now(clock)

    fun parseInstant(value: String?): ZonedDateTime? {
        if (value.isNullOrBlank()) return null
        return try {
            ZonedDateTime.parse(value).withZoneSameInstant(ZONE)
        } catch (_: DateTimeParseException) {
            try {
                DateTimeFormatter.ISO_OFFSET_DATE_TIME.parse(value) { temporal ->
                    ZonedDateTime.from(temporal).withZoneSameInstant(ZONE)
                }
            } catch (_: DateTimeParseException) {
                null
            }
        }
    }

    fun formatLongDate(date: LocalDate): String {
        val weekday = date.dayOfWeek.getDisplayName(TextStyle.FULL, LOCALE)
        val month = date.month.getDisplayName(TextStyle.FULL, LOCALE)
        return "$weekday ${date.dayOfMonth} $month ${date.year}"
    }

    fun formatLongDate(value: String): String {
        return runCatching { formatLongDate(LocalDate.parse(value.take(10))) }
            .getOrElse { value }
    }

    fun formatClock(time: ZonedDateTime): String {
        val local = time.withZoneSameInstant(ZONE)
        val hour24 = local.hour
        val hour12 = when (val h = hour24 % 12) {
            0 -> 12
            else -> h
        }
        val minute = local.minute.toString().padStart(2, '0')
        val suffix = if (hour24 < 12) "am" else "pm"
        return "$hour12:$minute $suffix"
    }

    fun formatItemTime(value: String?): String {
        val time = parseInstant(value) ?: return "Time not given"
        return "${formatLongDate(time.toLocalDate())}, ${formatClock(time)}"
    }

    fun isToday(editionDate: String, clock: Clock = clock()): Boolean {
        return runCatching { LocalDate.parse(editionDate.take(10)) == today(clock) }
            .getOrDefault(false)
    }
}
