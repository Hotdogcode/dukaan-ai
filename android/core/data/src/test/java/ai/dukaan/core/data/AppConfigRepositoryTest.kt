package ai.dukaan.core.data

import ai.dukaan.core.data.repository.AppConfigRepositoryImpl
import ai.dukaan.core.datastore.UserPreferencesDataSource
import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ThemePreference
import app.cash.turbine.test
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test
import java.util.UUID

class AppConfigRepositoryTest {

    private val userPreferencesDataSource: UserPreferencesDataSource = mockk(relaxed = true)

    @Test
    fun appConfigFlow_emitsUnderlyingDataSourceEmissions() = runTest {
        val expectedConfig = AppConfig(
            selectedBusinessId = UUID.randomUUID(),
            theme = ThemePreference.DARK,
            language = "hi",
            isOnboardingCompleted = true,
        )
        coEvery { userPreferencesDataSource.appConfig } returns flowOf(expectedConfig)

        val repository = AppConfigRepositoryImpl(userPreferencesDataSource)

        repository.appConfig.test {
            val item = awaitItem()
            assertEquals(expectedConfig, item)
            awaitComplete()
        }
    }

    @Test
    fun setSelectedBusinessId_delegatesToDataSource() = runTest {
        val repository = AppConfigRepositoryImpl(userPreferencesDataSource)
        val businessId = UUID.randomUUID()

        repository.setSelectedBusinessId(businessId)

        coVerify(exactly = 1) { userPreferencesDataSource.setSelectedBusinessId(businessId) }
    }

    @Test
    fun setOnboardingCompleted_delegatesToDataSource() = runTest {
        val repository = AppConfigRepositoryImpl(userPreferencesDataSource)

        repository.setOnboardingCompleted(true)

        coVerify(exactly = 1) { userPreferencesDataSource.setOnboardingCompleted(true) }
    }
}
