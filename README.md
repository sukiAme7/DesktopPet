# 🌟 AI Live2D Desktop Pet 

![Python](https://img.shields.io/badge/Python-3.11-blue) ![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 📢News

- [2026-2-23] Created the repo.
- [2026-3-01] Test the MVP.
- [2026-3-02] 接入高德地图MCP Server:支持天气查询、路径查询等功能.

## 📝 TODO 
- [x] Release the MVP
- [ ] Release version 1.0
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

Windows:

```powershell
curl.exe -u sukiame:desktoppet -O https://dl.sukiame.cn/assets.zip
```

Linux:

```bash
wget --user sukiame --password desktoppet https://dl.sukiame.cn/assets.zip
```

Then unzip the file.

### 2.env

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-你的密钥
AMAP_API_KEY=输入AMAP的密钥
```

> 💡DeepSeek API 密钥获取地址：https://platform.deepseek.com/
>
> 💡高德MCP API Key 地址:  https://lbs.amap.com/api/mcp-server/create-project-and-key

编辑 `src/gui/index.html` 第 184-185 行，修改 `modelUrl` 即可切换不同的 Live2D 模型：

```javascript
// 可选模型：
const modelUrl = '../../assets/hutao/1.model3.json'; // hutao（默认）
//const modelUrl = '../../assets/koharu/koharu.model3.json';
// const modelUrl = '../../assets/haruto/haruto.model3.json';   
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
