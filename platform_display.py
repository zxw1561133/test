# 设置Z轴的显示范围
Z_DISPLAY_MIN = 1695.0  # Z轴显示的最小值
Z_DISPLAY_MAX = 3700.0  # Z轴显示的最大值

# 将Z轴数据转换为实际高度
df['altitude'] = REF_ALT + df['z']  # 将Z坐标加上参考高度得到真实高度

# 计算坐标轴范围 - 考虑所有数据点
print("正在计算坐标轴范围...")

# 初始化范围变量
x_min_all = float('inf')  # 北向最小值
x_max_all = float('-inf')  # 北向最大值
y_min_all = float('inf')  # 东向最小值
y_max_all = float('-inf')  # 东向最大值

# 考虑本机和邻居飞机的位置数据
x_min_all = min(x_min_all, df['x'].min())
x_max_all = max(x_max_all, df['x'].max())
y_min_all = min(y_min_all, df['y'].min())
y_max_all = max(y_max_all, df['y'].max())

# 考虑目标点位置
x_min_all = min(x_min_all, df['target_x'].min())
x_max_all = max(x_max_all, df['target_x'].max())
y_min_all = min(y_min_all, df['target_y'].min())
y_max_all = max(y_max_all, df['target_y'].max())

# 考虑参考点数据
for i in range(10):  # 0-9共10个参考点
    ref_x_col = f'ref{i}_x'
    ref_y_col = f'ref{i}_y'
    
    if ref_x_col in df.columns and ref_y_col in df.columns:
        # 过滤掉NaN值
        valid_ref_x = df[ref_x_col].dropna()
        valid_ref_y = df[ref_y_col].dropna()
        
        if not valid_ref_x.empty and not valid_ref_y.empty:
            x_min_all = min(x_min_all, valid_ref_x.min())
            x_max_all = max(x_max_all, valid_ref_x.max())
            y_min_all = min(y_min_all, valid_ref_y.min())
            y_max_all = max(y_max_all, valid_ref_y.max())

# 考虑风险数据
if risk_df is not None:
    # 风险点位置 (pos0=x, pos1=y)
    if 'pos0' in risk_df.columns and 'pos1' in risk_df.columns:
        valid_pos0 = risk_df['pos0'].dropna()
        valid_pos1 = risk_df['pos1'].dropna()
        
        if not valid_pos0.empty and not valid_pos1.empty:
            x_min_all = min(x_min_all, valid_pos0.min())
            x_max_all = max(x_max_all, valid_pos0.max())
            y_min_all = min(y_min_all, valid_pos1.min())
            y_max_all = max(y_max_all, valid_pos1.max())
    
    # 风险信息发布者位置 (cmd0=x, cmd1=y)
    if 'cmd_0' in risk_df.columns and 'cmd_1' in risk_df.columns:
        # 只考虑风险类型为1的数据
        risk_type_1 = risk_df[risk_df['risk_type'] == 1]
        valid_cmd0 = risk_type_1['cmd_0'].dropna()
        valid_cmd1 = risk_type_1['cmd_1'].dropna()
        
        if not valid_cmd0.empty and not valid_cmd1.empty:
            # 将经纬度转换为NED坐标
            for _, row in risk_type_1.iterrows():
                if not pd.isna(row['cmd_0']) and not pd.isna(row['cmd_1']):
                    reporter_lat = row['cmd_0']
                    reporter_lon = row['cmd_1']
                    north, east, _ = geo_to_ned(
                        reporter_lat, reporter_lon, 0,
                        REF_LAT, REF_LON, REF_ALT
                    )
                    x_min_all = min(x_min_all, north)
                    x_max_all = max(x_max_all, north)
                    y_min_all = min(y_min_all, east)
                    y_max_all = max(y_max_all, east)

# 球体轨迹数据
if ball_traj_df is not None:
    for i in range(10):  # 0-9共10个参考点
        ref_x_col = f'ref{i}_x'
        ref_y_col = f'ref{i}_y'
        
        if ref_x_col in ball_traj_df.columns and ref_y_col in ball_traj_df.columns:
            valid_ref_x = ball_traj_df[ref_x_col].dropna()
            valid_ref_y = ball_traj_df[ref_y_col].dropna()
            
            if not valid_ref_x.empty and not valid_ref_y.empty:
                x_min_all = min(x_min_all, valid_ref_x.min())
                x_max_all = max(x_max_all, valid_ref_x.max())
                y_min_all = min(y_min_all, valid_ref_y.min())
                y_max_all = max(y_max_all, valid_ref_y.max())

# 添加边界空间 - 使用更大的边界比例（20%）确保所有点都在视图内
margin_percent = 0.2
x_range = x_max_all - x_min_all
y_range = y_max_all - y_min_all

x_min_with_margin = x_min_all - margin_percent * x_range
x_max_with_margin = x_max_all + margin_percent * x_range
y_min_with_margin = y_min_all - margin_percent * y_range
y_max_with_margin = y_max_all + margin_percent * y_range

print(f"计算出的坐标轴范围:")
print(f"X轴(北向): {x_min_with_margin:.2f} 到 {x_max_with_margin:.2f}")
print(f"Y轴(东向): {y_min_with_margin:.2f} 到 {y_max_with_margin:.2f}")

# 全局变量
is_paused = False

# 创建图形和3D轴
fig = plt.figure(figsize=(12, 10), dpi=100)
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('East (m)', fontsize=12)
ax.set_ylabel('North (m)', fontsize=12)
ax.set_zlabel('Altitude (m)', fontsize=12)
ax.set_title('Platform Trajectories - 3D View with Altitude', fontsize=16)

# 设置坐标轴范围 - 使用新计算的边界值
ax.set_ylim(x_min_with_margin, x_max_with_margin)  # Y轴设置为北向
ax.set_xlim(y_min_with_margin, y_max_with_margin)  # X轴设置为东向
ax.set_zlim(Z_DISPLAY_MIN, Z_DISPLAY_MAX)  # Z轴设置为固定范围

# 添加参考平面 - 最低高度平面
x_ground = np.linspace(y_min_with_margin, y_max_with_margin, 10)
y_ground = np.linspace(x_min_with_margin, x_max_with_margin, 10)
X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
Z_min = np.ones(X_ground.shape) * Z_DISPLAY_MIN
ax.plot_surface(X_ground, Y_ground, Z_min, alpha=0.2, color='lightgray')

# 记录初始collections用于后续清除时避免删除初始元素
ax.collections_init = list(ax.collections)

# 构建时间帧索引
unique_times = sorted(df['time'].unique()) 