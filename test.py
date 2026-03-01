import pyautogui
import torch
from huggingface_hub import hf_hub_download
from ultralytics import YOLO


class GUIDetector:
    """
    Captures the screen and runs Salesforce's GPA-GUI-Detector (YOLO fine-tuned
    on GUI elements) to produce detections in the format expected by VisualPlanner.

    Weights are downloaded automatically from HuggingFace on first run.
    """

    _REPO_ID  = "Salesforce/GPA-GUI-Detector"
    _FILENAME = "model.pt"

    def __init__(
        self,
        confidence: float = 0.05,
        imgsz: int = 640,
        iou: float = 0.7,
    ):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        model_path = hf_hub_download(repo_id=self._REPO_ID, filename=self._FILENAME)
        self._model = YOLO(model_path)
        self._confidence = confidence
        self._imgsz = imgsz
        self._iou = iou

    def detect(self) -> list[dict]:
        """Screenshot + GPA-GUI-Detector inference → list of detection dicts."""
        screenshot = pyautogui.screenshot()
        results = self._model.predict(
            source=screenshot,
            conf=self._confidence,
            imgsz=self._imgsz,
            iou=self._iou,
            device=self._device,
            verbose=False,
        )[0]

        detections = []
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            detections.append({
                "label":      results.names[int(box.cls)],
                "confidence": round(float(box.conf), 3),
                "bbox": {
                    "x":      x1,
                    "y":      y1,
                    "width":  x2 - x1,
                    "height": y2 - y1,
                },
            })
        return detections