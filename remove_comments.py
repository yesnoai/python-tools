#!/usr/bin/env python3
"""
递归删除目录下所有C/C++文件注释的工具
支持的文件扩展名: .c, .cpp, .cc, .cxx, .h, .hpp, .hxx
"""

import os
import re
import argparse
import sys
from pathlib import Path
from typing import Tuple, List, Dict

class CommentRemover:
    def __init__(self):
        # 匹配字符串字面量的正则表达式
        self.string_pattern = r'\"(?:\\.|[^\"\\])*\"'
        # 匹配字符字面量的正则表达式
        self.char_pattern = r"\'(?:\\.|[^\'\\])*\'"
        # 匹配单行注释的正则表达式
        self.single_line_comment_pattern = r'//.*?$'
        # 匹配多行注释的正则表达式
        self.multi_line_comment_pattern = r'/\*.*?\*/'
        
        # 支持的C/C++文件扩展名
        self.supported_extensions = {
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx', '.hpp', '.ipp'
        }
    
    def is_cpp_file(self, file_path: str) -> bool:
        """检查文件是否是C/C++文件"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def remove_comments(self, code: str) -> str:
        """
        删除C/C++代码中的所有注释
        """
        if not code.strip():
            return code
            
        lines = code.split('\n')
        result_lines = []
        in_multiline_comment = False
        multiline_buffer = []
        
        for line in lines:
            if not in_multiline_comment:
                # 处理新行，不在多行注释中
                processed_line, in_multiline_comment = self._process_line(line, in_multiline_comment)
                if processed_line is not None:
                    result_lines.append(processed_line)
            else:
                # 当前在多行注释中，查找注释结束
                end_index = line.find('*/')
                if end_index != -1:
                    # 找到注释结束
                    in_multiline_comment = False
                    # 处理注释后的部分
                    remaining_part = line[end_index + 2:]
                    if remaining_part.strip():
                        processed_part, _ = self._process_line(remaining_part, False)
                        if processed_part is not None:
                            if multiline_buffer:
                                result_lines.append(multiline_buffer[0] + processed_part)
                                multiline_buffer.clear()
                            else:
                                result_lines.append(processed_part)
                else:
                    # 整行都在注释中，跳过
                    continue
        
        return '\n'.join(result_lines)
    
    def _process_line(self, line: str, in_comment: bool) -> Tuple[str, bool]:
        """处理单行代码，移除注释"""
        if in_comment:
            return None, True
            
        # 保护字符串字面量
        protected_line, string_map = self._protect_strings(line)
        
        # 移除单行注释
        protected_line = re.sub(self.single_line_comment_pattern, '', protected_line)
        
        # 检查多行注释
        multiline_start = protected_line.find('/*')
        if multiline_start != -1:
            multiline_end = protected_line.find('*/', multiline_start + 2)
            if multiline_end != -1:
                # 单行内的完整多行注释
                protected_line = protected_line[:multiline_start] + protected_line[multiline_end + 2:]
            else:
                # 多行注释开始
                protected_line = protected_line[:multiline_start]
                in_comment = True
        
        # 恢复字符串字面量
        processed_line = self._restore_strings(protected_line, string_map)
        
        # 移除空行或只包含空白字符的行
        processed_line = processed_line.rstrip()
        if not processed_line.strip():
            return None, in_comment
            
        return processed_line, in_comment
    
    def _protect_strings(self, line: str) -> Tuple[str, dict]:
        """保护字符串字面量，防止被误认为是注释"""
        string_map = {}
        protected_line = line
        
        # 保护双引号字符串
        str_count = 0
        for match in re.finditer(self.string_pattern, protected_line):
            placeholder = f'__STRING_{str_count}__'
            string_map[placeholder] = match.group()
            protected_line = protected_line.replace(match.group(), placeholder, 1)
            str_count += 1
        
        # 保护单引号字符
        char_count = 0
        for match in re.finditer(self.char_pattern, protected_line):
            placeholder = f'__CHAR_{char_count}__'
            string_map[placeholder] = match.group()
            protected_line = protected_line.replace(match.group(), placeholder, 1)
            char_count += 1
        
        return protected_line, string_map
    
    def _restore_strings(self, line: str, string_map: dict) -> str:
        """恢复被保护的字符串字面量"""
        restored_line = line
        for placeholder, original in string_map.items():
            restored_line = restored_line.replace(placeholder, original)
        return restored_line

class DirectoryCommentCleaner:
    def __init__(self, backup: bool = True, verbose: bool = False):
        self.remover = CommentRemover()
        self.backup = backup
        self.verbose = verbose
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'total_files': 0
        }
    
    def find_cpp_files(self, directory: str) -> List[str]:
        """递归查找目录中的所有C/C++文件"""
        cpp_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            print(f"错误: 目录不存在 {directory}")
            return []
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and self.remover.is_cpp_file(file_path.name):
                cpp_files.append(str(file_path))
        
        return cpp_files
    
    def backup_file(self, file_path: str) -> str:
        """创建文件备份"""
        backup_path = file_path + '.backup'
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return backup_path
        except Exception as e:
            print(f"警告: 无法创建备份文件 {backup_path}: {e}")
            return None
    
    def process_file(self, file_path: str) -> bool:
        """处理单个文件，删除注释"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 创建备份
            if self.backup:
                backup_path = self.backup_file(file_path)
                if backup_path and self.verbose:
                    print(f"创建备份: {backup_path}")
            
            # 删除注释
            cleaned_content = self.remover.remove_comments(original_content)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            if self.verbose:
                print(f"处理完成: {file_path}")
            
            return True
            
        except UnicodeDecodeError:
            print(f"跳过文件（编码问题）: {file_path}")
            return False
        except Exception as e:
            print(f"处理文件失败 {file_path}: {e}")
            return False
    
    def process_directory(self, directory: str, recursive: bool = True) -> Dict:
        """处理目录中的所有C/C++文件"""
        print(f"扫描目录: {directory}")
        
        if recursive:
            cpp_files = self.find_cpp_files(directory)
        else:
            # 只处理当前目录
            cpp_files = []
            dir_path = Path(directory)
            for file_path in dir_path.iterdir():
                if file_path.is_file() and self.remover.is_cpp_file(file_path.name):
                    cpp_files.append(str(file_path))
        
        self.stats['total_files'] = len(cpp_files)
        
        if not cpp_files:
            print("未找到C/C++文件")
            return self.stats
        
        print(f"找到 {len(cpp_files)} 个C/C++文件")
        
        for i, file_path in enumerate(cpp_files, 1):
            print(f"[{i}/{len(cpp_files)}] 处理: {file_path}")
            
            if self.process_file(file_path):
                self.stats['files_processed'] += 1
            else:
                self.stats['files_skipped'] += 1
        
        return self.stats
    
    def print_stats(self):
        """打印处理统计信息"""
        print("\n" + "="*50)
        print("处理统计:")
        print(f"总文件数: {self.stats['total_files']}")
        print(f"成功处理: {self.stats['files_processed']}")
        print(f"跳过文件: {self.stats['files_skipped']}")
        print("="*50)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='递归删除目录下所有C/C++文件的注释',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s /path/to/src                    # 处理目录（递归，包含备份）
  %(prog)s /path/to/src --no-backup        # 不创建备份文件
  %(prog)s /path/to/src --no-recursive     # 只处理当前目录
  %(prog)s /path/to/src --verbose          # 显示详细输出
  %(prog)s /path/to/src --dry-run          # 干跑模式，不修改文件
        '''
    )
    
    parser.add_argument('directory', help='要处理的目录路径')
    parser.add_argument('--no-backup', action='store_true', 
                       help='不创建备份文件（危险）')
    parser.add_argument('--no-recursive', action='store_true',
                       help='不递归处理子目录')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    parser.add_argument('--dry-run', action='store_true',
                       help='干跑模式，只显示将要处理的文件，不实际修改')
    parser.add_argument('--extensions', nargs='+',
                       help='自定义文件扩展名（例如：.c .cpp .h .hpp）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"错误: 目录不存在 {args.directory}")
        sys.exit(1)
    
    if not os.path.isdir(args.directory):
        print(f"错误: {args.directory} 不是目录")
        sys.exit(1)
    
    # 创建清理器实例
    cleaner = DirectoryCommentCleaner(
        backup=not args.no_backup,
        verbose=args.verbose
    )
    
    # 自定义扩展名
    if args.extensions:
        cleaner.remover.supported_extensions = set(args.extensions)
    
    if args.dry_run:
        # 干跑模式：只显示文件列表
        print("干跑模式 - 将要处理的文件:")
        print("-" * 50)
        cpp_files = cleaner.find_cpp_files(args.directory)
        for file_path in cpp_files:
            print(file_path)
        print(f"\n总共找到 {len(cpp_files)} 个文件")
        return
    
    # 实际处理
    print("开始处理C/C++文件注释删除...")
    if not args.no_backup:
        print("注意: 将自动创建 .backup 备份文件")
    else:
        print("警告: 备份功能已禁用，原始文件将被修改！")
    
    stats = cleaner.process_directory(
        args.directory, 
        recursive=not args.no_recursive
    )
    
    cleaner.print_stats()

if __name__ == "__main__":
    main()