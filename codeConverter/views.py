# import base64
# import json
# import re
# import subprocess
# import sys
# import io
# from concurrent.futures import ThreadPoolExecutor
# from matplotlib import pyplot as plt
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# import functools

# # Import other necessary modules

# # Global variables for caching installed packages
# installed_packages_cache = set()

# @functools.lru_cache(maxsize=128)
# @csrf_exempt
# def execute_python(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method'})

#     data = json.loads(request.body.decode('utf-8'))
#     code = data.get('code', '')

#     # Split the input code into blocks based on newlines
#     code_blocks = code.split('\n')

#     # Initialize variables to store results
#     result = ''
#     images = []
#     error = ''
#     installation_messages = []

#     # Initialize variables to store import statements and remaining code
#     import_statements = []
#     remaining_code = []

#     # Process each line of code separately
#     for line in code_blocks:
#         # Check if the line starts with 'from' or 'import'
#         if line.startswith('from') or line.startswith('import'):
#             # Add the import statement to the list
#             import_statements.append(line)
#         else:
#             remaining_code.append(line)

#     # Check if each imported package is already installed or in cache
#     missing_packages = set()
#     for import_stmt in import_statements:
#         package_name = import_stmt.split()[1].split('.')[0]  # Extract package name
#         if package_name not in installed_packages_cache:
#             missing_packages.add(package_name)

#     # Install missing packages asynchronously
#     install_missing_packages(missing_packages)

#     # Execute import statements
#     for import_stmt in import_statements:
#         try:
#             # Execute import statement
#             exec(import_stmt, globals())
#             installation_messages.append(f"Successfully imported: {import_stmt}")
#         except Exception as e:
#             installation_messages.append(f"Error importing {import_stmt}: {str(e)}")

#     # Join remaining code
#     processed_code = '\n'.join(remaining_code)

#     # Execute the rest of the Python code and collect stdout output
#     with io.StringIO() as stdout_buffer, io.StringIO() as stderr_buffer:
#         sys.stdout = stdout_buffer
#         sys.stderr = stderr_buffer

#         try:
#             # Set matplotlib backend and execute the code
#             with plt.style.context('ggplot'), plt.rc_context({'backend': 'Agg'}):
#                 exec(processed_code, globals())

#                 # Collect all figures and encode them as base64
#                 for fig in plt.get_fignums():
#                     img_data = io.BytesIO()
#                     plt.figure(fig).savefig(img_data, format='png', bbox_inches='tight')
#                     encoded_img = base64.b64encode(img_data.getvalue()).decode('utf-8')
#                     images.append(f"data:image/png;base64,{encoded_img}")
#                 plt.clf()  # Clear the current figure after saving all images

#                 # Collect stdout output
#                 result = stdout_buffer.getvalue().strip() or "No output to display."

#         except Exception as e:
#             # If an error occurs, collect the error message
#             error = str(e)

#     # Reset stdout
#     sys.stdout = sys.__stdout__

#     # Return results along with installation status and errors as JSON response
#     return JsonResponse({'result': result, 'result_images': images, 'error': error, 'installation_messages': installation_messages})

# def install_package(package_name):
#     try:
#         # Run pip install command
#         result = subprocess.run([sys.executable, '-m', 'pip', 'install', package_name], capture_output=True, text=True, check=True)

#         # Check if installation was successful
#         if result.returncode == 0:
#             print(f"Successfully installed {package_name}")
#             installed_packages_cache.add(package_name)
#             return True
#         else:
#             print(f"Failed to install {package_name}: {result.stderr}")
#             return False
#     except subprocess.CalledProcessError as e:
#         print(f"Error installing {package_name}: {e}")
#         return False


# def install_missing_packages(missing_packages):
#     with ThreadPoolExecutor() as executor:
#         futures = [executor.submit(install_package, package) for package in missing_packages]
#         for future in futures:
#             future.result()  # Wait for each installation to complete


# @csrf_exempt
# def check_installation(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method'})

#     data = json.loads(request.body.decode('utf-8'))
#     code = data.get('code', '')

#     # Extract import statements from the code
#     imported_packages = set()
#     for line in code.split('\n'):
#         if 'from' in line and 'import' in line:
#             match = re.search(r'from\s+(\S+)\s+import', line)
#             if match:
#                 package = match.group(1).split('.')[0]  # Extract the package name before the first '.'
#                 imported_packages.add(package)
#         elif 'import' in line:
#             packages = re.findall(r'import\s+(\S+)', line)
#             for pkg in packages:
#                 package = pkg.split('.')[0]  # Extract the package name before the first '.'
#                 imported_packages.add(package)

#     # Check if each imported package is already installed or in cache
#     missing_packages = [pkg for pkg in imported_packages if pkg not in installed_packages_cache]

#     return JsonResponse({'missing_packages': missing_packages})


import base64
import json
import os
import re
import subprocess
import sys
import io
from matplotlib import pyplot as plt
import pandas as pd
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import pycodestyle
import uuid 
import requests
import json


from keras import backend as K
K.clear_session()




@csrf_exempt
def execute_python(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    data = json.loads(request.body.decode('utf-8'))
    code = data.get('code', '')

    # Check if the code contains any plotting commands
    has_plots = False
    for line in code.split('\n'):
        if ('plt.' in line and not '# plt.' in line) or ('sns.' in line and not '# sns.' in line):
            has_plots = True
            break
    for line in code.split('\n'):
        if ' input'+'(' in line:
            result = "Sorry, the 'input' command is not supported. if you have a variable with name 'input' please change it"
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
            plt.clf() # Clear the current figure after saving all images

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
    return JsonResponse({'result': result, 'result_images': images, 'error': ''})

