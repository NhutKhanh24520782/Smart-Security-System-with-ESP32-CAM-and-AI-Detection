import boto3
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from config import (
    AI_METHOD, CONFIDENCE_THRESHOLD, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY,
    AWS_FACE_COLLECTION_ID, AWS_FACE_MATCH_THRESHOLD, AWS_FACE_SIMILARITY_THRESHOLD,
    AWS_KNOWN_FACES_DB, AWS_UNKNOWN_FACES_DIR
)

logger = logging.getLogger(__name__)


class FaceRecognitionManager:
    """
    AWS Rekognition-based face detection and recognition manager.
    Supports face detection, recognition against known faces, and person management.
    """

    def __init__(self):
        self.method = AI_METHOD
        self.collection_id = AWS_FACE_COLLECTION_ID
        self.match_threshold = AWS_FACE_MATCH_THRESHOLD
        self.similarity_threshold = AWS_FACE_SIMILARITY_THRESHOLD
        self.known_faces_db_path = AWS_KNOWN_FACES_DB
        self.unknown_faces_dir = AWS_UNKNOWN_FACES_DIR

        if self.method == 'aws':
            self._init_aws()
            self._init_directories()
            self._load_known_faces_db()
        else:
            raise ValueError(f"Unsupported AI method: {self.method}")

    def _init_aws(self):
        """Initialize AWS Rekognition client"""
        try:
            self.rekognition = boto3.client(
                'rekognition',
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY
            )
            logger.info("AWS Rekognition client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Rekognition: {str(e)}")
            raise

    def _init_directories(self):
        """Create necessary directories for unknown face storage"""
        try:
            Path(self.unknown_faces_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Directories initialized: {self.unknown_faces_dir}")
        except Exception as e:
            logger.error(f"Failed to create directories: {str(e)}")

    def _load_known_faces_db(self):
        """Load known faces database from local JSON file"""
        try:
            if os.path.exists(self.known_faces_db_path):
                with open(self.known_faces_db_path, 'r') as f:
                    self.known_faces = json.load(f)
                logger.info(f"Loaded {len(self.known_faces)} known faces from database")
            else:
                self.known_faces = {}
                logger.info("Known faces database not found, starting with empty database")
        except Exception as e:
            logger.error(f"Failed to load known faces database: {str(e)}")
            self.known_faces = {}

    def _save_known_faces_db(self):
        """Save known faces database to local JSON file"""
        try:
            with open(self.known_faces_db_path, 'w') as f:
                json.dump(self.known_faces, f, indent=2)
            logger.info("Known faces database saved")
        except Exception as e:
            logger.error(f"Failed to save known faces database: {str(e)}")

    def detect_and_recognize_faces(self, image_bytes):
        """
        Detect faces in image and recognize if they match known faces.

        Args:
            image_bytes: Raw image bytes (JPEG)

        Returns:
            dict: {
                "human_detected": bool,
                "faces": [
                    {"status": "KNOWN", "name": str, "confidence": float, "bbox": dict},
                    {"status": "UNKNOWN", "confidence": float, "bbox": dict}
                ]
            }
        """
        try:
            result = {
                "human_detected": False,
                "faces": []
            }

            # Step 1: Detect faces in image
            faces_data = self._detect_faces(image_bytes)
            if not faces_data or len(faces_data) == 0:
                logger.info("No faces detected in image")
                return result

            result["human_detected"] = True
            logger.info(f"Detected {len(faces_data)} face(s)")

            # Step 2: Try to recognize each face
            for i, face in enumerate(faces_data):
                face_confidence = face['Confidence']
                bbox = self._extract_bbox(face['BoundingBox'])

                # Try to match against known faces in collection
                match_result = self._search_face_in_collection(image_bytes, face)

                if match_result and match_result['status'] == 'KNOWN':
                    result["faces"].append({
                        "status": "KNOWN",
                        "name": match_result['name'],
                        "confidence": face_confidence,
                        "bbox": bbox
                    })
                    logger.info(f"Face {i+1}: KNOWN - {match_result['name']}")
                else:
                    result["faces"].append({
                        "status": "UNKNOWN",
                        "confidence": face_confidence,
                        "bbox": bbox
                    })
                    logger.info(f"Face {i+1}: UNKNOWN")

                    # Save unknown face for review
                    self._save_unknown_face(image_bytes, i, face_confidence)

            return result

        except Exception as e:
            logger.error(f"Error in face detection and recognition: {str(e)}")
            return {"human_detected": False, "faces": [], "error": str(e)}

    def _detect_faces(self, image_bytes):
        """
        Detect faces in image using AWS Rekognition.

        Args:
            image_bytes: Raw image bytes

        Returns:
            list: List of face data with confidence and bounding boxes
        """
        try:
            response = self.rekognition.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['DEFAULT']
            )
            return response.get('FaceDetails', [])
        except Exception as e:
            logger.error(f"AWS detect_faces error: {str(e)}")
            return []

    def _extract_bbox(self, bounding_box):
        """
        Extract bounding box coordinates.

        Args:
            bounding_box: AWS bounding box data

        Returns:
            dict: {x, y, width, height}
        """
        return {
            'x': bounding_box.get('Left', 0),
            'y': bounding_box.get('Top', 0),
            'width': bounding_box.get('Width', 0),
            'height': bounding_box.get('Height', 0)
        }

    def _search_face_in_collection(self, image_bytes, face):
        """
        Search for face in known faces collection.

        Args:
            image_bytes: Raw image bytes
            face: Face data from detect_faces response

        Returns:
            dict: {"status": "KNOWN", "name": str, "similarity": float} or None
        """
        try:
            # First, try searching the collection for similar faces
            response = self.rekognition.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=self.similarity_threshold
            )

            if response.get('FaceMatches') and len(response['FaceMatches']) > 0:
                match = response['FaceMatches'][0]
                confidence = match['Similarity']
                face_id = match['Face']['FaceId']

                # Look up name from database
                if face_id in self.known_faces:
                    name = self.known_faces[face_id]['name']
                    logger.info(f"Face matched: {name} (confidence: {confidence}%)")
                    return {
                        "status": "KNOWN",
                        "name": name,
                        "similarity": confidence
                    }

            logger.info("No matching face found in collection")
            return None

        except self.rekognition.exceptions.InvalidParameterException:
            # Collection doesn't exist or is empty
            logger.warning("Face collection not initialized or empty")
            return None
        except Exception as e:
            logger.error(f"Error searching face in collection: {str(e)}")
            return None

    def _save_unknown_face(self, image_bytes, face_index, confidence):
        """
        Save unknown face image to local storage for later review.

        Args:
            image_bytes: Raw image bytes
            face_index: Index of face in image
            confidence: Face detection confidence
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_face_{face_index}_conf_{confidence:.0f}.jpg"
            filepath = os.path.join(self.unknown_faces_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            logger.info(f"Unknown face saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save unknown face: {str(e)}")

    # ==================== Person Management Functions ====================

    def create_collection(self):
        """
        Create a face collection for storing known faces.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if collection already exists
            try:
                self.rekognition.describe_collection(CollectionId=self.collection_id)
                logger.info(f"Collection '{self.collection_id}' already exists")
                return True
            except self.rekognition.exceptions.ResourceNotFoundException:
                pass

            # Create new collection
            response = self.rekognition.create_collection(CollectionId=self.collection_id)
            logger.info(f"Collection created: {self.collection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            return False

    def register_face(self, image_bytes, person_name):
        """
        Register a new face/person to the known faces collection.

        Args:
            image_bytes: Raw image bytes (JPEG)
            person_name: Name of the person

        Returns:
            dict: {"success": bool, "face_id": str, "message": str}
        """
        try:
            # First, index the face in the collection
            response = self.rekognition.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                QualityFilter='AUTO'
            )

            if response.get('FaceRecords') and len(response['FaceRecords']) > 0:
                face_id = response['FaceRecords'][0]['Face']['FaceId']
                confidence = response['FaceRecords'][0]['FaceDetail']['Confidence']

                # Store in local database
                self.known_faces[face_id] = {
                    'name': person_name,
                    'registered_at': datetime.now().isoformat(),
                    'confidence': confidence
                }
                self._save_known_faces_db()

                logger.info(f"Face registered for {person_name}: {face_id} (confidence: {confidence})")
                return {
                    "success": True,
                    "face_id": face_id,
                    "message": f"Successfully registered {person_name}",
                    "confidence": confidence
                }
            else:
                return {
                    "success": False,
                    "message": "No face detected in image"
                }

        except Exception as e:
            logger.error(f"Failed to register face: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    def remove_face(self, face_id):
        """
        Remove a face from the collection and local database.

        Args:
            face_id: AWS FaceId to remove

        Returns:
            bool: True if successful
        """
        try:
            self.rekognition.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=[face_id]
            )

            if face_id in self.known_faces:
                name = self.known_faces[face_id]['name']
                del self.known_faces[face_id]
                self._save_known_faces_db()
                logger.info(f"Face removed for {name}")
            else:
                logger.warning(f"Face {face_id} not found in local database")

            return True

        except Exception as e:
            logger.error(f"Failed to remove face: {str(e)}")
            return False

    def list_known_faces(self):
        """
        List all known faces in the collection.

        Returns:
            dict: {face_id: {"name": str, "registered_at": str}}
        """
        return self.known_faces.copy()

    def get_person_by_name(self, person_name):
        """
        Get face_id by person name.

        Args:
            person_name: Name of the person

        Returns:
            str: face_id or None
        """
        for face_id, data in self.known_faces.items():
            if data['name'].lower() == person_name.lower():
                return face_id
        return None

    def rename_person(self, face_id, new_name):
        """
        Rename a person in the known faces database.

        Args:
            face_id: AWS FaceId
            new_name: New name for the person

        Returns:
            bool: True if successful
        """
        try:
            if face_id in self.known_faces:
                old_name = self.known_faces[face_id]['name']
                self.known_faces[face_id]['name'] = new_name
                self._save_known_faces_db()
                logger.info(f"Renamed: {old_name} -> {new_name}")
                return True
            else:
                logger.warning(f"Face {face_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to rename person: {str(e)}")
            return False

    def get_collection_stats(self):
        """
        Get statistics about the face collection.

        Returns:
            dict: Collection statistics
        """
        try:
            response = self.rekognition.describe_collection(CollectionId=self.collection_id)
            return {
                "collection_id": self.collection_id,
                "face_count": response.get('FaceCount', 0),
                "creation_timestamp": response.get('CreationTimestamp'),
                "known_faces_in_db": len(self.known_faces)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}


# ==================== Global Instance ====================
detector = None

def init_detector():
    """Initialize the global detector instance"""
    global detector
    if detector is None:
        detector = FaceRecognitionManager()
    return detector


def detect_and_recognize_faces(image_bytes):
    """
    Convenience function to detect and recognize faces in image.

    Args:
        image_bytes: Raw image bytes

    Returns:
        dict: Detection result with faces info
    """
    global detector
    if detector is None:
        detector = init_detector()
    return detector.detect_and_recognize_faces(image_bytes)


def register_face(image_bytes, person_name):
    """Register a new face to the collection"""
    global detector
    if detector is None:
        detector = init_detector()
    return detector.register_face(image_bytes, person_name)


def remove_face(face_id):
    """Remove a face from the collection"""
    global detector
    if detector is None:
        detector = init_detector()
    return detector.remove_face(face_id)


def list_known_faces():
    """List all known faces"""
    global detector
    if detector is None:
        detector = init_detector()
    return detector.list_known_faces()


def get_collection_stats():
    """Get collection statistics"""
    global detector
    if detector is None:
        detector = init_detector()
    return detector.get_collection_stats()