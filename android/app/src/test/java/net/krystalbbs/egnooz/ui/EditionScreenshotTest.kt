package net.krystalbbs.egnooz.ui

import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.Paparazzi
import net.krystalbbs.egnooz.data.EditionJson
import org.junit.Rule
import org.junit.Test

class EditionScreenshotTest {
    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_6,
        theme = "android:Theme.Material.Light.NoActionBar",
        showSystemUi = false,
        maxPercentDifference = 0.5,
    )

    @Test
    fun publishedEdition() {
        val edition = EditionJson.parse(
            javaClass.getResource("/fixtures/latest.json")!!.readText(),
        )
        paparazzi.snapshot("published-edition") {
            EgnoozTheme {
                EditionContent(
                    state = EditionUiState(
                        loading = false,
                        edition = edition,
                        todayPublished = true,
                    ),
                    onRefresh = {},
                    onOpenUrl = {},
                )
            }
        }
    }

    @Test
    fun notPublishedYet() {
        paparazzi.snapshot("not-published-yet") {
            EgnoozTheme {
                EditionContent(
                    state = EditionUiState(
                        loading = false,
                        banner = BannerKind.NOT_PUBLISHED,
                    ),
                    onRefresh = {},
                    onOpenUrl = {},
                )
            }
        }
    }
}
