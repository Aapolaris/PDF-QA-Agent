# 如何租用AutoDl服务器加速项目

#### 1. 使用vscode远程连接autodl

- 更改新建环境和包的位置到数据盘，未雨绸缪（方便数据盘扩容等等...）

```bash
mkdir -p /root/autodl-tmp/conda/pkgs 
conda config --add pkgs_dirs /root/autodl-tmp/conda/pkgs 
mkdir -p /root/autodl-tmp/conda/envs 
conda config --add envs_dirs /root/autodl-tmp/conda/envs
```

- 创建新的环境、初始化环境、重启shell

```bash
conda create -n langchain python=3.11
```
```bash
conda init
```
```bash
source ~/.bashrc
```

- 配置项目环境

```bash
conda activate langchain
```
```bash
pip install requirements.txt
```

#### 2. 安装并部署Ollama

> 🔗 [基于AutoDL+Ollama的开源大模型私有化部署 | Ming-Log's Blog](https://blog.minglog.cn/2025/07/02/%E5%9F%BA%E4%BA%8EAutoDL+Ollama%E7%9A%84%E5%BC%80%E6%BA%90%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%A7%81%E6%9C%89%E5%8C%96%E9%83%A8%E7%BD%B2/)

##### 2.1 安装ollama

- 进入项目并开启学术加速

```bash
cd /root/autodl-tmp  && source /etc/network_turbo
```

- 下载ollama安装文件

```bash
curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz
```

- 解压并部署ollama

```bash
sudo tar -C /usr -xzf ollama-linux-amd64.tgz
```

- **配置环境变量**

```bash
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_MODELS=/root/autodl-tmp/ollama/models
```

> **注意，这种环境变量的配置方式只在当前终端有效**。因此每次使用新的终端都要重新设置，如果想一劳永逸，可以通过图形界面配置系统的环境变量；或是使用 `vim` 命令进行配置。具体可以
> [参考这里](https://blog.minglog.cn/2025/07/02/%E5%9F%BA%E4%BA%8EAutoDL+Ollama%E7%9A%84%E5%BC%80%E6%BA%90%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%A7%81%E6%9C%89%E5%8C%96%E9%83%A8%E7%BD%B2/)

- 开启ollama服务

```bash
ollama serve
```

##### 2.2 挂载ollama服务

在本地计算机，如果不退出程序的话，Ollama服务会自己在后台运行。但如果我们使用的是autodl平台，启动ollama服务后不能关闭当前窗口，非常不方便。因此需要一个工具帮助我们离线托管终端代码。
`tmux` 是一个 terminal multiplexer （终端复用器），它可以启动一系列终端会话。可以用其查看代码运行状态，可以在关闭terminal下仍然运行程序

- 下载 `tumx` 工具

```bash
apt install tmux
```

> 这里如果第一个命令报错 `Unable to locate package tmux` ，则先使用下面命令更新包和存储库的缓存。如果还是没解决，可以自行搜索一下。
> ``` bash
> sudo apt-get update
> sudo apt-get upgrade -y
> ```

- 创建一个可用于离线托管的终端，（**注意设置环境变量**）并在该终端下启动ollama服务：`ollama serve` 

```bash
tumx
```

- 使用快捷键 `Ctrl+b` `d` 完成终端托管，此时会自动退出我们之前使用的那个终端

> 其它 `tmux` 命令：
> 
> 查看所有后台终端：
> ```bash
> tmux list
> ```
> 
> 切换后台终端：
> `Ctrl+b` `s`
> 
> 关闭所有窗口：
> ```bash
> tmux kill-window
> ```

##### 2.3 利用ollama拉取模型

输入`tmux` 创建一个新的终端， （**配置环境变量后**）现在我们可以执行以下命令拉取模型并使用。（模型选择可到ollama官网看）

```bash
ollama run deepseek-r1:8b
```

#### 3. 上传模型

- 下载模型

先 `cd` 到要下载模型的目录，然后执行下面的命令下载完整的模型

```bash
huggingface-cli download sentence-transformers/all-mpnet-base-v2 --local-dir ./ --local-dir-use-symlinks False
```

