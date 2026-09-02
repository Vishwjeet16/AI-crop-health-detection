"""
Train the CropGuard AI detection model.

This script has NOT been run — building and running it needs a GPU and a
prepared dataset, neither of which this sandbox has. Run it yourself:

    # Local machine with a GPU:
    cd ml/training
    pip install ultralytics
    python train.py --epochs 100 --model yolov8s.pt

    # Google Colab (free GPU, easiest path if you don't own one):
    # 1. Upload ml/ to a Colab session (or clone the repo there).
    # 2. Runtime -> Change runtime type -> GPU.
    # 3. !pip install ultralytics
    # 4. !python ml/training/train.py --epochs 100

Before running this, ml/dataset/yolo_format/ must exist with images/ and
labels/ in YOLO format — see ml/dataset/prepare_dataset.py and
ml/dataset/README.md.
"""

import argparse
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
DATA_YAML = THIS_DIR / "data.yaml"
OUTPUT_WEIGHTS = THIS_DIR.parent.parent / "backend" / "models" / "cropguard-yolo.pt"


def main():
    parser = argparse.ArgumentParser(description="Train the CropGuard AI YOLO detector.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Base checkpoint to fine-tune from. yolov8n.pt (nano) is fastest to "
        "iterate with; yolov8s.pt or yolov8m.pt trade speed for accuracy once the "
        "pipeline is validated end-to-end.",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(
            "ultralytics isn't installed. Run: pip install ultralytics\n"
            "(It's commented out in backend/requirements.txt until this stage "
            "is actually run, to keep the demo-mode install lightweight.)"
        ) from e

    if not DATA_YAML.exists():
        raise SystemExit(
            f"{DATA_YAML} not found, or the dataset it points to hasn't been "
            "prepared yet. Run ml/dataset/prepare_dataset.py first — see "
            "ml/dataset/README.md."
        )

    model = YOLO(args.model)
    results = model.train(
        data=str(DATA_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(THIS_DIR / "runs"),
        name="cropguard",
    )

    # Copy the best checkpoint to where ai_service.py expects it.
    best = Path(results.save_dir) / "weights" / "best.pt"
    OUTPUT_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_WEIGHTS.write_bytes(best.read_bytes())
    print(f"\nTraining complete. Best weights copied to {OUTPUT_WEIGHTS}")
    print("Set AI_MODE=production in backend/.env to start using it.")


if __name__ == "__main__":
    main()
