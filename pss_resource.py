import re
import os

def get_file_size(file_path):
    """
    返回指定文件的大小（字节）。如果文件不存在或发生错误，返回 None。
    """
    try:
        return os.path.getsize(file_path)
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{file_path}'")
        return None
    except OSError as e:
        print(f"发生错误: {e}")
        return None
    
def parse_section_sizes(file_path):
    """
    解析 readelf 输出文件，提取指定 section 的 Size。
    """
    targets = {
        ".ramVectors": None,
        ".appTextRam": None,
        ".data": None,
        ".noinit": None,
        ".bss": None,
        ".bootstrapText": None,
        ".bootstrapze[...]": None,
        ".bootstrapData": None,
        ".bootstrapBss": None
    }
    
    # 定义正则表达式来匹配 Section 行
    # 典型格式: [ 1] .ramVectors       NOBITS          20001000 001000 000158 00  WA  0   0 512
    # 解释:
    #   \[\s*\d+\]      匹配索引，如 [ 1] 或 [10]
    #   \s+             空白
    #   (\S+)           捕获组1: Section Name (非空字符)
    #   \s+\S+          Type 列 (忽略)
    #   \s+[0-9a-fA-F]+ Addr 列 (忽略)
    #   \s+[0-9a-fA-F]+ Off 列 (忽略)
    #   \s+([0-9a-fA-F]+) 捕获组2: Size 列 (十六进制数值)
    pattern = re.compile(r"\[\s*\d+\]\s+(\S+)\s+\S+\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    section_name = match.group(1)
                    size_hex = match.group(2)
                    
                    if section_name in targets:
                        # 保存十六进制字符串和转换后的十进制整数
                        size_int = int(size_hex, 16)
                        targets[section_name] = {
                            "hex": size_hex,
                            "int": size_int
                        }
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{file_path}'")
        return
    except Exception as e:
        print(f"发生错误: {e}")
        return

    return targets

    
# 创建一个示例文件（模拟用户上传的 crab.readelf 内容），以便代码可以直接运行测试
# 实际使用时，脚本会直接读取磁盘上的 crab.readelf 文件
def create_mock_file(filename):
    content = """
There are 29 section headers, starting at offset 0x3aec5c:

Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .ramVectors       NOBITS          20001000 001000 000158 00  WA  0   0 512
  [ 2] .appTextRam       PROGBITS        04001158 061158 0065e8 00  AX  0   0  8
  [ 3] .data             PROGBITS        20007740 067740 002214 00  WA  0   0  8
  [ 4] .noinit           NOBITS          20009958 069954 000058 00  WA  0   0  8
  [ 5] .bss              NOBITS          200099b0 069954 006b34 00  WA  0   0  8
  [ 6] .heap             NOBITS          200104e4 069954 02d71c 00  WA  0   0  1
  [ 7] .bootstrapText    PROGBITS        0403dc00 00dc00 001648 00  AX  0   0  8
  [ 8] .bootstrapze[...] PROGBITS        0403f248 00f248 000008 00  WA  0   0  1
  [ 9] .bootstrapData    PROGBITS        2003f250 00f250 000074 00   A  0   0  4
  [10] .bootstrapBss     PROGBITS        2003f2c4 069954 000000 00   W  0   0  1
  [11] .appText          PROGBITS        08022a00 012a00 04a358 00  AX  0   0  8
  [12] .copy.table       PROGBITS        0806cd58 05cd58 000018 00  WA  0   0  1
  [13] .ARM.exidx        ARM_EXIDX       0806cd70 05cd70 000008 00  AL 11   0  4
  [14] .zero.table       PROGBITS        0806cd78 05cd78 000008 00  WA  0   0  1
  [15] .ARM.attributes   ARM_ATTRIBUTES  00000000 069954 00002e 00      0   0  1
  [16] .comment          PROGBITS        00000000 069982 000033 01  MS  0   0  1
  [17] .debug_line       PROGBITS        00000000 0699b5 093d18 00      0   0  1
  [18] .debug_line_str   PROGBITS        00000000 0fd6cd 00013f 01  MS  0   0  1
  [19] .debug_info       PROGBITS        00000000 0fd80c 16f9b0 00      0   0  1
  [20] .debug_abbrev     PROGBITS        00000000 26d1bc 0312b1 00      0   0  1
  [21] .debug_aranges    PROGBITS        00000000 29e470 0070c8 00      0   0  8
  [22] .debug_str        PROGBITS        00000000 2a5538 04253d 01  MS  0   0  1
  [23] .debug_loclists   PROGBITS        00000000 2e7a75 06811e 00      0   0  1
  [24] .debug_rnglists   PROGBITS        00000000 34fb93 009849 00      0   0  1
  [25] .debug_frame      PROGBITS        00000000 3593dc 015224 00      0   0  4
  [26] .symtab           SYMTAB          00000000 36e600 029040 10     27 7818  4
  [27] .strtab           STRTAB          00000000 397640 0174ca 00      0   0  1
  [28] .shstrtab         STRTAB          00000000 3aeb0a 00014f 00      0   0  1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), y (purecode), p (processor specific)

Elf file type is EXEC (Executable file)
Entry point 0x403dd81
There are 7 program headers, starting at offset 52

Program Headers:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  EXIDX          0x05cd70 0x0806cd70 0x6006cd70 0x00008 0x00008 R   0x4
  LOAD           0x000000 0x20000000 0x20000000 0x00114 0x01158 RW  0x10000
  LOAD           0x00dc00 0x0403dc00 0x60020450 0x01650 0x01650 RWE 0x10000
  LOAD           0x00f250 0x2003f250 0x60021aa0 0x00074 0x00074 R   0x10000
  LOAD           0x012a00 0x08022a00 0x60022a00 0x4a380 0x4a380 RWE 0x10000
  LOAD           0x061158 0x04001158 0x6006cd80 0x065e8 0x065e8 R E 0x10000
  LOAD           0x067740 0x20007740 0x60073368 0x02214 0x364c0 RW  0x10000

Section to Segment mapping:
  Segment Sections...
   00     .ARM.exidx 
   01     .ramVectors 
   02     .bootstrapText .bootstrapzero.table 
   03     .bootstrapData 
   04     .appText .copy.table .ARM.exidx .zero.table 
   05     .appTextRam 
   06     .data .noinit .bss .heap 
"""
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建测试文件: {filename}\n")

if __name__ == "__main__":
    filename = "crab.bin"
    size = get_file_size(filename)  # 测试文件大小函数
    print("code size=",size)
    
    filename = "crab.readelf"
    
    # 这一步是为了演示方便，如果你本地已经有这个文件，可以注释掉下面这行
    create_mock_file(filename)
    
    # 执行解析
    targets = parse_section_sizes(filename)
    
        # 输出结果
    print(f"{'Section Name':<15} | {'Size (Hex)':<10} | {'Size (Bytes)'}")
    print("-" * 45)
    
    size = 0
    for name, data in targets.items():
        if data:
            print(f"{name:<15} | 0x{data['hex']:<8} | {data['int']}")
            size += data['int']
        else:
            print(f"{name:<15} | {'Not Found':<10} | -")
            
    print("ram size=",size)
