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
from django.utils import timezone

from SDWebUI.settings import BASE_DIR, MEDIA_ROOT
from web.models import SDImageQueue, SDImage, SDModel
import datetime
import json
import time
import random

import torch
import os
from base64 import b64encode, b64decode
from io import BytesIO

import threading

from web.ws_consumers import WS_Create

queue = Queue()
sdQueueThread = None
CURRENT_PROCESS = {
    'steps': 0,
    'step': 0,
    'percent': 0,
    'timestep': 0,
    'data': None,
    'img_state': None
}


def fetch_queue_from_db():
    global sdQueueThread
    print("Fetching SDImageQueue..")
    qu = SDImageQueue.objects.all().order_by('created_at')
    for q in qu: queue.put(q)
    print(f"Fetched {qu.count()} SDImageQueue Elements!")

    if sdQueueThread is None and qu.count() > 0:
        sdQueueThread = SDQueueThread()
        sdQueueThread.do_run = True
        sdQueueThread.start()

def run():
    global sdQueueThread
    if sdQueueThread is None:
        sdQueueThread = SDQueueThread()
        sdQueueThread.do_run = True
        sdQueueThread.start()

class SDQueueThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "SDQueueThread"
        self.do_run = True

        self.data = None
        self.start_time = 0
        self.current_pipe = None
        self.current_upscaler = None

        if torch.cuda.is_available():
            self.torch_dtype = torch.bfloat16
            self.device = "cuda"
        else:
            self.torch_dtype = torch.float32
            self.device = "cpu"

    def check_nsfw(self, pipeline):
        nsfw_flag = False
        '''
            if hasattr(pipeline, "nsfw_content_detected"):
                nsfw_flag = any(pipeline.nsfw_content_detected)
            elif hasattr(pipeline, "has_nsfw_concept"):
                nsfw_flag = any(pipeline.has_nsfw_concept)
            if nsfw_flag:
                try:
                    socket_payload = {
                        'event': 'creation-failed',
                        'data': 'Mögliche NSFW Inhalte wurden erkannt.'
                    }
                    for socket in WS_Create:
                        socket.send_json(socket_payload)
                except Exception as e:
                    print(e)
            return nsfw_flag
            '''
        return False

    def txt2img(self, settings, progress_callback):
        self.current_pipe = pipe = DiffusionPipeline.from_pretrained(settings["model"], torch_dtype=self.torch_dtype,
                                                                     cache_dir=os.path.join(BASE_DIR, 'sd_model_cache'))
        pipe = pipe.to(self.device)
        # if settings['allow_nsfw']: pipe.safety_checker = None
        pipe.safety_checker = None

        # Add Sampler to pipe
        self.add_sampler(pipe, settings["sampler"])

        if settings["tiling"]:
            pipe.enable_vae_tiling()
            pipe.enable_sequential_cpu_offload()

        seed = settings["seed"] if settings["seed"] != -1 else random.randint(0, 2 ** 32 - 1)
        generator = torch.Generator(device=self.device).manual_seed(seed)

        settings['seed'] = seed
        sett = self.data.settings
        sett['settings'] = settings
        self.data.settings = sett
        self.data.save()

        self.start_time = time.time()
        result = pipe(
            prompt=settings["prompt"],
            negative_prompt=settings["negative"],
            width=settings["width"],
            height=settings["height"],
            num_inference_steps=settings["steps"],
            true_cfg_scale=settings["cfg"],
            generator=generator,
            callback=progress_callback,
            callback_steps=1
        )
        image = result.images[0]
        if self.check_nsfw(result): return None

        file_name = os.path.join(MEDIA_ROOT, "sd_images", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".png")
        image.save(file_name, format="PNG")
        return file_name

    def img2img(self, settings, image):
        pass

    def upscale(self, upscaler_name, image, prompt, negative_prompt, progress_callback_upscaler):
        file_name = os.path.join(MEDIA_ROOT, "sd_images", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".png")

        match upscaler_name:
            case "4x-UltraSharp":
                self.current_upscaler = upscaler = StableDiffusionUpscalePipeline.from_pretrained(
                    "stabilityai/stable-diffusion-x4-upscaler",
                    torch_dtype=self.torch_dtype,
                    cache_dir=os.path.join(BASE_DIR, 'sd_model_cache')
                ).to("cuda")

                self.start_time = time.time()
                upscaled_result = upscaler(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=image,
                    callback=progress_callback_upscaler,
                    callback_steps=1
                )

                upscaled = upscaled_result.images[0]
                if self.check_nsfw(upscaled_result): return None
                upscaled.save(file_name, format="PNG")
        return file_name

    def add_meta(self, image_path, meta):
        print(f"Meta: {meta}")
        targetImage = Image.open(image_path)
        metadata = PngInfo()
        metadata.add_text("SD_Data", json.dumps(meta))
        targetImage.save(image_path, format="PNG", pnginfo=metadata)

    def add_sampler(self, pipe, sampler):
        match str(sampler):
            case "Euler a":
                pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
            case "DDIM":
                pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
            case "DPM++ 2M":
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            case "UniPC":
                pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    def broadcast_result(self, image_path):
        image = Image.open(image_path)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        try:
            socket_payload = {
                'event': 'creation-finished',
                'data': b64encode(buffer.getvalue()).decode(),
            }
            for socket in WS_Create: socket.send_json(socket_payload)
        except Exception as e:
            print(e)

    def progress_callback(self, step: int, timestep: int, latents):
        total_steps = self.current_pipe.scheduler.num_inference_steps
        elapsed = time.time() - self.start_time
        steps_done = step + 1
        percent = int(steps_done / total_steps * 100)

        avg_time = elapsed / steps_done

        remaining = (total_steps - steps_done) * avg_time
        eta = time.strftime("%H:%M:%S", time.gmtime(remaining))

        with torch.no_grad():
            image_tensor = self.current_pipe.vae.decode(latents / 0.18215).sample
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
            'data': self.data.as_json(),
            'img_state': img_state
        }
        socket_payload_p = {
            'event': 'progress',
            'data': CURRENT_PROCESS
        }
        for socket_p in WS_Create:
            socket_p.send_json(socket_payload_p)

    def progress_callback_upscaler(self, step: int, timestep: int, latents):
        total_steps = self.current_upscaler.scheduler.num_inference_steps
        elapsed = time.time() - self.start_time
        steps_done = step + 1
        percent = int(steps_done / total_steps * 100)

        avg_time = elapsed / steps_done

        remaining = (total_steps - steps_done) * avg_time
        eta = time.strftime("%H:%M:%S", time.gmtime(remaining))

        with torch.no_grad():
            image_tensor = self.current_upscaler.vae.decode(latents / 0.18215).sample
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
            'data': self.data.as_json(),
            'img_state': img_state
        }
        socket_payload_p = {
            'event': 'progress-upscaler',
            'data': CURRENT_PROCESS
        }
        for socket_p in WS_Create:
            socket_p.send_json(socket_payload_p)

    def run(self):
        global queue, CURRENT_PROCESS

        print(f"{self.name} started.")

        while self.do_run:
            try:
                self.data = data = queue.get()
                data.is_processing = timezone.now()
                data.save()
                print(f"Processing {data}")

                event_type = data.action_type  # eg txt2img, img2img, etc..
                settings = data.settings['settings']

                result_path = None

                if event_type == 'upscale':
                    image_data = b64decode(data.settings['img'].replace('data:image/jpeg;base64,', ''))
                    image_file = BytesIO(image_data)
                    image = Image.open(image_file)
                    result_path = self.upscale(settings["upscaler"], image, settings["prompt"], settings["negative"],
                                               progress_callback_upscaler=self.progress_callback_upscaler)

                if event_type == 'txt2img':
                    result_path = self.txt2img(settings, progress_callback=self.progress_callback)
                    image_to_upscale = Image.open(result_path)
                    result_path = self.upscale(settings["upscaler"], image_to_upscale, '', '', progress_callback_upscaler=self.progress_callback_upscaler)

                if result_path is None: continue

                settings = data.settings['settings']
                self.add_meta(result_path, settings)
                self.broadcast_result(result_path)

                file_name = result_path.split('\\')[-1]
                model = SDModel.objects.filter(hgf_name=settings['model']).first()
                SDImage.objects.create(
                    model=model,
                    creator=data.user,
                    image=f"sd_images/{file_name}",
                ).save()
                data.delete()

                '''
                start_time = time.time()
                result_path = None

                # img2img = data["img2img"] if 'img2img' in data else None
                if event_type == "txt2img":
                    print("Processing txt2img..")
                    result_path = self.txt2img(settings, pipe, generator, progress_callback=progress_callback)
                    if result_path is None: continue

                img_to_upscale = Image.open(result_path)
                result_path = self.upscale(settings["upscaler"], img_to_upscale, settings["prompt"], settings["negative"], progress_callback_upscaler=progress_callback_upscaler)
                if result_path is None: continue
                self.add_meta(result_path, settings)
                self.broadcast_result(result_path)
                '''
            except Empty:
                print("Queue is empty")
                # self.do_run = False
            '''
            except Exception as e:
                print("Error:", e)
                e.with_traceback()
                continue
            '''

        print(f"{self.name} stopped!")
