import os
from astropy.io import fits

import utils
import paths
import numpy as np

from tqdm import tqdm

def unpack_data(detector):
    path_pattern = os.path.join(detector.output_path, paths.path_packets, '*.fits')

    processed_log = os.path.join(detector.output_path, paths.path_log, paths.log_processed_packets)
    
    unprocessed_files = utils.find_unprocessed_files(path_pattern, processed_log)

    unpacked_output_path = os.path.join(detector.output_path, paths.path_unpacked_data)

    # unprocessed_files = []

    for filename in tqdm(unprocessed_files, desc="Unpacking Packets", leave=False, ncols=100):
        print('Unpacking data from ' + filename + '...')
        # Unpack data from file
        packets_all = {}
        unpacked_data_all_info = {}

        with fits.open(filename) as hdu_list:
            for hdu in hdu_list:
                if hdu.name == 'PRIMARY':
                    continue
                packet_type = hdu.name
                packets = hdu.data['PACKET']
                packets_all[packet_type] = packets

        print("Reading File Complete ...")
        
        for packet_type in packets_all.keys():
            print(packet_type)
            packets = packets_all[packet_type]
            all_len = set()
            for packet in packets:
                all_len.add(len(packet))
            print(all_len)
            unpacked_data_info = detector.unpack_packets(packet_type, packets)
            unpacked_data_all_info[packet_type] = unpacked_data_info
        
        # Save unpacked data to path_unpacked_data
        
        save_filename = detector.short_name + '_unp_' + os.path.basename(filename)[8:]
        save_path = os.path.join(unpacked_output_path, save_filename)
        save_unpacked_data(unpacked_data_all_info, save_path)
        utils.record_processed_file(filename, processed_log)

def save_unpacked_data(unpacked_data_all_info, save_path):
    
        
    hdu_primary = fits.PrimaryHDU()
    all_hdus = [hdu_primary]
    for data_type in unpacked_data_all_info.keys():
        print("saving ", data_type)
        all_columns = []
        for key in unpacked_data_all_info[data_type].keys():
            if key in ['LONG_SPECTRA', 'SHORT_SPECTRA']:
                # print('111')
                column = create_spectrum_column(field_name= key, data_type=data_type, 
                                                    all_info=unpacked_data_all_info)
            else:
                # print('222')
                array_data = unpacked_data_all_info[data_type][key][2]
                array_data = np.array(array_data)
                dtype_map = {'J': np.int32, 'K': np.int64, 'I': np.int32, 'E': np.float32, 'D': np.float64}  # 根据格式映射 dtype
                col_format = unpacked_data_all_info[data_type][key][0]
                dtype_t = dtype_map.get(col_format, np.float64)  # 默认浮点
                
                if len(array_data) == 0:
                    empty_array = np.zeros((0,), dtype=dtype_t)
                else:
                    empty_array = array_data
                column = fits.Column(name=key,
                                    format=col_format,
                                    unit=unpacked_data_all_info[data_type][key][1],
                                    array=empty_array)
            all_columns.append(column)

        if len(all_columns) == 0:
            continue
        print("检查所有列的长度:")
        for i, col in enumerate(all_columns):
            print(f"列 {i}: {col.name}, 长度: {len(col.array)}")

        # 确保所有列长度相同
        lengths = [len(col.array) for col in all_columns]
        if len(set(lengths)) > 1:
            print(f"警告：列长度不一致: {lengths}")

        hdu_unpacked_data = fits.BinTableHDU.from_columns(all_columns, name=data_type)
        all_hdus.append(hdu_unpacked_data)

    print('fits_save_path: ', save_path)
    
    fits.HDUList(all_hdus).writeto(save_path, overwrite=True)



def create_spectrum_column(field_name, all_info, data_type):
    """为光谱数据创建合适的 FITS 列"""
    base_format = all_info[data_type][field_name][0]
    unit = all_info[data_type][field_name][1]
    data = all_info[data_type][field_name][2]

    data = np.array(data)    

    if len(data) == 0:
        # 对于空数据，创建空列（行数为0），避免返回None
        if field_name == 'LONG_SPECTRA':
            n_channels = 82  # 假设通道数，根据你的实际数据调整
            col = fits.Column(
                name=field_name,
                format=f'{n_channels}{base_format}',
                unit=unit,
                array=np.zeros((0, n_channels), dtype=np.int32)  # 空数组，类型根据base_format调整
            )
        elif field_name == 'SHORT_SPECTRA':
            total_elements = 160  # 假设20x8=160，根据你的实际数据调整
            col = fits.Column(
                name=field_name,
                format=f'{total_elements}{base_format}',
                unit=unit,
                array=np.zeros((0, total_elements), dtype=np.int32)  # 空数组
            )
        return col

    if field_name == 'LONG_SPECTRA':
        n_rows, n_channels = data.shape

        col = fits.Column(
            name=field_name,
            format=f'{n_channels}{base_format}',  # 82个元素的数组
            unit=unit,
            array=data,
            dim=f'({n_channels})'
        )
        
    elif field_name == 'SHORT_SPECTRA':
        n_rows, dim1, dim2 = data.shape
        total_elements = dim1 * dim2

        data_reshaped = data.reshape(n_rows, total_elements)
        
        col = fits.Column(
            name=field_name,
            format=f'{total_elements}{base_format}',  # 160个元素的数组 (20×8)
            unit=unit,
            array=data_reshaped,
            dim=f'({dim2}, {dim1})'  # 指定原始维度为 8×20（FITS 中维度顺序相反）
        )
        
    return col