package net.krystalbbs.egnooz.data

import kotlinx.serialization.Serializable

@Serializable
data class Edition(
    val schemaVersion: Int = 1,
    val timezone: String = "Australia/Melbourne",
    val editionDate: String,
    val status: String = "published",
    val generatedAt: String? = null,
    val publishedAt: String? = null,
    val editorNote: String = "",
    val warnings: Warnings? = null,
    val items: List<NewsItem> = emptyList(),
)

@Serializable
data class NewsItem(
    val id: String,
    val title: String,
    val url: String,
    val sourceId: String = "",
    val sourceName: String = "",
    val publishedAt: String? = null,
    val snippet: String = "",
    val matchReason: String = "",
    val matchedPlaces: List<String> = emptyList(),
)

@Serializable
data class Warnings(
    val source: String = "VicEmergency",
    val attribution: String = "",
    val attributionUrl: String = "",
    val license: String = "",
    val disclaimer: String = "",
    val feedLastUpdated: String? = null,
    val fetchedAt: String? = null,
    val districtFireDanger: String? = null,
    val districtTotalFireBan: String? = null,
    val items: List<WarningItem> = emptyList(),
) {
    val hasStrip: Boolean
        get() = items.isNotEmpty()
}

@Serializable
data class WarningItem(
    val id: String,
    val title: String,
    val url: String,
    val location: String = "",
    val category: String = "",
    val status: String = "",
    val updatedAt: String? = null,
    val feedType: String = "",
    val matchedPlaces: List<String> = emptyList(),
)
