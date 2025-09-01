import cv2
import time
import queue
import platform
from interfaces.ecal_interface import EcalSubscriber
from core import imagen_pb2
from ADASMulti.img_processing import images
from utils import config


class SubscriberApp:
    def __init__(self):
        self.received_frames = 0
        self.lost_frames = 0
        self.last_frame_number = -1
        self.timestamps = []
        self.frame_queue = queue.Queue(maxsize=1)
        self.running = True

    def setup_environment(self):
        """Configuración específica por SO"""
        if platform.system() == "Linux":
            import os
            # Forzar X11 en Linux para evitar problemas con Wayland
            os.environ['QT_QPA_PLATFORM'] = 'xcb'
            print("✓ Configurado para X11 en Linux")

    def callback(self, topic_id, data_type_info, receive_data):
        """Callback ejecutado en el thread de eCAL"""
        try:
            msg = imagen_pb2.VideoFrame()
            msg.ParseFromString(receive_data.buffer)

            now = time.time()
            latency = now - msg.timestamp

            # Detectar frames perdidos (thread-safe)
            lost = 0
            current_frame = msg.frame_number
            if self.last_frame_number != -1 and current_frame > self.last_frame_number + 1:
                lost = current_frame - self.last_frame_number - 1

            # Preparar datos para el thread principal
            frame_data = {
                'msg': msg,
                'latency': latency,
                'lost': lost,
                'timestamp': now,
                'frame_number': current_frame
            }

            # Mantener solo el frame más reciente
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            self.frame_queue.put_nowait(frame_data)

            # Actualizar contadores (en el callback thread)
            self.lost_frames += lost
            self.last_frame_number = current_frame
            self.received_frames += 1

        except Exception as e:
            print(f"Error en callback: {e}")

    def process_frames(self):
        """Procesamiento en el thread principal"""
        lost_total = 0

        while self.running:
            try:
                frame_data = self.frame_queue.get(timeout=0.1)

                msg = frame_data['msg']
                latency = frame_data['latency']
                lost = frame_data['lost']
                lost_total += lost

                # Calcular FPS
                self.timestamps.append(frame_data['timestamp'])
                if len(self.timestamps) > 30:
                    self.timestamps.pop(0)

                fps = (len(self.timestamps) - 1) / (self.timestamps[-1] - self.timestamps[0]) if len(
                    self.timestamps) > 1 else 0

                # Procesar y mostrar frame
                frame = images.proto_to_frame(msg)
                display = images.draw_overlay(frame, msg, fps=fps,
                                              latency=latency, lost=lost_total)

                cv2.imshow("Subscriber", display)

                # Salir con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False

                print(f"[SUB] Frame {frame_data['frame_number']} | "
                      f"Latencia {latency * 1000:.1f}ms | FPS {fps:.1f} | "
                      f"Perdidos: {lost_total}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error procesando frame: {e}")

    def stop(self):
        self.running = False


def main():
    app = SubscriberApp()
    app.setup_environment()  # Configurar entorno según SO

    sub = EcalSubscriber(
        topic_name=config.TOPIC_NAME,
        descriptor_file="protos/imagen.desc",
        type_name="proto:protocolBuffers.VideoFrame",
        callback=app.callback
    )

    try:
        app.process_frames()
    except KeyboardInterrupt:
        print("\nInterrupción por usuario")
    finally:
        app.stop()
        cv2.destroyAllWindows()
        sub.close()


if __name__ == "__main__":
    main()