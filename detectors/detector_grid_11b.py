import os, re, struct, json, numpy as np

from .detector import Detector
from .detector_utils import crc16_xmodem_nd, checksum_11b, print_hex_bytes

# from .const_grid_11b import const

class GRID11BDetector(Detector):
    def __init__(self):
        super().__init__(
            detector_name='GRID-11B',
            short_name='11B',
            source_pattern='JL1PT02A03_*',
            valid_channels=[0, 1, 2]
        )
        
        # 预编译正则表达式模式
        self.lvds_pattern = re.compile(b'\xeb\x90\x57\x16.{2040}\x10\xbd\x59\xbf', re.S)

        self.app_header_pattern = re.compile(b'\x47\x52\x49\x44.{14}', re.S)
        self.app_tail_pattern = b'\x37\x37\x33\x77'

        self.housekeeping_pattern = re.compile(b'\x1a\\x2b\x3c\x4d.{183}', re.S)
        self.event_pattern = re.compile(b'\x1c\x1c\x22\x88.{520}\xcc\x11\x88\x22', re.S)
        self.spectra_pattern = re.compile(b'\\x3f\\x3f\x44\xcc.{520}\x33\xff\xcc\x44', re.S)

        self.output_path = r'/srv/gridftp/GRID-11B_temporary_pipeline/output'


    def find_and_unpack_lvds_packets(self, data_lvds: bytes) -> dict:
        """
        解析并检查lvds数据包

        Args:
            data_lvds (bytes): 字节形式的原始数据

        Returns:
            dict: 
                data(bytes): 提取出的数据部分的拼接，期望也为应用层数据包的拼接
                lvds_count(int): 找到的lvds包总数
                errors(dict[str, int]): 各种错误的数量统计
        """
        # 依据帧头帧尾和长度获得所有包
        lvds_packets = re.findall(self.lvds_pattern, data_lvds)
        
        # 输出调试信息
        # print(f'    {len(lvds_packets)} lvds packets found')
        
        # 逐个校验
        datas = []
        checksum_error_count = 0
        len_error_count = 0
        for packet in lvds_packets:
            # 长度检查
            data_len = struct.unpack('>H', packet[4: 6])[0] + 1
            if data_len > 2036 or data_len <= 4:
                # data too short
                len_error_count += 1
                continue

            # 校验和检查
            check_sum = struct.unpack('>H', packet[2042: 2044])[0]
            if check_sum != checksum_11b(packet[4: 2042]):
                # checksum error
                checksum_error_count += 1
                continue

            datas.append(packet[10: 6 + data_len])
        
        # 输出调试信息
        # print('    errors:')
        # print(f'        len: {len_error_count} packets')
        # print(f'        checksum: {checksum_error_count} packets')

        # 拼接有效数据
        data = b''.join(datas)
    
        return data


    def find_and_unpack_app_packets(self, data_app: bytes) -> dict[str, bytes]:
        """拆分出并解析和检查应用层数据包

        Args:
            data_app (bytes): 字节形式的应用层包数据

        Returns:
            dict[str, bytes]: 按照帧类型分开的应用层包字节数据
        """
        apps_packet_count = 0
        checksum_error_count = 0
        len_error_count = 0
        frame_type_error_count = 0

        hk_data = []
        sci_data = []

        for match in self.app_header_pattern.finditer(data_app):
            start_pos = match.start()
            apps_packet_count += 1
            
            # 包长度验证
            data_len = struct.unpack('>I', data_app[start_pos+14: start_pos+18])[0]
            total_len = 24 + data_len
            if data_len > 8192 or (start_pos + total_len) > len(data_app):
                # 长度过长
                len_error_count += 1
                continue

            packet = data_app[start_pos: start_pos + total_len]

            # 包尾验证
            if packet[total_len - 4: total_len] != self.app_tail_pattern:
                len_error_count += 1
                continue

            # 校验
            check_sum = struct.unpack('>H', packet[total_len - 6: total_len - 4])[0]
            if check_sum != checksum_11b(packet[4: total_len - 6]):
                checksum_error_count += 1
                continue
            
            # 判定类别
            frame_type = packet[12]
            packet_data = packet[18: 18 + data_len]
            
            match frame_type:
                case 0x02:
                    # log文件数据，暂不处理
                    pass
                case 0x03:
                    # HK文件数据
                    hk_data.append(packet_data)
                case 0x04:
                    # 科学文件数据
                    sci_data.append(packet_data)
                case 0x05:
                    # IV/VBR，暂不处理
                    pass
                case _:
                    # 未定义类别号
                    frame_type_error_count += 1
                    pass

        # 输出调试信息
        # print(f'    {apps_packet_count} app headers found')
        # print('    errors:')
        # print(f'        len: {len_error_count}')
        # print(f'        checksum: {checksum_error_count}')
        # print(f'        frame type: {frame_type_error_count}')

        hk_data_bytes = b''.join(hk_data)
        sci_data_bytes = b''.join(sci_data)

        data = {
            'hk': hk_data_bytes,
            'sci': sci_data_bytes
        }
        
        return data


    def find_and_classify_tte_frames(self, data_sci: bytes, valid_frame_data):
        """寻找并分类所有 tte 科学数据帧

        Args:
            data_sci (bytes): 字节形式的科学数据

        Returns:
            dict: 键为包类型，值为[utcs, timestamps, packets, 包长度(字节)]，暂时仅处理特征量数据
        """
        # 依据帧头帧尾和长度获得所有包
        event_frames = re.findall(self.event_pattern, data_sci)

        # 输出调试信息
        # print(f'    {len(event_frames)} event frames found')

        # 逐个校验
        event_utcs = []
        event_timestamps = []
        valid_events = []
        checksum_error_count = 0
        time_error_count = 0

        for frame in event_frames:
            # 校验和检查
            check_sum = struct.unpack('>H', frame[522: 524])[0]
            if check_sum != crc16_xmodem_nd(np.frombuffer(frame[0: 522], dtype=np.uint8)):
                # checksum error
                checksum_error_count += 1
                continue
                
            # 检查UTC时间
            utc = struct.unpack('>I', frame[4:8])[0]
            if utc == 0:
                time_error_count += 1
                continue

            timestamp_offset = struct.unpack('>I', frame[28:32])[0]

            valid_events.append(frame)
            event_utcs.append(utc)
            event_timestamps.append(timestamp_offset)

        # 输出调试信息
        # print('    errors:')
        # print(f'        checksum: {checksum_error_count}')
        # print(f'        time: {time_error_count}')

        valid_frame_data['EVENTS'] = [event_utcs, event_timestamps, valid_events, 528]

        return

    def find_and_classify_spec_frames(self, data_sci: bytes, valid_frame_data):
        """寻找并分类所有 spec 能谱模式 科学数据帧

        Args:
            data_sci (bytes): 字节形式的科学数据

        Returns:
            dict: 键为包类型，值为[utcs, timestamps, packets, 包长度(字节)]，暂时仅处理特征量数据
        """
        # 依据帧头帧尾和长度获得所有包
        spectra_frames = re.findall(self.spectra_pattern, data_sci)

        # 输出调试信息
        # print(f'    {len(spectra_frames)} event frames found')

        # 逐个校验
        spec_utcs = []
        spec_timestamps = []
        valid_specs = []
        checksum_error_count = 0
        time_error_count = 0

        for frame in spectra_frames:
            # 校验和检查
            check_sum = struct.unpack('>H', frame[522: 524])[0]
            if check_sum != crc16_xmodem_nd(np.frombuffer(frame[0: 522], dtype=np.uint8)):
                # checksum error
                checksum_error_count += 1
                continue
                
            # 检查UTC时间
            utc = struct.unpack('>I', frame[4:8])[0]
            if utc == 0:
                time_error_count += 1
                continue

            timestamp_offset = struct.unpack('>I', frame[28:32])[0]

            valid_specs.append(frame)
            spec_utcs.append(utc)
            spec_timestamps.append(timestamp_offset)

        # 输出调试信息
        # print('    errors:')
        # print(f'        checksum: {checksum_error_count}')
        # print(f'        time: {time_error_count}')

        valid_frame_data['SPECTRA'] = [spec_utcs, spec_timestamps, valid_specs, 528]

        return

    def find_and_handle_hk_frames(self, data_hk: bytes, valid_frame_data):
        """寻找并处理所有hk数据

        Args:
            data_hk (bytes): 字节形式的 house keeping 数据

        Returns:
            list: 值为[utcs, [], packets, 包长度(字节)]
        """
        # 依据帧头和长度获得所有包
        hk_frames = re.findall(self.housekeeping_pattern, data_hk)


        # 输出调试信息
        # print(f'    {len(hk_frames)} house keeping frames found')

        # 逐个校验
        hk_utcs = []
        valid_hks = []
        time_error_count = 0
        checksum_error_count = 0
        # print('######################################')
        # print('HK file length error Warning!!! :')
        for frame in hk_frames:
            if len(frame) != 187:
                print('% ')

            # CRC-16 校验
            check_sum = struct.unpack('>H', frame[185 : 187])[0]
            if check_sum != crc16_xmodem_nd(np.frombuffer(frame[0: 185], dtype=np.uint8)):
                # checksum error
                checksum_error_count += 1
                continue

            # 检查UTC时间
            utc = struct.unpack('>I', frame[4:8])[0]
            if utc == 0:
                time_error_count += 1
                continue

            valid_hks.append(frame)
            hk_utcs.append(utc)

        # 输出调试信息
        # print('\n    errors:')
        # print(f'        time: {time_error_count}')

        # print('######################################')
        valid_frame_data['HOUSEKEEPING'] = [hk_utcs, [], valid_hks, 187]

        return


    def extract_packets(self, filename: str) -> dict[str, list]:
        """GRID-11B的数据包提取函数

        Args:
            filename (str): 待处理文件

        Returns:
            dict[str, list]: 分类存放的包和对应时间数据，键为包类型，值为[utcs, timestamps, packets, 包长度(字节)]
        """
        with open(filename, 'rb') as f:
            data_lvds = f.read()

        # 输出调试信息
        # print(f'detector file extraction logs:')
        
        # LVDS包解析
        data_app = self.find_and_unpack_lvds_packets(data_lvds)

        # 应用层包解析
        data_frame = self.find_and_unpack_app_packets(data_app)

        valid_frame_data = {}
        # 数据帧查找与处理
        self.find_and_classify_tte_frames(data_frame['sci'], valid_frame_data)
        self.find_and_classify_spec_frames(data_frame['sci'], valid_frame_data)
        self.find_and_handle_hk_frames(data_frame['hk'], valid_frame_data)

        return valid_frame_data
        # valid_frame_data['EVENTS', 'SPECTRA', 'HOUSEKEEPING']


    def unpack_packets(self, packet_type: str, raw_packets) -> dict[str, list]:
        """GRID-11B的包解析
        Args:
            packet_type(): 
            raw_pacets(): 
        
        Returns:
            dict[str, list]: 
        """

        if packet_type == 'EVENTS':
            unpacked = unpack_event_packets(raw_packets)

        elif packet_type == 'SPECTRA':
            unpacked = unpack_spec_packets(raw_packets)

        elif packet_type == 'HOUSEKEEPING': 
            unpacked = unpack_hk_packets(raw_packets)

        return unpacked


    def calibrate_adc(self, adc_value, channel):
        """GRID-11B的ADC校准"""

        
        return np.nan if channel == 3 else float(adc_value)

    def read_ec_coef(self):
        self.ec_low = {}
        self.ec_high = {}
        for channel in range(4):
            filename_channel = '20230903214430_ec_coef_sci_ch' + str(channel) + '.json'
            ec_coef_data_path = os.path.join('03B', filename_channel)
            self.ec_low[channel], self.ec_high[channel] = read_ec_coef(ec_coef_data_path)

        return


    def adc_to_energy(self, adc_calibrated, channel):


        if channel == 3:
            return np.nan

        ec_low = self.ec_low[channel]
        a, b, c = ec_low[0], ec_low[1], ec_low[2]
        energy = a * adc_calibrated**2 + b * adc_calibrated + c       
        if energy <= 50.2:
            return energy
        
        ec_high = self.ec_high[channel]
        a, b, c = ec_high[0], ec_high[1], ec_high[2]
        energy = a * adc_calibrated**2 + b * adc_calibrated + c
        return energy
    
def read_ec_coef(path) -> dict:

    with open(path, 'r') as f:
        json_data = f.read()

    data = json.loads(json_data)

    channel = data['channel']
    ec_low = data['EC_low']
    ec_low_err = data['EC_low_err']
    ec_high = data['EC_high']
    ec_high_err = data['EC_high_err']
    resolution_low = data['resolution_low']
    resolution_low_err = data['resolution_low_err']
    resolution_high = data['resolution_high']
    resolution_high_err = data['resolution_high_err']

    return ec_low, ec_high






def unpack_event_packets(raw_packets) -> dict[str, list]:

    fields = {
        'UTC': [],
        'TIMESTAMP_REF': [],
        'TIMESTAMP_OFFSET': [],
        'CHANNEL': [],
        'ADC_VALUE': []
    }

    print("unpacking events")

    for pkt in raw_packets:
        # 解析包头信息
        utc = struct.unpack('>I', pkt[4:8])[0]
        timestamp_ref = struct.unpack('>Q', pkt[12:20])[0]
        channel = struct.unpack('>H', pkt[20:22])[0]

        # 解析事件体（每个包包含41个事件）
        for i in range(41):
            offset              =   28 + 12*i
            timestamp_offset    =   struct.unpack('>I', pkt[offset:offset+4])[0]
            adc_max             =   struct.unpack('>H', pkt[offset+4:offset+6])[0]
            adc_base            =   round(struct.unpack('>H', pkt[offset+6:offset+8])[0] / 4)
            
            fields['UTC']               .append(utc)
            fields['TIMESTAMP_REF']     .append(timestamp_ref)
            fields['TIMESTAMP_OFFSET']  .append(timestamp_offset)
            fields['CHANNEL']           .append(channel)
            fields['ADC_VALUE']         .append(adc_max - adc_base)

    # 构建返回数据结构
    #  unpacked[key] = [format, unit, data_array]

    unpacked = {
        'UTC': ['J', 's', fields['UTC']],
        'TIMESTAMP_REF': ['K', '', fields['TIMESTAMP_REF']],
        'TIMESTAMP_OFFSET': ['J', '', fields['TIMESTAMP_OFFSET']],
        'CHANNEL': ['I', '', fields['CHANNEL']],
        'ADC_VALUE': ['I', '', fields['ADC_VALUE']]
    }

    return unpacked

def unpack_spec_packets(raw_packets) -> dict[str, list]:
    fields = {
                'UTC': [],
                'TIMESTAMP_REF': [],
                'TIMESTAMP_OFFSET': [],
                'CHANNEL': [],
                'LONG_SPECTRA':[],
                'SHORT_SPECTRA':[]
            }

    print("unpacking spec")

    for pkt in raw_packets:
        # 解析包头信息
        
        utc                 =   struct.unpack('>I', pkt[4:8])[0]
        timestamp_ref       =   struct.unpack('>Q', pkt[12:20])[0]
        timestamp_offset    =   struct.unpack('>Q', pkt[30:38])[0]
        channel             =   struct.unpack('>H', pkt[20:22])[0]
        
        spectrum_long = []
        spectrum_shorts = []
        for i in range(82):
            spectrum_long .append(struct.unpack('>H', pkt[38+2*i:38+2*i+2])[0])
        for i in range(20):
            spectrum_short = []
            for j in range(8):
                spectrum_short .append(struct.unpack('>H', pkt[202+16*i+2*j:202+16*i+2*j+2])[0])
            spectrum_shorts .append(spectrum_short)
        
        fields['UTC']               .append(utc)
        fields['TIMESTAMP_REF']     .append(timestamp_ref)
        fields['TIMESTAMP_OFFSET']  .append(timestamp_offset)
        fields['CHANNEL']           .append(channel)
        fields['LONG_SPECTRA']      .append(spectrum_long)
        fields['SHORT_SPECTRA']     .append(spectrum_shorts)

    # 构建返回数据结构
    unpacked = {
        'UTC': ['J', 's', fields['UTC']],
        'TIMESTAMP_REF': ['K', '', fields['TIMESTAMP_REF']],
        'TIMESTAMP_OFFSET': ['J', '', fields['TIMESTAMP_OFFSET']],
        'CHANNEL': ['I', '', fields['CHANNEL']],

        #  FITS 格式类型 是否会允许每个单元格存储 list 或者 Matrix 
        'LONG_SPECTRA': ['I', '', fields['LONG_SPECTRA']], 
        'SHORT_SPECTRA': ['I', '', fields['SHORT_SPECTRA']]
    }

    return unpacked

def unpack_hk_packets(raw_packets) -> dict[str, list]:

    total_hk_num = len(raw_packets)
    print('hk_num = ', total_hk_num)

    # all_len = set()
    # for packet in raw_packets:
    #     all_len.add(len(packet))
    # if (len(all_len)>1):
    #     print('#'*300)
    # print(all_len)

    utc = []

    sipm_temp0 = []
    sipm_temp1 = []
    sipm_temp2 = []
    sipm_temp3 = []
    vmon0 =      []
    vmon1 =      []
    vmon2 =      []
    vmon3 =      []
    imon0 =      []
    imon1 =      []
    imon2 =      []
    imon3 =      []

    strTrack_1_q1 = []
    strTrack_1_q2 = []
    strTrack_1_q3 = []
    strTrack_1_q4 = []
    strTrack_2_q1 = []
    strTrack_2_q2 = []
    strTrack_2_q3 = []
    strTrack_2_q4 = []

    Longitude = []
    Latitude = []

    for package in raw_packets:

        # print(len(package))
        
        t = struct.unpack('>I', package[4 : 8])[0]
        utc.        append(t)

        t = struct.unpack('>H', package[86  :  88])[0]
        sipm_temp0. append(t if t < (1<<15) else -((1 << 16) - t + 1))
        t = struct.unpack('>H', package[92  :  94])[0]
        sipm_temp1. append(t if t < (1<<15) else -((1 << 16) - t + 1))
        t = struct.unpack('>H', package[98  : 100])[0]
        sipm_temp2. append(t if t < (1<<15) else -((1 << 16) - t + 1))
        t = struct.unpack('>H', package[104 : 106])[0]
        sipm_temp3. append(t if t < (1<<15) else -((1 << 16) - t + 1))
        
        vmon0.  append(struct.unpack('>H', package[82  :  84])[0])
        vmon1.  append(struct.unpack('>H', package[88  :  90])[0])
        vmon2.  append(struct.unpack('>H', package[94  :  96])[0])
        vmon3.  append(struct.unpack('>H', package[100 : 102])[0])
        
        imon0.  append(struct.unpack('>H', package[84  :  86])[0])
        imon1.  append(struct.unpack('>H', package[90  :  92])[0])
        imon2.  append(struct.unpack('>H', package[96  :  98])[0])
        imon3.  append(struct.unpack('>H', package[102 : 104])[0])

        strTrack_1_q1.  append(struct.unpack('>I', package[142 : 146])[0])
        strTrack_1_q2.  append(struct.unpack('>I', package[146 : 150])[0])
        strTrack_1_q3.  append(struct.unpack('>I', package[150 : 154])[0])
        strTrack_1_q4.  append(struct.unpack('>I', package[154 : 158])[0])

        strTrack_2_q1.  append(struct.unpack('>I', package[165 : 169])[0])
        strTrack_2_q2.  append(struct.unpack('>I', package[169 : 173])[0])
        strTrack_2_q3.  append(struct.unpack('>I', package[173 : 177])[0])
        strTrack_2_q4.  append(struct.unpack('>I', package[177 : 181])[0])

        Longitude.  append(struct.unpack('>H', package[181 : 183])[0])
        Latitude.   append(struct.unpack('>H', package[183 : 185])[0])

    # 构建返回数据结构
    unpacked = {
        'UTC': ['J', 's', utc],

        # 数字量 / 100 得到 开氏温度， 减去 273.15 得到 摄氏度
        'SIPM_TEMP0': ['I', '0.01K', sipm_temp0],
        'SIPM_TEMP1': ['I', '0.01K', sipm_temp1],
        'SIPM_TEMP2': ['I', '0.01K', sipm_temp2],
        'SIPM_TEMP3': ['I', '0.01K', sipm_temp3],
        'VMON0': ['I', 'mV', vmon0],
        'VMON1': ['I', 'mV', vmon1],
        'VMON2': ['I', 'mV', vmon2],
        'VMON3': ['I', 'mV', vmon3],
        'IMON0': ['I', 'uA', imon0],
        'IMON1': ['I', 'uA', imon1],
        'IMON2': ['I', 'uA', imon2],
        'IMON3': ['I', 'uA', imon3],
        
        # 星敏-1 与 星敏-2 [q1, q2, q3] 为矢量 q4 为标量  当量为 1/2147483647
        'SCTR_1_Q1': ['J', '', strTrack_1_q1], 
        'SCTR_1_Q2': ['J', '', strTrack_1_q2],
        'SCTR_1_Q3': ['J', '', strTrack_1_q3],
        'SCTR_1_Q4': ['J', '', strTrack_1_q4],
        'SCTR_2_Q1': ['J', '', strTrack_2_q1],
        'SCTR_2_Q2': ['J', '', strTrack_2_q2],
        'SCTR_2_Q3': ['J', '', strTrack_2_q3],
        'SCTR_2_Q4': ['J', '', strTrack_2_q4],

        # 星下点经度 与 星下点纬度   单位：度  权重：0.01/bit 
        'LONGITUDE': ['I', 'degree', strTrack_1_q1],
        'LATITUDE': ['I', 'degree', strTrack_1_q1]
    }

    return unpacked



def correct_temperature(utc, temp, q_err):
    '''
    Correct abnormal temperature data
    修正异常的温度数据

    Parameters
    ---------- 
    utc : array_like
        time data
        时间数据

    temp : array_like
        temperature data
        温度数据
        
    q_err : float
        quadratuer error of temperature data
        温度数据的量化误差

    Returns
    -------
    temp_n : array_like
        temperature data after correcting abnormal data
        修正异常值后的温度数据

    '''
    temp_n = np.copy(temp)
    wrong_flag = np.zeros_like(temp, dtype=int)
    # find abnormal data
    for i in range(len(temp)):
        # find 8 nearest points within 30 seconds
        near_ind_all = np.array([], dtype=int)
        near_utc_delta_all = np.array([], dtype=float)
        for j in range(1, 9):
            if i - j >= 0:
                d_utc = np.abs(utc[i - j] - utc[i])
                if d_utc <= 30:
                    near_ind_all = np.append(near_ind_all, i - j)
                    near_utc_delta_all = np.append(near_utc_delta_all, d_utc)
            if i + j < len(temp):
                d_utc = np.abs(utc[i + j] - utc[i])
                if d_utc <= 30:
                    near_ind_all = np.append(near_ind_all, i + j)
                    near_utc_delta_all = np.append(near_utc_delta_all, d_utc)
        sort_ind = np.argsort(near_utc_delta_all)
        num = np.min([8, len(near_ind_all)])
        near_ind = near_ind_all[sort_ind][0:num]
        near_utc_delta = near_utc_delta_all[sort_ind][0:num]

        # check whether this temperature point is correct
        wrong_cnt = 0
        for j in range(num):
            if np.abs(temp[i] - temp[near_ind[j]]) > near_utc_delta[j] * 0.1 + q_err:
                wrong_cnt += 1
        if wrong_cnt >= num / 3.:
            wrong_flag[i] = 1
    
    # correct abnormal data
    for i in range(len(temp)):
        if wrong_flag[i]:
            last_corr_ind = -1
            next_corr_ind = -1

            # find two nearest correct data within 30 seconds
            j = 1
            while i - j >= 0:
                if np.abs(utc[i - j] - utc[i]) > 30:
                    break
                if not wrong_flag[i - j]:
                    last_corr_ind = i - j
                    break
                j += 1
            j = 1
            while i + j < len(temp):
                if np.abs(utc[i + j] - utc[i]) > 30:
                    break
                if not wrong_flag[i + j]:
                    next_corr_ind = i + j
                    break
                j += 1
            if last_corr_ind >= 0 and next_corr_ind >= 0:
                if np.abs(temp[next_corr_ind] - temp[last_corr_ind]) <= \
                   np.abs(utc[next_corr_ind] - utc[last_corr_ind]) * 0.1 + q_err:
                    temp_n[i] = np.interp(utc[i], [utc[last_corr_ind], utc[next_corr_ind]], 
                                                [temp[last_corr_ind], temp[next_corr_ind]])
                elif np.abs(utc[last_corr_ind] - utc[i]) <= np.abs(utc[next_corr_ind] - utc[i]): 
                    temp_n[i] = temp[last_corr_ind]
                else:
                    temp_n[i] = temp[next_corr_ind]
            elif last_corr_ind >= 0:
                temp_n[i] = temp[last_corr_ind]
            elif next_corr_ind >= 0:
                temp_n[i] = temp[next_corr_ind]
    return temp_n




class Adc_mapping:
    def __init__(self, const):
        '''
        Initialization ``Adc_mapping`` instance
        初始化 ``Adc_mapping`` 实例

        Parameters
        ----------
        const : dict
            gallery defined constants such as file path
            gallery 文件定义的文件路径等常数

        '''
        self.tempbias_coef, self.ec_coef, self.ab_coef, self.corr_coef = self.readcali(const)
        return
    
    def ecmap(self, i, adcv):
        '''
        ADC value - energy convention based on temperature-voltagebias correction
        在温度 - 偏压修正后，进行 ADC 值 - 能量转换

        Parameters
        ----------
        i : int
            channel number
            通道号

        adcv : float
            corrected ADC value
            已经过修正的 ADC 值

        temp : float
            measured temperature
            实测温度

        bias : float
            measured voltage bias
            实测偏压

        Returns
        -------
        E : float
            energy
            能量

        '''
        if adcv < self.ab_coef[i]:
            E = self.ec_coef[i]['EC_low'][0] * adcv ** 2 + self.ec_coef[i]['EC_low'][1] * adcv \
                + self.ec_coef[i]['EC_low'][2]  # derive energy using low quadratic function
        else:
            E = self.ec_coef[i]['EC_high'][0] * adcv ** 2 + self.ec_coef[i]['EC_high'][1] * adcv \
                + self.ec_coef[i]['EC_high'][2]  # derive energy using high quadratic function
        return E

    def adcmap(self, channel, adcv, temp, bias):
        '''
        temperature-voltagebias correction of ADC value
        对 ADC 值进行温度 - 偏压修正

        Parameters
        ----------
        channel : int
            channel number
            通道号

        adcv : int
            uncorrected ADC value
            未经修正的 ADC 值

        temp : float
            measured temperature
            实测温度

        bias : float
            measured voltage bias
            实测偏压

        Returns
        -------
        adcv : float
            corrected ADC value
            修正过的 ADC 值

        '''
        p = self.tempbias_coef[channel]  # Read temperature-voltagebias correction coefficients
        adcv_t = tempbiasfunc(np.array([[temp, bias]]), p['G0'], p['k'], p['V0'], p['b'], p['c']).item()
        adcv_s = tempbiasfunc(np.array([[25., 28.5]]), p['G0'], p['k'], p['V0'], p['b'], p['c']).item()
        adcv = (adcv / adcv_t * adcv_s) * self.corr_coef[channel][0] + self.corr_coef[channel][1]
        return adcv

    def readcali(self, const):
        '''
        Read calibration ``.json`` files
        读取标定数据 ``.json`` 文件

        Parameters
        ----------
        const : dict
            gallery defined constants such as file path
            gallery 文件定义的文件路径等常数

        Returns
        -------
        tempbiascoef : dict
            coefficients of temperature-voltagebias correction
            温度 - 偏压修正参数
        
        eccoef : dict
            channel-energy convention functions & coefficients
            ADC 值 - 能量转化函数和参数

        '''
        ec_coef = []
        for i in range(4):
            ec_coef.append(json.load(open(const['ec_coef'][i], 'r')))  # load new coefficient of channel-energy convention
        tempbias_coef = json.load(open(const['tempbias'], 'r'))  # load temperature-voltagebias correction of ADC value
        ab_coef = np.load(const['absorption_edges'])
        corr_coef = const['corr_coef']
        return tempbias_coef, ec_coef, ab_coef, corr_coef


def tempbiasfunc(input_array, G0, k, V0, b, c):
    '''
    temperature-bias correction function
    温度偏压校正函数

    Parameters
    ----------
    input : array_like
        array of ``(T, V)``
        ``(T, V)`` 序列

    G0, k, V0, b, c : sequence of float
        5 coefficient
        各项参数，共 5 个

    Returns
    -------
    z : array_like
        result
        计算结果

    '''
    xdata = input_array[:, 0]
    ydata = input_array[:, 1]

    Vov = ydata - k * xdata - V0
    z = G0 * Vov ** 2 * (-xdata ** 2 + b * xdata + c)
    return z


def read_temp_bias(path) -> dict:

    with open(path, 'r') as f:
        json_data = f.read()

    data = json.loads(json_data)

    channel = data['channel']
    ec_low = data['EC_low']
    ec_low_err = data['EC_low_err']
    ec_high = data['EC_high']
    ec_high_err = data['EC_high_err']
    resolution_low = data['resolution_low']
    resolution_low_err = data['resolution_low_err']
    resolution_high = data['resolution_high']
    resolution_high_err = data['resolution_high_err']

    return ec_low, ec_high