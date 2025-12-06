# JumpServer XPack 扩展包

## 概述

XPack是JumpServer的扩展包目录，用于存放各种功能插件。本目录采用模块化设计，每个插件独立开发和维护。

## 目录结构

```
apps/xpack/
├── __init__.py              # 包初始化文件
├── apps.py                  # Django App配置
├── utils.py                 # 工具函数
├── README.md                # 本文档
├── urls/                    # URL路由
│   ├── __init__.py
│   └── api_urls.py         # API路由配置
├── templates/               # 模板文件
│   └── feishu_sso/         # 飞书SSO模板
└── plugins/                 # 插件目录
    ├── __init__.py
    └── feishu_sso/         # 飞书SSO插件
        ├── __init__.py
        ├── apps.py
        ├── auth_backend.py  # 认证后端
        ├── views.py         # 视图
        ├── urls.py          # 路由
        ├── README.md        # 插件文档
        ├── INSTALL.md       # 安装指南
        ├── config_example.yml  # 配置示例
        └── sdk/             # SDK客户端
            ├── __init__.py
            └── client.py    # 飞书API客户端
```

## 已安装插件

### 1. 飞书SSO插件 (feishu_sso)

**功能：** 提供飞书（Lark）企业单点登录功能

**特性：**
- OAuth 2.0 标准认证
- 自动创建和同步用户
- JS-SDK支持网页内免登录
- 灵活的配置选项

**文档：**
- [使用文档](plugins/feishu_sso/README.md)
- [安装指南](plugins/feishu_sso/INSTALL.md)
- [配置示例](plugins/feishu_sso/config_example.yml)

**快速开始：**
```yaml
# 在config.yml中添加
FEISHU_SSO_ENABLED: true
FEISHU_SSO_APP_ID: 'your_app_id'
FEISHU_SSO_APP_SECRET: 'your_app_secret'
```

## 开发新插件

### 插件目录结构

```
apps/xpack/plugins/your_plugin/
├── __init__.py              # 插件初始化
├── apps.py                  # Django App配置
├── models.py                # 数据模型（可选）
├── views.py                 # 视图
├── urls.py                  # URL路由
├── serializers.py           # 序列化器（可选）
├── README.md                # 插件文档
└── templates/               # 模板文件（可选）
```

### 开发步骤

#### 1. 创建插件目录

```bash
mkdir -p apps/xpack/plugins/your_plugin
```

#### 2. 创建基础文件

**`__init__.py`**
```python
# -*- coding: utf-8 -*-
#
default_app_config = 'xpack.plugins.your_plugin.apps.YourPluginConfig'
```

**`apps.py`**
```python
# -*- coding: utf-8 -*-
#
from django.apps import AppConfig

class YourPluginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xpack.plugins.your_plugin'
    verbose_name = '你的插件名称'
    
    def ready(self):
        """插件初始化逻辑"""
        pass
```

**`urls.py`**
```python
# -*- coding: utf-8 -*-
#
from django.urls import path
from . import views

app_name = 'your_plugin'

urlpatterns = [
    path('example/', views.ExampleView.as_view(), name='example'),
]
```

#### 3. 注册插件路由

在 `apps/xpack/urls/api_urls.py` 中添加：

```python
path('your-plugin/', include('xpack.plugins.your_plugin.urls', namespace='your-plugin')),
```

#### 4. 添加配置支持

在 `apps/jumpserver/conf.py` 的 `Config.defaults` 中添加：

```python
'YOUR_PLUGIN_ENABLED': False,
'YOUR_PLUGIN_OPTION': 'default_value',
```

#### 5. 编写文档

创建 `README.md` 和 `INSTALL.md` 文档。

### 最佳实践

1. **遵循Django规范**
   - 使用Django的App结构
   - 遵循MTV设计模式
   - 使用Django的认证和权限系统

2. **错误处理**
   - 使用try-except捕获异常
   - 记录详细的错误日志
   - 提供友好的错误提示

3. **日志记录**
   ```python
   from common.utils import get_logger
   logger = get_logger(__file__)
   logger.info('操作成功')
   logger.error('操作失败', exc_info=True)
   ```

4. **配置管理**
   - 所有配置项都应有默认值
   - 敏感信息使用环境变量
   - 提供配置示例文件

5. **测试**
   - 编写单元测试
   - 编写集成测试
   - 提供测试数据

6. **文档**
   - 编写详细的README
   - 提供安装指南
   - 编写API文档
   - 提供故障排查指南

## 插件开发规范

### 命名规范

- 插件目录：使用小写字母和下划线，如 `feishu_sso`
- Python模块：使用小写字母和下划线
- 类名：使用驼峰命名法，如 `FeishuSSOClient`
- URL路由：使用小写字母和连字符，如 `/feishu-sso/login/`

### 代码规范

- 遵循PEP 8编码规范
- 使用类型提示（Python 3.6+）
- 编写详细的docstring
- 保持代码简洁和可读性

### 安全规范

- 验证所有用户输入
- 使用Django的CSRF保护
- 敏感数据加密存储
- 记录安全相关操作
- 定期更新依赖包

## 贡献指南

欢迎为XPack贡献插件！

### 提交插件

1. Fork JumpServer仓库
2. 创建插件分支
3. 开发和测试插件
4. 编写文档
5. 提交Pull Request

### 代码审查

所有插件都会经过以下审查：

- 代码质量
- 安全性
- 性能
- 文档完整性
- 测试覆盖率

## 常见问题

### Q: 如何禁用某个插件？

A: 在配置文件中设置相应的 `ENABLED` 选项为 `false`。

### Q: 插件之间如何通信？

A: 可以使用Django的信号机制或直接导入其他插件的模块。

### Q: 如何调试插件？

A: 启用DEBUG模式，查看日志文件：
```bash
tail -f data/logs/jumpserver.log | grep your_plugin
```

### Q: 插件可以修改核心代码吗？

A: 不建议。应该使用Django的钩子机制（signals、middleware等）来扩展功能。

## 许可证

XPack及所有插件遵循JumpServer项目的许可证协议。

## 技术支持

- 文档：https://docs.jumpserver.org/
- GitHub：https://github.com/jumpserver/jumpserver
- 社区：https://community.jumpserver.org/

---

**版本：** 1.0.0  
**更新日期：** 2024-12-06