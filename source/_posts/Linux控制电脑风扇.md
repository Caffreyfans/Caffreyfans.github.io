---
title: Linux 系统下手动控制电脑风扇
date: 2018-12-19
tags:
- Linux
---

## 命令控制简单方便
笔记本风扇的轴承坏了，导致电脑运行时声音特别大。所以我到处在网上找资料看能不能通过手动的方法来限制风扇的转速，皇天不负有心人我还是找到了文档。风扇应该是I2C控制的，这样主板可以控制风扇的转速，风扇的转速也可以反馈到电脑。
我们需要先找到风扇控制在 **Linux** 下的位置。我们只需要通过安装一个很小的工具就可以检测我们的电脑风扇了位置了。

```bash
sudo apt-get install lm-sensors fancontrol -y # 安装 lm-sensors fancontrol
```
<!--more-->
这里讲解一下 **lm-sensors** 与 **fancontrol** 这两个工具的作用。

| 工具包名 | 使用命令 | 作用 |
| --- | --- | --- |
| lm-sensors | sensors | 查看硬件温度 |
| fancontrol | pwmconfig | 查找风扇位置 |

安装好工具包之后我们首先通过
```bash
sudo pwmconfig
```
来找到我们风扇的位置，如果你是第一次使用它会询问你，输入 `y`  确认一下就行了。看一下执行结果

| sudo pwmconfig | sensors |
| --- | --- |
| ![1](https://raw.githubusercontent.com/Caffreyfans/Public-Source/master/pictures/blog_2/1.jpg) | ![2](https://raw.githubusercontent.com/Caffreyfans/Public-Source/master/pictures/blog_2/2.jpg) |

从 `sudo pwmconfig` 的执行结果来看，`Found the following PWM controls:` `hwmon3/pwm1` 那么就说明风扇的控制文件位置在 `hwmon3/pwm1` 了，那么我们直接在这个文件里直接填入控制值就可以实现手动控制电脑风扇了。
```bash
echo 50 > /etc/class/hwmon/hwmon3/pwm1
```

风扇的转速通过 **PWM** 控制，也就是脉冲宽度调制。可以这样理解在一个周期内，高电平所占的时间长那么风扇就会转的更快，**PWM** 值可以取 0~255 之间的整数，0 就代表停止，255就代表最大转速。比如我这里查到我风扇对应的控制文件位置是 /hwmon3/pwm1，那么你就可以通过修改 **/sys/class/hwmon/hwmon3/pwm1** 文件里面的数值来改变风扇的转速了，这种办法只是暂时有效，一旦用户休眠或则注销，又得重新设置了。所以如果你想开机就让风扇转速受到控制你还得写个脚本再把它做成服务，然后让它开机执行。

其实最好的解决风扇的问题就是换个风扇。换个笔记本风扇不难，去网上自己买个笔记本风扇就几十块钱，把笔记本拆开自己就换了用不了多就，要不然就找外面修理店的人帮你换。对于一般的笔记本来说超过 **50** 就算坑你了，自己可以在网上先看看你那种机型的风扇值多少。