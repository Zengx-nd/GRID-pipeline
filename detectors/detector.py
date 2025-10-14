import sys
import numpy as np
from os.path import join

sys.path.append('..')
import paths

class Detector:
    def __init__(self, detector_name: str, short_name: str, source_pattern: str, valid_channels: list[int]):
        self.detector_name = detector_name
        self.short_name = short_name
        self.source_path_pattern = join(
            paths.source_dir,
            short_name,
            source_pattern,
            '*.dat'
        )
        self.output_path = join(
            paths.output_dir,
            # short_name
        )
        self.gagg_channels = valid_channels

    def extract_packets(self, filename: str) -> dict[str, list]:
        """从原始文件提取数据包（需要子类实现）

        Args:
            filename (str): 待处理文件

        Returns:
            dict[str, list]: 分类存放的包和对应时间数据，键为包类型，值为[utcs, timestamps, packets, 包长度(字节)]
        """
        raise NotImplementedError("Subclasses must implement extract_packets method")

    def unpack_packets(self, packet_type, raw_packets):
        """解析数据包（需要子类实现）"""
        raise NotImplementedError("Subclasses must implement unpack_packets method")

    def calibrate_adc(self, adc_value, channel):
        """ADC校准（需要子类实现）"""
        raise NotImplementedError("Subclasses must implement calibrate_adc method")

    def adc_to_energy(self, adc_calibrated, channel):
        """能量转换（需要子类实现）"""
        raise NotImplementedError("Subclasses must implement adc_to_energy method")
