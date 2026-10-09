#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""worklog_template.py — 生成/补齐「工作日志模板」（幕布 Markdown 骨架）。

两种模式：
  A. 从零生成：--year 2026 [--holidays holidays.json]          全年工作日周骨架 + 非双休节假日节点
  B. 补齐现有：--input existing.md [--year 2026]               保留现有内容，插入缺失节假日节点、
                                                               追加剩余工作日周节点

格式规范见 ../references/worklog-format.md，节假日数据见 ../references/holidays-cn.md。
日期/星期必须用本脚本的 datetime 计算；跨年度时先用当年官方通知替换内置节假日数据。
"""
import argparse
import datetime as dt
import io
import json
import re
import sys

# ---------------------------------------------------------------------------
# 内置数据：2026 年官方安排（国办发明电〔2025〕7号）
# 来源：https://www.gov.cn/zhengce/content/202511/content_7047090.htm
# 新年度：替换 year/holidays/makeup_workdays，或 --holidays 传入同结构 JSON。
# ---------------------------------------------------------------------------
HOLIDAYS_2026 = {
    "year": 2026,
    "notice": "国办发明电〔2025〕7号",
    "source": "https://www.gov.cn/zhengce/content/202511/content_7047090.htm",
    "holidays": [
        {"name": "元旦假期",     "start": "2026-01-01", "end": "2026-01-03",
         "desc": "元旦：1月1日（周四）至3日（周六）放假调休，共3天；1月4日（周日）上班"},
        {"name": "春节假期",     "start": "2026-02-15", "end": "2026-02-23",
         "desc": "春节：2月15日（周日）至23日（周一）放假调休，共9天；2月14日（周六）、2月28日（周六）上班"},
        {"name": "清明节假期",   "start": "2026-04-04", "end": "2026-04-06",
         "desc": "清明节：4月4日（周六）至6日（周一）放假，共3天"},
        {"name": "劳动节假期",   "start": "2026-05-01", "end": "2026-05-05",
         "desc": "劳动节：5月1日（周五）至5日（周二）放假调休，共5天；5月9日（周六）上班"},
        {"name": "端午节假期",   "start": "2026-06-19", "end": "2026-06-21",
         "desc": "端午节：6月19日（周五）至21日（周日）放假，共3天"},
        {"name": "中秋节假期",   "start": "2026-09-25", "end": "2026-09-27",
         "desc": "中秋节：9月25日（周五）至27日（周日）放假，共3天"},
        {"name": "国庆节假期",   "start": "2026-10-01", "end": "2026-10-07",
         "desc": "国庆节：10月1日（周四）至7日（周三）放假调休，共7天；9月20日（周日）、10月10日（周六）上班"},
    ],
    # 调休上班日（周六/周日上班）
    "makeup_workdays": ["2026-01-04", "2026-02-14", "2026-02-28",
                        "2026-05-09", "2026-09-20", "2026-10-10"],
}


def load_holidays(year, holidays_json=None):
    if holidays_json:
        with io.open(holidays_json, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("year") != year:
            print(f"警告: 节假日数据年份 {data.get('year')} 与 --year {year} 不一致", file=sys.stderr)
        return data
    return HOLIDAYS_2026


def parse_date(s):
    return dt.date.fromisoformat(s)


def fmt_mmdd(d):
    return f"{d.month:02d}{d.day:02d}"


def compute_workdays(year, holidays):
    """全年工作日：周一~周五 + 调休上班日，剔除节假日区间。返回升序 date 列表。"""
    holiday_ranges = []
    for h in holidays["holidays"]:
        holiday_ranges.append((parse_date(h["start"]), parse_date(h["end"])))
    makeup = {parse_date(s) for s in holidays.get("makeup_workdays", [])}
    workdays = []
    d = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31)
    while d <= end:
        in_holiday = any(s <= d <= e for s, e in holiday_ranges)
        is_weekend = d.weekday() >= 5
        if (not is_weekend or d in makeup) and not in_holiday:
            workdays.append(d)
        d += dt.timedelta(days=1)
    return workdays


def group_weeks(workdays):
    """连续工作日分组（相邻日差 1 天为一组）。"""
    if not workdays:
        return []
    weeks, cur = [], [workdays[0]]
    for d in workdays[1:]:
        if (d - cur[-1]).days == 1:
            cur.append(d)
        else:
            weeks.append(cur)
            cur = [d]
    weeks.append(cur)
    return weeks


def week_heading(seg):
    """周标题：同月 `# MMDD-DD`，跨月 `# MMDD-MMDD`，单日 `# MMDD`。"""
    start, end = seg[0], seg[-1]
    s = fmt_mmdd(start)
    if len(seg) == 1:
        return f"# {s}"
    e = fmt_mmdd(end) if end.month != start.month else f"{end.day:02d}"
    return f"# {s}-{e}"


def day_nodes(seg):
    """日期节点（与用户既有格式一致）：
    段内首月日期 `- DD`（不补零，如 `- 4`）；非首月的每月首日 `- MMDD`
    （如 `- 0401`），该月其余日 `- DD`（补零，如 `- 02`）。"""
    out, first_month, prev_month = [], seg[0].month, None
    for d in seg:
        if d.month == first_month:
            out.append(f"- {d.day}")
        else:
            if prev_month is not None and d.month != prev_month:
                out.append(f"- {fmt_mmdd(d)}")
            else:
                out.append(f"- {d.day:02d}")
        prev_month = d.month
    return out


def holiday_lines(h, with_desc=True):
    start, end = parse_date(h["start"]), parse_date(h["end"])
    e = fmt_mmdd(end) if end.month != start.month else f"{end.day:02d}"
    lines = [f"# {fmt_mmdd(start)}-{e}-{h['name']}"]
    if with_desc and h.get("desc"):
        lines.append(f"> {h['desc']}")
    return lines


def parse_existing_headings(lines):
    """解析现有文档的周标题：返回 (开始date, 结束date, 行号) 列表。"""
    out = []
    pat_full = re.compile(r"^# (\d{4})-(\d{2,4})(?:-|\s|$)")
    pat_single = re.compile(r"^# (\d{4})(?:-|\s|$)")
    for i, ln in enumerate(lines):
        m = pat_full.match(ln)
        if m:
            # 年份由调用方补全，这里先解析月日
            s_month, s_day = int(m.group(1)[:2]), int(m.group(1)[2:])
            e = m.group(2)
            e_month, e_day = (int(e[:2]), int(e[2:])) if len(e) == 4 else (s_month, int(e))
            out.append((s_month, s_day, e_month, e_day, i))
        else:
            m = pat_single.match(ln)
            if m:
                out.append((int(m.group(1)[:2]), int(m.group(1)[2:]),
                            int(m.group(1)[:2]), int(m.group(1)[2:]), i))
    return out


def build(year, holidays, input_lines=None, with_desc=True):
    """生成补齐后的 Markdown 行列表。"""
    def d8(y, m, d):
        return dt.date(y, m, d)

    if input_lines is None:
        # 模式 A：全年骨架（节假日按时间插入到工作日段之间）
        segs = group_weeks(compute_workdays(year, holidays))
        events = []  # (起始日, 排序键, 行)
        for h in holidays["holidays"]:
            hs = parse_date(h["start"])
            if hs.year == year:
                events.append((hs, 0, holiday_lines(h, with_desc)))
        for seg in segs:
            events.append((seg[0], 1, [week_heading(seg)] + day_nodes(seg)))
        events.sort(key=lambda x: (x[0], x[1]))
        return [ln for _, _, lines in events for ln in lines]

    # 模式 B：补齐现有文档
    src = [l.rstrip() for l in input_lines]
    heads = parse_existing_headings(src)
    if not heads:
        # 无任何周标题：退化为全年骨架
        return build(year, holidays, None, with_desc)

    # 年份补全：用给定 year，若标题月日属于去年（如 1月 且 year 初）由调用方保证
    def to_date(month, day):
        return d8(year, month, day)

    last_end = to_date(heads[-1][2], heads[-1][3])
    covered = [(to_date(sm, sd), to_date(em, ed)) for sm, sd, em, ed, _ in heads]

    # 需要插入的节假日：未被现有标题区间覆盖
    need = []
    for h in holidays["holidays"]:
        hs, he = parse_date(h["start"]), parse_date(h["end"])
        if hs.year != year:
            continue
        if any(s <= hs and he <= e for s, e in covered):
            continue  # 已被现有周覆盖（如春节在原文已标注）
        need.append(h)
    need.sort(key=lambda h: parse_date(h["start"]))

    # 插入位置：第一个开始日期在节假日结束日之后的标题行号；否则追加到文末
    insert_at = {}
    for h in need:
        he = parse_date(h["end"])
        pos = None
        for sm, sd, em, ed, i in heads:
            if to_date(sm, sd) > he:
                pos = i
                break
        insert_at[pos] = insert_at.get(pos, []) + [h]

    # 剩余工作日：从最后已记录周结束日的次日 到 年底
    rest = [d for d in compute_workdays(year, holidays) if d > last_end]
    rest_segs = group_weeks(rest)

    out = []
    for i, ln in enumerate(src):
        if i in insert_at:
            for h in insert_at[i]:
                out.extend(holiday_lines(h, with_desc))
        out.append(ln)
    # 末尾：未插入的节假日（在最后标题之后）+ 剩余周
    for h in insert_at.get(None, []):
        out.extend(holiday_lines(h, with_desc))
    for seg in rest_segs:
        out.append(week_heading(seg))
        out.extend(day_nodes(seg))
    return out


def main():
    ap = argparse.ArgumentParser(description="生成/补齐工作日志模板 Markdown")
    ap.add_argument("--year", type=int, default=2026, help="目标年份（默认 2026）")
    ap.add_argument("--holidays", default=None, help="官方安排 JSON（同内置结构）")
    ap.add_argument("--input", default=None, help="现有文档 Markdown 文件路径（补齐模式）")
    ap.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    ap.add_argument("--no-desc", action="store_true", help="节假日节点不带官方安排备注")
    args = ap.parse_args()

    holidays = load_holidays(args.year, args.holidays)
    input_lines = None
    if args.input:
        with io.open(args.input, encoding="utf-8") as f:
            input_lines = f.read().splitlines()

    out = build(args.year, holidays, input_lines, with_desc=not args.no_desc)
    text = "\n".join(out) + "\n"
    if args.output:
        with io.open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"已写入 {args.output}（{len(out)} 行）", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
