# JumpshotTracker

Real-time basketball shot analysis using computer vision. Tracks joint angles and angular velocity through each shooting motion via webcam, detects shot attempts automatically, and logs biomechanical data for post-session review.

Built with OpenCV, MediaPipe Pose, and NumPy.

---

## What It Does

- Detects your right-arm shooting motion in real time using pose estimation
- Calculates **elbow angle** (shoulder → elbow → wrist) and **wrist angle** (elbow → wrist → index finger) on every frame
- Computes angular velocity at both joints to identify shot release events
- Logs each detected shot with peak velocities, joint position paths, and timestamps
- Plots arm angular velocity across all shots at the end of the session

---

## How It Works

MediaPipe Pose extracts 33 body landmarks from each video frame. The tracker computes joint angles using the dot product formula between adjacent limb vectors, then derives angular velocity frame-over-frame using a rolling window. A shot is detected when elbow angular velocity exceeds a threshold, indicating an explosive upward arm extension and the sequencial movement simalr to a jumpshot.

Shot state flows: `IDLE → IN_SHOT → IDLE`

---

## Tech Stack

| Library | Purpose |
|---|---|
| `opencv-python` | Webcam capture and frame rendering |
| `mediapipe` | Real-time pose landmark detection |
| `numpy` | Joint angle and velocity calculations |
| `matplotlib` | Post-session velocity plots |

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/Ravonte-K/jumpshotTracker.git
cd jumpshotTracker
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run**
```bash
python main.py
```

Press `q` to end the session. A velocity plot for all detected shots will display automatically.

---

## Requirements

- Python 3.9+
- Webcam
- Adequate lighting for pose detection

See `requirements.txt` for exact package versions.

---

## Output

Each detected shot is logged as a dictionary:

```python
{
  "shot_num": 1,
  "timestamp": 1234567890.12,
  "peak_arm_velo": 312.4,       # degrees/second
  "peak_wrist_velo": 95.7,      # degrees/second
  "duration": 0.73,             # seconds
  "elbow_path": [[x, y], ...],  # normalized coordinates per frame
  "wrist_path": [[x, y], ...],
  "arm_velo_frames": [...]      # velocity at each frame during shot
}
```

---

## Planned Features

- [ ] Left-hand shooting support
- [ ] Release angle classification (too flat / optimal / too steep)
- [ ] CSV export for multi-session tracking
- [ ] Follow-through consistency scoring

---

## License

MIT