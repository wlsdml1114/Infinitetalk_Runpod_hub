#!/bin/bash
set -e # 스크립트 실행 중 에러가 발생하면 즉시 중단

# 설치 여부를 확인할 파일 경로
INSTALL_FLAG="/opt/sage_attention_installed.flag"

# 플래그 파일이 없다면 설치를 진행
if [ ! -f "$INSTALL_FLAG" ]; then
    echo ">>> First time running. Installing SageAttention..."
    
    cd /SageAttention
    # 런타임에는 GPU 접근이 가능하므로 설치가 성공합니다.
    python setup.py install
    
    # 설치가 완료되었다는 플래그 파일을 생성하여 다음 실행부터는 설치를 건너뜀
    touch "$INSTALL_FLAG"
    echo ">>> SageAttention installation complete."
else
    echo ">>> SageAttention is already installed. Skipping installation."
fi

# 이 스크립트의 주된 작업(설치)이 끝난 후,
# CMD로 전달된 원래 명령어를 실행합니다. (예: python app.py)
cd /
exec "$@"