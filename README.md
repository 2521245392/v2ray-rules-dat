# Personal geosite.dat

这是一个根据个人 Mihomo/Clash 路由顺序定制的精简规则项目。它只生成 `geosite.dat`，不下载、构建或发布 `geoip.dat`。

## 文件中包含的类别

| 类别 | 建议动作 | 内容 |
|---|---|---|
| `geosite:private` | 直连 | 局域网、本机和特殊用途域名 |
| `geosite:cn` | 直连 | 明确维护为国内可直连的域名、Apple 中国和 Google 中国域名 |
| `geosite:gfw` | 代理 | GFWList 域名 |

文件经过构建后会自动解析验证，确保恰好只有以上三个类别。

个人版的 `geosite:cn` 是一个有意合并的类别：

- `direct-list.txt`：Loyalsoldier 维护的国内可直连域名，但构建时会剔除其中全部裸 TLD 规则
- `apple-cn.txt`：Apple 中国可直连域名
- `google-cn.txt`：Google 中国可直连域名

裸 TLD 排除表取自 `direct-tld-list.txt`，包括 `cn`、`alibaba`、`wang` 等规则。域名仅仅使用某个后缀不能证明服务器位于中国或适合直连，因此本项目不会用后缀把未知域名整体判定为国内流量。

在 UDP/443 拦截规则之前只需要一条 `GEOSITE,cn,DIRECT`。未被域名列表明确收录的网站会继续执行后续规则，并可由 `GEOIP,CN,DIRECT` 根据解析后的服务器 IP 捞回直连。如果一个明确维护的域名同时出现在 `cn` 和 `gfw` 中，因为 `cn` 规则靠前，最终会按预期直连。

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

## 对应的 Mihomo/Clash 路由

```yaml
rules:
  # 1. 局域网和本地域名/IP 最优先
  - GEOSITE,private,DIRECT
  - GEOIP,private,DIRECT,no-resolve

  # 2. 精确 IP 规则
  - IP-CIDR6,2606:4700:4700::1111/128,手动选择
  - IP-CIDR,43.156.187.2/32,DIRECT

  # 3. 明确可直连的国内、Apple 中国和 Google 中国域名放行 QUIC
  - GEOSITE,cn,DIRECT

  # 4. 其余 UDP/443 拒绝，促使海外应用回退 TCP
  - AND,((NETWORK,UDP),(DST-PORT,443)),REJECT

  # 5. GFWList 走代理
  - GEOSITE,gfw,手动选择

  # 6. 未被域名规则收录、但解析到国内 IP 的流量直连
  - GEOIP,CN,DIRECT

  # 7. 兜底
  - MATCH,手动选择
```

`GEOIP,private` 和 `GEOIP,CN` 不属于 `geosite.dat`。客户端仍需提供正常的 GeoIP 数据文件或规则提供器；本项目不会替代它。

## 数据来源与可重复性

`private` 取自 `v2fly/domain-list-community`。`cn` 和 `gfw` 的成品文本取自 `Loyalsoldier/v2ray-rules-dat` 的 `release` 分支。编译器使用 `Loyalsoldier/domain-list-custom`，并固定到 `efacb51b8950ae673ebb6dcb9e7ecdd1decb1b6d`，避免编译器在无人审核的情况下变化。规则数据本身仍会随上游每日更新。

本项目只是精简构建器；规则数据和编译器分别遵循各上游项目的许可条款。
