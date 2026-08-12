import time
from time import sleep

import cv2
import dxcam
import numpy as np


camera = None
running = False


def _get_camera():
    global camera
    if camera is None:
        camera = dxcam.create()
    return camera


def generate_frames():
    # создаём камеру
    global running
    camera = _get_camera()

    if not running:
    # Запускаем захват в режиме видео на частоте 120 фпс
    # В режиме video_mode=True DXcam всегда записывает экран
    # Если было бы video_mode=False
        camera.start(target_fps=120, video_mode=False)
        running = True

    try:
        while True:
            # 1. Захват кадра из памяти видеокарты (занимает < 1 мс)
            frame = camera.get_latest_frame()
            if frame is None:
                # Если новый кадр на экране еще не отрисовался, не тратим ресурсы
                time.sleep(0.001)
                continue

            # ПРИМЕЧАНИЕ: DXcam выдает кадр в формате RGB.
            # OpenCV для корректных цветов требует BGR.
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 2. Быстрый ресайз в 2 раза (из Full HD делаем 960x540)
            # На слабом ПК обработка уменьшенного кадра экономит до 70% ресурсов процессора
            low_res = cv2.resize(frame_bgr, (0, 0), fx=0.75, fy=0.75, interpolation=cv2.INTER_NEAREST)

            # 3. Быстрое сжатие в JPEG в байты (качество 60% — баланс веса и четкости)
            success, encoded_img = cv2.imencode('.jpg', low_res, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            jpg_bytes = encoded_img.tobytes()

            yield (b'--frame\r\n' # b'' это байтовые string, он нужен потому что мы не можем склеить обычный string с байтами
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')

    except GeneratorExit:
        pass


    except Exception as e:
        print(e)
    finally:
        # Обязательно останавливаем поток захвата видеокарты при выходе
        if camera is not None:
            camera.stop()
            sleep(0.3)
            running = False
            try:
                del camera
            except:
                pass
            camera = None
