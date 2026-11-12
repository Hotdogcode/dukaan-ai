package ai.dukaan.core.database

import ai.dukaan.core.database.dao.AppMetadataDao
import ai.dukaan.core.database.entity.AppMetadataEntity
import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config
import java.io.IOException

@RunWith(AndroidJUnit4::class)
@Config(manifest = Config.NONE)
class AppMetadataDaoTest {

    private lateinit var db: DukaanDatabase
    private lateinit var dao: AppMetadataDao

    @Before
    fun createDb() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db = Room.inMemoryDatabaseBuilder(context, DukaanDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = db.appMetadataDao()
    }

    @After
    @Throws(IOException::class)
    fun closeDb() {
        db.close()
    }

    @Test
    fun insertAndGetMetadata() = runTest {
        val entity = AppMetadataEntity(key = "schema_version", value = "1.0.0")
        dao.upsert(entity)

        val retrieved = dao.getByKey("schema_version")
        assertNotNull(retrieved)
        assertEquals("1.0.0", retrieved?.value)
    }

    @Test
    fun deleteMetadata() = runTest {
        val entity = AppMetadataEntity(key = "temp_flag", value = "true")
        dao.upsert(entity)
        dao.deleteByKey("temp_flag")

        val retrieved = dao.getByKey("temp_flag")
        assertNull(retrieved)
    }
}
