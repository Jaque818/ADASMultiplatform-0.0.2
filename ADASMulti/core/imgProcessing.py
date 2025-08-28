import cv2
import time
import numpy as np
from core import imagen_pb2
from utils import config


def capture_frame(cap):
    """Lee un frame de la cámara."""
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("X-Error: No se pudo leer el frame")
    return frame


def frame_to_proto(frame, frame_number, quality=config.DEFAULT_QUALITY):
    """Convierte un frame a mensaje protobuf VideoFrame."""
    msg = imagen_pb2.VideoFrame()

    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
    if not success:
        raise ValueError("X-Error al comprimir el frame")

    msg.frame_data = encoded_frame.tobytes()
    msg.width = frame.shape[1]
    msg.height = frame.shape[0]
    msg.channels = frame.shape[2] if len(frame.shape) > 2 else 1
    msg.encoding = "jpg"
    msg.frame_number = frame_number
    msg.timestamp = time.time()
    msg.compression_quality = quality
    msg.is_keyframe = (frame_number % config.KEYFRAME_INTERVAL == 0)

    return msg


def proto_to_frame(msg):
    """Convierte un mensaje protobuf a frame OpenCV."""
    frame_data = np.frombuffer(msg.frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame_data, cv2.IMREAD_GRAYSCALE)
    if frame is None:
        raise ValueError("X-Error al decodificar el frame")
    return frame


def draw_overlay(frame, msg, fps=0, latency=0, lost=0):
    """Dibuja overlays con info del frame."""
    display_frame = frame.copy()

    cv2.putText(display_frame, f"Frame: {msg.frame_number}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Latencia: {latency*1000:.1f} ms", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Lost: {lost}", (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255) if lost > 0 else (0, 255, 0), 2)
    cv2.putText(display_frame, f"Size: {len(msg.frame_data)} bytes", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if msg.is_keyframe:
        cv2.putText(display_frame, "KEYFRAME", (msg.width - 150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return display_frame
