import cv2
import time
from interfaces.ecal_interface import EcalPublisher
from ADASMulti.img_processing import images
from utils import config


def main():
    # Inicializar cámara
    backend = images.get_optimal_backend()
    cap = cv2.VideoCapture(config.CAMERA_INDEX, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.FPS)

    if not cap.isOpened():
        raise Exception("X-Error: No se pudo abrir la cámara")

    # Inicializar Publisher
    pub = EcalPublisher(
        topic_name=config.TOPIC_NAME,
        descriptor_file="protos/imagen.desc",
        type_name="proto:protocolBuffers.VideoFrame"
    )

    frame_number = 1
    try:
        while True:
            start_time = time.time()

            frame = images.capture_frame(cap)
            msg = images.frame_to_proto(frame, frame_number)

            size = pub.send(msg)
            print(f"[PUB] Frame {frame_number} enviado ({size} bytes)")

            cv2.imshow("Publisher", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_number += 1
            time.sleep(0.033)  # ~30fps

    except KeyboardInterrupt:
        print("\nX-Interrupción por usuario")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pub.close()


if __name__ == "__main__":
    main()