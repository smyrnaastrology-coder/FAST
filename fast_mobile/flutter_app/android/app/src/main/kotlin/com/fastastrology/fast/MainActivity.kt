package com.fastastrology.fast

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.StandardIntegrityManager
import com.google.android.play.core.integrity.StandardIntegrityManager.PrepareIntegrityTokenRequest
import com.google.android.play.core.integrity.StandardIntegrityManager.StandardIntegrityTokenRequest

class MainActivity : FlutterActivity() {
    private val channel = "com.fastastrology.fast/play_integrity"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel).setMethodCallHandler { call, result ->
            if (call.method == "requestToken") {
                val project = (call.argument<String>("cloudProjectNumber") ?: "").toLongOrNull()
                if (project == null) {
                    result.error("ARG", "cloudProjectNumber gerekli", null)
                    return@setMethodCallHandler
                }
                requestToken(project, call.argument<String>("requestHash"), result)
            } else {
                result.notImplemented()
            }
        }
    }

    private fun requestToken(projectNumber: Long, requestHash: String?, result: MethodChannel.Result) {
        try {
            val manager = IntegrityManagerFactory.createStandard(applicationContext)
            val prepareRequest = PrepareIntegrityTokenRequest.builder()
                .setCloudProjectNumber(projectNumber)
                .build()
            manager.prepareIntegrityToken(prepareRequest)
                .addOnSuccessListener { provider ->
                    val tokenRequestBuilder = StandardIntegrityTokenRequest.builder()
                    if (!requestHash.isNullOrEmpty()) {
                        tokenRequestBuilder.setRequestHash(requestHash)
                    }
                    provider.request(tokenRequestBuilder.build())
                        .addOnSuccessListener { response -> result.success(response.token()) }
                        .addOnFailureListener { e -> result.error("TOKEN", e.message, null) }
                }
                .addOnFailureListener { e -> result.error("PREPARE", e.message, null) }
        } catch (e: Exception) {
            result.error("INIT", e.message, null)
        }
    }
}
