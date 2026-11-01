package net.krystalbbs.egnooz.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class EditionJsonTest {
    @Test
    fun parseSchemaVersion1Fixture() {
        val text = javaClass.getResource("/fixtures/latest.json")!!.readText()
        val edition = EditionJson.parse(text)
        assertEquals(1, edition.schemaVersion)
        assertEquals("Australia/Melbourne", edition.timezone)
        assertEquals("2026-11-01", edition.editionDate)
        assertEquals("published", edition.status)
        assertEquals(3, edition.items.size)
        val first = edition.items.first()
        assertEquals("lakes-post-c10567359460", first.id)
        assertEquals("Club Eastwood prepares to upgrade popular function spaces", first.title)
        assertEquals("Lakes Post", first.sourceName)
        assertEquals("lakes-post", first.sourceId)
        assertTrue(first.snippet.isNotBlank())
        assertTrue(first.url.startsWith("https://"))
        assertEquals("local-source", first.matchReason)
        val warnings = edition.warnings!!
        assertEquals("VicEmergency", warnings.source)
        assertTrue(warnings.disclaimer.contains("not an emergency service"))
        assertEquals("MODERATE", warnings.districtFireDanger)
        assertEquals(2, warnings.items.size)
        assertEquals("Advice — Thunderstorm Asthma — North East District", warnings.items.first().title)
    }

    @Test
    fun ignoresUnknownFields() {
        val edition = EditionJson.parse(
            """
            {
              "schemaVersion": 1,
              "timezone": "Australia/Melbourne",
              "editionDate": "2026-11-01",
              "status": "published",
              "futureField": true,
              "items": [
                {
                  "id": "x",
                  "title": "Hello",
                  "url": "https://example.test/story",
                  "sourceName": "Test",
                  "extra": 1
                }
              ]
            }
            """.trimIndent(),
        )
        assertEquals("Hello", edition.items.single().title)
        assertEquals("", edition.items.single().snippet)
    }

    @Test
    fun roundTripCache() {
        val text = javaClass.getResource("/fixtures/latest.json")!!.readText()
        val parsed = EditionJson.parse(text)
        val again = EditionJson.parse(EditionJson.stringify(parsed))
        assertEquals(parsed, again)
    }
}
