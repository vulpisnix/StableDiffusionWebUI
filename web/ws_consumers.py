import datetime
import json
import threading
import time
import random
import torch
import os
from base64 import b64encode
from io import BytesIO
from queue import Queue, Empty
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from diffusers import (
    DiffusionPipeline,
    DDIMScheduler,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    UniPCMultistepScheduler,
    StableDiffusionUpscalePipeline
)

from channels.generic.websocket import JsonWebsocketConsumer
from SDWebUI.settings import BASE_DIR, MEDIA_ROOT

queue = Queue()
sdQueueThread = None

WS_Create = []
CURRENT_PROCESS = {
    'steps': 0,
    'step': 0,
    'percent': 0,
    'timestep': 0,
    'data': None,
    'img_state': None
}
class WSConsumer_Create(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        WS_Create.append(self)

    def disconnect(self, code):
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

        start_time = -1

        while self.do_run:
            try:
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

                def progress_callback(step: int, timestep: int, latents):
                    total_steps = pipe.scheduler.num_inference_steps
                    elapsed = time.time() - start_time
                    steps_done = step + 1
                    percent = int(steps_done / total_steps * 100)

                    avg_time = elapsed / steps_done

                    remaining = (total_steps - steps_done) * avg_time
                    eta = time.strftime("%H:%M:%S", time.gmtime(remaining))

                    with torch.no_grad():
                        image_tensor = pipe.vae.decode(latents / 0.18215).sample
                        if image_tensor.dtype in [torch.bfloat16, torch.float16]:
                            image_tensor = image_tensor.to(torch.float32)
                        image_tensor = (image_tensor / 2 + 0.5).clamp(0, 1)
                        im = image_tensor.cpu().permute(0, 2, 3, 1)[0].numpy()
                        im = (im * 255).round().astype("uint8")

                        img = Image.fromarray(im)
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        buffered.seek(0)
                        img_state = b64encode(buffered.getvalue()).decode(),

                    CURRENT_PROCESS = {
                        'steps': total_steps,
                        'step': step,
                        'percent': percent,
                        'timestep': f"{timestep}",
                        'eta': eta,
                        'data': data,
                        'img_state': img_state
                    }
                    socket_payload_p = {
                        'event': 'progress',
                        'data': CURRENT_PROCESS
                    }
                    for socket_p in WS_Create:
                        socket_p.send_json(socket_payload_p)

                def progress_callback_upscaler(step: int, timestep: int, latents):
                    total_steps = upscaler.scheduler.num_inference_steps
                    elapsed = time.time() - start_time
                    steps_done = step + 1
                    percent = int(steps_done / total_steps * 100)

                    avg_time = elapsed / steps_done

                    remaining = (total_steps - steps_done) * avg_time
                    eta = time.strftime("%H:%M:%S", time.gmtime(remaining))

                    with torch.no_grad():
                        image_tensor = upscaler.vae.decode(latents / 0.18215).sample
                        if image_tensor.dtype in [torch.bfloat16, torch.float16]:
                            image_tensor = image_tensor.to(torch.float32)
                        image_tensor = (image_tensor / 2 + 0.5).clamp(0, 1)
                        im = image_tensor.cpu().permute(0, 2, 3, 1)[0].numpy()
                        im = (im * 255).round().astype("uint8")

                        img = Image.fromarray(im)
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        buffered.seek(0)
                        img_state = b64encode(buffered.getvalue()).decode(),

                    CURRENT_PROCESS = {
                        'steps': total_steps,
                        'step': step,
                        'percent': percent,
                        'timestep': f"{timestep}",
                        'eta': eta,
                        'data': data,
                        'img_state': img_state
                    }
                    socket_payload_p = {
                        'event': 'progress-upscaler',
                        'data': CURRENT_PROCESS
                    }
                    for socket_p in WS_Create:
                        socket_p.send_json(socket_payload_p)


                pipe = DiffusionPipeline.from_pretrained(settings["model"], torch_dtype=torch_dtype, cache_dir=os.path.join(BASE_DIR, 'sd_model_cache'))
                pipe = pipe.to(device)

                match str(settings["sampler"]):
                    case "Euler a":
                        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
                    case "DDIM":
                        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
                    case "DPM++ 2M":
                        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
                    case "UniPC":
                        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

                if settings["tiling"]:
                    pipe.enable_vae_tiling()
                    pipe.enable_sequential_cpu_offload()

                seed = settings["seed"] if settings["seed"] != -1 else random.randint(0, 2 ** 32 - 1)
                generator = torch.Generator(device="cuda").manual_seed(seed)

                start_time = time.time()

                image = pipe(
                    prompt=settings["prompt"],
                    negative_prompt="nsfw," + settings["negative"],
                    width=settings["width"],
                    height=settings["height"],
                    num_inference_steps=settings["steps"],
                    true_cfg_scale=settings["cfg"],
                    generator=generator,
                    callback=progress_callback,
                    callback_steps=1
                ).images[0]

                file_name = os.path.join(MEDIA_ROOT, "sd_images", datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".png")
                image.save(file_name, format="PNG")

                match settings["upscaler"]:
                    case "4x-UltraSharp":
                        upscaler = StableDiffusionUpscalePipeline.from_pretrained(
                            "stabilityai/stable-diffusion-x4-upscaler",
                            torch_dtype=torch_dtype,
                            cache_dir = os.path.join(BASE_DIR, 'sd_model_cache')
                        ).to("cuda")

                        start_time = time.time()
                        upscaled = upscaler(
                            prompt=settings["prompt"],
                            image=image,
                            #num_inference_steps=settings["steps"],
                            #generator=generator,
                            callback=progress_callback_upscaler,
                            callback_steps=1
                        ).images[0]
                        upscaled.save(file_name, format="PNG")


                targetImage = Image.open(file_name)
                metadata = PngInfo()
                metadata.add_text("SD_Data", json.dumps(data))
                targetImage.save(file_name, format="PNG", pnginfo=metadata)

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
                pass

        print(f"{self.name} stopped!")