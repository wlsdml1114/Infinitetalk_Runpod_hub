# Use the base image that has necessary CUDA and Python environments
FROM wlsdml1114/multitalk-base:1.0

WORKDIR /

RUN pip install -U "huggingface_hub[hf_transfer]"

# Copy all necessary files from your project folder into the container.
# This includes the modified entrypoint.sh, handler.py, and any other required files.
COPY . .

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Set the entrypoint script to run when the container starts.
# All setup tasks are now handled within this script.
ENTRYPOINT ["./entrypoint.sh"]

# The default command to run after the entrypoint script finishes its setup.
# This will be passed to the `exec "$@"` line in entrypoint.sh.
CMD ["python", "handler.py"]
