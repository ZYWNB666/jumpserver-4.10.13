# ✅ 镜像配置更新完成

## 🎯 更新内容

### 1. 修改了镜像地址

**旧地址**:
```
registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106
```

**新地址**:
```
registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13-202512052106-abc1234
registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

### 2. 优化了版本号策略

采用**智能版本号**策略，根据不同场景自动生成合适的版本号：

| 触发方式 | 生成的版本号 | 示例 |
|---------|------------|------|
| 推送 Git 标签 | 使用标签名称 | `v4.10.13` |
| 推送代码到分支 | 基础版本-时间戳-commit | `v4.10.13-202512052106-a1b2c3d` |
| 手动触发+后缀 | 基础版本-时间戳-commit-后缀 | `v4.10.13-202512052106-a1b2c3d-beta` |
| 任何构建 | latest（自动更新） | `latest` |

### 3. 修复了阿里云缓存问题

**问题**: 
```
ERROR: denied: unknown manifest class for application/vnd.buildkit.cacheconfig.v0
```

**原因**: 阿里云容器镜像服务不支持 BuildKit 缓存格式

**解决方案**: 改用 inline cache
```yaml
cache-from: type=registry,ref=registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
cache-to: type=inline
```

---

## 📦 镜像版本号详解

### 场景1: 生产发布（推荐）

```bash
# 打标签
git tag v4.10.13
git push origin v4.10.13

# 自动构建，生成镜像:
registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13
```

**特点**:
- ✅ 版本号简洁明了
- ✅ 易于管理和回滚
- ✅ 适合生产环境

---

### 场景2: 日常开发（自动）

```bash
# 推送代码
git commit -m "feat: add feature"
git push origin dev

# 自动构建，生成镜像:
registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13-202512052106-a1b2c3d
```

**版本号组成**:
- `v4.10.13`: 基础版本（对应 JumpServer 版本）
- `202512052106`: 构建时间（2025年12月5日 21:06）
- `a1b2c3d`: Git commit 短 hash

**特点**:
- ✅ 包含完整的追踪信息
- ✅ 可以精确定位到某次提交
- ✅ 适合开发和测试环境

---

### 场景3: 测试版本（手动）

```bash
# 在 GitHub Actions 手动触发
# 输入后缀: beta

# 生成镜像:
registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13-202512052106-a1b2c3d-beta
```

**特点**:
- ✅ 可以标记特殊用途
- ✅ 方便区分不同测试版本
- ✅ 适合预发布测试

---

## 🚀 使用示例

### 拉取镜像

```bash
# 拉取正式版本（生产环境）
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13

# 拉取开发版本（测试环境）
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13-202512052106-a1b2c3d

# 拉取最新版本（快速测试）
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

### 运行容器

```bash
# 使用正式版本
docker run -d \
  --name jumpserver \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e BOOTSTRAP_TOKEN=your-token \
  registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13

# 使用最新版本
docker run -d \
  --name jumpserver \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e BOOTSTRAP_TOKEN=your-token \
  registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

---

## 📋 推荐工作流

### 开发阶段
```bash
# 1. 日常开发，推送代码
git push origin dev

# 2. 自动生成开发版本
# registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13-202512052106-a1b2c3d

# 3. 拉取测试
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
```

### 发布阶段
```bash
# 1. 代码合并到主分支
git checkout main
git merge dev
git push origin main

# 2. 打正式标签
git tag v4.10.13
git push origin v4.10.13

# 3. 自动生成正式版本
# registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13

# 4. 部署生产
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13
```

---

## 🔧 配置修改

如需修改基础版本号，编辑 `.github/workflows/build-and-push.yml`:

```yaml
# 第 43 行，修改基础版本号
BASE_VERSION="v4.10.13"  # 改为你需要的版本
```

---

## 📚 相关文档

- `.github/VERSION_STRATEGY.md` - 详细的版本号策略说明
- `.github/README.md` - 完整使用文档
- `.github/SETUP_GUIDE.md` - 快速上手指南

---

## 💡 最佳实践

### ✅ 推荐

1. **生产环境使用标签版本**
   ```bash
   # 明确指定版本号
   docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:v4.10.13
   ```

2. **开发环境使用 latest**
   ```bash
   # 快速获取最新版本
   docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/jmp-core:latest
   ```

3. **重要版本打标签**
   ```bash
   git tag v4.10.13
   git push origin v4.10.13
   ```

### ❌ 避免

1. ❌ 生产环境使用 `latest`
   - latest 会自动更新，可能导致不可预期的问题

2. ❌ 删除已发布的标签
   - 会导致版本管理混乱

---

## 🎉 总结

### 更新要点

1. ✅ 镜像地址简化: `zywdockers/jmp-core`
2. ✅ 版本号智能化: 自动适配不同场景
3. ✅ 修复了阿里云缓存问题
4. ✅ 增加了详细的版本号文档

### 现在你可以

- ✅ 推送代码自动构建开发版本
- ✅ 打标签发布正式版本
- ✅ 手动触发自定义版本
- ✅ 使用 latest 快速测试

**配置更新完成，现在可以开始使用了！** 🚀

