# 🚀 快速命令参考

## GitHub Actions 构建

### 查看构建状态
```bash
# 访问 Actions 页面
https://github.com/你的用户名/jumpserver-4.10.13/actions
```

## 触发构建

### 自动触发（推送代码）
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

### 自动触发（推送标签）
```bash
git tag v4.10.13-custom
git push origin v4.10.13-custom
```

### 手动触发
1. 访问 GitHub Actions 页面
2. 选择 "Build and Push JumpServer Image"
3. 点击 "Run workflow"

## 本地测试

### Linux/Mac
```bash
# 赋予执行权限
chmod +x test-build.sh

# 运行测试
./test-build.sh
```

### Windows
```cmd
test-build.bat
```

## Docker 镜像操作

### 登录阿里云
```bash
docker login registry.cn-shanghai.aliyuncs.com
# 输入用户名和密码
```

### 拉取镜像
```bash
# 拉取最新版本
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest

# 拉取指定版本
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106
```

### 运行容器
```bash
docker run -d \
  --name jumpserver \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e BOOTSTRAP_TOKEN=your-bootstrap-token \
  -e DB_HOST=mysql-host \
  -e DB_PORT=3306 \
  -e DB_USER=jumpserver \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=jumpserver \
  -e REDIS_HOST=redis-host \
  -e REDIS_PORT=6379 \
  -e REDIS_PASSWORD=your-redis-password \
  -v /opt/jumpserver/data:/opt/jumpserver/data \
  registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest
```

### 查看容器日志
```bash
docker logs -f jumpserver
```

### 进入容器
```bash
docker exec -it jumpserver bash
```

### 停止和删除容器
```bash
# 停止
docker stop jumpserver

# 删除
docker rm jumpserver
```

## 本地构建（手动）

### 构建镜像
```bash
# 基本构建
docker build -t jumpserver-local:test .

# 指定版本
docker build -t jumpserver-local:v4.10.13 \
  --build-arg VERSION=v4.10.13 \
  .
```

### 推送到阿里云
```bash
# 登录
docker login registry.cn-shanghai.aliyuncs.com

# 标记镜像
docker tag jumpserver-local:test \
  registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-test

# 推送
docker push registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-test
```

## 镜像管理

### 列出本地镜像
```bash
docker images | grep jumpserver
```

### 删除本地镜像
```bash
# 删除指定镜像
docker rmi registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106

# 删除所有 jumpserver 镜像
docker rmi $(docker images -q "*/images:jmp-core-*")
```

### 清理未使用的镜像
```bash
docker image prune -a
```

## Git 操作

### 查看远程仓库
```bash
git remote -v
```

### 查看标签
```bash
# 列出所有标签
git tag

# 查看特定标签
git show v4.10.13
```

### 删除标签
```bash
# 删除本地标签
git tag -d v4.10.13

# 删除远程标签
git push origin :refs/tags/v4.10.13
```

### 查看提交历史
```bash
git log --oneline --graph --decorate
```

## GitHub Secrets 配置

### 配置路径
```
仓库 → Settings → Secrets and variables → Actions → New repository secret
```

### 需要配置的 Secrets
```
名称: ALIYUN_USERNAME
值: 你的阿里云容器镜像服务用户名

名称: ALIYUN_PASSWORD
值: 你的阿里云容器镜像服务密码
```

## 阿里云操作

### 获取访问凭证
```
1. 访问 https://cr.console.aliyun.com/
2. 进入 个人实例 → 访问凭证
3. 设置或查看固定密码
```

### 创建镜像仓库
```
1. 访问 https://cr.console.aliyun.com/
2. 进入 个人实例 → 仓库管理 → 镜像仓库
3. 创建仓库：
   - 命名空间: zywdockers
   - 仓库名: images
   - 仓库类型: 私有
```

### 查看镜像列表
```bash
# 使用阿里云 CLI (需要安装)
aliyun cr GetRepoTags --RepoNamespace=zywdockers --RepoName=images
```

## 故障排查

### 查看构建失败原因
```
1. 访问 GitHub Actions 页面
2. 点击失败的构建
3. 展开失败的步骤查看日志
```

### 测试 Docker 构建
```bash
# 启用详细日志
docker build --progress=plain -t test .
```

### 测试镜像推送
```bash
# 测试登录
docker login registry.cn-shanghai.aliyuncs.com

# 测试推送
docker push registry.cn-shanghai.aliyuncs.com/zywdockers/images:test
```

### 查看容器内进程
```bash
docker exec jumpserver ps aux
```

### 查看容器网络
```bash
docker inspect jumpserver | grep IPAddress
```

## 常用环境变量

### 必需变量
```bash
SECRET_KEY          # 加密密钥（必须）
BOOTSTRAP_TOKEN     # 初始化令牌（必须）
```

### 数据库配置
```bash
DB_ENGINE          # 数据库引擎: mysql, postgresql
DB_HOST            # 数据库主机
DB_PORT            # 数据库端口
DB_USER            # 数据库用户
DB_PASSWORD        # 数据库密码
DB_NAME            # 数据库名称
```

### Redis 配置
```bash
REDIS_HOST         # Redis 主机
REDIS_PORT         # Redis 端口
REDIS_PASSWORD     # Redis 密码
```

### 文件服务器配置（自定义）
```bash
FILE_SERVER_TYPE          # minio, s3, oss
FILE_SERVER_ENDPOINT      # 文件服务器地址
FILE_SERVER_ACCESS_KEY    # 访问密钥
FILE_SERVER_SECRET_KEY    # 密钥
FILE_SERVER_BUCKET        # 存储桶名称
```

## 链接

- [GitHub 仓库](https://github.com/你的用户名/jumpserver-4.10.13)
- [GitHub Actions](https://github.com/你的用户名/jumpserver-4.10.13/actions)
- [阿里云容器镜像](https://cr.console.aliyun.com/)
- [JumpServer 官方文档](https://docs.jumpserver.org/)

