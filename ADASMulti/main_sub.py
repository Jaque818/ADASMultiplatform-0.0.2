import cv2
import time
from interfaces.ecal_interface import EcalSubscriber
from core import img_processing, imagen_pb2
from utils import config


class SubscriberApp:
    def __init__(self):
        self.received_frames = 0
        self.lost_frames = 0
        self.last_frame_number = -1
        self.timestamps = []
        self.last_receive_time = time.time()

    def callback(self, topic_id, data_type_info, receive_data):
        msg = imagen_pb2.VideoFrame()
        msg.ParseFromString(receive_data.buffer)

        self.received_frames += 1
        now = time.time()

        # Latencia
        latency = now - msg.timestamp

        # Detectar frames perdidos
        if self.last_frame_number != -1 and msg.frame_number > self.last_frame_number + 1:
            lost = msg.frame_number - self.last_frame_number - 1
            self.lost_frames += lost
            print(f"*** Frames perdidos: {lost} (total: {self.lost_frames})")

        self.last_frame_number = msg.frame_number

        # Guardar timestamps
        self.timestamps.append(now)
        if len(self.timestamps) > 30:
            self.timestamps.pop(0)

        fps = (len(self.timestamps)-1) / (self.timestamps[-1] - self.timestamps[0]) if len(self.timestamps) > 1 else 0

        # Decodificar frame
        frame = img_processing.proto_to_frame(msg)
        display = img_processing.draw_overlay(frame, msg, fps=fps, latency=latency, lost=self.lost_frames)

        cv2.imshow("Subscriber", display)
        cv2.waitKey(1)

        print(f"[SUB] Frame {msg.frame_number} recibido | Latencia {latency*1000:.1f} ms | FPS {fps:.1f}")


def main():
    app = SubscriberApp()

    sub = EcalSubscriber(
        topic_name=config.TOPIC_NAME,
        descriptor_file="protos/imagen.desc",
        type_name="proto:protocolBuffers.VideoFrame",
        callback=app.callback
    )

    try:
        while True:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nX-Interrupción por usuario")
    finally:
        cv2.destroyAllWindows()
        sub.close()


if __name__ == "__main__":
    main()
