"""
OCR module for extracting text from images.

Supports PaddleOCR as primary engine with Tesseract fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from inception.config import get_config


@dataclass
class TextBox:
    """A detected text region with bounding box."""
    
    text: str
    confidence: float
    
    # Bounding box (normalized 0-1 coordinates)
    x0: float
    y0: float
    x1: float
    y1: float
    
    # Pixel coordinates (for reference)
    px_x0: int = 0
    px_y0: int = 0
    px_x1: int = 0
    px_y1: int = 0
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)


@dataclass
class OCRResult:
    """Result of OCR on an image."""
    
    image_path: Path
    text_boxes: list[TextBox] = field(default_factory=list)
    
    # Image dimensions
    width: int = 0
    height: int = 0
    
    # Processing info
    engine: str = "paddleocr"
    processing_time_seconds: float = 0.0
    
    @property
    def full_text(self) -> str:
        """Get full text from all boxes, ordered by position."""
        # Sort by y position, then x position
        sorted_boxes = sorted(self.text_boxes, key=lambda b: (b.y0, b.x0))
        return "\n".join(box.text for box in sorted_boxes)
    
    @property
    def avg_confidence(self) -> float:
        if not self.text_boxes:
            return 0.0
        return sum(b.confidence for b in self.text_boxes) / len(self.text_boxes)
    
    def get_text_in_region(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> list[TextBox]:
        """Get text boxes that overlap with a region."""
        result = []
        for box in self.text_boxes:
            # Check overlap
            if box.x0 < x1 and box.x1 > x0 and box.y0 < y1 and box.y1 > y0:
                result.append(box)
        return result


class OCREngine:
    """
    OCR engine with PaddleOCR primary and Tesseract fallback.
    """
    
    def __init__(
        self,
        engine: str | None = None,
        languages: list[str] | None = None,
        use_gpu: bool = False,
    ):
        """
        Initialize the OCR engine.
        
        Args:
            engine: OCR engine ('paddleocr' or 'tesseract')
            languages: Languages to detect
            use_gpu: Whether to use GPU acceleration
        """
        config = get_config()
        
        self.engine = engine or config.ocr.engine
        self.languages = languages or config.ocr.languages
        self.use_gpu = use_gpu or config.ocr.use_gpu
        
        self._paddle_ocr = None
        self._tesseract_available = None
    
    def _get_paddle_ocr(self):
        """Lazy-load PaddleOCR."""
        if self._paddle_ocr is None:
            from paddleocr import PaddleOCR
            
            lang = "en"
            if self.languages:
                # Map common language codes
                lang_map = {
                    "en": "en",
                    "zh": "ch",
                    "ja": "japan",
                    "ko": "korean",
                    "de": "german",
                    "fr": "french",
                }
                lang = lang_map.get(self.languages[0], "en")
            
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=self.use_gpu,
                show_log=False,
            )
        
        return self._paddle_ocr
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available
    
    def recognize(
        self,
        image_path: Path | str,
        preprocess: bool = True,
    ) -> OCRResult:
        """
        Perform OCR on an image.
        
        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image for better OCR
        
        Returns:
            OCRResult with detected text boxes
        """
        import time
        
        image_path = Path(image_path)
        start_time = time.time()
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        height, width = image.shape[:2]
        
        # Preprocess if requested
        if preprocess:
            image = self._preprocess_image(image)
        
        # Try PaddleOCR first
        text_boxes = []
        engine_used = self.engine
        
        try:
            if self.engine == "paddleocr":
                text_boxes = self._run_paddle_ocr(image, width, height)
            elif self.engine == "tesseract":
                text_boxes = self._run_tesseract(image, width, height)
            else:
                # Default to PaddleOCR
                text_boxes = self._run_paddle_ocr(image, width, height)
        except Exception as e:
            # Fallback to Tesseract if available
            if self._check_tesseract():
                text_boxes = self._run_tesseract(image, width, height)
                engine_used = "tesseract"
            else:
                raise RuntimeError(f"OCR failed: {e}")
        
        processing_time = time.time() - start_time
        
        return OCRResult(
            image_path=image_path,
            text_boxes=text_boxes,
            width=width,
            height=height,
            engine=engine_used,
            processing_time_seconds=processing_time,
        )
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Adaptive threshold for better text contrast
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        
        # Convert back to BGR for PaddleOCR
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def _run_paddle_ocr(
        self,
        image: np.ndarray,
        width: int,
        height: int,
    ) -> list[TextBox]:
        """Run PaddleOCR on image."""
        ocr = self._get_paddle_ocr()
        results = ocr.ocr(image, cls=True)
        
        text_boxes = []
        
        if results and results[0]:
            for line in results[0]:
                if len(line) >= 2:
                    box_points = line[0]
                    text_info = line[1]
                    
                    text = text_info[0]
                    confidence = text_info[1]
                    
                    # Extract bounding box (4 points)
                    xs = [p[0] for p in box_points]
                    ys = [p[1] for p in box_points]
                    
                    px_x0 = int(min(xs))
                    px_y0 = int(min(ys))
                    px_x1 = int(max(xs))
                    px_y1 = int(max(ys))
                    
                    text_box = TextBox(
                        text=text,
                        confidence=confidence,
                        x0=px_x0 / width,
                        y0=px_y0 / height,
                        x1=px_x1 / width,
                        y1=px_y1 / height,
                        px_x0=px_x0,
                        px_y0=px_y0,
                        px_x1=px_x1,
                        px_y1=px_y1,
                    )
                    text_boxes.append(text_box)
        
        return text_boxes
    
    def _run_tesseract(
        self,
        image: np.ndarray,
        width: int,
        height: int,
    ) -> list[TextBox]:
        """Run Tesseract OCR on image."""
        import pytesseract
        
        # Get detailed output
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
        )
        
        text_boxes = []
        
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            
            if text and conf > 0:
                px_x0 = data["left"][i]
                px_y0 = data["top"][i]
                px_x1 = px_x0 + data["width"][i]
                px_y1 = px_y0 + data["height"][i]
                
                text_box = TextBox(
                    text=text,
                    confidence=conf / 100.0,
                    x0=px_x0 / width,
                    y0=px_y0 / height,
                    x1=px_x1 / width,
                    y1=px_y1 / height,
                    px_x0=px_x0,
                    px_y0=px_y0,
                    px_x1=px_x1,
                    px_y1=px_y1,
                )
                text_boxes.append(text_box)
        
        return text_boxes


def ocr_image(
    image_path: Path | str,
    engine: str | None = None,
) -> OCRResult:
    """
    Convenience function to OCR an image.
    
    Args:
        image_path: Path to image file
        engine: Optional engine override
    
    Returns:
        OCRResult
    """
    ocr_engine = OCREngine(engine=engine)
    return ocr_engine.recognize(image_path)


def ocr_keyframes(
    keyframe_paths: list[Path],
    engine: str | None = None,
    parallel: bool = True,
) -> list[OCRResult]:
    """
    OCR multiple keyframes.
    
    Args:
        keyframe_paths: List of keyframe image paths
        engine: Optional engine override
        parallel: Whether to process in parallel
    
    Returns:
        List of OCRResult objects
    """
    ocr_engine = OCREngine(engine=engine)
    
    if parallel:
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(ocr_engine.recognize, keyframe_paths))
    else:
        results = [ocr_engine.recognize(path) for path in keyframe_paths]
    
    return results


def merge_duplicate_boxes(
    boxes: list[TextBox],
    iou_threshold: float = 0.5,
) -> list[TextBox]:
    """
    Merge duplicate text boxes based on IoU overlap.
    
    Args:
        boxes: List of text boxes
        iou_threshold: IoU threshold for merging
    
    Returns:
        Merged list of text boxes
    """
    if not boxes:
        return []
    
    # Sort by confidence
    boxes = sorted(boxes, key=lambda b: b.confidence, reverse=True)
    
    merged = []
    used = set()
    
    for i, box in enumerate(boxes):
        if i in used:
            continue
        
        merged.append(box)
        used.add(i)
        
        for j in range(i + 1, len(boxes)):
            if j in used:
                continue
            
            # Check IoU
            iou = _compute_iou(box, boxes[j])
            if iou > iou_threshold:
                used.add(j)
    
    return merged


def _compute_iou(box1: TextBox, box2: TextBox) -> float:
    """Compute Intersection over Union for two boxes."""
    x0 = max(box1.x0, box2.x0)
    y0 = max(box1.y0, box2.y0)
    x1 = min(box1.x1, box2.x1)
    y1 = min(box1.y1, box2.y1)
    
    if x1 <= x0 or y1 <= y0:
        return 0.0
    
    intersection = (x1 - x0) * (y1 - y0)
    area1 = box1.width * box1.height
    area2 = box2.width * box2.height
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0
