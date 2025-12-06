# 飞书SSO插件安装指南

## 📦 安装步骤

### 步骤1：确认JumpServer版本

飞书SSO插件需要JumpServer 4.x或更高版本。

```bash
# 检查JumpServer版本
./jms --version
```

### 步骤2：确认xpack目录已创建

插件已包含在 `apps/xpack/plugins/feishu_sso/` 目录中。

```bash
# 检查插件目录
ls -la apps/xpack/plugins/feishu_sso/
```

应该看到以下文件：
- `__init__.py`
- `apps.py`
- `auth_backend.py`
- `views.py`
- `urls.py`
- `README.md`
- `sdk/client.py`

### 步骤3：修改JumpServer配置

在JumpServer的 `config.yml` 文件中添加飞书SSO配置：

```yaml
# 飞书SSO配置
FEISHU_SSO_ENABLED: true
FEISHU_SSO_APP_ID: '你的飞书App ID'
FEISHU_SSO_APP_SECRET: '你的飞书App Secret'
FEISHU_SSO_AUTO_CREATE_USER: true
FEISHU_SSO_DEFAULT_ORG_IDS:
  - '00000000-0000-0000-0000-000000000002'
```

### 步骤4：修改JumpServer settings配置

确保xpack已在Django配置中启用。在 `apps/jumpserver/settings/_xpack.py` 中应该已经有类似配置：

```python
XPACK_ENABLED = os.path.isdir(XPACK_DIR)

if XPACK_ENABLED:
    from xpack.utils import get_xpack_templates_dir, get_xpack_context_processor
    INSTALLED_APPS.insert(0, 'xpack.apps.XpackConfig')
    # ...
```

### 步骤5：添加飞书SSO默认配置

在 `apps/jumpserver/conf.py` 的 `Config.defaults` 字典中添加默认值：

```python
defaults = {
    # ... 其他配置 ...
    
    # 飞书SSO配置
    'FEISHU_SSO_ENABLED': False,
    'FEISHU_SSO_APP_ID': '',
    'FEISHU_SSO_APP_SECRET': '',
    'FEISHU_SSO_AUTO_CREATE_USER': False,
    'FEISHU_SSO_ALWAYS_UPDATE_USER': True,
    'FEISHU_SSO_MATCH_BY_EMAIL': False,
    'FEISHU_SSO_USERNAME_FIELD': 'user_id',
    'FEISHU_SSO_DEFAULT_ORG_IDS': [],
}
```

### 步骤6：重启JumpServer

```bash
# 停止JumpServer
./jms stop

# 启动JumpServer
./jms start

# 或者直接重启
./jms restart
```

### 步骤7：验证安装

1. **检查日志**
```bash
tail -f data/logs/jumpserver.log | grep feishu
```

2. **访问登录URL**
```
https://your-jumpserver.com/api/v1/xpack/feishu-sso/login/
```

应该自动跳转到飞书授权页面。

3. **检查状态API**
```bash
curl http://your-jumpserver.com/api/v1/xpack/feishu-sso/status/
```

---

## 🔧 飞书应用配置

### 1. 创建飞书企业自建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 登录后进入「开发者后台」
3. 点击「创建企业自建应用」
4. 填写应用名称和描述
5. 上传应用图标（建议使用JumpServer Logo）

### 2. 配置应用权限

在应用管理页面，进入「权限管理」添加以下权限：

**必需权限：**
- `获取用户基本信息` (contact:user.base:readonly)
- `获取用户身份信息` (authen:identity)

**推荐权限：**
- `获取用户邮箱信息` (contact:user.email:readonly)
- `获取用户手机号` (contact:user.phone:readonly)

点击「申请权限」并等待管理员审核通过。

### 3. 配置网页设置

在应用管理页面，进入「网页」→「网页配置」：

1. **桌面端主页**：`https://your-jumpserver.com/api/v1/xpack/feishu-sso/login/`
2. **移动端主页**：`https://your-jumpserver.com/api/v1/xpack/feishu-sso/login/`

### 4. 配置安全设置

在应用管理页面，进入「安全设置」：

1. **重定向URL**：
   ```
   https://your-jumpserver.com/api/v1/xpack/feishu-sso/callback/
   ```

2. **IP白名单**（可选）：
   如果JumpServer有固定IP，可以添加到白名单提高安全性

### 5. 获取凭证

在应用管理页面，进入「凭证与基础信息」：

1. 复制 **App ID**
2. 复制 **App Secret**
3. 将这两个值填入JumpServer的 `config.yml`

### 6. 发布应用

1. 在应用管理页面，点击「版本管理与发布」
2. 创建版本并提交审核
3. 审核通过后，点击「发布」
4. 将应用添加到工作台

---

## ✅ 功能测试

### 测试1：基本登录流程

1. 访问飞书SSO登录URL
2. 应该跳转到飞书授权页面
3. 授权后应该自动登录JumpServer
4. 检查用户信息是否正确同步

### 测试2：自动创建用户

前提：`FEISHU_SSO_AUTO_CREATE_USER: true`

1. 使用从未登录过的飞书账号
2. 完成授权流程
3. 检查是否自动创建了用户
4. 检查用户的组织归属

### 测试3：用户信息同步

前提：`FEISHU_SSO_ALWAYS_UPDATE_USER: true`

1. 在飞书中修改用户信息（如姓名）
2. 重新登录JumpServer
3. 检查用户信息是否更新

### 测试4：JS-SDK配置

1. 访问JS-SDK配置接口：
   ```bash
   curl "http://your-jumpserver.com/api/v1/xpack/feishu-sso/jssdk/config/?url=http://your-jumpserver.com"
   ```
2. 应该返回包含appId、timestamp、signature等字段的JSON

---

## 🐛 常见问题

### 问题：启动时报错 "No module named 'xpack'"

**解决：**
1. 确认xpack目录存在：`ls apps/xpack/`
2. 检查 `__init__.py` 文件是否存在
3. 重启JumpServer

### 问题：配置后没有生效

**解决：**
1. 检查 `config.yml` 语法是否正确（YAML格式）
2. 确认已重启JumpServer
3. 检查日志是否有错误信息

### 问题：飞书回调提示redirect_uri_mismatch

**解决：**
1. 检查飞书应用后台的重定向URI配置
2. 确保URI完全一致（注意http/https、域名、路径）
3. 不要有多余的斜杠

### 问题：登录成功但没有创建用户

**解决：**
1. 检查 `FEISHU_SSO_AUTO_CREATE_USER` 是否为 `true`
2. 查看日志中的错误信息
3. 检查是否有权限问题

---

## 📊 日志调试

### 启用调试日志

在 `config.yml` 中设置：

```yaml
DEBUG: true
LOG_LEVEL: DEBUG
```

### 查看飞书SSO相关日志

```bash
# 实时查看日志
tail -f data/logs/jumpserver.log | grep -i feishu

# 查看最近的错误
tail -n 100 data/logs/jumpserver.log | grep -i error

# 查看认证相关日志
tail -f data/logs/jumpserver.log | grep -i "authentication\|feishu"
```

---

## 🔄 升级指南

### 升级插件

1. 备份当前配置
2. 替换插件文件
3. 检查配置文件是否有新增项
4. 重启JumpServer
5. 测试功能是否正常

### 回滚

如果升级后出现问题：

1. 停止JumpServer
2. 恢复备份的插件文件
3. 恢复配置文件
4. 启动JumpServer

---

## 📞 技术支持

如遇到问题，请提供以下信息：

1. JumpServer版本
2. 错误日志
3. 配置文件（脱敏后）
4. 问题重现步骤

联系方式：
- GitHub Issues
- 社区论坛
- 技术支持邮箱

---

**祝您使用愉快！** 🎉