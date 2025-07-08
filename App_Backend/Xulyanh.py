import os
import cv2
import numpy as np

# Cắt ảnh vuông từ giữa
def crop_center_square(image):
    h, w = image.shape[:2]
    min_dim = min(h, w)
    start_x = (w - min_dim) // 2
    start_y = (h - min_dim) // 2
    return image[start_y:start_y + min_dim, start_x:start_x + min_dim]

# Resize ảnh về 160x160
def resize_image(image, size=(160, 160)):
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)

# Làm nét ảnh
def sharpen_image(image):
    kernel = np.array([
        [0, -1,  0],
        [-1, 5, -1],
        [0, -1,  0]
    ])
    return cv2.filter2D(image, -1, kernel)

# Phát hiện ảnh có quả (dựa vào màu HSV)
def contains_fruit(image, color_threshold=5000):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    fruit_colors = [
        ((0, 70, 50), (10, 255, 255)),    # Đỏ
        ((20, 100, 100), (30, 255, 255)), # Vàng
        ((35, 50, 50), (85, 255, 255)),   # Xanh lá
        ((10, 100, 20), (20, 255, 255)),  # Cam
    ]
    mask = sum(cv2.inRange(hsv, np.array(low), np.array(high)) for low, high in fruit_colors)
    fruit_pixels = cv2.countNonZero(mask)
    return fruit_pixels > color_threshold

# Xử lý ảnh trong thư mục
def process_images_in_directory(input_root, output_root):
    folder_counters = {}

    for root, dirs, files in os.walk(input_root):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                input_path = os.path.join(root, file)

                image = cv2.imread(input_path)
                if image is None:
                    print(f" Không thể đọc ảnh: {input_path}")
                    continue

                if not contains_fruit(image):
                    print(f" Không có quả, bỏ qua: {file}")
                    continue

                image = crop_center_square(image)
                image = resize_image(image)
                image = sharpen_image(image)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Tính đường dẫn tương đối từ input_root
                rel_dir = os.path.relpath(root, input_root)
                folder_name = os.path.basename(rel_dir)

                if folder_name == '.':
                    folder_name = 'root'

                # Tăng số thứ tự trong thư mục này
                count = folder_counters.get(root, 1)
                folder_counters[root] = count + 1

                # Đặt tên ảnh theo "folder_name (số).jpg"
                new_filename = f"{folder_name} ({count}).jpg"
                output_subdir = os.path.join(output_root, rel_dir)
                os.makedirs(output_subdir, exist_ok=True)
                output_path = os.path.join(output_subdir, new_filename)

                cv2.imwrite(output_path, image_rgb)
                print(f" Đã xử lý: {output_path}")

# Thư mục nguồn và đích
input_root = "input_images"
output_root = "output_images"
os.makedirs(output_root, exist_ok=True)

process_images_in_directory(input_root, output_root)
