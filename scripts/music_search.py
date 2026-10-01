#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐平台在架核查工具（免登录、免浏览器）

已实测可用的平台接口：
  - netease : 网易云音乐公开搜索 API
  - qq      : QQ音乐 search_for_qq_cp API
  - kugou   : 酷狗音乐 song_search_v2 API

未能攻下的平台（勿假装可用，改用 WebFetch 抓页面）：
  - 酷我 kuwo  : 接口要求 JS 生成的 kw_token，服务端校验，返回 "The request is illegal!"
  - 咪咕 migu  : 搜索接口已改为返回 HTML 页面而非 JSON

用法：
  python3 music_search.py --kw "最佳损友"
  python3 music_search.py --kw "最佳损友" --artist "陈奕迅"
  python3 music_search.py --kw "去年夏天" --artist "王大毛" --platform all
  python3 music_search.py --kw "瞬" --platform qq --limit 5

说明：
  - 纯只读查询，不写入任何文件，不处理任何账号凭证。
  - 接口若失效会明确报错，绝不返回伪造数据。
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

FEE_MAP = {0: "免费", 1: "单曲付费", 4: "专辑付费", 8: "VIP/数字专辑"}


def _get(url, referer, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer,
        "Accept": "application/json, text/plain, */*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def search_netease(kw, limit=8):
    """网易云音乐搜索（已实测可用）。返回 [(歌名, 歌手, 专辑, id, 付费)]"""
    url = ("https://music.163.com/api/search/get?s="
           + urllib.parse.quote(kw) + f"&type=1&limit={limit}")
    data = _get(url, "https://music.163.com/")
    songs = (data.get("result") or {}).get("songs") or []
    out = []
    for s in songs:
        artists = "/".join(a.get("name", "") for a in s.get("artists", []))
        album = (s.get("album") or {}).get("name", "")
        out.append((s.get("name", ""), artists, album,
                    str(s.get("id")), FEE_MAP.get(s.get("fee", 0), s.get("fee"))))
    return out


def search_kugou(kw, limit=8):
    """酷狗音乐搜索（已实测可用）。返回 [(歌名, 歌手, 专辑, id, 付费)]"""
    url = ("https://songsearch.kugou.com/song_search_v2?keyword="
           + urllib.parse.quote(kw)
           + f"&page=1&pagesize={limit}&platform=WebFilter")
    data = _get(url, "https://www.kugou.com/")
    lists = ((data.get("data") or {}).get("lists")) or []
    out = []
    for x in lists:
        # FileName 形如 "陈奕迅 - 最佳损友"，也可能带 (Live) 等后缀
        name = x.get("FileName", "") or ""
        singer = x.get("SingerName", "") or ""
        if " - " in name:
            name = name.split(" - ", 1)[1]
        out.append((name, singer, x.get("AlbumName", "") or "",
                    str(x.get("ID")), ""))
    return out


def search_qqmusic(kw, limit=8):
    """QQ音乐搜索（已实测可用）。返回 [(歌名, 歌手, 专辑, id, 付费)]"""
    url = ("https://c.y.qq.com/soso/fcgi-bin/search_for_qq_cp?w="
           + urllib.parse.quote(kw) + f"&format=json&p=1&n={limit}")
    data = _get(url, "https://y.qq.com/")
    songs = ((data.get("data") or {}).get("song") or {}).get("list") or []
    out = []
    for s in songs:
        singers = "/".join(x.get("name", "") for x in s.get("singer", []))
        out.append((s.get("songname", ""), singers, s.get("albumname", "") or "",
                    str(s.get("songid")), ""))
    return out


PLATFORMS = {
    "netease": ("网易云音乐", search_netease),
    "qq": ("QQ音乐", search_qqmusic),
    "kugou": ("酷狗音乐", search_kugou),
}


def main():
    ap = argparse.ArgumentParser(description="音乐平台在架核查（免登录）")
    ap.add_argument("--kw", required=True, help="搜索关键词（歌名）")
    ap.add_argument("--artist", default="", help="目标歌手名（用于命中标记）")
    ap.add_argument("--platform", default="all",
                    choices=["all", "netease", "qq", "kugou"], help="平台")
    ap.add_argument("--limit", type=int, default=8, help="每平台返回条数")
    args = ap.parse_args()

    targets = (list(PLATFORMS.items()) if args.platform == "all"
               else [(args.platform, PLATFORMS[args.platform])])

    print(f"查询关键词：「{args.kw}」" + (f"  目标歌手：{args.artist}" if args.artist else ""))
    print("=" * 72)

    for key, (label, fn) in targets:
        print(f"\n【{label}】")
        try:
            rows = fn(args.kw, args.limit)
        except Exception as e:
            print(f"   [!] 查询失败（接口可能失效或有风控）: {type(e).__name__}: {e}")
            continue
        if not rows:
            print("   未查到任何结果（注意：关键词组合可能导致误报，建议拆词重试）")
            continue
        hit = False
        for name, singer, album, sid, fee in rows:
            mark = ""
            if args.artist and args.artist in singer:
                mark = "   <<< 命中目标歌手"
                hit = True
            fee_txt = f" | {fee}" if fee else ""
            print(f"   · {name} | 歌手: {singer} | 专辑: {album} | id: {sid}{fee_txt}{mark}")
        if args.artist and not hit:
            print(f"   → 未出现目标歌手「{args.artist}」"
                  f"（可能未上架、署名不同，或需换关键词重试）")
        time.sleep(0.8)

    print("\n" + "=" * 72)
    print("提示：本工具只验证「平台页面上在架」，不验证音频能否实际播放。")


if __name__ == "__main__":
    main()
