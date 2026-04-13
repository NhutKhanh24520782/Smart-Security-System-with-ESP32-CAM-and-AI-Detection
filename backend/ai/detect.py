import cv2
import numpy as np
import boto3
import logging
from config import AI_METHOD, CONFIDENCE_THRESHOLD, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY

logger = logging.getLogger(__name__)

class HumanDetector:
    def __init__(self):
        self.method = AI_METHOD
        if self.method == 'opencv':
            self._init_opencv()
        elif self.method == 'aws':
            self._init_aws()

    def _init_opencv(self):
        """Initialize OpenCV Haar cascade classifier for human detection"""
        # Load Haar cascade for full body detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # Alternative: Haar cascade for upper body
        # self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')

        logger.info("OpenCV human detector initialized")

    def _init_aws(self):
        """Initialize AWS Rekognition client"""
        self.rekognition = boto3.client(
            'rekognition',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        logger.info("AWS Rekognition human detector initialized")

    def detect_human(self, image_bytes):
        """
        Detect if a human is present in the image

        Args:
            image_bytes: Raw image bytes (JPEG)

        Returns:
            tuple: (is_human_detected, confidence_score)
        """
        try:
            if self.method == 'opencv':
                return self._detect_opencv(image_bytes)
            elif self.method == 'aws':
                return self._detect_aws(image_bytes)
            else:
                logger.error(f"Unknown AI method: {self.method}")
                return False, 0.0
        except Exception as e:
            logger.error(f"Error in human detection: {str(e)}")
            return False, 0.0

    def _detect_opencv(self, image_bytes):
        """Detect human using OpenCV HOG descriptor"""
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            logger.error("Failed to decode image")
            return False, 0.0

        # Detect people using HOG
        boxes, weights = self.hog.detectMultiScale(
            image,
            winStride=(8, 8),
            padding=(32, 32),
            scale=1.05
        )

        if len(boxes) > 0:
            # Use the highest confidence detection
            max_confidence = max(weights) if len(weights) > 0 else 0.0
            is_detected = max_confidence >= CONFIDENCE_THRESHOLD
            logger.info(f"OpenCV detection: {len(boxes)} boxes, max confidence: {max_confidence}")
            return is_detected, float(max_confidence)
        else:
            return False, 0.0

    def _detect_aws(self, image_bytes):
        """Detect human using AWS Rekognition"""
        try:
            response = self.rekognition.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=CONFIDENCE_THRESHOLD * 100  # AWS uses percentage
            )

            # Check for person/human labels
            human_labels = ['Person', 'Human', 'People']
            max_confidence = 0.0

            for label in response['Labels']:
                if label['Name'] in human_labels:
                    confidence = label['Confidence'] / 100.0  # Convert to 0-1 scale
                    max_confidence = max(max_confidence, confidence)

            is_detected = max_confidence >= CONFIDENCE_THRESHOLD
            logger.info(f"AWS detection: confidence: {max_confidence}")
            return is_detected, max_confidence

        except Exception as e:
            logger.error(f"AWS Rekognition error: {str(e)}")
            return False, 0.0

# Global detector instance
detector = HumanDetector()

def detect_human(image_bytes):
    """
    Convenience function to detect human in image

    Args:
        image_bytes: Raw image bytes

    Returns:
        tuple: (is_human_detected, confidence)
    """
    return detector.detect_human(image_bytes)