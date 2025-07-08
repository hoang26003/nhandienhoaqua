# backend_server.py

import os
import cv2
import numpy as np
import tensorflow as tf
from flask import Flask, request, jsonify

# --- KHỞI TẠO ỨNG DỤNG FLASK ---
app = Flask(__name__)

# --- CẤU HÌNH VÀ TẢI MODEL (Chỉ tải 1 lần khi server khởi động) ---
MODEL_PATH = "mobilenetv2_fruit.keras"  # Đảm bảo tên file này chính xác
INPUT_SIZE = (160, 160)
CLASS_NAMES = []
MODEL = None


def load_model_and_classes():
    """Tải model và danh sách class từ thư mục."""
    global MODEL, CLASS_NAMES
    try:
        # Tải model Keras
        print(f"[*] Đang tải model từ: {MODEL_PATH}...")
        MODEL = tf.keras.models.load_model(MODEL_PATH)
        print(f"[*] Model '{MODEL_PATH}' đã được tải thành công.")

        # Tải danh sách class từ cấu trúc thư mục
        class_path = os.path.join("input_images", "input_images")
        if os.path.exists(class_path):
            CLASS_NAMES = sorted(os.listdir(class_path))
            print(f"[*] Đã tìm thấy {len(CLASS_NAMES)} class: {CLASS_NAMES}")
        else:
            print(f"[!] CẢNH BÁO: Không tìm thấy thư mục class tại '{class_path}'")

    except Exception as e:
        print(f"[!] LỖI NGHIÊM TRỌNG KHI TẢI MODEL: {e}")
        MODEL = None


# --- CÁC HÀM XỬ LÝ ẢNH VÀ DỰ ĐOÁN ---
def preprocess_image(image_bytes):
    """Đọc và tiền xử lý ảnh từ chuỗi bytes mà Android gửi lên."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Không thể decode ảnh từ dữ liệu được gửi.")

    # Tiền xử lý để phù hợp với model MobileNetV2
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, INPUT_SIZE)
    img_array = np.array(img_resized, dtype=np.float32)
    # Chuẩn hóa pixel về khoảng [-1, 1]
    img_array = (img_array / 127.5) - 1.0
    return np.expand_dims(img_array, axis=0)


def predict(image_bytes):
    """Thực hiện dự đoán từ dữ liệu ảnh dạng bytes."""
    if MODEL is None or not CLASS_NAMES:
        return "Lỗi Server: Model chưa sẵn sàng", 0.0

    preprocessed_img = preprocess_image(image_bytes)
    prediction = MODEL.predict(preprocessed_img)[0]

    class_index = np.argmax(prediction)
    confidence = float(prediction[class_index] * 100)
    class_name = CLASS_NAMES[class_index].capitalize()
    return class_name, confidence


# --- ĐỊNH NGHĨA API ENDPOINT ---
@app.route('/predict', methods=['POST'])
def handle_prediction():
    """Endpoint nhận ảnh và trả về kết quả dự đoán."""
    if 'file' not in request.files:
        return jsonify({'error': 'Yêu cầu thiếu file ảnh'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'File được gửi không có tên'}), 400

    try:
        image_bytes = file.read()
        class_name, confidence = predict(image_bytes)

        result = {
            'success': True,
            'prediction': {
                'class_name': class_name,
                'confidence': f"{confidence:.2f}%"
            }
        }
        return jsonify(result)
    except Exception as e:
        print(f"[!] Lỗi khi xử lý ảnh: {e}")
        return jsonify({'error': f'Lỗi phía server: {str(e)}'}), 500


# --- CHẠY SERVER ---
if __name__ == '__main__':
    # Tải model ngay khi khởi động
    load_model_and_classes()

    if MODEL is not None:
        # Chạy server, lắng nghe trên tất cả các địa chỉ IP của máy
        print("\n[*] Server sẵn sàng nhận yêu cầu tại http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)  # Đặt debug=False để ổn định hơn
    else:
        print("\n[!] Server không thể khởi động do lỗi tải model.")