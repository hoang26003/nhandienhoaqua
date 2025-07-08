package com.example.fruitrecognizerv2 // Đảm bảo package name này đúng với dự án của bạn

import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import coil.load
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.IOException

class MainActivity : AppCompatActivity() {

    // #######################################################################
    // ### QUAN TRỌNG: THAY ĐỔI ĐỊA CHỈ IP NÀY CHO ĐÚNG VỚI MÁY TÍNH CỦA BẠN ###
    // #######################################################################
    private val SERVER_URL = "http://192.168.2.102:5000/predict" // Ví dụ IP, hãy thay đổi

    private lateinit var imageView: ImageView
    private lateinit var tvResult: TextView
    private lateinit var btnSelectImage: Button
    private lateinit var btnCaptureImage: Button
    private lateinit var progressBar: ProgressBar

    private var latestTmpUri: Uri? = null
    private val okHttpClient = OkHttpClient()

    // ActivityResultLauncher để chọn ảnh từ thư viện
    private val selectImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let {
            imageView.load(it)
            val bitmap = uriToBitmap(it)
            bitmap?.let { b -> uploadImage(b) }
        }
    }

    // ActivityResultLauncher để chụp ảnh từ camera
    private val takeImageLauncher = registerForActivityResult(ActivityResultContracts.TakePicture()) { isSuccess: Boolean ->
        if (isSuccess) {
            latestTmpUri?.let { uri ->
                imageView.load(uri)
                val bitmap = uriToBitmap(uri)
                bitmap?.let { b -> uploadImage(b) }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Ánh xạ các view từ layout XML
        imageView = findViewById(R.id.imageView)
        tvResult = findViewById(R.id.tvResult)
        btnSelectImage = findViewById(R.id.btnSelectImage)
        btnCaptureImage = findViewById(R.id.btnCaptureImage)
        progressBar = findViewById(R.id.progressBar)

        // Gán sự kiện click cho các nút
        btnSelectImage.setOnClickListener { selectImageLauncher.launch("image/*") }
        btnCaptureImage.setOnClickListener { takeImage() }
    }

    private fun takeImage() {
        getTmpFileUri().let { uri ->
            latestTmpUri = uri
            takeImageLauncher.launch(uri)
        }
    }

    private fun getTmpFileUri(): Uri {
        val tmpFile = File.createTempFile("tmp_image_file", ".png", cacheDir).apply {
            createNewFile()
            deleteOnExit()
        }
        return FileProvider.getUriForFile(this, "${applicationContext.packageName}.provider", tmpFile)
    }

    private fun uriToBitmap(uri: Uri): Bitmap? {
        return try {
            contentResolver.openInputStream(uri)?.use { inputStream ->
                android.graphics.BitmapFactory.decodeStream(inputStream)
            }
        } catch (e: IOException) {
            e.printStackTrace()
            null
        }
    }

    private fun uploadImage(bitmap: Bitmap) {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, stream) // Nén ảnh chất lượng 90%
        val byteArray = stream.toByteArray()

        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart(
                "file", // Phải khớp với key 'file' trong code Python
                "upload.jpg",
                byteArray.toRequestBody("image/jpeg".toMediaTypeOrNull())
            )
            .build()

        val request = Request.Builder().url(SERVER_URL).post(requestBody).build()

        setLoadingState(true)

        // Gửi request bất đồng bộ để không làm treo UI
        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    setLoadingState(false)
                    tvResult.text = "Lỗi kết nối: ${e.message}"
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val responseBody = response.body?.string()
                runOnUiThread {
                    setLoadingState(false)
                    if (response.isSuccessful && responseBody != null) {
                        try {
                            val json = JSONObject(responseBody)
                            if (json.getBoolean("success")) {
                                val prediction = json.getJSONObject("prediction")
                                val className = prediction.getString("class_name")
                                val confidence = prediction.getString("confidence")
                                tvResult.text = "Kết quả: $className\nĐộ tin cậy: $confidence"
                            } else {
                                tvResult.text = "Lỗi từ server: ${json.optString("error", "Không rõ")}"
                            }
                        } catch (e: Exception) {
                            tvResult.text = "Lỗi phân tích JSON."
                        }
                    } else {
                        tvResult.text = "Lỗi server: ${response.code}\n${responseBody}"
                    }
                }
            }
        })
    }

    // Hàm tiện ích để quản lý trạng thái loading của UI
    private fun setLoadingState(isLoading: Boolean) {
        if (isLoading) {
            progressBar.visibility = View.VISIBLE
            tvResult.text = "Đang nhận diện..."
            btnSelectImage.isEnabled = false
            btnCaptureImage.isEnabled = false
        } else {
            progressBar.visibility = View.GONE
            btnSelectImage.isEnabled = true
            btnCaptureImage.isEnabled = true
        }
    }
}