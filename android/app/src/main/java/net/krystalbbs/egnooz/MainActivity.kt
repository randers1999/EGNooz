package net.krystalbbs.egnooz

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import net.krystalbbs.egnooz.ui.EditionScreen
import net.krystalbbs.egnooz.ui.EditionViewModel
import net.krystalbbs.egnooz.ui.EgnoozTheme
import net.krystalbbs.egnooz.ui.Paper

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val previewUnpublished =
            BuildConfig.DEBUG && intent.getBooleanExtra(EXTRA_PREVIEW_UNPUBLISHED, false)
        setContent {
            EgnoozTheme {
                Surface(
                    modifier = Modifier
                        .fillMaxSize()
                        .safeDrawingPadding(),
                    color = Paper,
                ) {
                    val viewModel: EditionViewModel = viewModel(
                        factory = EditionViewModel.factory(
                            cacheDir = filesDir,
                            editionUrl = BuildConfig.EDITION_URL,
                            previewUnpublished = previewUnpublished,
                        ),
                    )
                    EditionScreen(viewModel)
                }
            }
        }
    }

    companion object {
        const val EXTRA_PREVIEW_UNPUBLISHED = "preview_unpublished"
    }
}
