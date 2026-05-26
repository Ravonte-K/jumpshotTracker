import numpy as np
import cv2 as cv
import mediapipe as mp
import time
from collections import deque

angle_history = deque(maxlen=30)
wrist_history = deque(maxlen=30)
prev_time = time.time()
veloTrack = []
wristVeloTrack = []
cap = cv.VideoCapture(0)
mp_pose = mp.solutions.pose # type: ignore
mp_draw = mp.solutions.drawing_utils # type: ignore

start_time = time.time()


def getAngle(a, b,c):
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

def armFlickReg(velo: float):
    if velo >= 250:
        veloTrack.append(float(velo))
        return veloTrack

def wristFlickReg(velo: float):
    if velo >= 40:
        wristVeloTrack.append(float(velo))
        print(wristresult)
        return wristVeloTrack
    

with mp_pose.Pose() as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            lm = results.pose_landmarks.landmark
            # Example: elbow angle (shoulder → elbow → wrist)
            shoulder = [lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow    = [lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist    = [lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                        lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            index = [lm[mp_pose.PoseLandmark.RIGHT_INDEX.value].x,
                    lm[mp_pose.PoseLandmark.RIGHT_INDEX.value].y]
            
            elbow_angle = getAngle(shoulder, elbow, wrist)
            # fix this

            wrist_angle = getAngle(elbow, wrist, index)  # angle at wrist between forearm → wrist → finger


            # Overlay on frame
            cv.putText(frame, f"Elbow: {int(elbow_angle)}",
                    (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv.putText(frame, f"wrist: {int(wrist_angle)}",
                    (50, 300), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            


            now = time.time()
            dt = now - prev_time
            prev_time = now

            if (now - start_time > 2):

                elbowflick = flickSpeed(elbow_angle, angle_history, dt) or 0.0
                wristflick = flickSpeed(wrist_angle, wrist_history, dt) or 0.0

                armresult = armFlickReg(elbowflick)
                if armresult is not None:
                    cv.putText(frame, f"Arm: {armresult}",
                        (50, 200), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv.rectangle(frame, (100, 200), (400, 230), (0, 0, 255), -1)

                wristresult = wristFlickReg(wristflick)
                if wristresult is not None:
                    cv.putText(frame, f"Wrist: {wristresult}",
                        (50, 250), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv.rectangle(frame, (200, 300), (400, 230), (255, 0, 0), -1)

            



        cv.imshow('Shot Tracker', frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break