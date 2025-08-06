# Use the base image that has necessary CUDA and Python environments
FROM wlsdml1114/multitalk-base:1.1 as runtime

WORKDIR /

# Copy all necessary files from your project folder into the container.
# This includes the modified entrypoint.sh, handler.py, and any other required files.
COPY . .


# The default command to run after the entrypoint script finishes its setup.
# This will be passed to the `exec "$@"` line in entrypoint.sh.
CMD ["python", "handler.py"]
