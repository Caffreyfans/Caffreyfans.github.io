---
title: 一键部署小鹤音形方案
date: 2019-01-01
categories: Linux

---
### 部署原理
1. 安装 Fcitx 输入框架
2. 安装 Rime 输入法
3. 部署音形方案

**Fcitx** (Flexible Input Method Framework) ──即小企鹅输入法，它是一个以 **GPL** 方式发布的输入法平台,可以通过安装引擎支持多种输入法，支持简入繁出，是在 Linux 操作系统中常用的中文输入法。它的优点是，短小精悍、跟程序的兼容性比较好。

**Rime** 是一种中文输入法引擎是一种被广泛支持的输入法。**Rime** 输入法引擎可以被用在 **IBus** 和 **Fcitx** 输入框架下。

这也就是说小鹤音形只是一种输入法方案，并不是输入法。我们可以将这个方案挂接在 **Rime** 输入法下。**ibus-rime** 和 **fcitx-rime** 都可以部署音形方案。

该脚本就是在 **fcitx-rime** 这种模式下部署的小鹤音形方案。

### 演示
![example](https://raw.githubusercontent.com/Caffreyfans/flypy-install/master/example.gif)

### 手动安装演示
[bilibili](https://bilibili.com/video/av46403021)

### 安装
该一键安装脚本只适用于 Debian、Ubuntu、Centos 系统。
直接在终端下执行以下命令就是了。该项目地址 [github](https://github.com/Caffreyfans/flypy-install)

```shell
wget -O install.sh https://raw.githubusercontent.com/Caffreyfans/flypy-install/master/install.sh && sudo chmod +x install.sh && ./install.sh
```
