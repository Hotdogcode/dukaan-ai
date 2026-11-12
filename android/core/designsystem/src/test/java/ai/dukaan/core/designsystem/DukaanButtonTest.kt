package ai.dukaan.core.designsystem

import ai.dukaan.core.designsystem.component.DukaanPrimaryButton
import ai.dukaan.core.designsystem.theme.DukaanTheme
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config

@RunWith(AndroidJUnit4::class)
class DukaanButtonTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun primaryButton_displaysTextAndTriggersClick() {
        var clicked = false

        composeTestRule.setContent {
            DukaanTheme {
                DukaanPrimaryButton(
                    text = "Confirm Bill • बिल बनाएं",
                    onClick = { clicked = true },
                )
            }
        }

        composeTestRule
            .onNodeWithText("Confirm Bill • बिल बनाएं")
            .assertIsDisplayed()
            .performClick()

        assertTrue(clicked)
    }
}
