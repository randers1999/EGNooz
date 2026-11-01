package net.krystalbbs.egnooz.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val Ink = Color(0xFF14232E)
val Muted = Color(0xFF4D5C58)
val Paper = Color(0xFFF4EFE4)
val CardFill = Color(0xFFFFFDF8)
val Teal = Color(0xFF1F5C57)
val TealDark = Color(0xFF143C39)
val Warn = Color(0xFF8B2E1A)
val Line = Color(0xFFD9D0C2)
val Ok = Color(0xFF215C38)
val WarnWash = Color(0xFFF6E4DC)
val BannerWash = Color(0xFFEFE4CF)
val OfflineWash = Color(0xFFE4EFE6)

private val EgnoozColours = lightColorScheme(
    primary = Teal,
    onPrimary = Color.White,
    secondary = TealDark,
    onSecondary = Color.White,
    background = Paper,
    onBackground = Ink,
    surface = CardFill,
    onSurface = Ink,
    surfaceVariant = BannerWash,
    onSurfaceVariant = Muted,
    outline = Line,
    error = Warn,
    onError = Color.White,
)

@Composable
fun EgnoozTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = EgnoozColours,
        content = content,
    )
}
