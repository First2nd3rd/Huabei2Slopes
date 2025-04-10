# 滑呗轨迹导出工具

这是一个将滑呗（Huabei）滑雪轨迹转换为 GPX 格式的工具，方便导入到 Slopes 等滑雪应用中使用。

## 功能特点

- 支持从滑呗分享链接提取滑雪轨迹数据
- 将轨迹数据转换为标准 GPX 格式
- 自动处理同一天多条轨迹的文件命名
- 支持批量处理多个链接
- 提供 Web 界面方便使用

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行方式

```bash
python converter_gpx.py "https://h5.fenxuekeji.com/h5/oact/wakeup?type=ski_record_detail&track_type=once&track_uuid=YOUR_TRACK_UUID&user_id=YOUR_USER_ID"
```

### Web 界面方式

1. 启动 Web 服务器：
```bash
python web_interface.py
```

2. 在浏览器中访问：http://localhost:5001

3. 在网页界面中：
   - 输入滑呗分享链接
   - 点击"添加更多链接"可以添加多个链接
   - 点击"转换并下载"开始处理

## 注意事项

- 确保输入的链接是有效的滑呗分享链接
- 同一天的多个轨迹会自动添加序号（如：`February 05, 2024 - Resort Name_1.gpx`）
- 转换后的 GPX 文件可以直接导入到 Slopes 等滑雪应用中

## 依赖说明

- requests: 用于发送 HTTP 请求获取滑呗数据
- flask: 用于提供 Web 界面
- 其他依赖均为 Python 标准库，无需额外安装

## 新特性：自动命名文件

现在，脚本会自动根据滑雪日期和雪场名称为生成的 GPX 文件命名，格式为：`YYYYMMDD-雪场名称.gpx`

例如：
```
20240205-Yuzawa_Iwa-ppara汤泽岩原滑雪场.gpx
```

## 数据处理

脚本现在可以正确处理滑呗API返回的复杂数据结构：

- 支持处理多个滑行路线（multiple ski runs）
- 从 `track_detail` 中提取所有滑行路线的经纬度坐标数据
- 保留每条滑行路线的结构，确保轨迹正确展示
- 智能匹配海拔高度和时间信息
- 当海拔数据不足时，使用最大海拔数据作为默认值
- 当时间数据不足时，基于开始时间自动生成合理的时间序列

## 轨迹质量

新版本确保处理轨迹时：
- 保留完整的多路线结构，更精确地反映你的滑雪体验
- 输出详细的处理日志，显示每条滑行路线的点数
- 报告最终添加到GPX文件的总点数，确保完整保留你的滑雪记录

## 示例

使用分享链接：
```
python converter_gpx.py "https://h5.fenxuekeji.com/h5/oact/wakeup?type=ski_record_detail&track_type=once&track_uuid=7ebc254a-0785-4c09-80df-caa2599ce363&user_id=179732b5-4a5f-4630-b688-0d4c469a2678"
```

使用已保存的 API 数据：
```
python converter_gpx.py apimsg.json
```

## 参数说明

- `url_or_file`: 必填参数，可以是滑呗分享的 URL（包含 track_uuid），或保存 API 响应的 JSON 文件路径
- `-o, --output`: 可选参数，输出的 GPX 文件路径（不指定时将自动生成格式为 YYYYMMDD-resort_name.gpx 的文件名）

## 注意事项

- 该工具通过非官方 API 获取滑雪轨迹数据，API 可能随时变化
- 脚本现在支持多滑行路线格式，能够处理完整的滑雪记录
- 处理后的 GPX 文件将保留每条滑行路线的结构，适合导入到 Slopes 应用
- 如果在使用过程中遇到问题，可以检查命令行输出的详细日志信息
- 导入 Slopes 时可能需要一些手动调整 