import os
import random
import sys
from datetime import datetime
import svgwrite

# 修复导入问题 - 添加路径处理
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from github_api import get_contributions
except ImportError:
    # 如果从不同位置运行时的后备方案
    from scripts.github_api import get_contributions

# 配置参数
USERNAME = os.getenv('GITHUB_USER', 'jamespaulzhang')
TOKEN = os.getenv('GH_TOKEN')
SVG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), "minesweeper.svg")
STYLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), "assets", "styles.css")

# 难度设置
MINE_PROB_NO_COMMIT = 0.7  # 无commit时的地雷概率
MINE_PROB_COMMIT = 0.1     # 有commit时的地雷概率

def generate_minesweeper_svg():
    """生成扫雷风格贡献图"""
    try:
        print(f"开始生成扫雷图，用户: {USERNAME}")
        print(f"SVG文件路径: {SVG_FILE}")
        print(f"样式文件路径: {STYLE_FILE}")
        
        # 1. 获取贡献数据
        calendar = get_contributions(USERNAME, TOKEN)
        weeks = calendar["weeks"]
        print(f"获取到 {len(weeks)} 周数据")
        
        # 提取最近7周数据
        recent_weeks = weeks[-7:]
        contributions = []
        
        for week in recent_weeks:
            week_data = [0] * 7  # 初始化一周7天
            for day in week["contributionDays"]:
                try:
                    date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
                    weekday = date_obj.weekday()  # 0=周一, 6=周日
                    week_data[weekday] = day["contributionCount"]
                except Exception as e:
                    print(f"日期解析错误: {e}")
            contributions.append(week_data)
        
        print("贡献数据:")
        for i, week in enumerate(contributions):
            print(f"周 {i+1}: {week}")
        
        # 2. 创建SVG画布
        cell_size = 25
        padding = 10
        width = 7 * cell_size + 2 * padding
        height = 7 * cell_size + 2 * padding + 30  # 额外空间用于标题
        
        dwg = svgwrite.Drawing(SVG_FILE, (f"{width}px", f"{height}px"))
        dwg.viewbox(0, 0, width, height)
        
        # 添加CSS样式
        if os.path.exists(STYLE_FILE):
            with open(STYLE_FILE) as f:
                css = f.read()
            dwg.defs.add(dwg.style(css))
            print("已加载样式文件")
        else:
            print(f"警告: 样式文件不存在 {STYLE_FILE}")
        
        # 3. 添加标题
        last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        title = dwg.text(
            f"GitHub Minesweeper - {USERNAME} (Updated: {last_updated})",
            insert=(width/2, 20),
            text_anchor="middle",
            class_="title"
        )
        dwg.add(title)
        
        # 4. 生成扫雷格子
        mine_grid = []
        y_offset = 40
        
        # 首先创建完整的地雷网格
        for y, week in enumerate(contributions):
            row = []
            for x, count in enumerate(week):
                # 确定格子类型
                if count == 0:
                    cell_type = "mine" if random.random() < MINE_PROB_NO_COMMIT else "empty"
                else:
                    cell_type = "safe" if random.random() < (1 - MINE_PROB_COMMIT) else "mine"
                row.append(cell_type)
            mine_grid.append(row)
        
        print("地雷网格:")
        for i, row in enumerate(mine_grid):
            print(f"行 {i+1}: {row}")
        
        # 然后绘制所有格子并计算邻居
        for y in range(len(contributions)):
            for x in range(7):
                cell_type = mine_grid[y][x]
                
                # 绘制格子
                rect = dwg.rect(
                    (x * cell_size + padding, y * cell_size + y_offset),
                    (cell_size - 2, cell_size - 2),
                    class_=f"cell {cell_type}"
                )
                dwg.add(rect)
                
                # 添加内容
                if cell_type == "mine":
                    text = dwg.text("💣", 
                        insert=(x * cell_size + padding + cell_size/2 - 6, 
                                y * cell_size + y_offset + cell_size/2 + 6),
                        class_="emoji"
                    )
                    dwg.add(text)
                else:
                    # 计算周围地雷数
                    neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            # 确保索引在有效范围内
                            if 0 <= ny < len(mine_grid) and 0 <= nx < 7:
                                if mine_grid[ny][nx] == "mine":
                                    neighbors += 1
                    
                    if neighbors > 0:
                        text = dwg.text(str(neighbors),
                            insert=(x * cell_size + padding + cell_size/2, 
                                    y * cell_size + y_offset + cell_size/2 + 6),
                            class_=f"number num-{min(neighbors, 8)}"
                        )
                        dwg.add(text)
        
        # 5. 添加图例
        legend_y = y_offset + 7 * cell_size + 10
        legend_items = [
            ("safe", "安全区 (有commit)", "#2ecc71"),
            ("mine", "地雷区 (无commit)", "#e74c3c"),
            ("empty", "空白区", "#3498db")
        ]
        
        for i, (cls, label, color) in enumerate(legend_items):
            dwg.add(dwg.rect((10 + i*150, legend_y), (15, 15), class_="cell " + cls))
            dwg.add(dwg.text(label, (30 + i*150, legend_y + 12), class_="legend-text"))
        
        dwg.save()
        print("SVG生成成功！")
        return True
    
    except Exception as e:
        import traceback
        print(f"生成SVG时出错: {e}")
        print(traceback.format_exc())
        # 创建错误信息SVG
        error_dwg = svgwrite.Drawing(SVG_FILE, ("400px", "100px"))
        error_dwg.add(error_dwg.text(f"Error: {str(e)}", insert=(20, 50), fill="red"))
        error_dwg.save()
        return False

if __name__ == "__main__":
    if generate_minesweeper_svg():
        print("扫雷图生成成功！")
    else:
        print("扫雷图生成失败！")
        sys.exit(1)
