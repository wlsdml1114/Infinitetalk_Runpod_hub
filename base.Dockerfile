# Use specific version of nvidia cuda image
FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04 as runtime

# Remove any third-party apt sources to avoid issues with expiring keys.
RUN rm -f /etc/apt/sources.list.d/*.list

# Set shell and noninteractive environment variables
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Set working directory
WORKDIR /

# Update and upgrade the system packages (Worker Template)
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt install --yes --no-install-recommends git wget curl bash libgl1 software-properties-common openssh-server nginx rsync ffmpeg && \
    apt-get install --yes --no-install-recommends build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev git-lfs && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt install python3.10-dev python3.10-venv -y --no-install-recommends && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Download and install pip
RUN ln -s /usr/bin/python3.10 /usr/bin/python && \
    rm /usr/bin/python3 && \
    ln -s /usr/bin/python3.10 /usr/bin/python3 && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py

RUN git clone https://github.com/MeiGen-AI/MultiTalk.git
WORKDIR /MultiTalk
    

ENV TORCH_CUDA_ARCH_LIST="8.6;8.9"

RUN pip install torch==2.7.0 torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu128
RUN pip install misaki[en]
RUN pip install ninja 
RUN pip install psutil 
RUN pip install packaging 
RUN pip install flash_attn==2.7.4.post1 --no-build-isolation
RUN pip install -r requirements.txt
RUN pip install librosa ffmpeg
RUN pip uninstall -y transformers
RUN pip install transformers==4.48.2

#docker build -t wlsdml1114/multitalk-base:1.0 -f base.Dockerfile .
#docker push wlsdml1114/multitalk-base:1.0