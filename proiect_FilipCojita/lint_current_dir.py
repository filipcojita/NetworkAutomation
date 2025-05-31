import os
import subprocess

# Get the current working directory
current_dir = os.getcwd()

# Optionally, print it
print(f"Linting all Python files in: {current_dir}")

# Collect all .py files in the directory
py_files = [f for f in os.listdir(current_dir) if f.endswith('.py')]

# Run pylint on the list of .py files
if py_files:
    subprocess.run(['pylint'] + py_files)
else:
    print("No Python files found in the current directory.")
