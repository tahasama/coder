import base64
import json
import subprocess
import sys
import io
from matplotlib import pyplot as plt
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

# Import other necessary modules and clear Keras session
from keras import backend as K
K.clear_session()

# Initialize a dictionary to cache installed packages
installed_packages = {}

@csrf_exempt
def execute_python(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    data = json.loads(request.body.decode('utf-8'))
    code = data.get('code', '')
    required_packages = data.get('requiredPackages', [])

    # Install required packages if not already installed
    for package in required_packages:
        if package not in installed_packages:
            subprocess.run(['pip', 'install', package])
            installed_packages[package] = True

    # Check if the code contains any plotting commands
    has_plots = any(('plt.' in line and not '# plt.' in line) or ('sns.' in line and not '# sns.' in line) for line in code.split('\n'))
    if 'input(' in code:
        result = "Sorry, the 'input' command is not supported. If you have a variable with name 'input', please change it."
        return JsonResponse({'result': result, 'result_images': [], 'error': ''})

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
                for fig in plt.get_fignums():
                    img_data = io.BytesIO()
                    plt.figure(fig).savefig(img_data, format='png', bbox_inches='tight')
                    encoded_img = base64.b64encode(img_data.getvalue()).decode('utf-8')
                    images.append(f"data:image/png;base64,{encoded_img}")
            plt.clf()  # Clear the current figure after saving all images

            # Collect stdout output
            result = stdout_buffer.getvalue().strip()
            if not result:
                result = "No output to display."

    except Exception as e:
        result = ''
        error = str(e)
        sys.stdout = sys.__stdout__
        return JsonResponse({'result': result, 'result_images': [], 'error': error})

    # Reset stdout
    sys.stdout = sys.__stdout__

    # Return results as JSON response
    return JsonResponse({'result': result, 'result_images': images, 'error': error})
