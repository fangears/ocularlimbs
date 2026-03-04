"""
智能图片清理模块
自动删除无用、重复、无效的图片
"""

import os
import hashlib
import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from PIL import Image
import io


class CleanReason(Enum):
    """清理原因"""
    DUPLICATE = "duplicate"           # 重复图片
    CORRUPTED = "corrupted"           # 损坏图片
    TOO_SMALL = "too_small"           # 太小
    ALL_SAME = "all_same"            # 全屏同色（黑屏等）
    BLURRY = "blurry"                # 模糊
    EXPIRED = "expired"              # 过期
    SIMILAR = "similar"              # 相似图片
    LOW_QUALITY = "low_quality"      # 低质量


@dataclass
class CleanupResult:
    """清理结果"""
    total_files: int
    checked_files: int
    deleted_files: int
    saved_space: int  # bytes
    details: List[Dict]
    duration: float  # seconds


class ImageCleaner:
    """图片清理器"""

    def __init__(
        self,
        min_size: Tuple[int, int] = (100, 100),
        min_file_size: int = 1024,  # 1KB
        duplicate_threshold: float = 0.95,  # 相似度阈值
        enable_duplicate_check: bool = True,
        enable_quality_check: bool = True,
        dry_run: bool = False  # 是否只模拟不删除
    ):
        self.min_size = min_size
        self.min_file_size = min_file_size
        self.duplicate_threshold = duplicate_threshold
        self.enable_duplicate_check = enable_duplicate_check
        self.enable_quality_check = enable_quality_check
        self.dry_run = dry_run

        self.stats = {
            'checked': 0,
            'deleted': 0,
            'saved_space': 0
        }

    def clean_directory(
        self,
        directory: str,
        recursive: bool = True,
        max_age_days: Optional[int] = None,
        keep_latest: int = 5
    ) -> CleanupResult:
        """
        清理目录中的图片

        Args:
            directory: 目录路径
            recursive: 是否递归处理子目录
            max_age_days: 最大保留天数（None = 不限制）
            keep_latest: 每个类别保留最新的N个文件

        Returns:
            清理结果
        """
        start_time = time.time()
        details = []

        # 1. 扫描所有图片文件
        image_files = self._scan_images(directory, recursive)
        total_files = len(image_files)

        print(f"扫描到 {total_files} 个图片文件")

        # 2. 检查每个文件
        checked_files = 0
        deleted_files = 0
        saved_space = 0

        for filepath in image_files:
            try:
                checked_files += 1
                result = self._check_and_clean(filepath, max_age_days)

                if result['should_delete']:
                    deleted_files += 1
                    saved_space += result['file_size']
                    details.append(result)

                    if not self.dry_run:
                        os.remove(filepath)
                        print(f"  [删除] {os.path.basename(filepath)} - {result['reason']}")
                    else:
                        print(f"  [模拟] {os.path.basename(filepath)} - {result['reason']}")

            except Exception as e:
                print(f"  [错误] {filepath}: {e}")

        # 3. 检查重复图片
        if self.enable_duplicate_check:
            duplicates = self._find_duplicates(image_files)
            for filepath, reason in duplicates:
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    deleted_files += 1
                    saved_space += file_size

                    if not self.dry_run:
                        os.remove(filepath)
                    details.append({
                        'file': filepath,
                        'reason': reason,
                        'file_size': file_size
                    })

        duration = time.time() - start_time

        return CleanupResult(
            total_files=total_files,
            checked_files=checked_files,
            deleted_files=deleted_files,
            saved_space=saved_space,
            details=details,
            duration=duration
        )

    def _scan_images(self, directory: str, recursive: bool) -> List[str]:
        """扫描目录中的图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        image_files = []

        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in image_extensions:
                        image_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                if os.path.isfile(filepath):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in image_extensions:
                        image_files.append(filepath)

        return sorted(image_files)

    def _check_and_clean(
        self,
        filepath: str,
        max_age_days: Optional[int]
    ) -> Dict:
        """
        检查单个文件是否应该删除

        Returns:
            包含 should_delete, reason, file_size 的字典
        """
        result = {
            'file': filepath,
            'should_delete': False,
            'reason': '',
            'file_size': 0
        }

        try:
            # 获取文件信息
            file_size = os.path.getsize(filepath)
            result['file_size'] = file_size

            # 检查文件大小
            if file_size < self.min_file_size:
                result['should_delete'] = True
                result['reason'] = f"文件太小 ({file_size} bytes)"
                return result

            # 检查文件年龄
            if max_age_days:
                file_age = time.time() - os.path.getmtime(filepath)
                if file_age > max_age_days * 86400:
                    result['should_delete'] = True
                    result['reason'] = f"文件过期 ({file_age/86400:.1f} 天)"
                    return result

            # 检查图片质量
            if self.enable_quality_check:
                quality_result = self._check_image_quality(filepath)
                if quality_result['should_delete']:
                    result['should_delete'] = True
                    result['reason'] = quality_result['reason']
                    return result

        except Exception as e:
            result['should_delete'] = True
            result['reason'] = f"文件损坏或无法读取: {str(e)[:50]}"

        return result

    def _check_image_quality(self, filepath: str) -> Dict:
        """检查图片质量"""
        result = {
            'should_delete': False,
            'reason': ''
        }

        try:
            with Image.open(filepath) as img:
                # 检查尺寸
                width, height = img.size
                if width < self.min_size[0] or height < self.min_size[1]:
                    result['should_delete'] = True
                    result['reason'] = f"尺寸太小 ({width}x{height})"
                    return result

                # 检查是否全屏同色（黑屏、白屏等）
                if self._is_monochrome_image(img):
                    result['should_delete'] = True
                    result['reason'] = "全屏同色（可能是黑屏）"
                    return result

                # 检查是否模糊（拉普拉斯方差）
                if self._is_blurry(img):
                    result['should_delete'] = True
                    result['reason'] = "图片模糊"
                    return result

        except Exception as e:
            result['should_delete'] = True
            result['reason'] = f"无法加载图片: {str(e)[:50]}"

        return result

    def _is_monochrome_image(self, img: Image, threshold: float = 0.95) -> bool:
        """检查是否是单色图片（黑屏等）"""
        try:
            # 缩小图片加快检测
            small = img.resize((100, 100)) if img.size[0] > 100 else img

            # 转换为 numpy
            import numpy as np
            arr = np.array(small)

            # 计算标准差
            if len(arr.shape) == 3:
                std = np.std(arr)
            else:
                std = np.std(arr)

            # 标准差很小表示颜色单一
            return std < 10  # 阈值可调

        except Exception:
            return False

    def _is_blurry(self, img: Image, threshold: float = 50.0) -> bool:
        """检查图片是否模糊"""
        try:
            import cv2
            import numpy as np

            # 转换为 OpenCV 格式
            if img.mode != 'L':
                img = img.convert('L')

            arr = np.array(img)

            # 计算拉普拉斯方差
            laplacian_var = cv2.Laplacian(arr, cv2.CV_64F).var()

            return laplacian_var < threshold

        except Exception:
            # 如果 OpenCV 不可用，使用简单方法
            return False

    def _find_duplicates(
        self,
        image_files: List[str]
    ) -> List[Tuple[str, str]]:
        """查找重复图片"""
        duplicates = []
        seen_hashes = {}

        for filepath in image_files:
            if not os.path.exists(filepath):
                continue

            try:
                # 计算文件哈希
                file_hash = self._calculate_hash(filepath)

                if file_hash in seen_hashes:
                    # 发现重复
                    original = seen_hashes[file_hash]
                    duplicates.append((
                        filepath,
                        f"重复文件 (原文件: {os.path.basename(original)})"
                    ))
                else:
                    seen_hashes[file_hash] = filepath

            except Exception:
                continue

        return duplicates

    def _calculate_hash(self, filepath: str) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def find_similar_images(
        self,
        directory: str,
        threshold: float = 0.90
    ) -> List[Tuple[str, str, float]]:
        """
        查找相似图片（基于感知哈希）

        Returns:
            [(文件1, 文件2, 相似度), ...]
        """
        try:
            from imagehash import phash
        except ImportError:
            print("警告: imagehash 未安装，相似度检测不可用")
            print("安装: pip install imagehash")
            return []

        similar_pairs = []
        image_files = self._scan_images(directory, recursive=True)

        # 计算所有图片的感知哈希
        hash_dict = {}
        for filepath in image_files:
            try:
                with Image.open(filepath) as img:
                    img_hash = phash(img)
                    hash_dict[filepath] = img_hash
            except Exception:
                continue

        # 比较所有图片对
        files = list(hash_dict.keys())
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                file1, file2 = files[i], files[j]
                hash1, hash2 = hash_dict[file1], hash_dict[file2]

                # 计算相似度（哈希距离越小越相似）
                distance = hash1 - hash2
                similarity = 1 - (distance / 64.0)  # 归一化到 0-1

                if similarity >= threshold:
                    similar_pairs.append((file1, file2, similarity))

        return sorted(similar_pairs, key=lambda x: -x[2])


class AutoCleaner:
    """自动清理器 - 定时清理"""

    def __init__(
        self,
        directories: List[str],
        interval_minutes: int = 60,
        **cleaner_kwargs
    ):
        self.directories = directories
        self.interval = interval_minutes * 60
        self.cleaner = ImageCleaner(**cleaner_kwargs)
        self.running = False

    def start(self):
        """启动自动清理"""
        import threading

        self.running = True

        def clean_loop():
            while self.running:
                try:
                    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始自动清理...")

                    for directory in self.directories:
                        if not os.path.exists(directory):
                            continue

                        print(f"清理目录: {directory}")
                        result = self.cleaner.clean_directory(
                            directory,
                            recursive=True,
                            max_age_days=7  # 默认保留7天
                        )

                        print(f"  检查: {result.checked_files} 个")
                        print(f"  删除: {result.deleted_files} 个")
                        print(f"  节省: {result.saved_space / 1024:.1f} KB")

                except Exception as e:
                    print(f"清理出错: {e}")

                # 等待下一次清理
                for _ in range(int(self.interval / 10)):
                    if not self.running:
                        break
                    time.sleep(10)

        thread = threading.Thread(target=clean_loop, daemon=True)
        thread.start()

        print(f"自动清理已启动，间隔: {self.interval // 60} 分钟")

    def stop(self):
        """停止自动清理"""
        self.running = False
        print("自动清理已停止")


# ============================================================================
# 便捷函数
# ============================================================================

def quick_clean(
    directory: str,
    dry_run: bool = True,
    max_age_days: int = 7
) -> CleanupResult:
    """
    快速清理

    Args:
        directory: 目录路径
        dry_run: 是否模拟运行（不真正删除）
        max_age_days: 最大保留天数

    Returns:
        清理结果
    """
    cleaner = ImageCleaner(dry_run=dry_run)

    print("="*70)
    print(f"{'模拟清理' if dry_run else '开始清理'}: {directory}")
    print(f"最大保留: {max_age_days} 天")
    print("="*70)

    result = cleaner.clean_directory(
        directory,
        recursive=True,
        max_age_days=max_age_days
    )

    # 打印结果
    print(f"\n清理完成:")
    print(f"  扫描文件: {result.total_files}")
    print(f"  检查文件: {result.checked_files}")
    print(f"  删除文件: {result.deleted_files}")
    print(f"  节省空间: {result.saved_space / 1024:.1f} KB")
    print(f"  耗时: {result.duration:.2f} 秒")

    if dry_run and result.deleted_files > 0:
        print(f"\n⚠️  这是模拟运行，没有真正删除文件")
        print(f"    再次运行时设置 dry_run=False 来真正删除")

    return result


def find_duplicates(directory: str) -> List[Tuple[str, str]]:
    """查找重复图片"""
    cleaner = ImageCleaner()
    image_files = cleaner._scan_images(directory, recursive=True)
    return cleaner._find_duplicates(image_files)
