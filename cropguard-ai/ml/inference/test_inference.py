"""
Quick sanity check for a trained model — run this before flipping
AI_MODE=production, so a bad training run doesn't surface first inside a
live demo.

    cd ml/inference
    python test_inference.py --image /path/to/leaf.jpg
"""

import argparse
from pathlib import Path

WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent / "backend" / "models" / "cropguard-yolo.pt"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to a test image.")
    parser.add_argument("--weights", default=str(WEIGHTS_PATH))
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold to display.")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit("Run: pip install ultralytics") from e

    weights = Path(args.weights)
    if not weights.exists():
        raise SystemExit(f"No weights found at {weights}. Train a model first (ml/training/train.py).")

    model = YOLO(str(weights))
    results = model(args.image, conf=args.conf)[0]

    if not results.boxes:
        print("No detections above the confidence threshold — image looks healthy, or the model isn't confident.")
        return

    print(f"{len(results.boxes)} detection(s):\n")
    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        print(f"  {label:20s}  confidence={conf:.2f}  box=({x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f})")


if __name__ == "__main__":
    main()