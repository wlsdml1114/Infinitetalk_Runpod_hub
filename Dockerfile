# Use the base image that has necessary CUDA and Python environments
FROM wlsdml1114/multitalk-base:1.3 as runtime

WORKDIR /

# Copy all necessary files from your project folder into the container.
# This includes the modified entrypoint.sh, handler.py, and any other required files.
COPY . .

RUN chmod +x ./entrypoint.sh

# Set the entrypoint script to run when the container starts.
# All setup tasks are now handled within this script.
ENTRYPOINT ["./entrypoint.sh"]