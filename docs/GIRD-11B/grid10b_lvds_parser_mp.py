import numpy as np
import zlib
import os
from frame_parser import parse_frame_data, parse_frame_single, get_frame_data
# from sda.tools.sda_tools import number_list_to_interval_str
from functools import partial
from multiprocessing import Pool

DEV_ID = {'DAQ_main': 0x1121, 
          'AI':       0x112b,
          'DAQ_bak':  0x111d,
          'GRID':     0x1131,
          }
FRAEM_TYPE = {'REAL': 0x1,
              'LOG':  0x2,
              'HK':   0x3,
              'SCI':  0x4,
              'IV':   0x5,
              }
DEV_TYPE = {'DAQ_main': 0x0,
            # 'AI':  0x1,
            }
COMPRESS_FLAG = {'UNCOMPRESS': 0x0,
                 'COMPRESSED': 0x1
                }

def parse_single_app_frame(data_app_tp,frame_total,et_packet):
    data_app = data_app_tp[0]
    frame_id = data_app_tp[1]
    frame_app,_ = parse_frame_single(np.atleast_2d(data_app),et_packet,1,1)
    frame_app['dev_type'] = np.atleast_1d((frame_app['frame_type'][0]>>6) & 0x1)
    frame_app['compress_flag'] = np.atleast_1d((frame_app['frame_type'][0]>>7) & 0x1)
    frame_app['frame_type'] = np.atleast_1d(frame_app['frame_type'][0] & 0xf)
    if frame_app['compress_flag']:
        try:
            decomp_data = zlib.decompress(frame_app['data'][:frame_app['data_len'][0]].tobytes())
        except:
            decomp_data = np.zeros(8192,dtype=np.uint8)
            print('\033[1;31;43mWarning: zlib decompress error at frame %d (%d)\033[0m' % (frame_id,frame_total))

        frame_app['data'] = np.frombuffer(decomp_data,dtype=np.uint8)
        frame_app['decompress_len'] = np.atleast_1d(len(decomp_data))
    else:
        frame_app['decompress_len'] = np.atleast_1d(frame_app['data_len'][0])
    return frame_app

def parse_grid10b_lvds_frame(file_name, xml_file, data_tag='lvds_packet', endian='MSB', data_stream=None):
    print('========> start to parse lvds frame')
    frame_lvds, index = parse_frame_data(file_name, xml_file, data_tag, endian=endian, data=data_stream)
    print('>> Get APP Stream')
    lvds_stream = frame_lvds['data'].flatten()[:(frame_lvds['data_len'][0]-4+1)*(frame_lvds['data_len'].shape[0]-1)+frame_lvds['data_len'][-1]-4+1]
    print('<< Get APP Stream')
    # frame_lvds.pop('data')
    summary_lvds_frame(frame_lvds)

    print('========> start to parse app frame')
    data_app, index, et_packet = get_frame_data('',xml_file,data_tag='app_packet',data_stream=lvds_stream, packet_len=10, forced_len=8216)
    print('P O O L -- B E G I N')
    with Pool() as pool:
        frames = pool.map(partial(parse_single_app_frame,frame_total=data_app.shape[0],et_packet=et_packet),zip(data_app,np.arange(data_app.shape[0])))
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
    # frame_app,_ = parse_frame_single(np.atleast_2d(data_app[0]),et_packet,1,1)
    # frame_app['dev_type'] = np.atleast_1d((frame_app['frame_type'][0]>>6) & 0x1)
    # frame_app['compress_flag'] = np.atleast_1d((frame_app['frame_type'][0]>>7) & 0x1)
    # frame_app['frame_type'] = np.atleast_1d(frame_app['frame_type'][0] & 0xf)
    # if frame_app['compress_flag']:
    #     decomp_data = zlib.decompress(frame_app['data'][:frame_app['data_len'][0]].tobytes())
    #     frame_app['data'] = np.frombuffer(decomp_data,dtype=np.uint8)
    #     frame_app['decompress_len'] = np.atleast_1d(len(decomp_data))
    # else:
    #     frame_app['decompress_len'] = np.atleast_1d(frame_app['data_len'][0])
    # _temp = np.zeros(data_app.shape[0],dtype=object)
    # _temp[0] = frame_app['data']
    # frame_app['data'] = _temp
    # for i in range(1,data_app.shape[0]):
    #     tmp,_ = parse_frame_single(np.atleast_2d(data_app[i]),et_packet,1,1)
    #     tmp['dev_type'] = np.atleast_1d((tmp['frame_type'][0]>>6) & 0x1)
    #     tmp['compress_flag'] = np.atleast_1d((tmp['frame_type'][0]>>7) & 0x1)
    #     tmp['frame_type'] = np.atleast_1d(tmp['frame_type'][0] & 0xf)
    #     if tmp['compress_flag']:
    #         try:
    #             decomp_data = zlib.decompress(tmp['data'][:tmp['data_len'][0]].tobytes())
    #         except:
    #             decomp_data = np.zeros(8192,dtype=np.uint8)
    #             print('\033[1;31;43mWarning: zlib decompress error at frame %d (%d)\033[0m' % (i,data_app.shape[0]))
    #         tmp['data'] = np.frombuffer(decomp_data,dtype=np.uint8)
    #         tmp['decompress_len'] = np.atleast_1d(len(decomp_data))
    #     else:
    #         tmp['decompress_len'] = np.atleast_1d(tmp['data_len'][0])
    #     for k in frame_app.keys():
    #         if k != 'data':
    #             frame_app[k] = np.r_[frame_app[k],tmp[k]]
    #         else:
    #             frame_app[k][i] = tmp[k]
    print('P O O L -- E N D')
    summary_app_frame(frame_app)
    return (frame_app, frame_lvds)

def save_app_frame_to_files(frame_app, save_path):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file_flags = np.vstack((frame_app['file_num'],frame_app['frame_type'],frame_app['dev_type']))
    file_index = np.unique(file_flags,axis=1,return_index=True)[1]
    for i,j in zip(np.sort(file_index),np.arange(file_index.shape[0])):
        file_num = frame_app['file_num'][i]
        frame_type = frame_app['frame_type'][i]
        dev_type = frame_app['dev_type'][i]

        if frame_type == FRAEM_TYPE['LOG'] and dev_type == DEV_TYPE['DAQ_main']:
            file_name = '{:03d}_log_{:03d}.txt'.format(j,file_num)
        elif frame_type == FRAEM_TYPE['HK'] and dev_type == DEV_TYPE['DAQ_main']:
            file_name = '{:03d}_hk_{:03d}.dat'.format(j,file_num)
        elif frame_type == FRAEM_TYPE['SCI'] and dev_type == DEV_TYPE['DAQ_main']:
            file_name = '{:03d}_sci_{:03d}.raw'.format(j,file_num)
        elif frame_type == FRAEM_TYPE['REAL'] and dev_type == DEV_TYPE['DAQ_main']:
            file_name = '{:03d}_real_{:03d}.raw'.format(j,file_num)
        elif frame_type == FRAEM_TYPE['IV'] and dev_type == DEV_TYPE['DAQ_main']:
            file_name = '{:03d}_iv_{:03d}.raw'.format(j,file_num)
        # elif dev_type == DEV_TYPE['AI']:
        #     file_name = 'ai_{:03d}.bin'.format(file_num)
        else:
            file_name = '{:03d}_unknown_{:03d}.bin'.format(j,file_num)
        file_path = os.path.join(save_path,file_name)
        unique_index = np.sort(np.unique(frame_app['frame_id'][(frame_app['file_num'] == file_num) & (frame_app['frame_type'] == frame_type) & (frame_app['dev_type'] == dev_type)], return_index=True)[1])
        data_sel = frame_app['data'][(frame_app['file_num'] == file_num) & (frame_app['frame_type'] == frame_type) & (frame_app['dev_type'] == dev_type) & (frame_app['sum_check'])]#[unique_index] # can not drop duplicate frame like this when multi-switch real-mode in grid-10b
        # data_sel = frame_app['data'][(frame_app['file_num'] == file_num) & (frame_app['frame_type'] == frame_type) & (frame_app['dev_type'] == dev_type)]#[unique_index] # can not drop duplicate frame like this when multi-switch real-mode in grid-10b
        data = np.concatenate(data_sel)
        data.tofile(file_path)
    return file_index

def summary_app_frame(app_frame, log_path):
    frame_num_total = app_frame['header'].shape[0]
    # sum_check_num = np.count_nonzero(app_frame['sum_check'])
    invalid_frame_index = np.nonzero(app_frame['sum_check']==0)[0]
    file = open(log_path, 'a')
    print('------------summary of app frame------------', file=file)
    print('total frame number: %d' % frame_num_total, file=file)
    # print('valid frame number: %d' % sum_check_num, file=file)
    print('invalid frame index: %s' % ', '.join(map(str,invalid_frame_index)), file=file)

    error_head_cnt = np.count_nonzero(app_frame['header'] != 0x47524944)
    error_tail_cnt = np.count_nonzero(app_frame['tail'] != 0x37373377)
    if(error_head_cnt):
        print('error head cnt: %d' % error_head_cnt, file=file)
    if(error_tail_cnt):
        print('error tail cnt: %d' % error_tail_cnt, file=file)
    print('')

    daq_main_frame_cnt = np.count_nonzero(app_frame['dev_type'] == DEV_TYPE['DAQ_main'])
    daq_real_frame_cnt = np.count_nonzero((app_frame['frame_type'] == FRAEM_TYPE['REAL']) & (app_frame['dev_type'] == DEV_TYPE['DAQ_main']))
    daq_log_frame_cnt = np.count_nonzero((app_frame['frame_type'] == FRAEM_TYPE['LOG']) & (app_frame['dev_type'] == DEV_TYPE['DAQ_main']))
    daq_hk_frame_cnt = np.count_nonzero((app_frame['frame_type'] == FRAEM_TYPE['HK']) & (app_frame['dev_type'] == DEV_TYPE['DAQ_main']))
    daq_sci_frame_cnt = np.count_nonzero((app_frame['frame_type'] == FRAEM_TYPE['SCI']) & (app_frame['dev_type'] == DEV_TYPE['DAQ_main']))
    daq_iv_frame_cnt = np.count_nonzero((app_frame['frame_type'] == FRAEM_TYPE['IV']) & (app_frame['dev_type'] == DEV_TYPE['DAQ_main']))
    # ai_frame_cnt = np.count_nonzero(app_frame['dev_type'] == DEV_TYPE['AI'])
    print('daq_main frame cnt: %d' % daq_main_frame_cnt, file=file)
    print('    daq_real frame cnt: %d' % daq_real_frame_cnt, file=file)
    print('    daq_log frame cnt: %d' % daq_log_frame_cnt, file=file)
    print('    daq_hk frame cnt: %d' % daq_hk_frame_cnt, file=file)
    print('    daq_sci frame cnt: %d' % daq_sci_frame_cnt, file=file)
    print('    daq_iv frame cnt: %d' % daq_iv_frame_cnt, file=file)
    # print('ai frame cnt: %d' % ai_frame_cnt)

    uncompress_frame_cnt = np.count_nonzero(app_frame['compress_flag'] == COMPRESS_FLAG['UNCOMPRESS'])
    compressed_frame_cnt = np.count_nonzero(app_frame['compress_flag'] == COMPRESS_FLAG['COMPRESSED'])
    print('uncompress frame cnt: %d' % uncompress_frame_cnt, file=file)
    print('compressed frame cnt: %d' % compressed_frame_cnt, file=file)
    print('', file=file)

    file_flags = np.vstack((app_frame['file_num'],app_frame['frame_type'],app_frame['dev_type']))
    file_index = np.unique(file_flags,axis=1,return_index=True)[1]
    for i,j in zip(np.sort(file_index),np.arange(file_index.shape[0])):
        file_num = app_frame['file_num'][i]
        frame_type = app_frame['frame_type'][i]
        dev_type = app_frame['dev_type'][i]
        file_num_str = str(file_num).zfill(3)
        frame_type_str = {v:k for k,v in FRAEM_TYPE.items()}[frame_type]
        dev_type_str = {v:k for k,v in DEV_TYPE.items()}[dev_type]
        
        print('======> %s-file, %s-%s, file_num: %s' %(str(j).zfill(3),dev_type_str, frame_type_str, file_num_str), file=file)
        frame_cnt = app_frame['file_num'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)].shape[0]
        # if app_frame['compress_flag'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)][0]:
        #     valid_file_len = np.sum(app_frame['decompress_len'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)])
        # else:
        #     valid_file_len = np.sum(app_frame['data_len'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)])
        print('    frame cnt: %d (since %d)' %(frame_cnt, i), file=file)
        # print('    valid file len: %d' %valid_file_len, file=file)
        # frame_cnt_seg = np.unique(app_frame['total_frame'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)])
        # print('    frame cnt(seg): %s' % ', '.join(map(str,frame_cnt_seg)), file=file)
        # if frame_cnt_seg.shape[0] == 1:
        #     frame_id_seg = app_frame['frame_id'][(app_frame['file_num'] == file_num) & (app_frame['frame_type'] == frame_type) & (app_frame['dev_type'] == dev_type)]
        #     unique_frame_id, count = np.unique(frame_id_seg, return_counts=True)
        #     miss_frame_id = np.array([i for i in range(frame_cnt_seg[0]) if i not in unique_frame_id])
        #     miss_frame_id_str = number_list_to_interval_str(miss_frame_id)
        #     duplicate_frame_id = unique_frame_id[count>1]
        #     duplicate_frame_id_str = number_list_to_interval_str(duplicate_frame_id)
        #     print('    miss frame id (%d): %s' %(miss_frame_id.shape[0],miss_frame_id_str))
        #     print('    duplicate frame id (%d): %s' %(duplicate_frame_id.shape[0],duplicate_frame_id_str))

    if 'decompress_len' in app_frame.keys():
        non_full_len_frame_cnt = np.count_nonzero(app_frame['decompress_len'] != 8192)
        non_full_len_frame_index = np.nonzero(app_frame['decompress_len'] != 8192)[0]
    else:
        non_full_len_frame_cnt = np.count_nonzero(app_frame['data_len'] != 8192)
        non_full_len_frame_index = np.nonzero(app_frame['data_len'] != 8192)[0]
    print('non full len frame cnt: %d' % non_full_len_frame_cnt, file=file)
    print('non full len frame index: %s' % ', '.join(map(str,non_full_len_frame_index)), file=file)
    print('-------------------end----------------------', file=file)
    file.close()

def summary_lvds_frame(frame_lvds, log_path):
    frame_num_total = frame_lvds['header'].shape[0]
    # sum_check_num = np.count_nonzero(frame_lvds['sum_check'])
    # valid_data_len_total = np.sum(frame_lvds['data_len'][frame_lvds['sum_check']]-4+1)
    invalid_frame_index = np.nonzero(frame_lvds['sum_check']==0)[0]
    with open(log_path, 'a') as file:
        print('------------summary of lvds frame------------', file=file)
        print(f'total frame number: {frame_num_total}', file=file)
        # print(f'valid frame number: {sum_check_num}', file=file)
        # print(f'valid data len: {valid_data_len_total}', file=file)
        print(f'invalid frame index: ', invalid_frame_index, file=file)
        error_head_cnt = np.count_nonzero(frame_lvds['header'] != 0xeb905716)
        error_tail_cnt = np.count_nonzero(frame_lvds['tail'] != 0x10bd59bf)
        if(error_head_cnt):
            print(f'error head cnt: {error_head_cnt}', file=file)
        if(error_tail_cnt):
            print(f'error tail cnt: {error_tail_cnt}', file=file)

        # daq_main_frame_cnt = np.count_nonzero(frame_lvds['dev_id'] == DEV_ID['DAQ_main'])
        # daq_bak_frame_cnt = np.count_nonzero(frame_lvds['dev_id'] == DEV_ID['DAQ_bak'])
        # ai_frame_cnt = np.count_nonzero(frame_lvds['dev_id'] == DEV_ID['AI'])
        # print('DAQ_main frame cnt: %d' % daq_main_frame_cnt)
        # print('DAQ_bak frame cnt: %d' % daq_bak_frame_cnt)
        # print('AI frame cnt: %d' % ai_frame_cnt)

        # grid_frame_cnt = np.count_nonzero(frame_lvds['dev_id'] == DEV_ID['GRID'])
        # print(f'GRID frame cnt: {grid_frame_cnt}', file=file)
        # non_full_len_frame_cnt = np.count_nonzero(frame_lvds['data_len'] != 2036 - 1)
        non_full_len_frame_index = np.nonzero(frame_lvds['data_len'] != 2036 - 1)[0]
        # print(f'non full len frame cnt: {non_full_len_frame_cnt}', file=file)
        print(f'non full len frame index: {non_full_len_frame_index}', file=file)
        # print(f'non full len frame data len: ', frame_lvds['data_len'][non_full_len_frame_index], file=file)
    

