package net.krystalbbs.egnooz.data

import java.io.File
import java.time.Clock
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class EditionRepositoryTest {
    private lateinit var server: MockWebServer
    private lateinit var cache: File

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        cache = File.createTempFile("egnooz-latest", ".json")
        cache.writeText("")
        cache.delete()
    }

    @After
    fun tearDown() {
        server.shutdown()
        cache.delete()
    }

    @Test
    fun fetchLatestSavesCache() {
        val body = javaClass.getResource("/fixtures/latest.json")!!.readText()
        server.enqueue(MockResponse().setResponseCode(200).setBody(body))
        val repo = repository()
        val result = repo.fetchLatest() as EditionLoadResult.Published
        assertEquals("2026-11-01", result.edition.editionDate)
        assertEquals(false, result.fromCache)
        assertTrue(cache.isFile)
        assertEquals("2026-11-01", repo.loadCache()?.editionDate)
        val recorded = server.takeRequest()
        assertEquals("/editions/latest.json", recorded.path)
        assertTrue(recorded.getHeader("User-Agent")!!.startsWith("EGNooz-Android/"))
    }

    @Test
    fun unpublished404KeepsCache() {
        val body = javaClass.getResource("/fixtures/latest.json")!!.readText()
        cache.writeText(body)
        server.enqueue(MockResponse().setResponseCode(404).setBody("not found"))
        val result = repository().fetchLatest() as EditionLoadResult.NotPublished
        assertEquals("2026-11-01", result.cached?.editionDate)
        assertEquals("2026-11-01", EditionJson.parse(cache.readText()).editionDate)
    }

    @Test
    fun unpublished404WithoutCache() {
        server.enqueue(MockResponse().setResponseCode(404))
        val result = repository().fetchLatest() as EditionLoadResult.NotPublished
        assertEquals(null, result.cached)
    }

    @Test
    fun networkFailureUsesCache() {
        val body = javaClass.getResource("/fixtures/latest.json")!!.readText()
        cache.writeText(body)
        server.shutdown()
        val result = repository().fetchLatest() as EditionLoadResult.Unavailable
        assertEquals(FailureReason.OFFLINE, result.reason)
        assertEquals("2026-11-01", result.cached?.editionDate)
    }

    @Test
    fun melbourneTodayFollowsClock() {
        val clock = Clock.fixed(Instant.parse("2026-11-01T08:00:00Z"), ZoneId.of("Australia/Melbourne"))
        val repo = EditionRepository(
            cacheFile = cache,
            editionUrl = server.url("/editions/latest.json").toString(),
            clock = clock,
        )
        assertEquals(LocalDate.parse("2026-11-01"), repo.melbourneToday())
    }

    private fun repository(): EditionRepository {
        return EditionRepository(
            cacheFile = cache,
            editionUrl = server.url("/editions/latest.json").toString(),
        )
    }
}
