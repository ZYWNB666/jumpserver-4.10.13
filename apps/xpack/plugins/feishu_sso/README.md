# 飞书企业单点登录(SSO)插件

## 📖 概述

飞书SSO插件为JumpServer提供了与飞书（Lark）的深度集成，支持企业用户通过飞书账号快速登录JumpServer，无需记忆额外的用户名和密码。

### 主要功能

✅ **单点登录（SSO）**：用户从飞书工作台点击应用直接登录JumpServer  
✅ **OAuth 2.0认证**：基于标准OAuth 2.0协议，安全可靠  
✅ **自动账号创建**：首次登录自动创建JumpServer账号  
✅ **用户信息同步**：自动同步飞书用户的姓名、邮箱、手机号  
✅ **JS-SDK集成**：支持在飞书客户端内网页免登录  
✅ **灵活配置**：支持多种配置选项，满足不同企业需求  

---

## 🚀 快速开始

### 1. 在飞书开放平台创建应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 进入「开发者后台」→「企业自建应用」
3. 创建新的企业自建应用
4. 记录 **App ID** 和 **App Secret**

### 2. 配置应用权限

在飞书应用管理后台，配置以下权限：

**必需权限：**
- `contact:user.base:readonly` - 获取用户基本信息
- `authen:identity` - 获取用户身份信息

**可选权限：**
- `contact:user.email:readonly` - 获取用户邮箱
- `contact:user.phone:readonly` - 获取用户手机号
- `contact:department.base:readonly` - 获取部门信息（用于组织同步）

### 3. 配置重定向URI

在飞书应用的「安全设置」中，添加重定向URI：

```
https://your-jumpserver.com/api/v1/xpack/feishu-sso/callback/
```

**注意：** 请替换为您实际的JumpServer域名

### 4. 配置JumpServer

编辑JumpServer配置文件 `config.yml`，添加以下配置：

```yaml
# 飞书SSO配置
FEISHU_SSO_ENABLED: true
FEISHU_SSO_APP_ID: 'cli_xxxxxxxxxxxxx'
FEISHU_SSO_APP_SECRET: 'xxxxxxxxxxxxxxxxxxxxx'

# 可选配置
FEISHU_SSO_AUTO_CREATE_USER: true              # 是否自动创建用户
FEISHU_SSO_ALWAYS_UPDATE_USER: true            # 是否每次登录更新用户信息
FEISHU_SSO_MATCH_BY_EMAIL: false               # 是否通过邮箱匹配已存在用户
FEISHU_SSO_USERNAME_FIELD: 'user_id'           # 使用哪个飞书字段作为用户名
FEISHU_SSO_DEFAULT_ORG_IDS:                    # 新用户默认所属组织
  - '00000000-0000-0000-0000-000000000002'
```

### 5. 重启JumpServer

```bash
./jms restart
```

---

## 📝 配置说明

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FEISHU_SSO_ENABLED` | 是否启用飞书SSO | `true` |
| `FEISHU_SSO_APP_ID` | 飞书应用的App ID | `cli_a1b2c3d4e5` |
| `FEISHU_SSO_APP_SECRET` | 飞书应用的App Secret | `xxxxxxxxxxxx` |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `FEISHU_SSO_AUTO_CREATE_USER` | 首次登录是否自动创建用户 | `false` |
| `FEISHU_SSO_ALWAYS_UPDATE_USER` | 每次登录是否更新用户信息 | `true` |
| `FEISHU_SSO_MATCH_BY_EMAIL` | 是否通过邮箱匹配已存在用户 | `false` |
| `FEISHU_SSO_USERNAME_FIELD` | 使用飞书哪个字段作为用户名 | `user_id` |
| `FEISHU_SSO_DEFAULT_ORG_IDS` | 新用户默认加入的组织ID列表 | `[]` |

### 配置说明

**`FEISHU_SSO_AUTO_CREATE_USER`**  
- 设为 `true`：首次通过飞书登录的用户会自动创建JumpServer账号
- 设为 `false`：只有已存在的用户可以登录，未绑定飞书的用户无法登录

**`FEISHU_SSO_MATCH_BY_EMAIL`**  
- 设为 `true`：如果用户未绑定飞书ID，会尝试通过邮箱查找已存在用户并自动绑定
- 设为 `false`：只能通过飞书ID查找用户

**`FEISHU_SSO_USERNAME_FIELD`**  
可选值：`user_id`（飞书用户ID）、`email`（邮箱）、`mobile`（手机号）

---

## 🔗 使用方式

### 方式1：登录页面飞书登录

用户可以在JumpServer登录页面看到「飞书登录」按钮，点击后跳转到飞书授权页面。

**登录URL：**
```
https://your-jumpserver.com/api/v1/xpack/feishu-sso/login/
```

### 方式2：飞书工作台直接登录

1. 在飞书应用管理后台，设置应用的「网页配置」
2. 设置首页地址为：
   ```
   https://your-jumpserver.com/api/v1/xpack/feishu-sso/login/
   ```
3. 用户从飞书工作台点击应用图标，即可自动登录

### 方式3：网页内免登录（可选）

如果您需要在飞书客户端内嵌网页中实现免登录，可以使用以下HTML页面：

```html
<!-- 使用提供的auto_login.html模板 -->
<a href="/static/feishu_sso/auto_login.html">飞书登录</a>
```

---

## 🔧 API接口

### 1. 获取飞书绑定状态

**接口：** `GET /api/v1/xpack/feishu-sso/status/`

**响应示例：**
```json
{
  "bound": true,
  "feishu_id": "ou_xxx",
  "username": "zhangsan"
}
```

### 2. 获取JS-SDK配置

**接口：** `GET /api/v1/xpack/feishu-sso/jssdk/config/?url=<当前页面URL>`

**响应示例：**
```json
{
  "appId": "cli_xxx",
  "timestamp": 1234567890,
  "nonceStr": "abc123",
  "signature": "xxx"
}
```

---

## 🐛 故障排查

### 问题1：点击飞书登录后提示"Feishu SSO is not enabled"

**原因：** 配置未正确启用

**解决：**
1. 检查 `config.yml` 中 `FEISHU_SSO_ENABLED` 是否设为 `true`
2. 重启JumpServer服务

### 问题2：登录后提示"Authentication failed"

**可能原因：**
1. 用户未绑定飞书账号，且未启用自动创建用户
2. 飞书返回的用户信息不完整
3. 用户账号被禁用

**解决：**
1. 检查日志：`tail -f data/logs/jumpserver.log`
2. 确认 `FEISHU_SSO_AUTO_CREATE_USER` 配置
3. 检查用户账号状态

### 问题3：无法获取用户信息

**原因：** 应用权限配置不正确

**解决：**
1. 登录飞书开放平台
2. 检查应用权限配置
3. 确保已添加必需的权限并通过审核

### 问题4：重定向URI不匹配

**错误信息：** `redirect_uri_mismatch`

**解决：**
1. 检查飞书应用后台配置的重定向URI
2. 确保URI完全匹配（包括协议、域名、路径）
3. 注意不要有多余的斜杠

---

## 📊 日志查看

插件的详细日志会记录在JumpServer主日志中：

```bash
# 查看实时日志
tail -f data/logs/jumpserver.log | grep feishu

# 查看错误日志
tail -f data/logs/jumpserver.log | grep ERROR
```

---

## 🔒 安全建议

1. **使用HTTPS**：生产环境必须使用HTTPS协议
2. **定期轮换密钥**：定期更换App Secret
3. **限制权限**：只申请必需的API权限
4. **监控日志**：定期检查登录日志，发现异常及时处理
5. **备份配置**：妥善保管App Secret等敏感信息

---

## 📚 相关文档

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [飞书OAuth 2.0接入指南](https://open.feishu.cn/document/ukTMukTMukTM/ukzN4UjL5cDO14SO3gTN)
- [飞书JS-SDK文档](https://open.feishu.cn/document/uYjL24iN/uYjN3QjL2YzN04iN2cDN)

---

## 💬 支持与反馈

如有问题或建议，请通过以下方式联系：

- 提交Issue到JumpServer GitHub仓库
- 加入JumpServer社区交流群
- 发送邮件至技术支持

---

## 📄 许可证

本插件遵循JumpServer项目的许可证协议。

---

**版本：** 1.0.0  
**更新日期：** 2024-12-06  
**作者：** JumpServer Team