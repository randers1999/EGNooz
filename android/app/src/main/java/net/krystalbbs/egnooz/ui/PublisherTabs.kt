package net.krystalbbs.egnooz.ui

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.browser.customtabs.CustomTabColorSchemeParams
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.graphics.toColorInt

object PublisherTabs {
    private val toolbarColor = "#1F5C57".toColorInt()

    fun open(context: Context, url: String) {
        val uri = Uri.parse(url)
        if (uri.scheme != "http" && uri.scheme != "https") return
        val colourScheme = CustomTabColorSchemeParams.Builder()
            .setToolbarColor(toolbarColor)
            .build()
        val customTabs = CustomTabsIntent.Builder()
            .setShowTitle(true)
            .setShareState(CustomTabsIntent.SHARE_STATE_ON)
            .setDefaultColorSchemeParams(colourScheme)
            .setUrlBarHidingEnabled(true)
            .build()
        customTabs.intent.putExtra(
            Intent.EXTRA_REFERRER,
            Uri.parse("android-app://${context.packageName}"),
        )
        try {
            customTabs.launchUrl(context, uri)
        } catch (_: ActivityNotFoundException) {
            val fallback = Intent(Intent.ACTION_VIEW, uri).addCategory(Intent.CATEGORY_BROWSABLE)
            context.startActivity(fallback)
        }
    }
}
