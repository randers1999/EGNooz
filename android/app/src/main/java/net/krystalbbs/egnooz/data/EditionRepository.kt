package net.krystalbbs.egnooz.data

import java.io.File
import java.io.IOException
import java.time.Clock
import java.time.LocalDate
import net.krystalbbs.egnooz.time.MelbourneTime
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

sealed class EditionLoadResult {
    data class Published(val edition: Edition, val fromCache: Boolean) : EditionLoadResult()
    data class NotPublished(val cached: Edition?) : EditionLoadResult()
    data class Unavailable(val cached: Edition?, val reason: FailureReason) : EditionLoadResult()
}

enum class FailureReason {
    OFFLINE,
    FAILED,
}

class EditionRepository(
    private val cacheFile: File,
    private val editionUrl: String,
    private val client: OkHttpClient = defaultClient(),
    private val clock: Clock = MelbourneTime.clock(),
) {
    fun melbourneToday(): LocalDate = LocalDate.now(clock)

    fun loadCache(): Edition? {
        if (!cacheFile.isFile) return null
        return runCatching { EditionJson.parse(cacheFile.readText()) }.getOrNull()
    }

    fun saveCache(edition: Edition) {
        cacheFile.parentFile?.mkdirs()
        cacheFile.writeText(EditionJson.stringify(edition))
    }

    fun fetchLatest(): EditionLoadResult {
        val request = Request.Builder()
            .url(editionUrl)
            .header("Accept", "application/json")
            .header("User-Agent", USER_AGENT)
            .get()
            .build()
        return try {
            client.newCall(request).execute().use { response ->
                when (response.code) {
                    404 -> EditionLoadResult.NotPublished(loadCache())
                    in 200..299 -> {
                        val body = response.body?.string().orEmpty()
                        if (body.isBlank()) {
                            EditionLoadResult.NotPublished(loadCache())
                        } else {
                            val edition = EditionJson.parse(body)
                            saveCache(edition)
                            EditionLoadResult.Published(edition, fromCache = false)
                        }
                    }
                    else -> EditionLoadResult.Unavailable(loadCache(), FailureReason.FAILED)
                }
            }
        } catch (_: IOException) {
            EditionLoadResult.Unavailable(loadCache(), FailureReason.OFFLINE)
        }
    }

    companion object {
        const val USER_AGENT = "EGNooz-Android/0.1 (East Gippsland daily edition)"

        fun defaultClient(): OkHttpClient =
            OkHttpClient.Builder()
                .connectTimeout(20, TimeUnit.SECONDS)
                .readTimeout(20, TimeUnit.SECONDS)
                .callTimeout(30, TimeUnit.SECONDS)
                .followRedirects(true)
                .build()
    }
}
