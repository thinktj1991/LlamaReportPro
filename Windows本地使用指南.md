# 📖 年报分析系统 - Windows本地使用指南

## 🎯 概述
这个指南将帮助您在Windows电脑上运行我们的年报分析系统。即使您是编程新手，也可以按照这个简单的步骤来操作。

## 📋 准备工作

### 第一步：下载项目代码
1. **在Replit中下载项目**
   - 在Replit项目页面左侧的文件树中
   - 右键点击根目录
   - 选择"Download as Zip"下载整个项目
   - 将下载的zip文件解压到您想要的文件夹中

### 第二步：安装Python
1. **下载Python**
   - 访问 https://www.python.org/downloads/
   - 下载最新版本的Python（推荐Python 3.9或更高版本）
   
2. **安装Python**
   - 运行下载的安装程序
   - ⚠️ **重要**: 勾选"Add Python to PATH"选项
   - 点击"Install Now"进行安装

3. **验证安装**
   - 按 `Win + R` 打开运行对话框
   - 输入 `cmd` 并按回车打开命令提示符
   - 输入 `python --version` 检查是否安装成功
   - 应该显示类似 "Python 3.11.x" 的版本信息

## 🚀 运行系统

### 第三步：安装依赖包
1. **打开命令提示符**
   - 按 `Win + R`，输入 `cmd`，按回车

2. **进入项目文件夹**
   ```bash
   cd C:\你的项目路径\项目文件夹名
   ```
   （将路径替换为您实际解压项目的位置）

3. **安装所需的包**
   ```bash
   pip install streamlit llama-index llama-index-embeddings-openai llama-index-llms-openai llama-index-readers-file openai openpyxl pandas pdfplumber plotly reportlab scikit-learn scipy statsmodels xlsxwriter
   ```

### 第四步：设置API密钥
1. **获取OpenAI API密钥**
   - 访问 https://platform.openai.com/
   - 注册并获取API密钥

2. **设置环境变量**
   - 在Windows搜索中输入"环境变量"
   - 选择"编辑系统环境变量"
   - 点击"环境变量"按钮
   - 在"用户变量"中点击"新建"
   - 变量名：`OPENAI_API_KEY`
   - 变量值：您的OpenAI API密钥
   - 点击确定保存

### 第五步：启动应用
1. **在命令提示符中运行**
   ```bash
   streamlit run app.py --server.port 5000
   ```

2. **访问应用**
   - 系统会自动打开浏览器
   - 或者手动访问：http://localhost:5000
   - 您现在可以使用完全中文化的年报分析系统了！

## 📱 使用说明

### 系统功能
- **📁 上传与处理**: 上传PDF年报文件
- **📊 数据分析**: 查看财务数据分析
- **💬 问答系统**: 与文档进行智能对话
- **🔍 公司对比**: 比较不同公司的财务指标
- **📈 比率分析**: 深入的财务比率分析
- **🤖 AI洞察**: 获得AI驱动的分析洞察
- **📤 数据导出**: 导出分析结果

### 基本使用流程
1. 首先上传PDF年报文件
2. 等待系统处理和分析
3. 使用各个功能页面进行分析
4. 导出需要的分析结果

## ❓ 常见问题

**Q: 如果看到"command not found"错误怎么办？**
A: 确保Python已正确安装并添加到PATH中。重新安装Python时勾选"Add Python to PATH"。

**Q: 安装包时出现错误怎么办？**
A: 尝试使用 `pip install --upgrade pip` 升级pip，然后重新安装包。

**Q: 如何停止应用？**
A: 在命令提示符中按 `Ctrl + C` 停止应用。

**Q: 应用无法访问怎么办？**
A: 检查防火墙设置，确保允许Python程序访问网络。

## 🔧 故障排除

如果遇到问题：
1. 确保所有依赖包都已正确安装
2. 检查OpenAI API密钥是否设置正确
3. 确保您有稳定的网络连接
4. 重启命令提示符和浏览器

---

🎉 现在您可以在自己的Windows电脑上使用这个强大的年报分析系统了！如有任何问题，请随时询问。