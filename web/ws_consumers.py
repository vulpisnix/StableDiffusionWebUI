import datetime
import threading
import time
from base64 import b64encode
from io import BytesIO
from queue import Queue, Empty
import random
from time import sleep

import torch
import os
from diffusers import DiffusionPipeline

from channels.generic.websocket import JsonWebsocketConsumer
from SDWebUI.settings import BASE_DIR, MEDIA_ROOT

import web.hgf_utility as hgf_utility

queue = Queue()
sdQueueThread = None

WS_Create = []
CURRENT_PROCESS = {
    'steps': 0,
    'step': 0,
    'percent': 0,
    'timestep': 0
}
class WSConsumer_Create(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        print("WS connected")
        WS_Create.append(self)

        '''
        def file_progress(filename, percent):
            print(f"[{filename}] {percent}%")

        def global_progress(done, total, percent):
            print(f"Gesamt: {done}/{total} Dateien ({percent}%)")

        downloader = hgf_utility.PipelineDownloader("Qwen/Qwen-Image")

        downloader.download_all(
            callback_file=file_progress,
            callback_global=global_progress
        )
        '''

    def disconnect(self, code):
        print('WS disconnected', f"Code: {code}")
        WS_Create.remove(self)

    def receive_json(self, content, **kwargs):
        global sdQueueThread
        event = content['event']
        data = content['data']

        if event == 'create':
            queue.put(data)
            if sdQueueThread is None:
                sdQueueThread = SDQueueThread()
                sdQueueThread.start()


class SDQueueThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "SDQueueThread"
        self.do_run = True

    def run(self):
        global queue, CURRENT_PROCESS
        while self.do_run:
            try:
                print(f"{self.name} Working on queue..")
                data = queue.get()
                if torch.cuda.is_available():
                    torch_dtype = torch.bfloat16
                    device = "cuda"
                else:
                    torch_dtype = torch.float32
                    device = "cpu"

                # Execute SD
                settings = data["settings"]
                img2img = data["img2img"] if 'img2img' in data else None

                start_time = time.time()

                def progress_callback(step: int, timestep: int, latents):
                    total_steps = pipe.scheduler.num_inference_steps
                    elapsed = time.time() - start_time
                    steps_done = step + 1
                    percent = int(steps_done / total_steps * 100)

                    avg_time = elapsed / steps_done

                    remaining = (total_steps - steps_done) * avg_time
                    eta = time.strftime("%H:%M:%S", time.gmtime(remaining))

                    CURRENT_PROCESS = {
                        'steps': total_steps,
                        'step': step,
                        'percent': percent,
                        'timestep': f"{timestep}",
                        "eta": eta
                    }
                    socket_payload_p = {
                        'event': 'progress',
                        'data': CURRENT_PROCESS
                    }
                    for socket_p in WS_Create:
                        socket_p.send_json(socket_payload_p)

                pipe = DiffusionPipeline.from_pretrained(settings["model"], torch_dtype=torch_dtype, cache_dir=os.path.join(BASE_DIR, 'sd_model_cache'))
                pipe = pipe.to(device)

                seed = settings["seed"] if settings["seed"] != -1 else random.randint(0, 2 ** 32 - 1)

                print(f"Seed: {seed}")

                image = pipe(
                    prompt=settings["prompt"],
                    negative_prompt=settings["negative"] + " nsfw",
                    width=settings["width"],
                    height=settings["height"],
                    num_inference_steps=settings["steps"],
                    true_cfg_scale=settings["cfg"],
                    generator=torch.Generator(device="cuda").manual_seed(seed),
                    callback=progress_callback,
                    callback_steps=1
                ).images[0]

                file_name = os.path.join(MEDIA_ROOT, "sd_images", datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".png")
                image.save(file_name, format="PNG")

                buffer = BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                try:
                    socket_payload = {
                        'event': 'creation-finished',
                        'data': b64encode(buffer.getvalue()).decode(),
                    }

                    for socket in WS_Create:
                        socket.send_json(socket_payload)
                except Exception as e:
                    print(e)

            except Empty:
                #self.do_run = False
                print("Queue is empty")
                sleep(1000)

        print(f"{self.name} stopped!")