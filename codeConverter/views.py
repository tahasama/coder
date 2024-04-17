import base64
import json
import subprocess
import sys
import io
from matplotlib import pyplot as plt
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import cv2
import hashlib

# Import other necessary modules and clear Keras session
from keras import backend as K
import numpy as np
K.clear_session()

# Initialize a dictionary to store installed packages
installed_packages = {}

# Initialize a dictionary to cache code execution results
code_cache = {}
@csrf_exempt
def execute_python(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    data = json.loads(request.body.decode('utf-8'))
    code = data.get('code', '')
    required_packages = data.get('requiredPackages', [])

    # Function to install packages sequentially
    def install_packages(packages):
        for package in packages:
            if package not in installed_packages:
                subprocess.run(['pip', 'install', package])
                installed_packages[package] = True

    # Install required packages if not already installed
    install_packages(required_packages)

    # Check if all required packages are installed
    if len(installed_packages) < len(required_packages):
        return JsonResponse({'error': 'Failed to install all required packages.'})

    # Check if the code contains any plotting commands
    has_plots = any(('plt.' in line and not '# plt.' in line) or ('sns.' in line and not '# sns.' in line) for line in code.split('\n'))
    if 'input(' in code:
        result = "Sorry, the 'input' command is not supported. If you have a variable with name 'input', please change it."
        return JsonResponse({'result': result, 'result_images': [], 'error': ''})

    # Check if code is already cached
    if code in code_cache:
        cached_result, cached_images = code_cache[code]
        return JsonResponse({'result': cached_result, 'result_images': cached_images, 'error': ''})

    # Redirect stdout and stderr to string buffers
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    sys.stdout = stdout_buffer
    sys.stderr = stderr_buffer

    # Execute the Python code
    result = ''
    images = []
    error = ''

    try:
        # Set matplotlib backend and execute the code
        with plt.style.context('ggplot'), plt.rc_context({'backend': 'Agg'}):
            exec(code, globals())

            # Collect all figures and encode them as base64
            if has_plots:
                unique_images = set()  # To store unique image hashes
                for fig in plt.get_fignums():
                    img_data = io.BytesIO()
                    plt.figure(fig).savefig(img_data, format='png', bbox_inches='tight')
                    img_bytes = img_data.getvalue()
                    # Filter out full empty white images
                    if not is_full_empty_white_image(img_bytes):
                        img_hash = hashlib.md5(img_bytes).hexdigest()  # Calculate MD5 hash of image bytes
                        if img_hash not in unique_images:
                            encoded_img = base64.b64encode(img_bytes).decode('utf-8')
                            images.append(f"data:image/png;base64,{encoded_img}")
                            unique_images.add(img_hash)
            plt.clf()  # Clear the current figure after saving all images

            # Collect stdout output
            result = stdout_buffer.getvalue().strip()
            if not result:
                result = "No output to display."

    except Exception as e:
        error = str(e)

    # Reset stdout
    sys.stdout = sys.__stdout__

    # Cache code execution result
    code_cache[code] = (result, images)

    # Return results as JSON response
    return JsonResponse({'result': result, 'result_images': images, 'error': error})



def is_full_empty_white_image(img_bytes):
    # Convert image bytes to numpy array
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

    # Threshold the image to identify white areas
    ret, thresh = cv2.threshold(img, 240, 255, cv2.THRESH_BINARY)

    # Calculate the percentage of white pixels
    white_pixel_percentage = np.sum(thresh == 255) / img.size

    # Consider the image as full empty white if more than 99% of pixels are white
    return white_pixel_percentage > 0.99 



