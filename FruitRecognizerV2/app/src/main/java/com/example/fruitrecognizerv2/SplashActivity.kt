package com.example.fruitrecognizerv2 // Đảm bảo package name này đúng với dự án của bạn

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity

@SuppressLint("CustomSplashScreen")
class SplashActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Liên kết Activity này với file layout activity_splash.xml
        setContentView(R.layout.activity_splash)

        // Tìm nút trong layout bằng ID của nó
        val getStartedButton: Button = findViewById(R.id.btnGetStarted)

        // Gán sự kiện click cho nút
        getStartedButton.setOnClickListener {
            // Tạo một Intent để mở MainActivity
            val intent = Intent(this, MainActivity::class.java)
            startActivity(intent)

            // Đóng SplashActivity lại để người dùng không thể quay lại nó
            finish()
        }
    }
}