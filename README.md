# Persona Studio

通过参考图和角色资产组织 AI 图片生成，探索跨场景角色一致性。

## 安装

需要 Python 3。也可直接在浏览器打开 prototype/index.html 查看界面。

克隆仓库后，在项目根目录执行以下步骤。

```sh
python3 -m persona_studio.server --port 8792
```

## 使用

打开 http://127.0.0.1:8792。建角色，添加参考图，设置场景和风格，再核对生成结果。原型的部分身份处理使用替代实现。

## 检查

```sh
python -m pytest
```

## 说明

仓库包含源码与启动所需的示例。模型、平台或推送服务的凭据由使用者在本机配置。
