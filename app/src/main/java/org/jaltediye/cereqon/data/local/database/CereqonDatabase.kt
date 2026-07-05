package org.jaltediye.cereqon.data.local.database

import androidx.room.Database
import androidx.room.RoomDatabase
import org.jaltediye.cereqon.data.local.dao.CalibrationAttemptDao
import org.jaltediye.cereqon.data.local.dao.ReportDao
import org.jaltediye.cereqon.data.local.dao.SessionDao
import org.jaltediye.cereqon.data.local.dao.WindowSnapshotDao
import org.jaltediye.cereqon.data.local.entity.CalibrationAttemptEntity
import org.jaltediye.cereqon.data.local.entity.ReportEntity
import org.jaltediye.cereqon.data.local.entity.SessionEntity
import org.jaltediye.cereqon.data.local.entity.WindowSnapshotEntity

@Database(
    entities = [
        SessionEntity::class,
        WindowSnapshotEntity::class,
        CalibrationAttemptEntity::class,
        ReportEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class CereqonDatabase : RoomDatabase() {
    abstract fun sessionDao(): SessionDao
    abstract fun windowSnapshotDao(): WindowSnapshotDao
    abstract fun calibrationAttemptDao(): CalibrationAttemptDao
    abstract fun reportDao(): ReportDao

    companion object {
        const val DATABASE_NAME = "cereqon.db"
    }
}
