import boto3
client = boto3.client('rekognition', region_name='us-east-1')
try:
    client.create_collection(CollectionId='family_faces')
    print("✅ OK: Đã tạo kho 'family_faces' thành công!")
except client.exceptions.ResourceAlreadyExistsException:
    print("ℹ️ Kho đã tồn tại rồi, không cần tạo mới.")
except Exception as e:
    print(f"❌ Lỗi: {e}")
