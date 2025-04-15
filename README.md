# 滑呗轨迹导出工具

这是一个将滑呗（Huabei）滑雪轨迹转换为 GPX 格式的工具，方便导入到 Slopes 等滑雪应用中使用。


## 功能特点

- 支持从滑呗分享链接提取滑雪轨迹数据
- 将轨迹数据转换为标准 GPX 格式
- 提供 Web 界面方便使用


## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 链接获取方式

打开滑呗——进入个人记录——选择一条轨迹——选择分享——选择链接分享——在浏览器打开复制链接

**注意**: 如果一天的滑行分多次记录，需要每段轨迹分别分享导出，导入slopes之后会自动合并

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

### Slopes导入

打开Slopes-进入Logbook界面-点击右上角+号-选择Import from file-选择刚刚导出的GPX文件-点击导入

## 目前问题

- 滑呗API中无法获取extended GPS data,导致无法获取
``<gte:gps speed="..." azimuth="...">``即速度和面朝方向，因此导出的GPX只有基本的经纬度以及海拔信息，Slopes在计算速度时可能会不准确（会有夸大的最大速度）


