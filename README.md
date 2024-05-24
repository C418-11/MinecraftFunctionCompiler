# MinecraftFunctionCompiler

将Python代码编译成Minecraft Function

欢迎大佬参与开发

### [`API文档`(点击跳转)](https://minecraftfunctioncompiler.readthedocs.io/zh/latest/index.html)

# *!!以下内容大部分已过时*

# 目录

* [环境](#环境)
* [功能](#功能)
* [1.编写源码](#1-编写源码)
    * [1.注意事项](#11-注意事项)
    * [2.示例](#12-示例)
* [2.编译源码](#2-编译源码)
    * [1.配置](#21-配置)
        * [1. 配置通用](#211-通用配置)
        * [2. 配置源码编译](#212-配置源码编译)
        * [3. 配置支持包编译](#213-配置支持包编译)
    * [2.编译打包](#22-编译打包)
        * [1. 编译支持包](#221-编译支持包)
        * [2. 编译源码](#222-编译源码)
        * [3. 组合编译后的源码](#223-组合编译后的源码)
* [3.制作模板函数](#3-制作模板函数)
    * [1.新建模板文件](#31-新建模板文件)
    * [2.编写模板函数](#32-编写模板函数)
    * [3.自定义断点](#33-自定义断点)

# 环境

* Python 3.12

# 功能

* 基于内置库ast将Python代码通过抽象语法树编译成Minecraft Function
* 支持If Function Import等基础语法
* 可以自行编写模板函数来拓展功能
* 可以在python环境下模拟在MC中执行
* 自定义断点

# 1. 编写源码

## 1.1. 注意事项

* 还有很多语法没有实现(class, lambda, for, while, raise, try-except, with, ...)
* 函数的参数目前不支持关键词参数
* 命名不可与内置函数名相同
* 只在1.16.5进行了测试, 理论向上兼容
* 编译时报错目前还是一团乱麻, 还请见谅

## 1.2. 示例

在[`./tests`(点击)](./tests)里包含了一些示例

* [`变量`(点击)](./tests/var_add.py)
* [`定义/调用函数`(点击)](./tests/func_add.py)
* [`if-else语句`(点击)](./tests/if_sub.py)
* [`命名空间测试`(点击)](./tests/namespace_test.py)
* [`递归`(点击)](./tests/recursive_call.py)
* [`导入函数`(点击)](./tests/import_add)
* [`From导入函数`(点击)](./tests/from_import_add)
* [`赋值导入变量`(点击)](./tests/assign_import_var)
* [`断点测试`(点击)](./tests/breakpoint_test.py)
* [`模板tprint`(点击)](./tests/template_print.py)
* [`模板bossbar`(点击)](./tests/template_bossbar.py)
* [`模板scoreboard`(点击)](./tests/scoreboard_op.py)

# 2. 编译源码

## 2.1. 配置

### 2.1.1 通用配置

* [`Constant.py`](./Constant.py)

  这里存储了主要的全局常量, 没有特殊需求不需要改动

### 2.1.2 配置源码编译

* [`DebuggingTools.py`](./DebuggingTools.py)
    * ENABLE_DEBUGGING

      这个常量控制是否开启调试模式, 开启后会生成调试用输出信息

      `**不建议启用** (长时间未维护 逻辑混乱)`
    * GENERATE_COMMENTS

      这个常量控制是否生成注释

      `**建议仅在调试编译时启用(如果在乎编译后体积的话)**`


* [`ScoreboardTools.py`](./ScoreboardTools.py)
    * IgnoreEncode

      这个常量控制是否禁止将命名空间编码为16进制

      `**仅应在调试编译时启用 (至少1.16.5计分板无法处理这么长的计分项)**`


* [`main.py`](./main.py)

  **!!!!!!!!!!如果发现下面这些值为None别急着在那里改值, 先去入口函数看一眼, 都在入口函数覆盖了值的**
    * SAVE_PATH = "./.output/"

      这个常量控制编译后的文件保存路径

    * READ_PATH = "./tests"

      这个常量控制读取的源码文件夹

    * TEMPLATE_PATH = "./template"

      这个常量控制模板函数源码文件夹

    * BASE_NAMESPACE = "source_code:"

      这个常量控制命名空间前缀

    * file_name

      这个变量用于读取源码入口文件

      `这个变量在入口函数 main 中`

### 2.1.3 配置支持包编译

* [`ReplacePlaceHolders.py`](./ReplacePlaceHolders.py)
    * file_extensions = [".mcfunction", ".mcmeta"]

      这个变量控制哪些文件后缀会进行替换操作
    * read_path = r".\\Python"

      这个变量控制读取的源码文件夹
    * save_path = r".\\.output"

      这个变量控制替换后保存的文件保存路径

## 2.2. 编译打包

### 2.2.1 编译支持包

(这个包是全局通用的, 只要Constant.py 未发生变更就不需要重新编译)

运行[`ReplacePlaceHolders.py`](./ReplacePlaceHolders.py)

如果你IDE支持执行markdown并且用的是虚拟环境, 你可以直接点击下面指令左边的绿色三角

```shell
python.exe .\\ReplacePlaceHolders.py
```

### 2.2.2 编译源码

运行[`main.py`](./main.py)

如果你IDE支持执行markdown并且用的是虚拟环境, 你可以直接点击下面指令左边的绿色三角

```shell
python.exe .\\main.py
```

### 2.2.3 组合编译后的源码

(引用)[`1.2 配置源码编译`(点击跳转)](#212-配置源码编译)中`main.py`配置的`BASE_NAMESPACE`

`BASE_NAMESPACE` 的默认值为 `"source_code:"`

这意味着为了使编译出来的代码正常工作, 你必须将编译出的代码放在`source_code`命名空间下

所以我们需要为编译出来的代码创建一个数据包

文件结构应该像这样

```text
datapacks  # 你存档的数据包文件夹
├── Python  # 编译后的支持包
└── 源码测试
    ├── pack.mcmeta
    └── data
        └── source_code
            └── functions
                ├── %file_name%  # 你配置的源码文件名
                │   ├── .__module.mcfunction  # 源码的入口文件
                │   ├── .if  # if分支(如果有的话)
                │   │   └── %id%.mcfunction
                │   └── %function name%
                │        ├── .if  # 函数内的if分支(如果有的话)
                │        └── ...
                └── ...  # 其他编译出的文件
```

# 3. 制作模板函数

## 3.1 新建模板文件

(引用)[`1.2 配置源码编译`(点击跳转)](#212-配置源码编译)中`main.py`配置的`TEMPLATE_PATH`

在`TEMPLATE_PATH`配置的文件夹下新建一个.py文件

在文件的开头写上如下注释

```python
# MCFC: Template
```

声明该文件是一个模板文件

随后进行必要的导入

``` python
from Template import register_func
```

## 3.2 编写模板函数

需要使用`@register_func`装饰器来注册模板函数

下面是一个简单的用法示例

``` python
def func_for_compile() -> str | None:
    # 当在编译环境下执行源码时将会执行这个函数
    # 这个函数应该返回一个以换行分割的MC指令字符串
    pass

@register_func(func_for_compile)
def func_for_python():
    # 当在python环境下执行源码时将会执行这个函数
    pass
```

我个人习惯这么写:

``` python
def _your_func_name() -> str | None:
    # func for compile
    pass

@register_func(_your_func_name)
def your_func_name():
    # func for python
    pass
```

func_for_compile 函数会有一些特殊参数

* `namespace` - 调用这个函数时的命名空间
* `file_namespace` - 调用这个函数时的文件命名空间

需要注意的是, 这些参数是编译期间自动传入的

如果函数头没有声明这些参数, 编译器调用时会忽略这些参数, 所以需要注意拼写

## 3.3 自定义断点

导入`raiseBreakPoint`函数

``` python
from BreakPointTools import raiseBreakPoint
```

在需要断点的位置调用`raiseBreakPoint`函数

``` python
raiseBreakPoint(file_namespace, func, *func_args, **func_kwargs)
```
