# 霍尔传感器硬件逐步测试清单

适用硬件：OpenRF1 STM32F103RCT6 控制板、1 个 HW-477/A3144 霍尔模块。

本清单只验证隔离霍尔模块。每次只执行一个编号步骤；该步骤不通过时立即停止，不要跳步。

## 测试边界

- 传感器 ID：`hall_1`。
- 用途：磁性地标或检查点检测。
- 模块供电：OpenRF1 5 V。
- STM32 输入：循迹接口 signal 3 / X3 / PB0。
- 固件：`OpenRF1_GroundSensors_Bringup`。
- 遥测字段：`payload.hall_sensor.raw_level` 和 `debounced_level`。
- 测试前不得假定有效电平、触发磁极、触发距离或最终安装方向。
- 本测试不验证里程计、最终装车方向、电机振动性能或完整整车运行。

## 所需物品

- OpenRF1 控制板。
- HW-477/A3144 霍尔模块 1 个。
- 磁铁 1 个。
- 10 kOhm 电阻 1 个，精度 5% 或更好。
- 15 kOhm 电阻 1 个，精度 5% 或更好。
- 数字万用表。
- 面包板、接线端子或分线器。
- 杜邦线。
- USB/串口线和 STM32 烧录工具。

## 锁定接线

```text
OpenRF1 5 V ------------------------------ Hall +

Hall S ---- 10 kOhm ----+---- 受保护的 X3 / PB0
                        |
                      15 kOhm
                        |
OpenRF1 GND ------------+----------------- Hall -
```

标称分压值：5.0 V 输入约得到 3.0 V。禁止把 Hall `S` 直接接到 PB0。

## 必须使用的“一拖多”节点

本接线需要两个一拖多节点。使用面包板同一排、接线端子或正规分线器；不要把多根松散导线硬塞进一个端子。

- 公共 GND 节点一拖三：OpenRF1 GND、Hall `-`、15 kOhm 电阻下端。
- 受保护 PB0 节点一拖三：10 kOhm 电阻下端、15 kOhm 电阻上端、X3/PB0。
- 霍尔必须使用独立的一对 10 kOhm / 15 kOhm 电阻；不得与 HC-SR04 共用分压节点或电阻。
- 分压电压测量合格前，不得把 X3/PB0 接入受保护节点。

## 立即停止条件

发生任意一种情况时，立即断电并停止：

- 板卡或模块发热。
- 出现烟、异味或可见损坏。
- 无法确认引脚标签或接口方向。
- 实测 5 V 电源高于 5.5 V。
- 任一磁状态下的分压输出高于 3.3 V。
- 发现 Hall `S` 直接连接 PB0。

## A. 准备

1. [ ] 断开 OpenRF1 的全部电源。
2. [ ] 断开 OpenRF1 上所有无关模块。
3. [ ] 将 Hall 模块的 `+`、`-`、`S` 标签朝上放置。
4. [ ] 拍摄 Hall 模块正面照片。
5. [ ] 拍摄 Hall 模块背面照片。
6. [ ] 确认循迹接口 pin 1 是 GND。
7. [ ] 确认循迹接口 pin 3 是 X3/PB0。
8. [ ] 确认循迹接口 pin 6 是 VCC_5V。
9. [ ] 保持 X3/PB0 断开。

## B. 电阻检查

10. [ ] 将万用表调到电阻档。
11. [ ] 测量未接入电路的 10 kOhm 电阻。
12. [ ] 记录 10 kOhm 电阻实测值。
13. [ ] 确认实测值位于 9.50 kOhm 至 10.50 kOhm。
14. [ ] 测量未接入电路的 15 kOhm 电阻。
15. [ ] 记录 15 kOhm 电阻实测值。
16. [ ] 确认实测值位于 14.25 kOhm 至 15.75 kOhm。

超出范围的电阻不要用于本次正式测试。

## C. 断电搭建分压器

17. [ ] 将 Hall `S` 接到 10 kOhm 电阻的一端。
18. [ ] 将 10 kOhm 电阻另一端接到空闲的受保护节点。
19. [ ] 将 15 kOhm 电阻一端接到受保护节点。
20. [ ] 将 15 kOhm 电阻另一端接到空闲的公共 GND 节点。
21. [ ] 将 Hall `-` 接到公共 GND 节点。
22. [ ] 将 OpenRF1 GND 接到公共 GND 节点。
23. [ ] 确认公共 GND 节点已经一拖三。
24. [ ] 确认受保护节点仍未连接 PB0。
25. [ ] 将 Hall `+` 接到 OpenRF1 VCC_5V。
26. [ ] 检查断电电路是否存在松线或短路。

## D. 测量模块供电

27. [ ] 将万用表调到直流电压档。
28. [ ] 将黑表笔接到公共 GND 节点。
29. [ ] 给 OpenRF1 上电。
30. [ ] 测量 Hall `+` 处的供电电压。
31. [ ] 记录 Hall 供电电压。
32. [ ] 确认 Hall 供电不高于 5.5 V。

## E. 在连接 PB0 前测量 Hall S

33. [ ] 将磁铁移到远离 Hall 模块的位置。
34. [ ] 测量 10 kOhm 电阻前的 Hall `S` 电压。
35. [ ] 记录无磁铁时的 Hall `S` 电压。
36. [ ] 用磁铁一个磁极缓慢靠近模块一个表面。
37. [ ] 测量触发状态下的 Hall `S` 电压。
38. [ ] 记录触发状态下的 Hall `S` 电压。
39. [ ] 移开磁铁。
40. [ ] 确认 Hall `S` 电压恢复到无磁铁状态。

如果没有出现变化，每次只改变一个条件：先换磁铁另一磁极，再换模块另一表面。记录能够稳定触发的表面和磁极。观察到重复变化前，不要定义有效电平。

## F. 测量受保护分压输出

41. [ ] 将磁铁移到远离 Hall 模块的位置。
42. [ ] 测量受保护节点电压。
43. [ ] 记录无磁铁时的受保护电压。
44. [ ] 将磁铁放到已确认的触发位置。
45. [ ] 测量受保护节点电压。
46. [ ] 记录触发状态下的受保护电压。
47. [ ] 确认两种受保护电压都不高于 3.3 V。
48. [ ] 移开磁铁。
49. [ ] 断开 OpenRF1 电源。

任一受保护电压超过 3.3 V 时，不得继续。

## G. 电压合格后连接 PB0

50. [ ] 将受保护节点接到 signal 3 / X3 / PB0。
51. [ ] 确认受保护节点已经一拖三。
52. [ ] 确认 Hall `S` 只能通过 10 kOhm 电阻到达 PB0。

## H. 编译和烧录隔离固件

53. [ ] 在 Keil 中打开 `firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx`。
54. [ ] Rebuild `OpenRF1_GroundSensors_Bringup` target。
55. [ ] 记录 Keil 的 error 和 warning 数量。
56. [ ] 在仓库根目录运行下面一条命令。

```powershell
Get-FileHash .\firmware\openrf1\keil\Objects_GroundSensors_Bringup\OpenRF1_GroundSensors_Bringup.hex -Algorithm SHA256
```

57. [ ] 记录 HEX SHA-256。
58. [ ] 使用批准的 STM32 烧录工具烧录 `OpenRF1_GroundSensors_Bringup.hex`。
59. [ ] 记录擦除、写入、校验和运行结果。

仓库证据中不要写入具体 COM 号、Windows 用户名、用户绝对路径或 MCU 唯一序列号。

## I. 观察实时 Hall 遥测

60. [ ] 将磁铁移到远离 Hall 模块的位置。
61. [ ] 给 OpenRF1 上电。
62. [ ] 将 `<USER_VERIFIED_PORT>` 替换为实际端口后运行下面一条命令。

```powershell
& '.\pc\.venv\Scripts\python.exe' -c "import serial; s=serial.Serial(); s.port='<USER_VERIFIED_PORT>'; s.baudrate=115200; s.timeout=2; s.dtr=False; s.rts=False; s.open(); s.readline(); [print(s.readline().decode('ascii','replace').rstrip()) for _ in range(10)]; s.close()"
```

63. [ ] 记录无磁铁时 Hall 的 raw 和 debounced 电平。
64. [ ] 将磁铁放到已确认的触发位置。
65. [ ] 再运行一次同一条 10 帧串口命令。
66. [ ] 记录触发时 Hall 的 raw 和 debounced 电平。
67. [ ] 移开磁铁。
68. [ ] 再运行一次同一条 10 帧串口命令。
69. [ ] 确认 Hall 电平恢复到无磁铁状态。

隔离 Hall 测试期间忽略 PC4/PC5 的 TCRT 数值。

## J. 重复性测试

70. [ ] 将磁铁移入触发位置十次。
71. [ ] 确认十次靠近都产生相同的 debounced 变化。
72. [ ] 将磁铁移出触发位置十次。
73. [ ] 确认十次移开都恢复到相同状态。
74. [ ] 记录可重复触发距离，单位为毫米。
75. [ ] 记录触发模块表面。
76. [ ] 记录触发磁极。

## K. 保存脱敏证据

77. [ ] 将磁铁移到远离 Hall 模块的位置。
78. [ ] 替换 `<USER_VERIFIED_PORT>` 后运行无磁铁采集命令。

```powershell
& '.\pc\.venv\Scripts\python.exe' -c "import serial,pathlib; p=pathlib.Path(r'.verification\phase3.2f\hall_1_no_magnet.jsonl'); p.parent.mkdir(parents=True,exist_ok=True); s=serial.Serial(); s.port='<USER_VERIFIED_PORT>'; s.baudrate=115200; s.timeout=2; s.dtr=False; s.rts=False; s.open(); s.readline(); lines=[s.readline().decode('ascii','replace') for _ in range(100)]; s.close(); p.write_text(''.join(lines),encoding='ascii'); print(p); print('frames:',len(lines))"
```

79. [ ] 将磁铁放到已确认的触发位置。
80. [ ] 替换 `<USER_VERIFIED_PORT>` 后运行有磁铁采集命令。

```powershell
& '.\pc\.venv\Scripts\python.exe' -c "import serial,pathlib; p=pathlib.Path(r'.verification\phase3.2f\hall_1_magnet.jsonl'); p.parent.mkdir(parents=True,exist_ok=True); s=serial.Serial(); s.port='<USER_VERIFIED_PORT>'; s.baudrate=115200; s.timeout=2; s.dtr=False; s.rts=False; s.open(); s.readline(); lines=[s.readline().decode('ascii','replace') for _ in range(100)]; s.close(); p.write_text(''.join(lines),encoding='ascii'); print(p); print('frames:',len(lines))"
```

81. [ ] 移开磁铁。
82. [ ] 运行下面一条证据哈希命令。

```powershell
Get-FileHash .\.verification\phase3.2f\hall_1_*.jsonl -Algorithm SHA256
```

83. [ ] 记录两份 JSONL 的 SHA-256。
84. [ ] 断开 OpenRF1 电源。

## 证据记录表

| 项目 | 结果 |
| --- | --- |
| 10 kOhm 电阻实测值 | |
| 15 kOhm 电阻实测值 | |
| Hall 供电电压 | |
| 无磁铁 Hall S 电压 | |
| 触发时 Hall S 电压 | |
| 无磁铁受保护电压 | |
| 触发时受保护电压 | |
| 无磁铁 raw/debounced | |
| 触发时 raw/debounced | |
| 触发模块表面 | |
| 触发磁极 | |
| 可重复触发距离 | |
| 十次靠近结果 | |
| 十次移开结果 | |
| Keil errors/warnings | |
| HEX SHA-256 | |
| 无磁铁 JSONL SHA-256 | |
| 有磁铁 JSONL SHA-256 | |

## 允许写入的结论

全部必需步骤通过后，只能将以下内容记录为 `MANUAL_EVIDENCE_VERIFIED`：隔离 Hall 接线、实测受保护电压、可重复的 raw/debounced 磁响应和隔离串口遥测。

最终装车方向、电机振动性能、磁性地标识别可靠性、长时间稳定性、完整 multisensor 固件、整车运行和里程计仍然保持 `UNVERIFIED`。
