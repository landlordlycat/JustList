# JustList

> JustList，仅仅是目录。
>
> 没错，又一款简单的网盘文件列表与分享工具。

* [Demo for JustList](https://lib.tls.moe/)

## 功能

* 支持不同网盘
  + 天翼云盘
  + 阿里云盘
  + OneDrive & 世纪互联
  + 本地文件
* 支持多个网盘的多用户使用
* 支持文件夹密码保护
* 简单的请求预处理机制

## 使用

### Docker

- [Docker Hub](https://hub.docker.com/r/txperl/justlist)

### 手动部署

- [部署演示视频](https://www.bilibili.com/video/BV15V4y1J7b4/) by [hcllmsx](https://github.com/hcllmsx)

本程序支持前后端分离，以下主要为后端部署说明。

总的来说，很简单的几步：安装依赖、修改配置、运行。

#### 1. 安装依赖

``` bash
# Python 3.7(+)
$ pip install -r requirements.txt
```

#### 2. 修改配置

所有配置文件都位于 `./app/config/` 文件夹中，如下：

- local: 本地目录配置项
- cloud189: 天翼云盘配置
- aliyundrive: 阿里云盘配置
- onedrive: OneDrive 配置
- switch: 插件开关与预处理相关配置

若要启用某个网盘，必须修改的是账号配置，它们位于各网盘配置文件头部的 `accounts` 字段。例如：

``` yaml
# OneDrive，下列字段位于 ./app/config/onedrive.yml
# 0 为国际版，1 为世纪互联版
accounts:
  OneDrive_INTL: 0
  OneDrive_CN: 1
```

需要注意的是，**部分网盘在启动时程序会引导您手动获取登录信息**。

#### 3. 启动程序

``` bash
$ python main.py
```

若要更改程序的运行地址，请修改 `./main.py`。默认为 `http://0.0.0.0:5000/`。

## 额外

以下皆为**可选操作**，并不是必须的。

### 文件夹密码

若要将特定文件夹设为私密，即设置文件夹密码，需进行如下操作。

1. 在预加密的网盘文件夹中，创建文件/文件夹
2. 将其名称设置为 `<password>._.jl` 格式

另外，程序支持在加密的文件夹下再设置其他私密文件夹。参考如下：

```
. 网盘目录
├── 私密文件夹 1（密码为 123）
├── ├── 123._.jl
├── ├── 1 files
├── ├── 私密文件夹 2（密码为 321）
├── ├── ├── 321._.jl
├── ├── ├── 2 files
```

私密文件夹下的所有文件也都是私密的，需要密码才可访问与下载。

### 默认显示用户

若要自定义前端 `md` 主题的默认显示用户，即默认显示的网盘文件列表，需进行如下操作。

1. 修改 `./templates/md.html` 中 `root_user` 一项

### 强制刷新目录缓存

如果需要手动强制刷新目录缓存，需进行如下操作。

1. 编辑 `./app/plugin/sys_update.py` ，将 `sys/update/xxxiiixxx` 改为你想要的强制刷新地址
2. 编辑 `./app/config/switch.yml` ，将 `sys_update.py` 设置为 `true`

**默认为停用状态，若开启请务必修改地址**！否则可能会被恶意请求。

## 开发

### 目录

```
. JustList
├── altfe                         # Altfe 代码框架核心
├── app                           # JustList 主程序代码
├── ├── config                      # 配置项
├── ├── lib                         # 全局模块，启动时加载并实例化相应模块，供其他模块调用
├── ├── ├── common                    # 通用类
├── ├── ├── core                      # 核心类
├── ├── ├── ins                       # 通用实例类
├── ├── ├── static                    # 静态类
├── ├── pre                         # 预处理模块，当收到请求后但在插件实例化前执行
├── ├── ├── rate_limit.py             # Rate Limit 代码
├── ├── ├── verify_referrer.py        # Rreferrer 验证代码
├── ├── plugin                      # 插件模块，当收到请求后会被实例化并执行
├── ├── ├── do_file.py                # 直链跳转
├── ├── ├── get_list.py               # 目录获取
├── ├── ├── sys_update.py             # 强制刷新缓存
├── templates                       # 前端主题
├── ├── md.html
├── main.py                           # 启动
```

### API

此部分可自行修改插件以更改。

1. **目录获取**
  + `[POST] api/get/list/`
  + `api/get/list/` : 返回全部目录
  + `api/get/list/user1/` : 返回 user1 的全部目录
  + `api/get/list/user2/a/b/` : 返回 user2 的 a 目录下的 b 目录/文件（如果存在）
      + `# application/json; charset=utf-8`
      + `password` : 目录密码（可选）
  + `api/get/list/user3/` : 返回 user3 的 id 为 xxx 的目录/文件
      + `# application/json; charset=utf-8`
      + `id` : 文件 ID
      + `password` : 目录密码（可选）

2. **文件下载**
  + `[GET] file/`
  + `file/user1/a/b/` : 返回 user1 的 a 目录下的 b 文件地址（如果存在）
  + `file/user2/?id=xxx` : 返回 user2 的 id 为 xxx 的文件地址
  + `file/user3/?id=xxx&password=psw` : 返回 user3 的 id 为 xxx 的文件地址，且访问密码为 psw

3. **强制刷新目录缓存**
  + `[GET] sys/update/xxxiiixxx/`

## 说明

* 本程序会一次性加载全部允许的文件并缓存，所以若文件较多此过程可能会较慢（取决于文件的数量与网络状况），但不影响正常运行
* 网盘操作代码参考自 [Aruelius/cloud189](https://github.com/Aruelius/cloud189)、[MoeClub/OneList](https://github.com/MoeClub/OneList)，感谢

## 声明

* 本程序仅供学习参考，请在达成目的后停止使用
* 使用后任何不可知事件都与原作者无关，原作者不承担任何后果
* [MIT License](https://choosealicense.com/licenses/mit/)

使用愉快。

; )
