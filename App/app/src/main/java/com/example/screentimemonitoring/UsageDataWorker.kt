package com.example.screentimemonitoring

import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.util.Log
import android.app.NotificationChannel
import android.app.NotificationManager
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException


class UsageDataWorker(appContext: Context, workerParams: WorkerParameters) :
    CoroutineWorker(appContext, workerParams) {

    companion object {
        // Deklarasi TAG statis, digunakan di seluruh kelas
        private const val TAG = "WorkerDebug"
    }

    override suspend fun doWork(): Result {
        Log.d(TAG, "Worker Started: Checking access and running task.")

        if (!hasUsageAccess()) {
            Log.e(TAG, "Worker Failed: Usage Access not granted. Returning FAILURE.")
            return Result.failure()
        }

        return try {
            // 1. Ambil data penggunaan dari sistem
            val (jsonArray, totalScreenTimeSeconds) = getUsageStats()

            // 2. Kirim data ke server
            sendDataToServer(jsonArray, totalScreenTimeSeconds)

            // 3. Berhasil
            Log.d(TAG, "Worker SUCCEEDED: Data sent to server.")
            Result.success()
        } catch (e: Exception) {
            // 4. Gagal (termasuk kegagalan jaringan/server)
            Log.e(TAG, "Worker FAILED (Network/Logic Error): ${e.message}", e)
            e.printStackTrace()
            // WorkManager akan mencoba lagi (retry)
            Result.retry()
        }
    }
    private fun hasUsageAccess(): Boolean {
        val appOps =
            applicationContext.getSystemService(Context.APP_OPS_SERVICE) as android.app.AppOpsManager
        val mode = appOps.checkOpNoThrow(
            android.app.AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            applicationContext.packageName
        )
        return mode == android.app.AppOpsManager.MODE_ALLOWED
    }
    private fun getUsageStats(): Pair<JSONArray, Long> {
        val usageStatsManager =
            applicationContext.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val endTime = System.currentTimeMillis()
        val startTime = endTime - 1000 * 60 * 60 * 24

        val usageStatsList: List<UsageStats> = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_BEST,
            startTime,
            endTime
        )

        val usageMap = mutableMapOf<String, Long>()
        var totalScreenTimeSeconds: Long = 0
        for (usage in usageStatsList) {
            val totalSec = usage.totalTimeInForeground / 1000
            if (totalSec > 0) {
                usageMap[usage.packageName] = (usageMap[usage.packageName] ?: 0) + totalSec
                totalScreenTimeSeconds += totalSec
            }
        }

        val jsonArray = JSONArray()
        val pm = applicationContext.packageManager
        val top10 = usageMap.entries.sortedByDescending { it.value }.take(10)

        for ((pkg, totalSec) in top10) {
            val appName = try {
                pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString()
            } catch (e: Exception) {
                pkg
            }

            val jsonObj = JSONObject()
            jsonObj.put("package", pkg)
            jsonObj.put("app_name", appName)
            jsonObj.put("foreground_time_s", totalSec.toInt())
            jsonArray.put(jsonObj)
        }
        return Pair(jsonArray, totalScreenTimeSeconds)
    }
    private fun showNotification(message: String) {
        val channelId = "usage_monitor_channel"
        val notificationManager =
            applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Buat channel untuk Android 8 ke atas
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Usage Monitor Alerts",
                NotificationManager.IMPORTANCE_HIGH
            )
            notificationManager.createNotificationChannel(channel)
        }

        val notification =
            NotificationCompat.Builder(applicationContext, channelId)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setContentTitle("Peringatan Penggunaan Layar")
                .setContentText(message)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .build()

        notificationManager.notify(1, notification)
    }
    @Throws(IOException::class)
    private fun sendDataToServer(jsonArray: JSONArray, totalScreenTimeSeconds: Long) {
        val finalPayload = JSONObject()
        finalPayload.put("total_screen_time_s", totalScreenTimeSeconds)
        finalPayload.put("usage_data", jsonArray)

        val client = OkHttpClient()
        val mediaType = "application/json; charset=utf-8".toMediaType()
        val body = finalPayload.toString().toRequestBody(mediaType)
        val fullUrl = "${ServerConfig.BASE_URL}/receive_usage"

        val request = Request.Builder()
            .url(fullUrl)
            .post(body)
            .build()

        client.newCall(request).execute().use { response ->

            val responseBody = response.body?.string()
            Log.d(TAG, "Response: code=${response.code}, body=$responseBody")

            if (!response.isSuccessful) {
                throw IOException("HTTP FAILED: ${response.code}")
            }

            if (responseBody != null) {
                val json = JSONObject(responseBody)
                val message = json.optString("message", "")

                if (message.isNotEmpty()) {
                    showNotification(message)
                }
            }
        }
    }
}