package net.krystalbbs.egnooz.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import net.krystalbbs.egnooz.R
import net.krystalbbs.egnooz.data.NewsItem
import net.krystalbbs.egnooz.data.WarningItem
import net.krystalbbs.egnooz.data.Warnings
import net.krystalbbs.egnooz.time.MelbourneTime

@Composable
fun EditionScreen(viewModel: EditionViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    EditionContent(
        state = state,
        onRefresh = viewModel::refresh,
        onOpenUrl = { PublisherTabs.open(context, it) },
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditionContent(
    state: EditionUiState,
    onRefresh: () -> Unit,
    onOpenUrl: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    PullToRefreshBox(
        isRefreshing = state.refreshing || state.loading,
        onRefresh = onRefresh,
        modifier = modifier
            .fillMaxSize()
            .background(Paper),
    ) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 18.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Column {
                    Text(
                        text = stringResource(R.string.kicker),
                        color = Teal,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.SansSerif,
                        letterSpacing = 2.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    Text(
                        text = stringResource(R.string.app_name),
                        color = Ink,
                        fontSize = 34.sp,
                        fontFamily = FontFamily.Serif,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = (-0.5).sp,
                    )
                    val edition = state.edition
                    if (edition != null) {
                        Text(
                            text = MelbourneTime.formatLongDate(edition.editionDate),
                            color = Muted,
                            fontSize = 16.sp,
                            modifier = Modifier.padding(top = 4.dp),
                        )
                    }
                }
            }

            val edition = state.edition
            val banner = state.banner
            if (banner != null && !(edition == null && banner == BannerKind.NOT_PUBLISHED)) {
                item {
                    StatusBanner(banner)
                }
            }

            if (edition == null && !state.loading &&
                (banner == null || banner == BannerKind.NOT_PUBLISHED)
            ) {
                item {
                    EmptyHold()
                }
            }

            if (edition != null) {
                if (edition.editorNote.isNotBlank()) {
                    item {
                        Text(
                            text = edition.editorNote,
                            color = Ink,
                            fontSize = 18.sp,
                            fontFamily = FontFamily.Serif,
                            modifier = Modifier.padding(top = 4.dp),
                        )
                    }
                }

                val warnings = edition.warnings
                if (warnings != null && warnings.hasStrip) {
                    item {
                        WarningsStrip(warnings = warnings, onOpen = onOpenUrl)
                    }
                }

                if (edition.items.isEmpty()) {
                    item {
                        Text(
                            text = stringResource(R.string.thin_day),
                            color = Muted,
                            fontSize = 16.sp,
                        )
                    }
                } else {
                    items(edition.items, key = { it.id }) { item ->
                        HeadlineCard(item = item, onClick = { onOpenUrl(item.url) })
                    }
                }

                item {
                    Text(
                        text = stringResource(R.string.fineprint),
                        color = Muted,
                        fontSize = 13.sp,
                        modifier = Modifier.padding(top = 8.dp, bottom = 24.dp),
                    )
                }
            } else {
                item { Spacer(Modifier.height(48.dp)) }
            }
        }
    }
}

@Composable
private fun StatusBanner(banner: BannerKind) {
    val (text, wash, accent) = when (banner) {
        BannerKind.NOT_PUBLISHED -> Triple(
            stringResource(R.string.not_published_yet),
            BannerWash,
            Teal,
        )
        BannerKind.NOT_PUBLISHED_SHOWING_LAST -> Triple(
            stringResource(R.string.not_published_showing_last),
            BannerWash,
            Teal,
        )
        BannerKind.OFFLINE_SHOWING_LAST -> Triple(
            stringResource(R.string.offline_showing_last),
            OfflineWash,
            Ok,
        )
        BannerKind.OFFLINE -> Triple(
            stringResource(R.string.offline),
            OfflineWash,
            Ok,
        )
        BannerKind.FAILED -> Triple(
            stringResource(R.string.fetch_failed),
            WarnWash,
            Warn,
        )
    }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(wash)
            .border(1.dp, accent.copy(alpha = 0.35f), RoundedCornerShape(12.dp))
            .padding(horizontal = 14.dp, vertical = 12.dp),
    ) {
        Text(text = text, color = Ink, fontSize = 15.sp, fontFamily = FontFamily.SansSerif)
    }
}

@Composable
private fun EmptyHold() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 24.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        Text(
            text = stringResource(R.string.not_published_yet),
            color = Ink,
            fontSize = 22.sp,
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.SemiBold,
        )
        Text(
            text = stringResource(R.string.not_published_body),
            color = Muted,
            fontSize = 16.sp,
            modifier = Modifier.padding(top = 8.dp),
        )
    }
}

@Composable
private fun WarningsStrip(
    warnings: Warnings,
    onOpen: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(CardFill)
            .border(1.dp, Warn.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
            .padding(16.dp),
    ) {
        Text(
            text = stringResource(R.string.warnings_heading),
            color = Warn,
            fontSize = 18.sp,
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.SemiBold,
        )
        val fire = warnings.districtFireDanger
        if (!fire.isNullOrBlank()) {
            val ban = warnings.districtTotalFireBan.orEmpty()
            Text(
                text = if (ban.isBlank()) {
                    stringResource(R.string.fire_danger, fire)
                } else {
                    stringResource(R.string.fire_danger_ban, fire, ban)
                },
                color = Muted,
                fontSize = 13.sp,
                modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
            )
        }
        warnings.items.forEachIndexed { index, item ->
            if (index > 0) {
                Spacer(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                        .height(1.dp)
                        .background(Line),
                )
            }
            WarningRow(item = item, onOpen = onOpen)
        }
        if (warnings.disclaimer.isNotBlank()) {
            Text(
                text = warnings.disclaimer,
                color = Warn,
                fontSize = 13.sp,
                modifier = Modifier.padding(top = 10.dp),
            )
        }
        val attribution = listOf(warnings.attribution, warnings.license)
            .filter { it.isNotBlank() }
            .joinToString(" ")
        if (attribution.isNotBlank()) {
            Text(
                text = attribution,
                color = Muted,
                fontSize = 12.sp,
                modifier = Modifier
                    .padding(top = 4.dp)
                    .then(
                        if (warnings.attributionUrl.isNotBlank()) {
                            Modifier.clickable { onOpen(warnings.attributionUrl) }
                        } else {
                            Modifier
                        },
                    ),
            )
        }
    }
}

@Composable
private fun WarningRow(
    item: WarningItem,
    onOpen: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(role = Role.Button) { onOpen(item.url) }
            .padding(vertical = 4.dp),
    ) {
        Text(
            text = item.title,
            color = TealDark,
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold,
        )
        val meta = listOf(item.location, item.status).filter { it.isNotBlank() }.joinToString(" · ")
        if (meta.isNotBlank()) {
            Text(text = meta, color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 2.dp))
        }
    }
}

@Composable
private fun HeadlineCard(
    item: NewsItem,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(CardFill)
            .border(1.dp, Line, RoundedCornerShape(14.dp))
            .clickable(role = Role.Button, onClick = onClick)
            .padding(16.dp),
    ) {
        Text(
            text = item.title,
            color = Ink,
            fontSize = 18.sp,
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.SemiBold,
        )
        val time = MelbourneTime.formatItemTime(item.publishedAt)
        Text(
            text = listOf(item.sourceName, time).filter { it.isNotBlank() }.joinToString(" · "),
            color = Muted,
            fontSize = 13.sp,
            fontFamily = FontFamily.SansSerif,
            modifier = Modifier.padding(top = 6.dp),
        )
        if (item.snippet.isNotBlank()) {
            Text(
                text = item.snippet,
                color = Ink,
                fontSize = 15.sp,
                modifier = Modifier.padding(top = 8.dp),
                lineHeight = 21.sp,
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFFF4EFE4, widthDp = 412, heightDp = 891)
@Composable
private fun PreviewUnpublished() {
    EgnoozTheme {
        EditionContent(
            state = EditionUiState(loading = false, banner = BannerKind.NOT_PUBLISHED),
            onRefresh = {},
            onOpenUrl = {},
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFFF4EFE4, widthDp = 412, heightDp = 891)
@Composable
private fun PreviewHeadlineCard() {
    EgnoozTheme {
        Box(Modifier.background(Paper).padding(18.dp)) {
            HeadlineCard(
                item = NewsItem(
                    id = "preview",
                    title = "Club Eastwood prepares to upgrade popular function spaces",
                    url = "https://lakespost.com.au/example",
                    sourceName = "Lakes Post",
                    publishedAt = "2026-11-01T17:00:00+11:00",
                    snippet = "Event organisers across East Gippsland are being encouraged to plan ahead.",
                ),
                onClick = {},
            )
        }
    }
}
