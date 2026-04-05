from django.shortcuts import render
# from django.http import HttpResponse
from django.shortcuts import render
import requests
from django.core.files.storage import FileSystemStorage
import json, os
# from pathlib import Path
from celery import shared_task
# import docker
from django.http import JsonResponse
from PIL import Image

# Create your views here.

def index(request):

    # Page from the theme 
    return render(request, 'pages/dashboard.html')


def resizeWPadding(img_path, target_size):
    img = Image.open(img_path).convert("RGB")

    width, height = img.size
    if width == height == target_size:
        return

    scale = min(target_size/width, target_size/height)

    new_width = int(width * scale)
    new_height = int(height * scale)

    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
    new_img = Image.new("RGB", (target_size, target_size))

    x_offset = (target_size - new_width) // 2
    y_offset = (target_size - new_height) // 2

    new_img.paste(resized_img, (x_offset, y_offset))
    new_img.save(img_path)


@shared_task(bind=True)
def classify(self, input_path, AI_SERVER):
    with open(input_path, "rb") as f:
        files = {"file": f}
        return requests.post(f"{AI_SERVER}/predict", files=files)


def imgUpload(request):
    if request.method == 'POST' and request.FILES.get('image'):
        fileObj = request.FILES['image']
        
        name, ext = os.path.splitext(fileObj.name)

        if ext not in ['.png', '.jpg', '.jpeg']:
            return JsonResponse({'ext': False})
    
        # Save to database/file system
        fs = FileSystemStorage()
        filePathName = fs.url(fs.save(fileObj.name, fileObj))
        # Return the URL of the saved image
        return JsonResponse({
            'success': True,
            'ext': True,
            'image_url': filePathName
        })

    return JsonResponse({'success': False, 'error': 'No image provided'}, status=400)


def analyze(request):

    if request.method == "POST":
        filePathName = request.POST.get('image_path')

    # Path to input image
    input_path = "." + filePathName
    output_path = input_path
    output_js = output_path[:-3] + "json"

    resizeWPadding(input_path, 800)

    # Server endpoint
    
    AI_SERVER = os.environ.get('OBD', 'OBD')
    # AI_SERVER = os.environ.get('http://localhost:8000', 'http://localhost:8000')
    response = classify(input_path, AI_SERVER)

    # Save result
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Output image saved to {output_path}")

        # return JsonResponse({'filePathName': output_path})
    
    AI_SERVER = os.environ.get('CAP', 'CAP')
    # AI_SERVER = os.environ.get('http://localhost:8001', 'http://localhost:8001')
    response = classify(input_path, AI_SERVER)


    if response.status_code == 200:    
        data = response.content.decode('utf-8')
        with open(output_js, "w") as f:
            f.write(data)
        print(f"Output results saved to {output_js}")

        with open(output_js, "r") as f:
            data = json.load(f)
    
        return JsonResponse({'filePathName': output_path, 'caption': data["caption"][0:-5], 'classification': data["classification"], 'evaluate': data["evaluate"]})
    else:
        print("//////Error//////:", response.status_code, response.text)