from django.shortcuts import render
import argparse
import torch
import base64
import io
import os
import json
from PIL import Image
from safetensors.torch import load_file
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers.models.modeling_outputs import Transformer2DModelOutput
from django.conf import settings
import tempfile
import requests
from io import BytesIO

# Hugging Face API 설정
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}


def disable_nsfw_filter(pipeline):
    def dummy_checker(images, **kwargs):
        # 항상 False를 반환하여 NSFW 필터 비활성화
        return images, [False] * len(images)

    pipeline.safety_checker = dummy_checker


def query():
    response = requests.post(API_URL, headers=headers)
    return response.content

def input_fn(request_body, request_content_type='application/json'):
    return request_body

def model_fn(lora_model_path, weight):
    # Hugging Face API를 통해 base 모델 로드
    model_id = "runwayml/stable-diffusion-v1-5"

    #from_single_file

    pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16
    ).to("cuda")

    # pipeline = load_lora_weights(pipeline, lora_model_path, 0.1)
    pipeline = load_lora_weights(pipeline, lora_model_path, weight)

    return pipeline

def load_lora_weights(pipeline, checkpoint_path, weight):
    pipeline.to("cuda")
    LORA_PREFIX_UNET = "lora_unet"
    LORA_PREFIX_TEXT_ENCODER = "lora_te"
    alpha = weight

    state_dict = load_file(checkpoint_path, device="cuda")
    visited = []

    for key in state_dict:
        if ".alpha" in key or key in visited:
            continue

        if "text" in key:
            layer_infos = key.split(".")[0].split(LORA_PREFIX_TEXT_ENCODER + "_")[-1].split("_")
            curr_layer = pipeline.text_encoder
        else:
            layer_infos = key.split(".")[0].split(LORA_PREFIX_UNET + "_")[-1].split("_")
            curr_layer = pipeline.unet

        temp_name = layer_infos.pop(0)
        while len(layer_infos) > -1:
            try:
                curr_layer = curr_layer.__getattr__(temp_name)
                if len(layer_infos) > 0:
                    temp_name = layer_infos.pop(0)
                elif len(layer_infos) == 0:
                    break
            except Exception:
                if len(temp_name) > 0:
                    temp_name += "_" + layer_infos.pop(0)
                else:
                    temp_name = layer_infos.pop(0)

        pair_keys = []
        if "lora_down" in key:
            pair_keys.append(key.replace("lora_down", "lora_up"))
            pair_keys.append(key)
        else:
            pair_keys.append(key)
            pair_keys.append(key.replace("lora_up", "lora_down"))
        
        if len(state_dict[pair_keys[0]].shape) == 4:
            weight_up = state_dict[pair_keys[0]].squeeze(3).squeeze(2).to(torch.float32)
            weight_down = state_dict[pair_keys[1]].squeeze(3).squeeze(2).to(torch.float32)
            curr_layer.weight.data += alpha * torch.mm(weight_up, weight_down).unsqueeze(2).unsqueeze(3)
        else:
            weight_up = state_dict[pair_keys[0]].to(torch.float32)
            weight_down = state_dict[pair_keys[1]].to(torch.float32)
            curr_layer.weight.data += alpha * torch.mm(weight_up, weight_down)

        for item in pair_keys:
            visited.append(item)

    return pipeline

def predict_fn(request_body, pipeline):
    input_data = json.loads(request_body)
    
    prompt = input_data['prompt']
    negative_prompt = input_data['negative_prompt']
    width = input_data['width']
    height = input_data['height']
    num_inference_steps = input_data['num_inference_steps']
    num_images_per_prompt = input_data['num_images_per_prompt']
    guidance_scale = input_data['guidance_scale']
    seed = input_data['seed']
    init_image_base64 = input_data['init_image']

    if seed == -1:
        generator = None
    else:
        generator = torch.Generator(device='cuda').manual_seed(seed)
    
    init_image_bytes = base64.b64decode(init_image_base64)
    init_image = Image.open(io.BytesIO(init_image_bytes)).convert("RGB")
    init_image = init_image.resize((width, height))
    
    prediction = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=init_image,
        num_inference_steps=num_inference_steps,
        num_images_per_prompt=num_images_per_prompt,
        generator=generator,
        guidance_scale=guidance_scale,
    ).images

    return prediction

def output_fn(prediction, accept='application/json'):
    encoded_images = []
    for image in prediction:
        img_byte_array = io.BytesIO()
        image.save(img_byte_array, format='PNG')
        img_byte_array = img_byte_array.getvalue()
        
        base64_image = base64.b64encode(img_byte_array).decode('utf-8')
        encoded_images.append(base64_image)
    
    response = {
        'base64' : encoded_images
    }

    return json.dumps(response)

# Create your views here.
def main(request):
    if request.method == 'GET':
        # GET 요청일 경우 기본값을 템플릿으로 전달
        return render(request, 'main2.html', {
            'images': [],
            'prompt': 'mi1kt3a, mi1kt3a style, crt, object',
            # 'negative_prompt': '',
            # 'num_inference_steps': '',
            # 'num_images_per_prompt': '',
            # 'guidance_scale': '',
            # 'seed': '',
            # 'batch_size': '',
            # 'batch_count': '',
            'weights': '0.00',
            'init_image': None
        })

    else:
        # model 변경
        lora_model_path = "/srv/image_be/model/last.safetensors"

        print("Loading model...")
        weights = float(request.POST.get('weights'))
        pipeline = model_fn(lora_model_path, weights)
        disable_nsfw_filter(pipeline)
        print("Model loaded.")

        # 사용자 입력값 받기
        prompt = request.POST.get('prompt')
        negative_prompt = request.POST.get('negative_prompt')
        num_inference_steps = int(request.POST.get('num_inference_steps'))
        num_images_per_prompt = int(request.POST.get('num_images_per_prompt'))
        guidance_scale = int(request.POST.get('guidance_scale'))
        seed = int(request.POST.get('seed'))
        batch_size = int(request.POST.get('batch_size'))
        batch_count = int(request.POST.get('batch_count'))

        # 이미지 파일 받아서 base64로 인코딩
        init_image_file = request.FILES['init_image']
        init_image_base64 = base64.b64encode(init_image_file.read()).decode('utf-8')

        base_request_body = {
            'prompt': prompt,
            # 'mi1kt3a animal, crt, same style, elephant, character, illustration, normal, simple',
            'negative_prompt': negative_prompt,
            # 'human, girl, man, woman, boy, ugly, background',
            'width': 512,
            'height': 512,
            'num_inference_steps': num_inference_steps,
            'num_images_per_prompt': num_images_per_prompt,
            'seed': seed,
            'guidance_scale': guidance_scale,
            'init_image': init_image_base64,
        }
        print(base_request_body)

        # 전체 결과 저장용 리스트
        all_predictions = []

        for batch_num in range(batch_count):
            print(f"Processing batch {batch_num+1}/{batch_count}...")
            # 입력 함수 호출
            input_data = input_fn(json.dumps(base_request_body))

            # 예측 함수 호출
            predictions = predict_fn(input_data, pipeline)

            # 결과를 리스트에 추가
            all_predictions.extend(predictions)

        # 출력 함수 호출
        output = output_fn(all_predictions)

        # with open('output.json', 'w') as f:
        #     f.write(output)

        # with open('output.json', 'r') as f:
        #     output_data = json.load(f)
        # output을 JSON으로 로드

        output_data = json.loads(output)

        base64_images = output_data['base64']

        # 이미지 데이터 저장을 위한 리스트
        image_data_list = []

        for i, base64_image in enumerate(base64_images):
            img_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(img_data)).convert("RGBA")
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_data_list.append(f"data:image/png;base64,{img_str}")

        return render(request, 'main2.html', {
            'images': image_data_list,
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'num_inference_steps': num_inference_steps,
            'num_images_per_prompt': num_images_per_prompt,
            'guidance_scale': guidance_scale,
            'seed': seed,
            'batch_size': batch_size,
            'batch_count': batch_count,
            'weights': weights,
            'init_image': init_image_file
            })
    
    

def main2(request):
    if request.method == 'GET':
        # GET 요청일 경우 기본값을 템플릿으로 전달
        return render(request, 'main2.html', {
            'images': [],
            'prompt': 'mi1kt3a, mi1kt3a style, crt, animal',
            'init_image': None
        })

    else:
        # model 변경
        lora_model_path = "/srv/image_be/model/last.safetensors"

        print("Loading model...")
        weights = float(request.POST.get('weights'))
        pipeline = model_fn(lora_model_path, weights)
        disable_nsfw_filter(pipeline)
        print("Model loaded.")

        # 사용자 입력값 받기
        prompt = request.POST.get('prompt')
        negative_prompt = request.POST.get('negative_prompt')
        num_inference_steps = int(request.POST.get('num_inference_steps'))
        num_images_per_prompt = int(request.POST.get('num_images_per_prompt'))
        guidance_scale = int(request.POST.get('guidance_scale'))
        seed = int(request.POST.get('seed'))
        batch_size = int(request.POST.get('batch_size'))
        batch_count = int(request.POST.get('batch_count'))

        # 이미지 파일 받아서 base64로 인코딩
        init_image_file = request.FILES['init_image']
        init_image_base64 = base64.b64encode(init_image_file.read()).decode('utf-8')

        base_request_body = {
            'prompt': prompt,
            # 'mi1kt3a animal, crt, same style, elephant, character, illustration, normal, simple',
            'negative_prompt': negative_prompt,
            # 'human, girl, man, woman, boy, ugly, background',
            'width': 512,
            'height': 512,
            'num_inference_steps': num_inference_steps,
            'num_images_per_prompt': num_images_per_prompt,
            'seed': seed,
            'guidance_scale': guidance_scale,
            'init_image': init_image_base64,
        }
        print(base_request_body)

        # 전체 결과 저장용 리스트
        all_predictions = []

        for batch_num in range(batch_count):
            print(f"Processing batch {batch_num+1}/{batch_count}...")
            # 입력 함수 호출
            input_data = input_fn(json.dumps(base_request_body))

            # 예측 함수 호출
            predictions = predict_fn(input_data, pipeline)

            # 결과를 리스트에 추가
            all_predictions.extend(predictions)

        # 출력 함수 호출
        output = output_fn(all_predictions)

        # with open('output.json', 'w') as f:
        #     f.write(output)

        # with open('output.json', 'r') as f:
        #     output_data = json.load(f)
        # output을 JSON으로 로드

        output_data = json.loads(output)

        base64_images = output_data['base64']

        # 이미지 데이터 저장을 위한 리스트
        image_data_list = []

        for i, base64_image in enumerate(base64_images):
            img_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(img_data)).convert("RGBA")
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_data_list.append(f"data:image/png;base64,{img_str}")

        return render(request, 'main2.html', {
            'images': image_data_list,
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'num_inference_steps': num_inference_steps,
            'num_images_per_prompt': num_images_per_prompt,
            'guidance_scale': guidance_scale,
            'seed': seed,
            'batch_size': batch_size,
            'batch_count': batch_count,
            'weights': weights,
            'init_image': init_image_file
            })
            
    # except Exception as e:
    #     print("Error:", str(e))4
    #     message = f'모델 로드 중 오류 발생: {str(e)}'
    
    
