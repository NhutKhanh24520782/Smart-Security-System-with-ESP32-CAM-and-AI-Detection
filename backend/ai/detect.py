import boto3
import logging
from config import AI_METHOD, CONFIDENCE_THRESHOLD, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY

logger = logging.getLogger(__name__)

class HumanDetector:
    def __init__(self):
        self.method = AI_METHOD
        if self.method == 'aws':
            self._init_aws()
        else:
            raise ValueError(f"Unsupported AI method: {self.method}")

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
            if self.method == 'aws':
                return self._detect_aws(image_bytes)
            else:
                logger.error(f"Unknown AI method: {self.method}")
                return False, 0.0
        except Exception as e:
            logger.error(f"Error in human detection: {str(e)}")
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