# 参与贡献

## 流程

1. 按 [《SKILL.md 编写规范》](docs/skill-authoring-guide.md) 在 `skills/<skill-name>/` 下创建 skill。
2. 本地校验:`python scripts/validate.py` 全绿。
3. 提交 PR,CI(validate.yml)必须通过。

## PR 硬性要求

- **对照实验**:每个新 skill 或重大修改,必须做一次"无 skill / 有 skill"对照任务,在 PR 描述中粘贴两侧输出证据(命令、根因、测试),不接受"回答看起来更好"作为证据。
- **供应链审查**:凡含 `scripts/` 或可执行文件(`.sh/.py/.js`)的 skill,PR 中必须列出清单并说明每个文件的作用。
- **安全红线**:不提交密钥、个人路径、私有基础设施地址;安全研究类内容按防御/研究导向撰写。

## 版本

skill 版本写在 `metadata.version`,遵循 semver;发布打 git tag 并写 Release 说明。
