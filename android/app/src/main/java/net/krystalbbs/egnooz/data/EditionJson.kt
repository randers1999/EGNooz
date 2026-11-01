package net.krystalbbs.egnooz.data

import kotlinx.serialization.json.Json

object EditionJson {
    val format: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        explicitNulls = false
        encodeDefaults = true
    }

    fun parse(text: String): Edition = format.decodeFromString(Edition.serializer(), text)

    fun stringify(edition: Edition): String =
        format.encodeToString(Edition.serializer(), edition)
}
