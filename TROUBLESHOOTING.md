# 🔧 常见问题解决方案

## 问题1: Permission Denied 错误

### 错误信息
```
Error response from daemon: failed to create task for container: failed to create shim task: 
OCI runtime create failed: runc create failed: unable to start container process: 
error during container init: exec: "./entrypoint.sh": permission denied
```

### 原因
`entrypoint.sh` 文件没有执行权限

### 解决方案
已在 Dockerfile 中添加：
```dockerfile
RUN chmod +x /opt/jumpserver/entrypoint.sh /opt/jumpserver/jms
```

### 验证
```bash
# 重新构建镜像
docker build -t test .

# 检查文件权限
docker run --rm test ls -la entrypoint.sh jms
```

---

## 问题2: No such file or directory: '/opt/jumpserver/tmp/gunicorn.pid'

### 错误信息
```
Start service error ['web']: [Errno 2] No such file or directory: '/opt/jumpserver/tmp/gunicorn.pid'
```

### 原因
`/opt/jumpserver/tmp` 目录不存在

### 解决方案
已在 Dockerfile 中添加：
```dockerfile
RUN mkdir -p /opt/jumpserver/tmp \
    /opt/jumpserver/data \
    /opt/jumpserver/logs
```

### 手动解决（临时）
如果已经运行了容器：
```bash
# 进入容器
docker exec -it jumpserver bash

# 创建目录
mkdir -p /opt/jumpserver/tmp /opt/jumpserver/data /opt/jumpserver/logs

# 重启服务
supervisorctl restart all
```

---

## 问题3: 阿里云缓存错误

### 错误信息
```
ERROR: denied: unknown manifest class for application/vnd.buildkit.cacheconfig.v0
```

### 原因
阿里云容器镜像服务不支持 BuildKit 缓存格式

### 解决方案
已在 `.github/workflows/build-and-push.yml` 中修改：
```yaml
# 从 registry cache 改为 inline cache
cache-from: type=registry,ref=registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
cache-to: type=inline
```

---

## 问题4: 数据库连接失败

### 错误信息
```
Database connect failed
Connection database failed, exit
```

### 原因
数据库配置不正确或数据库服务未启动

### 解决方案

#### 方案1: 使用 SQLite（测试环境）
```bash
docker run -d \
  --name jumpserver \
  -e SECRET_KEY=$(head -c100 < /dev/urandom | base64 | tr -dc A-Za-z0-9 | head -c 48) \
  -e BOOTSTRAP_TOKEN=test-token \
  -e DB_ENGINE=sqlite3 \
  -p 8080:8080 \
  registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

#### 方案2: 使用 MySQL（生产环境）
```bash
docker run -d \
  --name jumpserver \
  -e SECRET_KEY=your-secret-key \
  -e BOOTSTRAP_TOKEN=your-token \
  -e DB_ENGINE=mysql \
  -e DB_HOST=mysql-host \
  -e DB_PORT=3306 \
  -e DB_USER=jumpserver \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=jumpserver \
  -e REDIS_HOST=redis-host \
  -e REDIS_PORT=6379 \
  -p 8080:8080 \
  registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

#### 方案3: 使用 Docker Compose
创建 `docker-compose.yml`:
```yaml
version: '3'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: jumpserver
      MYSQL_USER: jumpserver
      MYSQL_PASSWORD: jumpserver123
    volumes:
      - mysql-data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass redis123
    volumes:
      - redis-data:/data

  core:
    image: registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
    depends_on:
      - mysql
      - redis
    environment:
      SECRET_KEY: your-secret-key-here
      BOOTSTRAP_TOKEN: your-token-here
      DB_ENGINE: mysql
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: jumpserver
      DB_PASSWORD: jumpserver123
      DB_NAME: jumpserver
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: redis123
    ports:
      - "8080:8080"
    volumes:
      - jumpserver-data:/opt/jumpserver/data

volumes:
  mysql-data:
  redis-data:
  jumpserver-data:
```

启动：
```bash
docker-compose up -d
```

---

## 问题5: 端口被占用

### 错误信息
```
Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use
```

### 原因
8080 端口已被其他服务占用

### 解决方案

#### 方案1: 使用其他端口
```bash
docker run -d \
  --name jumpserver \
  -p 18080:8080 \
  ...其他参数...
```

#### 方案2: 停止占用端口的服务
```bash
# 查找占用端口的进程
lsof -i :8080  # Linux/Mac
netstat -ano | findstr :8080  # Windows

# 停止进程
kill -9 PID  # Linux/Mac
taskkill /PID PID /F  # Windows
```

---

## 问题6: 容器启动后立即退出

### 检查方法
```bash
# 查看容器状态
docker ps -a

# 查看容器日志
docker logs jumpserver

# 查看最近的日志
docker logs --tail 100 jumpserver
```

### 常见原因和解决方案

#### 原因1: 缺少必需的环境变量
```bash
# 必须设置 SECRET_KEY 和 BOOTSTRAP_TOKEN
docker run -d \
  --name jumpserver \
  -e SECRET_KEY=$(head -c100 < /dev/urandom | base64 | tr -dc A-Za-z0-9 | head -c 48) \
  -e BOOTSTRAP_TOKEN=$(head -c24 < /dev/urandom | base64 | tr -dc A-Za-z0-9 | head -c 24) \
  ...
```

#### 原因2: 配置文件错误
```bash
# 检查配置
docker exec jumpserver cat /opt/jumpserver/config.yml
```

---

## 问题7: 构建失败

### 错误信息
```
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully
```

### 解决方案

#### 检查基础镜像
```bash
# 确认基础镜像存在
docker pull jumpserver/core-base:20251113_092612
```

#### 使用构建参数
```bash
# 使用国内镜像源
docker build \
  --build-arg APT_MIRROR=https://mirrors.aliyun.com/debian \
  --build-arg PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t jumpserver:test .
```

#### 查看详细构建日志
```bash
docker build --progress=plain -t jumpserver:test .
```

---

## 问题8: 网络连接问题

### 症状
```
Error: Get "http://core:8080/api/health/": dial tcp: lookup core on 127.0.0.11:53: no such host
```

### 原因
容器间无法通过主机名互相访问

### 解决方案

#### 方案1: 使用 Docker Network
```bash
# 创建网络
docker network create jumpserver-net

# 启动容器时指定网络
docker run -d \
  --name jumpserver-core \
  --network jumpserver-net \
  registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest

# 其他容器可以通过主机名访问
docker run -d \
  --name other-service \
  --network jumpserver-net \
  -e CORE_HOST=jumpserver-core \
  ...
```

#### 方案2: 使用 Docker Compose
Docker Compose 会自动创建网络，容器可以通过服务名互相访问

---

## 问题9: 性能问题

### 症状
- 容器启动慢
- 响应速度慢
- CPU/内存占用高

### 解决方案

#### 增加资源限制
```bash
docker run -d \
  --name jumpserver \
  --memory="4g" \
  --cpus="2.0" \
  ...
```

#### 优化配置
```yaml
# 在 docker-compose.yml 中
services:
  core:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## 问题10: 数据持久化

### 问题
容器删除后数据丢失

### 解决方案

#### 使用 Volume
```bash
# 创建 volume
docker volume create jumpserver-data

# 挂载 volume
docker run -d \
  --name jumpserver \
  -v jumpserver-data:/opt/jumpserver/data \
  ...
```

#### 使用主机目录
```bash
# 创建主机目录
mkdir -p /opt/jumpserver/data

# 挂载主机目录
docker run -d \
  --name jumpserver \
  -v /opt/jumpserver/data:/opt/jumpserver/data \
  ...
```

---

## 调试技巧

### 1. 进入容器调试
```bash
# 进入运行中的容器
docker exec -it jumpserver bash

# 查看进程
ps aux

# 查看日志
tail -f /opt/jumpserver/logs/*.log
```

### 2. 查看详细日志
```bash
# 查看所有日志
docker logs -f jumpserver

# 查看最近 100 行
docker logs --tail 100 jumpserver

# 查看指定时间的日志
docker logs --since 10m jumpserver
```

### 3. 检查容器状态
```bash
# 查看容器详细信息
docker inspect jumpserver

# 查看容器资源使用
docker stats jumpserver

# 查看容器网络
docker network inspect bridge
```

### 4. 测试网络连接
```bash
# 进入容器
docker exec -it jumpserver bash

# 测试数据库连接
nc -zv mysql-host 3306

# 测试 Redis 连接
redis-cli -h redis-host -p 6379 -a password ping

# 测试 DNS 解析
nslookup mysql-host
```

---

## 获取帮助

### 查看日志位置
```
/opt/jumpserver/logs/gunicorn.log    - Web 服务日志
/opt/jumpserver/logs/celery.log      - 任务队列日志
/opt/jumpserver/tmp/*.log            - 临时日志
```

### 收集诊断信息
```bash
# 导出容器日志
docker logs jumpserver > jumpserver.log 2>&1

# 导出容器配置
docker inspect jumpserver > jumpserver-inspect.json

# 打包诊断信息
tar -czf jumpserver-debug.tar.gz jumpserver.log jumpserver-inspect.json
```

### 联系支持
提供以上诊断信息，以及：
- JumpServer 版本
- 操作系统版本
- Docker 版本
- 完整的错误信息

---

**问题解决文档完成！** 🎉

如遇到其他问题，请查看官方文档：https://docs.jumpserver.org/

