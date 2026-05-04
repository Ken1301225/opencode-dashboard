# opencode-dashboard

🀙🀚🀛🀜🀝🀞 一个用麻将筒子做热力图、支持 twilight 渐变配色的终端 Token 消费可视化面板。

![preview](https://img.shields.io/badge/python-3.8%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

## 特性

- **麻将热力图**：用 Unicode 麻将筒子（🀙→🀞）做 1-6 级密度可视化，天然圆点递进
- **Twilight 渐变**：48 格连续 truecolor 光谱，indigo→rose 平滑过渡
- **光谱图例**：只标注实际出现的密度等级 + 两端边界，支持上下错位防重叠
- **周趋势 sparkline**：每周末尾显示 ▁▂▃▄▅▆▇█ 微柱状图 + 周总量
- **每日明细**：最近 5 个活跃日的 input/output/cache/total 分项统计
- **模型分布**：8 倍分辨率 eighth-block 柱状图（▏▎▍▌▋▊▉█）
- **零依赖**：仅使用 Python 标准库 + sqlite3

## 安装

### 方式一：直接下载使用

```bash
# 克隆仓库
git clone https://github.com/Ken1301225/opencode-dashboard.git
cd opencode-dashboard

# 赋予执行权限
chmod +x opencode-dashboard.py

# 测试运行
python3 opencode-dashboard.py
```

### 方式二：pip 安装（推荐）

```bash
pip install git+https://github.com/Ken1301225/opencode-dashboard.git

# 或者本地安装
git clone https://github.com/Ken1301225/opencode-dashboard.git
cd opencode-dashboard
pip install -e .
```

## 注册命令到 Shell

### Bash

```bash
# 添加到 ~/.bashrc
echo '
# opencode-dashboard
opencode-dashboard() {
    python3 /path/to/opencode-dashboard/opencode-dashboard.py
}
' >> ~/.bashrc

source ~/.bashrc
```

### Zsh

```bash
# 添加到 ~/.zshrc
echo '
# opencode-dashboard
opencode-dashboard() {
    python3 /path/to/opencode-dashboard/opencode-dashboard.py
}
' >> ~/.zshrc

source ~/.zshrc
```

### 使用 pip 安装后的命令

如果通过 pip 安装，会自动注册 `opencode-dashboard` 命令，直接运行：

```bash
opencode-dashboard
```

## 自定义数据库路径

默认读取 `~/.local/share/opencode/opencode.db`，可通过环境变量自定义：

```bash
export OPENCODE_DB=/custom/path/to/opencode.db
opencode-dashboard
```

## 强制启用颜色

如果输出被管道传递或重定向，颜色会自动禁用。可通过环境变量强制启用：

```bash
FORCE_COLOR=1 opencode-dashboard
```

## 效果预览

```
  ╭──────────────────────────────────────────────────────────────────────────╮
  │                    OP  encode  ·  token  dashboard                     │
  │                 160M  ·  $22.42  ·  15d  ·  1988 calls                 │
  │ ──────────────────────────────────────────────────────────────────────── │
  │   ●○○○○○○○○○○○○○○○○○○  input    7.2%                                    │
  │   ○○○○○○○○○○○○○○○○○○○○  output   0.6%                                    │
  │   ●●●●●●●●●●●●●●●●●●○○  cache   92.3%                                    │
  ╰──────────────────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────────────────╮
  │  calendar heatmap                                                        │
  │ ──────────────────────────────────────────────────────────────────────── │
  │        Mon   Tue   Wed   Thu   Fri   Sat   Sun                               │
  │ ──────────────────────────────────────────────────────────────────────── │
  │  Apr 20  🀙    🀙    🀙    🀙    🀙    🀙    🀙                        ▁    27M │
  │  Apr 27  🀛    🀙    🀙    🀞    🀙    🀛    🀚                        ▃   107M │
  │  May 04  🀜                                                      ▁    25M │
  │ ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮                                    │
  │ ↓        ↓         ↓        ↓                  ↓                         │
  │ 🀙 0    🀚 10M     🀛 20M    🀜 30M            🀞 49M                         │
  │ ──────────────────────────────────────────────────────────────────────── │
  │  daily breakdown (last 5 active)                                         │
  │ ──────────────────────────────────────────────────────────────────────── │
  │   → input  ← output  ⛁ cache  ─ total                                     │
  │ ──────────────────────────────────────────────────────────────────────── │
  │  Apr 30  →     2M   ←   132K   ⛁    47M   ─     49M                      │
  │  May 01  →   498K   ←    21K   ⛁     3M   ─      3M                      │
  │  May 02  →     2M   ←   222K   ⛁    15M   ─     17M                      │
  │  May 03  →   573K   ←    43K   ⛁     8M   ─      9M                      │
  │  May 04  →     1M   ←    35K   ⛁    24M   ─     25M                      │
  ╰──────────────────────────────────────────────────────────────────────────╯
```

## 终端要求

- **字体**：需要支持麻将字符（U+1F000+）和方块元素（U+2580+）的等宽字体
  - 推荐：[Nerd Fonts](https://www.nerdfonts.com/) 系列（如 Hack Nerd Font、JetBrainsMono Nerd Font）
  - macOS 默认终端、iTerm2、Windows Terminal、alacritty 均支持良好
- **颜色**：需要支持 truecolor（24-bit）的终端
  - 检测方法：`echo $COLORTERM` 应输出 `truecolor` 或 `24bit`

## 数据结构

本工具读取 opencode 的 SQLite 数据库中的 `message` 表，解析以下 JSON 字段：

```json
{
  "tokens": {
    "total": 1000,
    "input": 100,
    "output": 50,
    "cache": {
      "read": 850
    }
  },
  "cost": 0.001,
  "providerID": "openai",
  "modelID": "gpt-4",
  "role": "assistant"
}
```

## 技术细节

| 组件 | 实现 |
|------|------|
| 热力图符号 | Unicode 麻将筒子 🀙🀚🀛🀜🀝🀞 |
| 颜色系统 | ANSI truecolor 线性插值（6 个 twilight stop） |
| 柱状图 | 左向 eighth-block（▏▎▍▌▋▊▉█） |
| IO 仪表盘 | 空心/实心圆组合（●○） |
| 数据库 | sqlite3 原生查询 |

## License

MIT
