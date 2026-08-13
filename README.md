# Minimal geosite.dat

这是一个针对 V2Ray、Xray-core、mihomo 等兼容内核的精简规则构建项目。它只生成 `geosite.dat`，不下载、构建或发布 `geoip.dat`。

## 文件中包含的类别

| 类别 | 建议动作 | 内容 |
|---|---|---|
| `geosite:china-list` | 直连 | 中国大陆可直连域名 |
| `geosite:apple-cn` | 直连 | Apple 在中国大陆可直连域名 |
| `geosite:google-cn` | 直连 | Google 在中国大陆可直连域名 |
| `geosite:gfw` | 代理 | GFWList 域名 |
| `geosite:win-spy` | 按需拦截 | Windows 隐私跟踪域名 |
| `geosite:win-update` | 慎重拦截 | Windows 更新域名 |
| `geosite:win-extra` | 按需拦截 | Windows 附加跟踪域名 |

文件经过构建后会自动验证，确保恰好只有以上七个类别。

## 本地构建

依赖：

- Python 3.10 或更高版本
- Git
- Go（版本要求以编译器的 `go.mod` 为准）

执行：

```powershell
python build.py
```

输出位于 `dist/`：

- `geosite.dat`
- `geosite.dat.sha256sum`
- `manifest.json`（来源、数量、构建时间和校验值）

## 自动更新

将本目录推送到 GitHub 仓库并启用 Actions。工作流会在北京时间每天早上 6 点构建，保存 Workflow Artifact，并创建一个 Release。

## Xray/V2Ray 路由示例

规则按顺序匹配。直连规则应放在代理规则之前：

```json
{
  "routing": {
    "rules": [
      {
        "type": "field",
        "outboundTag": "Direct",
        "domain": [
          "geosite:china-list",
          "geosite:apple-cn",
          "geosite:google-cn"
        ]
      },
      {
        "type": "field",
        "outboundTag": "Proxy",
        "domain": ["geosite:gfw"]
      }
    ]
  }
}
```

如果确实需要屏蔽 Windows 类别，可添加：

```json
{
  "type": "field",
  "outboundTag": "Reject",
  "domain": [
    "geosite:win-spy",
    "geosite:win-extra"
  ]
}
```

不建议默认屏蔽 `geosite:win-update`，否则 Windows Update 和相关微软服务可能异常。

## 数据来源与可重复性

七份规则取自 `Loyalsoldier/v2ray-rules-dat` 的 `release` 分支。编译器使用 `Loyalsoldier/domain-list-custom`，并固定到 `efacb51b8950ae673ebb6dcb9e7ecdd1decb1b6d`，避免编译器在无人审核的情况下变化。规则数据本身仍会随上游每日更新。

本项目只是精简构建器；规则数据和编译器分别遵循各上游项目的许可条款。
