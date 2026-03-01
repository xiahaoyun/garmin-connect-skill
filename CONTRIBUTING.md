# 贡献指南

感谢您对 Garmin Connect Skill 的兴趣！

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 GitHub Issues 提交：

1. 使用清晰的标题描述问题
2. 描述复现步骤
3. 提供您的环境信息（Python版本、操作系统、手表型号）
4. 如果有错误信息，请提供完整的堆栈跟踪

### 提交代码

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 代码规范

- 遵循 PEP 8 风格指南
- 为新功能添加文档字符串
- 更新 README.md 以反映 API 变化

### 测试

在提交 PR 之前，请确保：

```bash
python3 scripts/garmin_skill.py
python3 scripts/example.py
```

能够正常运行且没有错误。

## 开发路线图

- [ ] 支持更多活动类型（游泳、骑行详细分析）
- [ ] 添加数据可视化功能
- [ ] 支持 Garmin 训练计划获取
- [ ] 添加数据导出为 CSV/GPX 格式
- [ ] 支持多用户数据对比

## 联系方式

- GitHub Issues: [项目 Issues 页面](https://github.com/haoyun/garmin-connect-skill/issues)

## 许可证

通过提交代码，您同意您的贡献将在 MIT 许可证下发布。
