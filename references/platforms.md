# 平台查询方法速查（含实测状态）

> 状态标注：`✅已实测` = 本人在沙箱跑通过；`⚠️` = 有条件可用；`❌` = 已失效或拿不到。
> 最后实测时间：2026-09-25

## 一、免登录 API（首选，最快最硬）

| 平台 | 状态 | 接口 | 关键 Header |
|------|------|------|------------|
| **网易云音乐** | ✅ 已实测 | `https://music.163.com/api/search/get?s=<关键词>&type=1&limit=8` | `Referer: https://music.163.com/` + 正常 UA |
| **QQ音乐** | ✅ 已实测 | `https://c.y.qq.com/soso/fcgi-bin/search_for_qq_cp?w=<关键词>&format=json&p=1&n=8` | `Referer: https://y.qq.com/` + 正常 UA |
| **酷狗音乐** | ✅ 已实测 | `https://songsearch.kugou.com/song_search_v2?keyword=<关键词>&page=1&pagesize=8&platform=WebFilter` | `Referer: https://www.kugou.com/` + 正常 UA |

三家**均无需登录、无需浏览器、无需 JS 渲染**，直接 curl/urllib 即可，返回 JSON。
国内主流已覆盖：网易云 + QQ音乐 + 酷狗（后两者同属腾讯音乐 TME，另有酷我属同集团）。

字段要点：
- 网易云：`result.songs[]` → `name` / `artists[].name` / `album.name` / `id` / `fee`（0免费 1单曲付费 4专辑付费 8 VIP/数字专辑）
- QQ音乐：`data.song.list[]` → `songname` / `singer[].name` / `albumname` / `songid` / `songmid`
- 酷狗：`data.lists[]` → `FileName`（形如"歌手 - 歌名"）、`SingerName`、`AlbumName`、`ID`

> 交叉验证技巧：QQ音乐 `songid` 可直接拼进详情页接口
> `i.y.qq.com/v8/fcg-bin/fcg_get_song_detail.fcg?songid=<id>&tpl=h5`
> 用 WebFetch 抓该页可拿到**发行公司、词曲、编曲、首次发行时间**——搜索 API 拿不到这些，二者配合最完整。

## 二、WebFetch 可抓的真实页面（次选）

| 页面 | 状态 | 说明 |
|------|------|------|
| QQ音乐单曲详情接口页 `i.y.qq.com/v8/fcg-bin/fcg_get_song_detail.fcg?songid=<id>&tpl=h5` | ✅ 已实测 | 能拿到演唱/词/曲/编曲/专辑/首次发行时间/**发行公司**/语种/流派 |
| 酷狗专辑页 `www2.kugou.kugou.com/yueku/v8/album/single/<id>-91.html` | ✅ 已实测 | 能拿到演唱者/发行时间/企划介绍/词曲署名 |
| 百科页（百度百科、快懂百科） | ✅ 一般可抓 | 聚合信息，多源一致时可采信 |
| Apple Music / Spotify 歌曲页 | ✅ 一般可抓 | **国际平台 ©/℗ 署名是最硬的版权证据** |

## 三、❌ 已失效 / 拿不到

| 目标 | 状态 | 备注 |
|------|------|------|
| QQ音乐 `c.y.qq.com/soso/fcgi-bin/client_search_cp?...` | ❌ 返回空 | 老接口已废弃，勿用（改用上面 `search_for_qq_cp`） |
| **酷我** `www.kuwo.cn/api/www/search/searchMusicBykeyWord?...` | ❌ `"The request is illegal!"` | 已试 4 种方案全败：加 `httpsStatus`、空 cookie、假 `kw_token`、**先取首页 cookie 再请求**——均失败。其 token 由前端 JS 生成、服务端校验，接口层拿不到。**改走 WebFetch 抓 `kuwo.cn` 歌曲页** |
| **咪咕** `music.migu.cn/v3/api/search/searchAll?...` | ❌ 返回 HTML | 接口已下线改为页面渲染，**改走 WebFetch / WebSearch** |
| QQ音乐 `client_music_search_song` / `fcg_global_search_cp` | ❌ HTTP 404 | 已失效 |
| 网易云 SPA 搜索页（hash 路由）用无头浏览器渲染 | ⚠️ 能渲染但拿不到结果 | 搜索走异步接口，SPA 直接打开会显示"未能找到相关搜索结果"，**不等于没有这首歌**，改用 API |
| 需登录的会员内容、私人歌单 | ❌ 拿不到 | 需用户自行导出 cookie |
| 微博 / 强反爬站点 | ❌ 拿不到 | — |
| **音频流能否实际播放** | ❌ 无法验证 | 只能验证"页面在架"，不能验证"能播" |

## 四、无头浏览器（兜底，playwright 已装）

仅当 API 与 WebFetch 都失效时使用：

```python
from playwright.sync_api import sync_playwright
# chromium 已装: /usr/bin/chromium；playwright 浏览器已下载 chromium-1208
# 必须加 --no-sandbox
```

用途：渲染 JS 页面、进 iframe、绕过简单静态限制。
**不要指望它解决登录态**——登录需账号凭证，见 SKILL.md 铁律 4。

## 五、国际平台版权署名（最强证据）

- **Spotify** 单曲页底部：`© <年份> xxx` / `℗ <年份> xxx` —— 直接给出录音版权与词曲版权主体
- **Apple Music / Shazam**：常标注发行方（如 "UMG China"）
- 这些**比国内百科/聚合文可靠得多**，核查版权时优先找

## 六、必须警惕的坑（血泪经验）

1. **「歌手+空格+歌名」会误报无结果**：网易云 API 对带空格组合词处理差。搜"王大毛 去年夏天"返回空，但拆开搜就命中。**永远拆词重试再下结论。**
2. **聚合文模板化**：今日头条一类"《XX》去哪听原版：全平台播放渠道解析"文章高度模板化、常带营销倾向（反复提"抖音精选"），**只能作辅助佐证，不可当主证据**。
3. **翻唱/翻唱 Cover 会污染结果**：如搜《去年夏天》会出现"柒玖 - 去年夏天 (Cover 王大毛)"，**不是原唱**，必须核对歌手署名。
4. **同一首歌多版本**：录音室版 / Live 版 / Remix 版 / 伴奏版，问"有没有"时要区分。
5. **平台在架会变**：下架、版权到期轮换常见，**必须在回答里注明核查时间**。
