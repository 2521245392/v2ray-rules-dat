# v2ray-rules-dat 自用版

这是我个人使用的 V2Ray/Xray `geosite.dat` 规则仓库，基于公开上游数据自动整理和构建。

> 本仓库按个人网络环境和分流需求维护，规则内容可能随时调整，不保证适合其他人的配置。需要通用规则时，建议直接使用文末列出的上游项目。

## 主要特点

- 每天北京时间 06:00 通过 GitHub Actions 自动更新和构建。
- 合并 `v2fly/domain-list-community` 与 `blackmatrix7/ios_rule_script` 的相关域名数据。
- `geosite:cn` 使用 Blackmatrix7 的精简 `China_Domain.txt` 中国域名集合。
- `geosite:apple` 仅包含 `apple.china.conf` 中可使用中国大陆 Apple CDN/DNS 的精确域名。
- 生成适用于 V2Ray、Xray-core 等程序的 `geosite.dat`。
- 支持通过 [`direct.txt`](./direct.txt) 维护额外需要直连的域名，无需修改工作流。
- 构建成功后自动发布到 GitHub Releases，并同步到 `release` 分支。
- 每次构建完成后删除旧 Releases 及其标签，只保留最新一次发布。

## 自定义直连域名

在仓库根目录的 [`direct.txt`](./direct.txt) 中每行填写一条规则：

```text
# 匹配 example.com 本身及其所有子域名
example.com

# 只匹配指定的完整域名
full:www.example.com
```

- 空行会被忽略。
- 以 `#` 开头的行是注释。
- 普通域名会匹配该域名本身及其所有子域名。
- `full:` 前缀仅匹配指定的完整域名。
- 修改并推送 `direct.txt` 后，GitHub Actions 会自动重新构建规则文件。

这些自定义规则最终会写入 `geosite:cn`，用于直连分流。

## 下载

- [geosite.dat（GitHub Releases）](https://github.com/2521245392/v2ray-rules-dat/releases/latest/download/geosite.dat)
- [geosite.dat.sha256sum（校验文件）](https://github.com/2521245392/v2ray-rules-dat/releases/latest/download/geosite.dat.sha256sum)
- [geosite.dat（jsDelivr）](https://cdn.jsdelivr.net/gh/2521245392/v2ray-rules-dat@release/geosite.dat)

## 使用示例

下载 `geosite.dat` 并替换程序数据目录中的同名文件，然后在路由配置中引用相应类别。例如：

```json
{
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "outboundTag": "block",
        "domain": ["geosite:category-ads-all"]
      },
      {
        "type": "field",
        "outboundTag": "proxy",
        "domain": ["geosite:gfw", "geosite:geolocation-!cn"]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "domain": ["geosite:cn", "geosite:private"]
      }
    ]
  }
}
```

`outboundTag` 需要根据自己的客户端配置进行调整。

## 数据来源与致谢

- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list)
- [Loyalsoldier/domain-list-custom](https://github.com/Loyalsoldier/domain-list-custom)
- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)

感谢以上项目及其贡献者。本仓库仅用于个人规则整合与自动构建。

## 许可证

本仓库沿用 [GPL-3.0](./LICENSE) 许可证。
