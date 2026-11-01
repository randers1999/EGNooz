package net.krystalbbs.egnooz.time

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MelbourneTimeTest {
    @Test
    fun longDateIsAustralianEnglish() {
        assertEquals(
            "Sunday 1 November 2026",
            MelbourneTime.formatLongDate(LocalDate.parse("2026-11-01")),
        )
        assertEquals(
            "Sunday 1 November 2026",
            MelbourneTime.formatLongDate("2026-11-01"),
        )
    }

    @Test
    fun itemTimeUsesMelbourneClock() {
        assertEquals(
            "Sunday 1 November 2026, 5:00 pm",
            MelbourneTime.formatItemTime("2026-11-01T17:00:00+11:00"),
        )
        assertEquals(
            "Sunday 1 November 2026, 9:05 am",
            MelbourneTime.formatItemTime("2026-11-01T09:05:00+11:00"),
        )
        assertEquals("Time not given", MelbourneTime.formatItemTime(null))
    }

    @Test
    fun utcOffsetConvertsToMelbourne() {
        // 06:00 UTC on 1 Nov 2026 is 17:00 in Melbourne (AEDT, UTC+11).
        assertEquals(
            "Sunday 1 November 2026, 5:00 pm",
            MelbourneTime.formatItemTime("2026-11-01T06:00:00Z"),
        )
    }

    @Test
    fun isTodayComparesCalendarDate() {
        val clock = java.time.Clock.fixed(
            java.time.Instant.parse("2026-11-01T08:00:00Z"),
            MelbourneTime.ZONE,
        )
        assertTrue(MelbourneTime.isToday("2026-11-01", clock))
        assertFalse(MelbourneTime.isToday("2026-10-31", clock))
    }
}
