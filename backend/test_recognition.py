# Script test nhận diện khuôn mặt - Có thể chỉnh sửa tên file ảnh
from ai.detect import FaceRecognitionManager

# 🔄 THAY ĐỔI TÊN FILE ẢNH Ở ĐÂY:
test_image = 'test_image_20260414_192344.jpg'  # ← Thay tên file ảnh muốn test

print(f"🔍 Test nhận diện khuôn mặt với ảnh: {test_image}")
print()

try:
    # Đọc ảnh thành bytes (để test trực tiếp)
    with open(test_image, 'rb') as f:
        image_bytes = f.read()

    print(f"📂 Đã đọc ảnh: {len(image_bytes)} bytes")

    # Test nhận diện
    manager = FaceRecognitionManager()
    result = manager.detect_and_recognize_faces(image_bytes)

    print("\n📊 Kết quả nhận diện:")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Confidence: {result.get('confidence', 'N/A')}%")

    if 'faces' in result:
        print(f"   Số khuôn mặt phát hiện: {len(result['faces'])}")
        for i, face in enumerate(result['faces']):
            print(f"     Face {i+1}: {face.get('name', 'Unknown')} ({face.get('confidence', 0):.1f}%)")

    if 'alert_message' in result:
        print(f"   Alert: {result['alert_message']}")

except Exception as e:
    print(f"❌ Lỗi: {str(e)}")
    import traceback
    traceback.print_exc()