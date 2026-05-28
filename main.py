import numpy as np
import cv2 as cv
import mediapipe as mp
import matplotlib.pyplot as plt
import time
from collections import deque

angle_history = deque(maxlen=30)
wrist_history = deque(maxlen=30)
prev_time = time.time()
shotLog = []
shotStatus = 'IDLE'
shot_start_time = 0.0
cap = cv.VideoCapture(0)
mp_pose = mp.solutions.pose # type: ignore
mp_draw = mp.solutions.drawing_utils # type: ignore
start_time = time.time()


def getAngle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

def flickSpeed(g, history, dt):
    history.append(g)
    if len(history) >= 2 and dt > 0.001:
        angular_velocity = (history[-1] - history[-2]) / dt
        return float(angular_velocity)

def shotAttempt(wristVelo: float, armVelo: float) -> bool | None:
    if (armVelo >= 250) and (wristVelo >= 80):
        return True
    elif (armVelo < 250 and armVelo > 20) or (wristVelo < 80 and wristVelo > 20):
        return False
    else:
        return None


with mp_pose.Pose() as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            lm = results.pose_landmarks.landmark

            shoulder = [lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow    = [lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist    = [lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            index    = [lm[mp_pose.PoseLandmark.RIGHT_INDEX.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_INDEX.value].y]

            elbow_angle = getAngle(shoulder, elbow, wrist)
            wrist_angle = getAngle(elbow, wrist, index)

            cv.putText(frame, f"Elbow: {int(elbow_angle)}",
                    (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv.putText(frame, f"Wrist: {int(wrist_angle)}",
                    (50, 300), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            now = time.time()
            dt = now - prev_time
            prev_time = now

            if (now - start_time > 2):

                elbowflick = flickSpeed(elbow_angle, angle_history, dt) or 0.0
                wristflick = flickSpeed(wrist_angle, wrist_history, dt) or 0.0

                attempted = shotAttempt(wristflick, elbowflick)

                if attempted == True and shotStatus == 'IDLE':
                    shotStatus = 'IN_SHOT'
                    shot_start_time = now
                    shotLog.append({
                        "shot_num":       len(shotLog) + 1,
                        "peak_arm_velo":  elbowflick,
                        "peak_wrist_velo": wristflick,
                        "timestamp":      now,
                        "elbow_path":     [elbow[:]],
                        "wrist_path":     [wrist[:]],
                        "arm_velo_frames": [elbowflick]
                    })
                    cv.rectangle(frame, (100, 200), (400, 230), (0, 255, 255), -1)

                elif shotStatus == 'IN_SHOT':
                    shotLog[-1]["peak_arm_velo"]    = max(shotLog[-1]["peak_arm_velo"], elbowflick)
                    shotLog[-1]["peak_wrist_velo"]  = max(shotLog[-1]["peak_wrist_velo"], wristflick)
                    shotLog[-1]["elbow_path"].append(elbow[:])
                    shotLog[-1]["wrist_path"].append(wrist[:])
                    shotLog[-1]["arm_velo_frames"].append(elbowflick)
                    cv.rectangle(frame, (100, 200), (400, 230), (0, 255, 255), -1)
                    

                    if (now - shot_start_time) > 0.8:
                        shotLog[-1]["duration"] = now - shot_start_time
                        shotStatus = 'IDLE'
                        print(shotLog[-1])

                elif attempted == False:
                    cv.rectangle(frame, (100, 200), (400, 230), (255, 255, 255), -1)

        cv.imshow('Shot Tracker', frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

if shotLog:
    for shot in shotLog:
        plt.plot(shot["arm_velo_frames"], label=f'Shot {shot["shot_num"]}')
    plt.title("Arm Speed Through Each Shot")
    plt.xlabel("Frame")
    plt.ylabel("Arm Angular Velocity (°/s)")
    plt.legend()
    plt.tight_layout()
    plt.show()
