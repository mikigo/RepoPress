# 生产环境部署

server info

```
ip = 10.0.21.144
user = pz
password= 123456
```

doc 端使用 sailwind_doc 的 github pages，仓库我已经在服务器上home下克隆好了（ssh 克隆）

sailwind_doc 的 github pages 是已有流程（github action），只要提交文档仓库的代码就会自动构建并部署 github pages

本地开发环境的RepoPress和sailwind_doc（C:\Users\Administrator\Desktop\code\sailwind_docs）还没有提交，因为有些url等是dev模式（localhost）

RepoPress 的代码更新路径，在本地开发环境推送到github，然后在服务器上git pull RepoPress

不可以将本地开发环境代码直接同步到服务器上

服务器上完全干净

```
pz@pzser:~$ cat /etc/os-release
PRETTY_NAME="Ubuntu 22.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.3 LTS (Jammy Jellyfish)"
```

```
pz@pzser:~$ python3
Python 3.10.12 (main, Mar  3 2026, 11:56:32) [GCC 11.4.0] on linux
```

```
pz@pzser:~$ pip3 --version
pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)
```