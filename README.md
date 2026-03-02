# 🌟 AI Live2D Desktop Pet 

![Python](https://img.shields.io/badge/Python-3.11-blue) ![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 📢News

- [2026-2-23] Created the repo.
- [2026-3-02] Release version 1.0

## 📝 TODO 
- [x] **Release version 1.0** 
  - 接入高德地图MCP Server
  - 支持基础对话
  - 支持天气查询 & IP 地址定位
  -  支持关键词搜索 & 地址经纬度转换
  -  支持驾车与步行路径规划
- [ ] Release version 1.1
- [ ] ...

## 🚀 Quick Start

### Installation

```bash
conda create -n DesktopPet python=3.11 -y
conda activate DesktopPet
cd DesktopPet
pip install -r requirements.txt 
```

## Usage

### 1.Download Live2D models

Windows Powershell:

```powershell
curl.exe -u sukiame:desktoppet -O https://dl.sukiame.cn/assets.zip
```

Linux:

```bash
wget --user sukiame --password desktoppet https://dl.sukiame.cn/assets.zip
```

Then unzip the file.

### 2.Environment Variable

当前目录下创建 `.env` 文件并编辑：

```env
DEEPSEEK_API_KEY=sk-你的密钥
AMAP_API_KEY=输入AMAP的密钥
```

> 💡DeepSeek API 密钥获取地址：https://platform.deepseek.com/
>
> 💡高德MCP API Key 地址:  https://lbs.amap.com/api/mcp-server/create-project-and-key

编辑 `src/gui/index.html` 第 330-333 行，修改 `modelUrl` 即可切换不同的 Live2D 模型：

```javascript
// 可选模型：
//const modelUrl = '../../assets/koharu/koharu.model3.json';
// const modelUrl = '../../assets/haruto/haruto.model3.json';
//const modelUrl = '../../assets/Nahida/Nahida.model3.json';
const modelUrl = '../../assets/hutao/1.model3.json';// hutao（默认）
```
### 3.Run

启动后端:

```bash
python src/api/api.py
```

启动前端:

```bash
cd src/gui
npm install  
npm start 
```

效果如下:

**示例1：天气查询**

Q:今天天津天气怎么样？

![image-20260302185649936](https://bu.dusays.com/2026/03/02/69a56dfd7ac29.png)

**示例2：问路**

Q:南开大学津南校区到天津大学北洋园校区走路怎么去？

![image-20260302185920336](https://bu.dusays.com/2026/03/02/69a56dfd7ac02.png)
