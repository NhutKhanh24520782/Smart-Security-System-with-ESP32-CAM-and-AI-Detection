# Script đăng ký khuôn mặt - Có thể chỉnh sửa tên file ảnh
from ai.detect import FaceRecognitionManager

# 🔄 THAY ĐỔI TÊN FILE ẢNH Ở ĐÂY:
test_image = 'test_image_20260414_200405.jpg'  # ← Thay tên file ảnh muốn đăng ký
person_name = 'Khanh'  # ← Thay tên người

print(f"🔍 Đăng ký khuôn mặt từ ảnh: {test_image}")
print(f"   Tên: {person_name}")
print()

try:
    # Đọc ảnh thành bytes
    with open(test_image, 'rb') as f:
        image_bytes = f.read()

    print(f"📂 Đã đọc ảnh: {len(image_bytes)} bytes")

    # Khởi tạo manager
    manager = FaceRecognitionManager()

    print("📤 Đang upload lên AWS Rekognition...")
    result = manager.register_face(image_bytes, person_name)

    if result['success']:
        print("✅ Đăng ký thành công!")
        print(f"   Face ID: {result.get('face_id', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   Tên: {person_name}")
        print(f"   Message: {result.get('message', '')}")
    else:
        print(f"❌ Đăng ký thất bại: {result.get('message', 'Unknown error')}")

except Exception as e:
    print(f"❌ Lỗi: {str(e)}")
    import traceback
    traceback.print_exc()