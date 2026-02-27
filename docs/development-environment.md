# 开发环境搭建

## OpenSpec

OpenSpec 是项目使用的开发工作流工具，用于规范需求开发流程和变更管理。

官网：https://github.com/Fission-AI/OpenSpec

### 安装

使用 npm 全局安装最新版本：

```
npm install -g @fission-ai/openspec@latest
```

### 初始化

在项目根目录运行初始化命令，创建 OpenSpec 配置：

```
openspec init
```

### 更新

定期更新 OpenSpec 到最新版本：

```
openspec update
```

### 使用方式

项目通过 opsx 命令（OpenSpec 的封装）进行开发工作流管理，详见 CLAUDE.md 中的开发流程规范。

## GitHub CLI (gh)

GitHub CLI 是 GitHub 的官方命令行工具，项目的某些技能（如 GitHub PR 审查）需要使用 `gh` 命令。

官网：https://cli.github.com/

### 安装

安装指南：https://github.com/cli/cli#installation

### 认证

安装完成后，需要创建 GitHub Personal Access Token 并进行认证。

**创建 Token**:

1. 访问 https://github.com/settings/apps
2. 点击 "Personal access tokens" → "Fine-grained tokens"
3. 点击 "Generate new token"
4. 设置 Token 名称、有效期和访问范围（选择需要访问的仓库）
5. 选择所需权限：
   - Repository permissions:
     - `Contents` - Read and write（用于 PR 操作）
     - `Pull requests` - Read and write（用于 PR 审查）
6. 点击生成并复制 Token

**认证**:

```bash
gh auth login
# 选择 GitHub.com
# 选择 HTTPS
# 粘贴刚才创建的 Token
```

**验证**:

```bash
gh auth status
```

## Claude Code 配置

### 插件安装

在项目根目录运行以下命令安装插件：

```bash
claude plugin marketplace add OneDragon-Anything/OneDragon-CC-Plugins
```

#### 所需插件列表

- uv-pyright-lsp - 使用uv run运行的LSP server
