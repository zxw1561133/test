import matplotlib
matplotlib.use('TkAgg')  # 尝试使用TkAgg后端以解决显示问题

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider, Button, TextBox

# 配置
data_file = "plugin_data/task_101_CA_get_next_position_data.csv"

# 读取数据
print(f"Reading data file: {data_file}")

# 读取并验证数据
try:
    df = pd.read_csv(data_file)
    # 验证必要的列是否存在
    required_columns = ['time', 'platformId', 'x', 'y', 'z', 'target_x', 'target_y', 'target_z']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"WARNING: Missing required columns: {missing_columns}")
        print("Available columns:", df.columns.tolist())
except Exception as e:
    print(f"ERROR: Could not read data file: {e}")
    import sys
    sys.exit(1)

# 添加数据验证和打印
print(f"Data shape: {df.shape}")
print(f"Sample data for first row:")
print(df.iloc[0][['time', 'platformId', 'x', 'y', 'z', 'target_x', 'target_y', 'target_z']])

# 获取所有时间戳并排序
timestamps = sorted(df['time'].unique())
print(f"Found {len(timestamps)} timestamps")

# 获取唯一平台ID
platform_ids = sorted(df['platformId'].unique())
print(f"Found {len(platform_ids)} platforms: {platform_ids}")

# 预处理数据 - 按时间戳打包数据
print("Preprocessing data by timestamp...")
timestamp_data = {}
for timestamp in timestamps:
    # 获取当前时间戳的所有数据
    current_data = df[df['time'] == timestamp]
    if current_data.empty:
        print(f"WARNING: No data for timestamp {timestamp}")
        continue
        
    # 按平台ID组织数据
    platform_data = {}
    for platform_id in platform_ids:
        platform_rows = current_data[current_data['platformId'] == platform_id]
        if not platform_rows.empty:
            # 创建安全的数据字典，确保所有必要字段都存在
            data_dict = platform_rows.iloc[0].to_dict()
            for field in ['x', 'y', 'z', 'target_x', 'target_y', 'target_z']:
                if field not in data_dict or pd.isna(data_dict[field]):
                    print(f"WARNING: Missing or invalid {field} for platform {platform_id} at timestamp {timestamp}")
                    # 设置默认值以避免错误
                    data_dict[field] = 0.0
            platform_data[platform_id] = data_dict
    
    # 存储打包的数据
    timestamp_data[timestamp] = platform_data

# 打印前三个时间戳的平台数据作为验证
print(f"Data packaged for {len(timestamp_data)} timestamps")
for i, timestamp in enumerate(timestamps[:3]):
    print(f"Timestamp {i+1}: {timestamp}")
    for platform_id, data in timestamp_data[timestamp].items():
        print(f"  Platform {platform_id}: pos=({data['x']:.1f}, {data['y']:.1f}, {data['z']:.1f}), "
              f"target=({data['target_x']:.1f}, {data['target_y']:.1f}, {data['target_z']:.1f})")

# 根据平台ID分配颜色
colors = {
    101: 'blue',
    102: 'green',
    103: 'red',
}

# 创建图形
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')
ax.set_title("Aircraft Trajectory Visualization")
ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')

# 改进视图设置
# 设置更合适的初始视角
ax.view_init(elev=35, azim=30)  # 改变视角以更好地展示3D数据

# 初始化图形对象
platform_markers = {}  # 飞机当前位置
platform_lines = {}    # 飞机历史轨迹
target_markers = {}    # 目标点位置
target_lines = {}      # 当前位置到目标点的连线

# 创建每个平台的图形对象
for platform_id in platform_ids:
    color = colors.get(platform_id, 'gray')
    # 初始化当前位置标记
    marker, = ax.plot([], [], [], 'o', color=color, markersize=8, label=f"Platform {platform_id}")
    platform_markers[platform_id] = marker
    
    # 初始化历史轨迹线
    line, = ax.plot([], [], [], '-', color=color, linewidth=1, alpha=0.7)
    platform_lines[platform_id] = line
    
    # 初始化目标点标记
    target, = ax.plot([], [], [], 'x', color=color, markersize=8, alpha=0.7)
    target_markers[platform_id] = target
    
    # 初始化连接线（当前位置到目标点）
    conn_line, = ax.plot([], [], [], '--', color=color, linewidth=1, alpha=0.5)
    target_lines[platform_id] = conn_line

# 设置图例
ax.legend()

# 添加控制元素
plt.subplots_adjust(bottom=0.3)

# 当前帧和播放状态
current_frame = 0
is_playing = False
frame_step = 1  # 默认每次更新1帧

# 自动旋转视图功能
auto_rotate = False
rotate_speed = 1

# 在update_frame函数中添加实时数据面板
def update_frame(frame):
    """更新特定帧的所有图形对象"""
    global current_frame
    current_frame = frame
    
    # 获取当前时间戳和数据
    timestamp = timestamps[frame]
    platform_data = timestamp_data[timestamp]
    
    # 清除之前的文本注释
    if hasattr(update_frame, 'data_texts'):
        for txt in update_frame.data_texts:
            txt.remove()
    update_frame.data_texts = []
    
    # 数据面板位置和样式
    panel_x = 0.05
    panel_y = 0.70
    line_height = 0.03
    
    # 添加数据面板标题
    title = plt.figtext(panel_x, panel_y + line_height, 
                      f"Frame {frame+1}/{len(timestamps)}", 
                      fontsize=9, color='black')
    update_frame.data_texts.append(title)
    
    # 更新每个平台的图形
    for i, platform_id in enumerate(platform_ids):
        if platform_id in platform_data:
            data = platform_data[platform_id]
            
            # 当前位置
            x = data['x']
            y = data['y']
            z = data['z']
            
            # 目标位置
            tx = data['target_x']
            ty = data['target_y']
            tz = data['target_z']
            
            # 计算平台到目标的距离
            distance = np.sqrt((tx-x)**2 + (ty-y)**2 + (tz-z)**2)
            
            # 添加到数据面板
            platform_text = plt.figtext(
                panel_x, panel_y - i*line_height,
                f"Platform {platform_id}: ({x:.1f}, {y:.1f}, {z:.1f}) → ({tx:.1f}, {ty:.1f}, {tz:.1f}) | Dist: {distance:.1f}m",
                fontsize=8, color=colors.get(platform_id, 'gray')
            )
            update_frame.data_texts.append(platform_text)
            
            # 更新历史位置数据
            if len(history_positions[platform_id]['x']) == 0 or (
                    history_positions[platform_id]['x'][-1] != x or 
                    history_positions[platform_id]['y'][-1] != y or 
                    history_positions[platform_id]['z'][-1] != z):
                history_positions[platform_id]['x'].append(x)
                history_positions[platform_id]['y'].append(y)
                history_positions[platform_id]['z'].append(z)
            
            # 限制历史轨迹长度
            max_history = 50
            if len(history_positions[platform_id]['x']) > max_history:
                history_positions[platform_id]['x'] = history_positions[platform_id]['x'][-max_history:]
                history_positions[platform_id]['y'] = history_positions[platform_id]['y'][-max_history:]
                history_positions[platform_id]['z'] = history_positions[platform_id]['z'][-max_history:]
            
            # 更新当前位置标记
            platform_markers[platform_id].set_data([x], [y])
            platform_markers[platform_id].set_3d_properties([z])
            
            # 更新历史轨迹线
            platform_lines[platform_id].set_data(history_positions[platform_id]['x'], history_positions[platform_id]['y'])
            platform_lines[platform_id].set_3d_properties(history_positions[platform_id]['z'])
            
            # 更新目标点标记
            target_markers[platform_id].set_data([tx], [ty])
            target_markers[platform_id].set_3d_properties([tz])
            
            # 更新连接线
            target_lines[platform_id].set_data([x, tx], [y, ty])
            target_lines[platform_id].set_3d_properties([z, tz])
        else:
            # 如果当前时间戳没有该平台数据，则隐藏图形
            platform_markers[platform_id].set_data([], [])
            platform_markers[platform_id].set_3d_properties([])
            platform_lines[platform_id].set_data([], [])
            platform_lines[platform_id].set_3d_properties([])
            target_markers[platform_id].set_data([], [])
            target_markers[platform_id].set_3d_properties([])
            target_lines[platform_id].set_data([], [])
            target_lines[platform_id].set_3d_properties([])
    
    # 更新状态文本
    status_text.set_text(f"Frame {frame+1}/{len(timestamps)} - Timestamp: {timestamp} - Step: {frame_step}")
    
    # 返回更新的图形对象
    artists = []
    artists.extend(platform_markers.values())
    artists.extend(platform_lines.values())
    artists.extend(target_markers.values())
    artists.extend(target_lines.values())
    return artists

# 初始化文本列表
update_frame.data_texts = []

# 存储历史位置数据
history_positions = {platform_id: {'x': [], 'y': [], 'z': []} for platform_id in platform_ids}

def init_animation():
    """初始化动画"""
    for marker in platform_markers.values():
        marker.set_data([], [])
        marker.set_3d_properties([])
    
    for line in platform_lines.values():
        line.set_data([], [])
        line.set_3d_properties([])
    
    for marker in target_markers.values():
        marker.set_data([], [])
        marker.set_3d_properties([])
    
    for line in target_lines.values():
        line.set_data([], [])
        line.set_3d_properties([])
    
    artists = []
    artists.extend(platform_markers.values())
    artists.extend(platform_lines.values())
    artists.extend(target_markers.values())
    artists.extend(target_lines.values())
    return artists

# 添加控制元素
# 添加帧滑块
ax_slider = plt.axes([0.2, 0.15, 0.6, 0.03])
frame_slider = Slider(ax_slider, 'Frame', 0, len(timestamps) - 1, valinit=0, valstep=1)

# 添加播放控制按钮
ax_play = plt.axes([0.3, 0.05, 0.15, 0.05])
btn_play = Button(ax_play, 'Play')

# 添加帧步长输入框
ax_step = plt.axes([0.5, 0.05, 0.08, 0.05])
text_step = TextBox(ax_step, 'Step:', initial='1')
text_step.label.set_text('Step:')  # 确保标签正确设置

# 添加应用步长按钮
ax_apply = plt.axes([0.62, 0.05, 0.08, 0.05])
btn_apply = Button(ax_apply, 'Apply')

# 添加旋转视图按钮
ax_rotate = plt.axes([0.8, 0.05, 0.15, 0.05])
btn_rotate = Button(ax_rotate, 'Auto Rotate')

# 添加状态文本
status_text = fig.text(0.5, 0.01, "Ready", ha="center")

def slider_update(val):
    """滑块更新回调"""
    global current_frame, is_playing
    current_frame = int(val)
    is_playing = False
    btn_play.label.set_text('Play')
    
    # 直接更新当前帧
    update_frame(current_frame)
    fig.canvas.draw_idle()

frame_slider.on_changed(slider_update)

def toggle_play(event):
    """切换播放/暂停状态"""
    global is_playing
    is_playing = not is_playing
    btn_play.label.set_text('Pause' if is_playing else 'Play')
    
    # 手动启动或停止动画
    if is_playing:
        ani.event_source.start()
    else:
        ani.event_source.stop()

btn_play.on_clicked(toggle_play)

def update_step(event):
    """更新帧步长"""
    global frame_step
    try:
        step = int(text_step.text)
        if step < 1:
            step = 1
        frame_step = step
        status_text.set_text(f"Frame step updated to {frame_step}")
        fig.canvas.draw_idle()
    except ValueError:
        # 如果输入无效，恢复原值
        text_step.set_val(str(frame_step))
        status_text.set_text(f"Invalid step value. Using {frame_step}")
        fig.canvas.draw_idle()

btn_apply.on_clicked(update_step)

def toggle_rotation(event):
    """切换自动旋转视图"""
    global auto_rotate
    auto_rotate = not auto_rotate
    btn_rotate.label.set_text('Stop Rotation' if auto_rotate else 'Auto Rotate')

btn_rotate.on_clicked(toggle_rotation)

def animate(frame_number):
    """动画更新函数"""
    global current_frame
    
    # 如果正在播放，更新当前帧
    if is_playing:
        # 使用步长参数更新帧
        current_frame = (current_frame + frame_step) % len(timestamps)
        # 更新滑块但不触发回调
        frame_slider.eventson = False
        frame_slider.set_val(current_frame)
        frame_slider.eventson = True
    
    # 自动旋转视图
    if auto_rotate:
        elev, azim = ax.elev, ax.azim
        ax.view_init(elev, azim + rotate_speed)
    
    # 更新并返回当前帧的艺术家对象
    return update_frame(current_frame)

# 改进坐标轴范围设置
def set_axes_limits():
    """设置坐标轴范围，确保有合理的视图"""
    try:
        x_values = []
        y_values = []
        z_values = []
        
        # 只收集前1000个时间戳的数据来计算轴范围，提高性能
        sample_timestamps = timestamps[:min(1000, len(timestamps))]
        
        for timestamp in sample_timestamps:
            if timestamp in timestamp_data:
                for data in timestamp_data[timestamp].values():
                    x_values.extend([data['x'], data['target_x']])
                    y_values.extend([data['y'], data['target_y']])
                    z_values.extend([data['z'], data['target_z']])
        
        # 确保有有效的值
        if x_values and y_values and z_values:
            # 剔除极端值以获得更好的显示效果
            x_values.sort()
            y_values.sort()
            z_values.sort()
            
            # 移除低端和高端的1%数据以去除异常值
            cutoff = max(1, len(x_values) // 100)
            x_values = x_values[cutoff:-cutoff]
            y_values = y_values[cutoff:-cutoff]
            z_values = z_values[cutoff:-cutoff]
            
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)
            z_min, z_max = min(z_values), max(z_values)
            
            # 确保范围合理
            if x_max <= x_min:
                x_min, x_max = x_min - 100, x_min + 100
            if y_max <= y_min:
                y_min, y_max = y_min - 100, y_min + 100
            if z_max <= z_min:
                z_min, z_max = z_min - 100, z_min + 100
            
            # 计算范围
            x_range = x_max - x_min
            y_range = y_max - y_min
            z_range = z_max - z_min
            
            # 使用更大的padding确保所有点都可见
            padding_x = x_range * 0.15
            padding_y = y_range * 0.15
            padding_z = z_range * 0.15
            
            ax.set_xlim(x_min - padding_x, x_max + padding_x)
            ax.set_ylim(y_min - padding_y, y_max + padding_y)
            ax.set_zlim(z_min - padding_z, z_max + padding_z)
            
            print(f"Setting axes limits: X=[{ax.get_xlim()[0]:.1f}, {ax.get_xlim()[1]:.1f}], "
                  f"Y=[{ax.get_ylim()[0]:.1f}, {ax.get_ylim()[1]:.1f}], "
                  f"Z=[{ax.get_zlim()[0]:.1f}, {ax.get_zlim()[1]:.1f}]")
        else:
            print("WARNING: No valid position data to set axes limits")
            ax.set_xlim(-1000, 1000)
            ax.set_ylim(-1000, 1000)
            ax.set_zlim(-100, 100)
    except Exception as e:
        print(f"ERROR setting axes limits: {e}")
        ax.set_xlim(-1000, 1000)
        ax.set_ylim(-1000, 1000)
        ax.set_zlim(-100, 100)

# 设置坐标轴范围
set_axes_limits()

# 设置动画 - 使用blit=False以确保正确渲染3D图形
ani = animation.FuncAnimation(
    fig, animate,
    init_func=init_animation,
    frames=None,
    interval=100,
    blit=False  # 对3D图形，禁用blit以避免渲染问题
)

# 确保初始帧正确显示
update_frame(0)

# 显示图形
plt.show() 