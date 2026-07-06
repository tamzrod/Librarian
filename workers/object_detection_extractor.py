"""
Object detection handler for the worker.

Operation Object Detection - YOLOv8n integration.

This module handles the 'object_detection' job type.
It detects objects in images using YOLOv8n and stores the observations.

Engine: YOLOv8n (CPU capable, GPU accelerated if available)
"""

import os
import logging
from pathlib import Path
from typing import Optional
from environment import get_library_root
from .base import BaseWorker

logger = logging.getLogger(__name__)


class ObjectDetectionExtractor(BaseWorker):
    """
    Detects objects in images using YOLOv8n.

    This is a job handler that can be registered with the Worker.
    It handles the 'object_detection' job type.

    Features:
    - YOLOv8n model (lightweight, fast, accurate)
    - CPU capable with GPU acceleration if available
    - Confidence filtering
    - Bounding box extraction
    - Normalized coordinates for cross-resolution compatibility
    """

    # Operation Plugin Foundation: Plugin identity
    PLUGIN_NAME = 'vision.object-detection.yolo'  # Fully qualified namespace
    ENGINE_NAME = 'yolo'                          # Engine identifier
    PLUGIN_VERSION = 'v8n'                        # Plugin version (YOLOv8 nano)

    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    # Minimum confidence threshold
    DEFAULT_CONFIDENCE_THRESHOLD = 0.25

    def __init__(self, backend, library_root: str = None, confidence_threshold: float = None):
        """
        Initialize the object detection extractor.

        Args:
            backend: Storage backend
            library_root: Root path of the document library
            confidence_threshold: Minimum confidence to include detection (0-1)
        """
        self.backend = backend
        self.library_root = library_root or get_library_root()
        self.confidence_threshold = confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD
        self._model = None

    @property
    def model(self):
        """Lazy load the YOLOv8 model."""
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self):
        """
        Load YOLOv8n model.

        Returns:
            YOLOv8 model instance
        """
        try:
            from ultralytics import YOLO
            # Use YOLOv8n (nano) for speed - 'yolov8n.pt' is the smallest/fastest
            model = YOLO('yolov8n.pt')
            logger.info("YOLOv8n model loaded successfully")
            return model
        except ImportError:
            logger.error("ultralytics package not installed. Run: pip install ultralytics")
            raise ImportError(
                "YOLOv8 not available. Install with: pip install ultralytics"
            )

    def process(self, job: dict) -> dict:
        """
        Detect objects in an image document.

        This is the job handler for 'object_detection' jobs.

        Args:
            job: Job dict with document_id and job_type

        Returns:
            Dict with detection results
        """
        document_id = job['document_id']
        job_id = job['id']

        logger.info(f"Starting object detection for document {document_id}")

        try:
            # Get document info
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, path, extension FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                raise ValueError(f"Document {document_id} not found")

            doc_id, doc_path, extension = row

            # Check if file is a supported image type
            if not self._is_supported_image(extension):
                raise ValueError(
                    f"Document {document_id} is not a supported image type: {extension}"
                )

            # Resolve full path
            if os.path.isabs(doc_path):
                full_path = Path(doc_path)
            else:
                full_path = Path(self.library_root) / doc_path

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")

            # Run detection
            detections = self._detect_objects(full_path)

            # Get provenance for Operation Plugin Foundation
            provenance = self.get_provenance(document_id)

            # Reprocessing: Soft-delete existing detections for this artifact
            # This ensures same artifact+plugin+engine replaces observations
            deleted_count = self.backend.delete_detections(document_id)
            if deleted_count > 0:
                logger.info(f"Soft-deleted {deleted_count} existing detections for document {document_id}")

            # Save detections to database
            saved_count = self._save_detections(artifact_id=document_id, detections=detections, provenance=provenance)

            # Transition document status if applicable
            if saved_count > 0:
                try:
                    self.backend.transition_document_status(
                        document_id,
                        'ANALYZED'
                    )
                except ValueError as e:
                    logger.debug(f"State transition skipped: {e}")

            # Log results
            unique_labels = set(d['label'] for d in detections)
            logger.info(
                f"Successfully detected {saved_count} objects "
                f"({len(unique_labels)} unique labels) in document {document_id}"
            )

            return {
                'document_id': document_id,
                'objects_detected': saved_count,
                'unique_labels': list(unique_labels),
                'labels_with_count': {
                    label: sum(1 for d in detections if d['label'] == label)
                    for label in unique_labels
                }
            }

        except Exception as e:
            logger.error(f"Object detection failed for document {document_id}: {e}")
            # Graceful failure: Update document status to failed
            try:
                self.backend.transition_document_status(
                    document_id,
                    'FAILED',
                    job_id=job_id,
                    error_message=str(e)
                )
            except Exception as status_error:
                logger.error(f"Failed to update document status: {status_error}")
            # Return error result instead of raising
            # This allows worker to continue processing other jobs
            return {
                'document_id': document_id,
                'objects_detected': 0,
                'unique_labels': [],
                'labels_with_count': {},
                'error': str(e)
            }

    def _is_supported_image(self, extension: str) -> bool:
        """Check if file extension is a supported image type."""
        if not extension:
            return False
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        return ext in self.SUPPORTED_EXTENSIONS

    def _detect_objects(self, filepath: Path) -> list:
        """
        Detect objects in an image file.

        Args:
            filepath: Path to the image file

        Returns:
            List of detection dicts with label, confidence, and bbox
        """
        try:
            # Run inference
            results = self.model(str(filepath), verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue

                # Get image dimensions for normalization
                img_height, img_width = result.orig_shape

                for box in boxes:
                    # Get confidence
                    confidence = float(box.conf[0])
                    if confidence < self.confidence_threshold:
                        continue

                    # Get class ID and label
                    class_id = int(box.cls[0])
                    label = result.names[class_id]

                    # Get bounding box (XYXY format: x1, y1, x2, y2)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Calculate normalized coordinates
                    norm_x1 = x1 / img_width
                    norm_y1 = y1 / img_height
                    norm_x2 = x2 / img_width
                    norm_y2 = y2 / img_height

                    detections.append({
                        'label': label,
                        'confidence': confidence,
                        'bbox_x1': int(x1),
                        'bbox_y1': int(y1),
                        'bbox_x2': int(x2),
                        'bbox_y2': int(y2),
                        'bbox_norm_x1': round(norm_x1, 6),
                        'bbox_norm_y1': round(norm_y1, 6),
                        'bbox_norm_x2': round(norm_x2, 6),
                        'bbox_norm_y2': round(norm_y2, 6),
                    })

            return detections

        except Exception as e:
            logger.error(f"Error running object detection on {filepath}: {e}")
            raise

    def _save_detections(
        self,
        artifact_id: int,
        detections: list,
        provenance: dict
    ) -> int:
        """Save detections to the database with provenance.

        Args:
            artifact_id: ID of the artifact
            detections: List of detection dicts
            provenance: Provenance dict from get_provenance()

        Returns:
            Number of detections saved
        """
        return self.backend.save_detections(
            artifact_id=artifact_id,
            detections=detections,
            plugin_name=provenance.get('plugin_name', self.PLUGIN_NAME),
            engine_name=provenance.get('engine_name', self.ENGINE_NAME),
            plugin_version=provenance.get('plugin_version', self.PLUGIN_VERSION),
            processed_at=provenance.get('processed_at'),
            artifact_hash=provenance.get('artifact_hash')
        )
