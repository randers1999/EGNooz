package net.krystalbbs.egnooz.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import net.krystalbbs.egnooz.data.Edition
import net.krystalbbs.egnooz.data.EditionLoadResult
import net.krystalbbs.egnooz.data.EditionRepository
import net.krystalbbs.egnooz.data.FailureReason

data class EditionUiState(
    val loading: Boolean = true,
    val refreshing: Boolean = false,
    val edition: Edition? = null,
    val fromCache: Boolean = false,
    val todayPublished: Boolean = false,
    val banner: BannerKind? = null,
)

enum class BannerKind {
    NOT_PUBLISHED,
    NOT_PUBLISHED_SHOWING_LAST,
    OFFLINE_SHOWING_LAST,
    OFFLINE,
    FAILED,
}

class EditionViewModel(
    private val repository: EditionRepository,
    private val previewUnpublished: Boolean = false,
) : ViewModel() {

    private val _state = MutableStateFlow(EditionUiState())
    val state: StateFlow<EditionUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            if (previewUnpublished) {
                _state.value = EditionUiState(
                    loading = false,
                    banner = BannerKind.NOT_PUBLISHED,
                )
                return@launch
            }
            val cached = withContext(Dispatchers.IO) { repository.loadCache() }
            if (cached != null) {
                _state.value = present(cached, fromCache = true, refreshing = true)
            }
            refreshInternal(isUserPull = false)
        }
    }

    fun refresh() {
        viewModelScope.launch { refreshInternal(isUserPull = true) }
    }

    private suspend fun refreshInternal(isUserPull: Boolean) {
        _state.update {
            it.copy(
                refreshing = true,
                loading = it.edition == null && !isUserPull,
            )
        }
        val result = withContext(Dispatchers.IO) { repository.fetchLatest() }
        _state.value = when (result) {
            is EditionLoadResult.Published -> present(result.edition, fromCache = false)
            is EditionLoadResult.NotPublished -> {
                val cached = result.cached
                if (cached == null) {
                    EditionUiState(
                        loading = false,
                        refreshing = false,
                        banner = BannerKind.NOT_PUBLISHED,
                    )
                } else {
                    present(cached, fromCache = true).copy(
                        banner = BannerKind.NOT_PUBLISHED_SHOWING_LAST,
                    )
                }
            }
            is EditionLoadResult.Unavailable -> {
                val cached = result.cached
                val banner = when {
                    cached != null && result.reason == FailureReason.OFFLINE ->
                        BannerKind.OFFLINE_SHOWING_LAST
                    cached != null -> BannerKind.FAILED
                    result.reason == FailureReason.OFFLINE -> BannerKind.OFFLINE
                    else -> BannerKind.FAILED
                }
                if (cached == null) {
                    EditionUiState(
                        loading = false,
                        refreshing = false,
                        banner = banner,
                    )
                } else {
                    present(cached, fromCache = true).copy(banner = banner)
                }
            }
        }
    }

    private fun present(
        edition: Edition,
        fromCache: Boolean,
        refreshing: Boolean = false,
    ): EditionUiState {
        val todayPublished = runCatching {
            java.time.LocalDate.parse(edition.editionDate.take(10)) == repository.melbourneToday()
        }.getOrDefault(false)
        val banner = if (!todayPublished) BannerKind.NOT_PUBLISHED_SHOWING_LAST else null
        return EditionUiState(
            loading = false,
            refreshing = refreshing,
            edition = edition,
            fromCache = fromCache,
            todayPublished = todayPublished,
            banner = banner,
        )
    }

    companion object {
        fun factory(
            cacheDir: File,
            editionUrl: String,
            previewUnpublished: Boolean = false,
        ): ViewModelProvider.Factory {
            return object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    val repository = EditionRepository(
                        cacheFile = File(cacheDir, "latest-edition.json"),
                        editionUrl = editionUrl,
                    )
                    return EditionViewModel(repository, previewUnpublished) as T
                }
            }
        }
    }
}
