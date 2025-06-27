import os
import random
from datetime import datetime, timedelta
import svgwrite
from .github_api import get_contributions

# 配置参数
USERNAME = os.getenv('GITHUB_USER', 'jamespaulzhang')
TOKEN = os.getenv('GH_TOKEN')
SVG_FILE = "../minesweeper.svg"
STYLE_FILE = "../assets/styles.css"

# 难度设置
MINE_PROB_NO_COMMIT = 0.7  # 无commit时的地雷概率
MINE_PROB_COMMIT = 0.1     # 有commit时的地雷概率

def generate_minesweeper_svg():
    """生成扫雷风格贡献图"""
    # 1. 获取贡献数据
    calendar = get_contributions(USERNAME, TOKEN)
    weeks = calendar["weeks"]
    
    # 提取最近7周数据
    recent_weeks = weeks[-7:]
    contributions = []
    
    for week in recent_weeks:
        week_data = [0] * 7  # 初始化一周7天
        for day in week["contributionDays"]:
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
            weekday = date_obj.weekday()  # 0=周一, 6=周日
            week_data[weekday] = day["contributionCount"]
        contributions.append(week_data)
    
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
    
    for y, week in enumerate(contributions):
        row = []
        for x, count in enumerate(week):
            # 确定格子类型
            if count == 0:
                cell_type = "mine" if random.random() < MINE_PROB_NO_COMMIT else "empty"
            else:
                cell_type = "safe" if random.random() < (1 - MINE_PROB_COMMIT) else "mine"
            
            row.append(cell_type)
            
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
            elif count > 0:
                # 计算周围地雷数
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < len(contributions) and 0 <= nx < 7:
                            if mine_grid[ny][nx] == "mine":
                                neighbors += 1
                
                if neighbors > 0:
                    text = dwg.text(str(neighbors),
                        insert=(x * cell_size + padding + cell_size/2, 
                                y * cell_size + y_offset + cell_size/2 + 6),
                        class_=f"number num-{min(neighbors, 8)}"
                    )
                    dwg.add(text)
        mine_grid.append(row)
    
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

if __name__ == "__main__":
    generate_minesweeper_svg()
