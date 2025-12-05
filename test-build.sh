#!/bin/bash
#
# 本地测试 Docker 构建脚本
# 用于在推送到 GitHub 之前验证构建是否成功
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 配置
TIMESTAMP=$(date +'%Y%m%d%H%M')
IMAGE_TAG="jmp-core-${TIMESTAMP}"
LOCAL_IMAGE="jumpserver-local:${IMAGE_TAG}"
ALIYUN_REGISTRY="registry.cn-shanghai.aliyuncs.com"
ALIYUN_NAMESPACE="zywdockers"
ALIYUN_REPO="images"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo_error "Docker is not installed!"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo_error "Docker daemon is not running!"
    exit 1
fi

echo_info "==================================="
echo_info "  JumpServer Local Build Test"
echo_info "==================================="
echo_info "Image Tag: ${IMAGE_TAG}"
echo_info "Local Image: ${LOCAL_IMAGE}"
echo ""

# 步骤1: 构建镜像
echo_step "Step 1: Building Docker image..."
docker build \
    -f Dockerfile \
    -t ${LOCAL_IMAGE} \
    --build-arg VERSION=local-test \
    .

if [ $? -eq 0 ]; then
    echo_info "✅ Build successful!"
else
    echo_error "❌ Build failed!"
    exit 1
fi

# 步骤2: 检查镜像大小
echo ""
echo_step "Step 2: Checking image size..."
IMAGE_SIZE=$(docker images ${LOCAL_IMAGE} --format "{{.Size}}")
echo_info "Image size: ${IMAGE_SIZE}"

# 步骤3: 测试镜像
echo ""
echo_step "Step 3: Testing image..."
echo_info "Starting test container..."

# 启动测试容器
docker run -d \
    --name jms-test-${TIMESTAMP} \
    -e SECRET_KEY=$(head -c100 < /dev/urandom | base64 | tr -dc A-Za-z0-9 | head -c 48) \
    -e BOOTSTRAP_TOKEN=test-token \
    -e DB_ENGINE=sqlite3 \
    -p 18080:8080 \
    ${LOCAL_IMAGE} \
    sleep 300

# 等待容器启动
echo_info "Waiting for container to start..."
sleep 5

# 检查容器状态
if docker ps | grep -q "jms-test-${TIMESTAMP}"; then
    echo_info "✅ Container started successfully!"
    
    # 显示容器日志（前20行）
    echo ""
    echo_info "Container logs (first 20 lines):"
    docker logs jms-test-${TIMESTAMP} 2>&1 | head -20
    
    # 检查进程
    echo ""
    echo_info "Container processes:"
    docker exec jms-test-${TIMESTAMP} ps aux | head -10
else
    echo_error "❌ Container failed to start!"
    docker logs jms-test-${TIMESTAMP}
    docker rm -f jms-test-${TIMESTAMP}
    exit 1
fi

# 步骤4: 清理
echo ""
echo_step "Step 4: Cleanup..."
read -p "Do you want to clean up the test container? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rm -f jms-test-${TIMESTAMP}
    echo_info "✅ Test container removed"
else
    echo_info "Test container kept running at: http://localhost:18080"
    echo_info "To stop: docker rm -f jms-test-${TIMESTAMP}"
fi

# 步骤5: 询问是否推送到阿里云
echo ""
read -p "Do you want to push this image to Aliyun? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_step "Step 5: Pushing to Aliyun Registry..."
    
    # 检查是否已登录
    echo_info "Logging in to Aliyun Container Registry..."
    echo_warn "Please enter your Aliyun credentials:"
    docker login ${ALIYUN_REGISTRY}
    
    # 标记镜像
    REMOTE_IMAGE="${ALIYUN_REGISTRY}/${ALIYUN_NAMESPACE}/${ALIYUN_REPO}:${IMAGE_TAG}"
    REMOTE_LATEST="${ALIYUN_REGISTRY}/${ALIYUN_NAMESPACE}/${ALIYUN_REPO}:jmp-core-latest"
    
    echo_info "Tagging image..."
    docker tag ${LOCAL_IMAGE} ${REMOTE_IMAGE}
    docker tag ${LOCAL_IMAGE} ${REMOTE_LATEST}
    
    # 推送镜像
    echo_info "Pushing ${REMOTE_IMAGE}..."
    docker push ${REMOTE_IMAGE}
    
    echo_info "Pushing ${REMOTE_LATEST}..."
    docker push ${REMOTE_LATEST}
    
    echo_info "✅ Images pushed successfully!"
    echo ""
    echo_info "Pull command:"
    echo "  docker pull ${REMOTE_IMAGE}"
    echo "  docker pull ${REMOTE_LATEST}"
fi

# 询问是否删除本地镜像
echo ""
read -p "Do you want to remove local image? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi ${LOCAL_IMAGE}
    echo_info "✅ Local image removed"
fi

echo ""
echo_info "==================================="
echo_info "  Test completed successfully! 🎉"
echo_info "==================================="

