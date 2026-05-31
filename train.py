"""
DermaLens AI — HAM10000 Training Script
Fine-tunes MobileNetV2 on the HAM10000 dermoscopy dataset.

Usage:
    python train.py --data_dir /path/to/HAM10000 --epochs 30 --batch_size 32

HAM10000 Download:
    https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T
    kaggle datasets download -d kmader/skin-lesion-analysis-toward-melanoma-detection
"""

import os
import argparse
import json
import time
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torchvision.transforms as transforms

# Import model from backend
import sys
sys.path.insert(0, str(Path(__file__).parent / "backend"))
from main import DermaLensModel

# ─── Config ───────────────────────────────────────────────────────────────────
LABEL_MAP = {
    "nv":    0, "mel":   1, "bkl":   2,
    "bcc":   3, "akiec": 4, "vasc":  5, "df": 6,
}
CLASS_NAMES = list(LABEL_MAP.keys())
CLASS_DISPLAY = [
    "Melanocytic Nevi", "Melanoma", "Benign Keratosis",
    "Basal Cell Carcinoma", "Actinic Keratosis", "Vascular Lesion", "Dermatofibroma"
]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")


# ─── Dataset ──────────────────────────────────────────────────────────────────
class HAM10000Dataset(Dataset):
    """
    HAM10000 dermoscopy dataset loader.

    Expected structure after downloading:
        data_dir/
            HAM10000_metadata.csv
            HAM10000_images_part1/   (or just images/)
            HAM10000_images_part2/
    """

    # HAM10000 channel statistics (precomputed)
    MEAN = [0.7630, 0.5456, 0.5700]
    STD  = [0.1409, 0.1523, 0.1692]

    TRAIN_TRANSFORMS = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15, hue=0.05),
        transforms.RandomRotation(degrees=30),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=MEAN, std=STD),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.1)),
    ])

    VAL_TRANSFORMS = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=MEAN, std=STD),
    ])

    def __init__(self, df: pd.DataFrame, img_dirs: list, transform=None):
        self.df       = df.reset_index(drop=True)
        self.img_dirs = [Path(d) for d in img_dirs]
        self.transform = transform

    def _find_image(self, image_id: str) -> Path:
        for d in self.img_dirs:
            for ext in (".jpg", ".jpeg", ".png"):
                p = d / f"{image_id}{ext}"
                if p.exists():
                    return p
        raise FileNotFoundError(f"Image not found: {image_id}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row   = self.df.iloc[idx]
        img_p = self._find_image(row["image_id"])
        image = Image.open(img_p).convert("RGB")
        label = LABEL_MAP[row["dx"]]
        if self.transform:
            image = self.transform(image)
        return image, label


# ─── Loss ─────────────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    """Focal loss for class-imbalanced HAM10000."""
    def __init__(self, gamma=2.0, weight=None):
        super().__init__()
        self.gamma  = gamma
        self.weight = weight

    def forward(self, logits, targets):
        ce   = nn.functional.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt   = torch.exp(-ce)
        loss = ((1 - pt) ** self.gamma) * ce
        return loss.mean()


# ─── Training ─────────────────────────────────────────────────────────────────
def compute_class_weights(labels):
    counts = Counter(labels)
    total  = len(labels)
    weights = torch.tensor([total / (7 * counts[i]) for i in range(7)], dtype=torch.float)
    return weights


def train_epoch(model, loader, optimizer, criterion, scaler, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()

        with torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
            logits = model(imgs)
            loss   = criterion(logits, labels)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item() * imgs.size(0)
        preds       = logits.argmax(dim=1)
        correct    += (preds == labels).sum().item()
        total      += imgs.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def val_epoch(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []

    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        logits = model(imgs)
        loss   = criterion(logits, labels)

        total_loss += loss.item() * imgs.size(0)
        preds       = logits.argmax(dim=1)
        correct    += (preds == labels).sum().item()
        total      += imgs.size(0)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    return total_loss / total, correct / total, all_preds, all_labels


def plot_confusion_matrix(y_true, y_pred, save_path: Path):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=CLASS_DISPLAY, yticklabels=CLASS_DISPLAY, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("DermaLens Confusion Matrix — HAM10000 Test Set")
    plt.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved confusion matrix → {save_path}")


def plot_training_curves(history: dict, save_path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, key, title in zip(axes, ["loss", "acc"], ["Loss", "Accuracy"]):
        ax.plot(history[f"train_{key}"], label="Train")
        ax.plot(history[f"val_{key}"], label="Val")
        ax.set_title(title); ax.set_xlabel("Epoch"); ax.legend()
    plt.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved training curves → {save_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main(args):
    data_dir  = Path(args.data_dir)
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    # Load metadata
    csv_path = data_dir / "HAM10000_metadata.csv"
    if not csv_path.exists():
        csv_path = data_dir / "hmnist_28_28_RGB.csv"
    assert csv_path.exists(), f"Metadata CSV not found in {data_dir}"

    df = pd.read_csv(csv_path)
    print(f"Dataset: {len(df)} total images")
    print(df["dx"].value_counts())

    # Deduplicate by lesion_id (keep one image per lesion)
    if "lesion_id" in df.columns:
        df = df.drop_duplicates(subset="lesion_id", keep="first")
        print(f"After dedup by lesion_id: {len(df)} images")

    # Train / val / test split (stratified)
    train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df["dx"], random_state=42)
    val_df, test_df   = train_test_split(temp_df, test_size=0.5, stratify=temp_df["dx"], random_state=42)
    print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    # Image directories
    img_dirs = [
        data_dir / "HAM10000_images_part1",
        data_dir / "HAM10000_images_part2",
        data_dir / "images",
        data_dir,
    ]

    # Datasets
    train_ds = HAM10000Dataset(train_df, img_dirs, HAM10000Dataset.TRAIN_TRANSFORMS)
    val_ds   = HAM10000Dataset(val_df,   img_dirs, HAM10000Dataset.VAL_TRANSFORMS)
    test_ds  = HAM10000Dataset(test_df,  img_dirs, HAM10000Dataset.VAL_TRANSFORMS)

    # Weighted sampler for class imbalance
    class_counts = Counter(train_df["dx"].map(LABEL_MAP).tolist())
    sample_weights = [1.0 / class_counts[LABEL_MAP[dx]] for dx in train_df["dx"]]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                              num_workers=args.num_workers, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False,
                              num_workers=args.num_workers, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False,
                              num_workers=args.num_workers, pin_memory=True)

    # Model
    model = DermaLensModel(num_classes=7, dropout=0.3).to(DEVICE)

    # Class weights for focal loss
    train_labels = [LABEL_MAP[dx] for dx in train_df["dx"]]
    class_weights = compute_class_weights(train_labels).to(DEVICE)
    criterion = FocalLoss(gamma=2.0, weight=class_weights)

    # Optimizer with layer-wise learning rates
    optimizer = optim.AdamW([
        {"params": model.features[:15].parameters(),  "lr": args.lr * 0.01},
        {"params": model.features[15:].parameters(),  "lr": args.lr * 0.1},
        {"params": model.classifier.parameters(),     "lr": args.lr},
        {"params": [model.temperature],               "lr": args.lr * 0.01},
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    scaler    = torch.cuda.amp.GradScaler(enabled=(DEVICE.type == "cuda"))

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val_acc = 0.0
    patience_counter = 0

    print(f"\n{'='*60}")
    print(f"Training DermaLens MobileNetV2 on HAM10000")
    print(f"Epochs: {args.epochs} | Batch: {args.batch_size} | Device: {DEVICE}")
    print(f"{'='*60}\n")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        tr_loss, tr_acc = train_epoch(model, train_loader, optimizer, criterion, scaler, DEVICE)
        vl_loss, vl_acc, vl_preds, vl_labels = val_epoch(model, val_loader, criterion, DEVICE)
        scheduler.step()

        history["train_loss"].append(tr_loss)
        history["train_acc"].append(tr_acc)
        history["val_loss"].append(vl_loss)
        history["val_acc"].append(vl_acc)

        elapsed = time.time() - t0
        print(f"Ep {epoch:3d}/{args.epochs} │ "
              f"Train Loss {tr_loss:.4f} Acc {tr_acc*100:.1f}% │ "
              f"Val Loss {vl_loss:.4f} Acc {vl_acc*100:.1f}% │ "
              f"{elapsed:.0f}s")

        if vl_acc > best_val_acc:
            best_val_acc = vl_acc
            patience_counter = 0
            save_path = model_dir / "dermalens_mobilenetv2.pth"
            torch.save(model.state_dict(), save_path)
            print(f"  ✓ New best val acc {vl_acc*100:.2f}% — saved to {save_path}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\nEarly stopping after {epoch} epochs (patience={args.patience})")
                break

    # ── Final evaluation ──
    print(f"\n{'='*60}")
    print("Final Test Set Evaluation")
    print(f"{'='*60}")

    # Load best model
    best_model = DermaLensModel(num_classes=7)
    best_model.load_state_dict(torch.load(model_dir / "dermalens_mobilenetv2.pth", map_location=DEVICE))
    best_model.to(DEVICE)

    _, test_acc, test_preds, test_labels = val_epoch(best_model, test_loader, criterion, DEVICE)
    print(f"\nTest Accuracy: {test_acc*100:.2f}%")
    print("\nPer-class Report:")
    print(classification_report(test_labels, test_preds, target_names=CLASS_DISPLAY))

    # Plots
    plot_confusion_matrix(test_labels, test_preds, model_dir / "confusion_matrix.png")
    plot_training_curves(history, model_dir / "training_curves.png")

    # Save training history
    with open(model_dir / "training_history.json", "w") as f:
        json.dump({**history, "best_val_acc": best_val_acc, "test_acc": test_acc}, f, indent=2)

    print(f"\n✅ Training complete. Best val acc: {best_val_acc*100:.2f}% | Test acc: {test_acc*100:.2f}%")
    print(f"Model saved to: {model_dir / 'dermalens_mobilenetv2.pth'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DermaLens on HAM10000")
    parser.add_argument("--data_dir",    type=str, required=True,  help="Path to HAM10000 dataset directory")
    parser.add_argument("--epochs",      type=int, default=30,     help="Number of training epochs")
    parser.add_argument("--batch_size",  type=int, default=32,     help="Batch size")
    parser.add_argument("--lr",          type=float, default=1e-3, help="Base learning rate")
    parser.add_argument("--patience",    type=int, default=8,      help="Early stopping patience")
    parser.add_argument("--num_workers", type=int, default=4,      help="DataLoader workers")
    args = parser.parse_args()
    main(args)
