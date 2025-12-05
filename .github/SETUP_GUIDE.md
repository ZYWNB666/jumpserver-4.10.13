## ✅ 完成！GitHub Actions 已精简

### 📂 保留的文件结构

```
.github/
├── workflows/
│   └── build-and-push.yml          ← 唯一的 workflow（Docker 构建和推送）
├── ISSUE_TEMPLATE/                 ← Issue 模板（保留）
│   ├── 1_bug_report.yml
│   ├── 2_question.yml
│   ├── 3_feature_request.yml
│   ├── 4_bug_report_cn.yml
│   ├── 5_question_cn.yml
│   └── 6_feature_request_cn.yml
└── README.md                       ← 使用文档（新增）
```

### 🗑️ 已删除的文件

- ❌ 所有其他 workflow（共17个）
- ❌ PR 模板
- ❌ Release 配置
- ❌ Dependabot 配置
- ❌ LLM 代码审查配置

### 🎯 镜像构建规则

**自动触发条件：**
- 推送到 `main`、`master` 或 `dev` 分支
- 推送 `v*` 标签
- 手动触发（GitHub Actions 页面）

**镜像命名格式：**
```
registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-YYYYMMDDHHmm
```

**示例：**
```
registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106
registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest
```

### ⚙️ 首次使用步骤

#### 1. 配置 GitHub Secrets

访问：`Settings → Secrets and variables → Actions`

添加以下 Secrets：

| 名称 | 值 |
|------|-----|
| `ALIYUN_USERNAME` | 阿里云容器镜像服务用户名 |
| `ALIYUN_PASSWORD` | 阿里云容器镜像服务密码 |

#### 2. 获取阿里云凭证

```bash
# 1. 登录阿里云容器镜像服务
https://cr.console.aliyun.com/

# 2. 进入个人实例 → 访问凭证
# 3. 设置/查看固定密码
```

#### 3. 触发构建

**方式一：推送代码**
```bash
git add .
git commit -m "feat: update code"
git push origin main
```

**方式二：打标签**
```bash
git tag v4.10.13-custom
git push origin v4.10.13-custom
```

**方式三：手动触发**
- 访问 GitHub Actions 页面
- 选择 "Build and Push JumpServer Image"
- 点击 "Run workflow"

### 📊 构建结果

构建成功后会生成：

1. **时间戳镜像**（永久保存）
   ```
   registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106
   ```

2. **latest 镜像**（自动更新）
   ```
   registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest
   ```

3. **构建缓存**（加速后续构建）
   ```
   registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-buildcache
   ```

### 🚀 使用镜像

```bash
# 拉取最新版本
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest

# 拉取指定版本
docker pull registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-202512052106

# 运行容器
docker run -d \
  --name jumpserver \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e BOOTSTRAP_TOKEN=your-bootstrap-token \
  registry.cn-shanghai.aliyuncs.com/zywdockers/images:jmp-core-latest
```

### 📖 详细文档

查看完整文档：`.github/README.md`

### ✨ 特性

- ✅ 自动化构建
- ✅ 镜像缓存（加速构建）
- ✅ 时间戳版本控制
- ✅ Latest 标签自动更新
- ✅ 构建摘要展示
- ✅ 支持手动触发
- ✅ 支持自定义标签后缀

### 🔍 验证构建

访问 GitHub Actions 页面查看构建状态：
```
https://github.com/你的用户名/jumpserver-4.10.13/actions
```

---

**重要提示：**
- ⚠️ 首次使用必须先配置 Secrets
- ⚠️ 确保阿里云镜像仓库已创建
- ⚠️ 时间戳基于 UTC+8（北京时间）

