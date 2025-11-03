import os
from frame_parser import parse_frame_single, get_frame_data
from grid10b_lvds_parser_mp import parse_single_app_frame
from grid10b_lvds_parser_mp import summary_app_frame, summary_lvds_frame
from grid10b_lvds_parser_mp import save_app_frame_to_files
from functools import partial
from multiprocessing import Pool
import numpy as np # type: ignore

xml_path = os.path.join(os.getcwd(), 'grid11b_packet.xml')
data_base_path = '/data/GRIDSatFTP/11B'
output_data_base_path = '/lime/GRID/quick_look/GRID-11B'

unpack_log_path = os.path.join('/lime/GRID/quick_look/GRID-11B', 'unpack_log.txt')
if not os.path.exists(unpack_log_path):
        with open(unpack_log_path, 'w') as f:
            print('', file=f)

raw_data_list = []
for root, dirs, files in os.walk(data_base_path):
    for file in files:
        if file.endswith('.dat'):
            raw_data_list.append(os.path.join(root, file))

# read processed files
unpacked_data_list = os.path.join(os.getcwd(), 'UNPACKED_DATA_LIST.txt')
with open(unpacked_data_list, 'r') as f:
    processed_files = f.readlines()
    processed_files = [single_file.strip() for single_file in processed_files]

for data_path in raw_data_list:

    if data_path in processed_files:
        continue

    data_add_path = data_path[len(data_base_path) - 1:]
    output_path = os.path.join(output_data_base_path, os.path.basename(data_path).split('.')[0]+'-splited')

    date = data_add_path[21:25]+' / '+data_add_path[25:27]+' / '+data_add_path[27:29]
    with open(unpack_log_path, 'a') as file:
        print('\n', '= '*50,'\n','$  '*30,'\n','= '*50, file=file)
        print(f'# DATE = {date}', file=file)
        print(f'# DATA_PATH = {data_add_path}', file=file)
        print(f'# OUTPUT_PATH = {output_path}\n', file=file)

    data0, index, et_packet = get_frame_data(file_name=data_path, xml_file=xml_path, data_tag='lvds_packet', 
        endian='MSB', data_stream=None, packet_len=None)

    frame_lvds, frame_lvds_byte = parse_frame_single(data0, et_packet, multi_evt=1, multi_step=1, 
                        endian='MSB', crc_check=True, bcc_check=True, skip_et=[])

    lvds_stream = frame_lvds['data'].flatten()[:(frame_lvds['data_len'][0]-4+1)*(frame_lvds['data_len'].shape[0]-1)+frame_lvds['data_len'][-1]-4+1]

    summary_lvds_frame(frame_lvds, unpack_log_path)

    data_app, index, et_packet = get_frame_data('', xml_path , data_tag='app_packet', data_stream=lvds_stream, packet_len=10, forced_len=8216)

    with Pool() as pool:
        print('POOL BEGIN')
        frames = pool.map(partial(parse_single_app_frame,frame_total=data_app.shape[0], et_packet=et_packet),zip(data_app, np.arange(data_app.shape[0])))
        print('POOL END')
        frame_app = frames[0]
        _temp = np.zeros(data_app.shape[0],dtype=object)
        _temp[0] = frame_app['data']
        frame_app['data'] = _temp
        for i in range(1,len(frames)):
            tmp = frames[i]
            for k in frame_app.keys():
                if k != 'data':
                    frame_app[k] = np.r_[frame_app[k],tmp[k]]
                else:
                    frame_app[k][i] = tmp[k]

    summary_app_frame(frame_app, unpack_log_path)

    save_app_frame_to_files(frame_app, output_path)

    with open(unpacked_data_list, 'a') as processed_list:
        print(data_path, file=processed_list)