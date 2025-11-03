import numpy as np
import os
import xml.etree.ElementTree as ET
import re
import h5py
from datetime import datetime,timedelta

from parity_check import crc16_xmodem_nd, bcc_nd, crc32_c_nd
import pandas as pd
import zlib

count = 0

def find_pattern_in_buffer(buffer, pattern):
    Pattern = re.compile(pattern, re.S)
    return np.array([(ip.start(), ip.end()) for ip in Pattern.finditer(buffer)]).astype(np.int_)

def get_frame_data(file_name, xml_file, data_tag, endian='MSB', data_stream=None,
                   packet_len=None, forced_len=None):
    """
    Retrieve frame data from a file or data stream based on the specified parameters.

    Args:
        file_name (str): The name of the file to parse.
        xml_file (str): The XML file containing the data tag.
        data_tag (str): The tag name of the data in the XML file.
        endian (str, optional): The endianness of the data. Defaults to 'MSB'.
        data_stream (ndarray, optional): The data stream to parse. Defaults to None.
        packet_len (int, optional): The length of each packet. Defaults to None.
        forced_len (int, optional): use to get data with specified length.

    Returns:
        tuple: A tuple containing the frame data, index, and the XML element representing the data tag.
    """

    if file_name:
        print('========> parsing file ',file_name)
        print('>> Read File')
        buffer = np.fromfile(file_name,dtype=np.uint8)
        print('<< Read File')
    elif data_stream is not None:
        print('========> parsing data')
        print('>> Read Stream')
        buffer = data_stream.flatten()
        print('<< Read Stream')
    else:
        raise ValueError('file_name or data_stream must be specified')

    print('>> Read XML')
    et_packet = ET.parse(xml_file).getroot().find(data_tag)
    if et_packet is None:
        raise ValueError(f'cannot find {data_tag} in {xml_file}')

    packet_len = int(et_packet.attrib['packet_len']) if packet_len is None else packet_len
    if ('endian' in et_packet.attrib):
        endian = et_packet.attrib['endian']

    head,tail = [],[]
    head = [int(v[2:],base=16) for v in et_packet.attrib['head'].split(';')]
    head = head[::-1] if endian=='LSB' else head
    if 'tail' in et_packet.attrib:
        tail = [int(v[2:],base=16) for v in et_packet.attrib['tail'].split(';')]
    tail = tail[::-1] if endian=='LSB' else tail
    match_num = packet_len - len(head) - len(tail)
    pattern = re.escape(bytes(head)) + b'.{' + bytes(f'{match_num}',encoding='utf-8') + b'}'
    if tail:
        pattern += re.escape(bytes(tail))
    print('<< Read XML')

    print('>> Find Pattern', pattern)
    index = find_pattern_in_buffer(buffer, pattern)
    if index.shape[0] == 0:
        raise ValueError(f'''donot find data frame with pattern {pattern}, 
                         please check the raw data file or the xml file,
                         or specify the packet_len parameter''')
    if not tail:
        index = np.array([(v[0],v[0]+packet_len) for v in index])
    print('<< Find Pattern')
    print('Index_len = ', len(index))

    print('>> Get frame_data')
    if forced_len:
        # data_index = np.r_[[np.arange(v[0],v[0]+forced_len) for v in index ]].astype(np.int_)
        # frame_data = np.r_[buffer,np.zeros(forced_len,dtype=np.uint8)][data_index].reshape(-1,forced_len)
        buffer = np.r_[buffer, np.zeros(forced_len,dtype=np.uint8)]
        frame_data = [buffer[ind[0]:ind[0]+forced_len] for ind in index]
    else:
        frame_data = [buffer[ind[0]:ind[1]] for ind in index]
    print('<< Get frame_data')
    
    print('>> List to Array')
    frame_data = np.array(frame_data)
    print('<< List to Array')

    return (frame_data, index, et_packet)

def parse_frame_data(file_name, xml_file, data_tag, multi_evt=None, multi_step=None, 
        endian='MSB', crc_check=True, bcc_check=True, data=None, skip_et=[],
        packet_len=None):
    """
    Parses frame data from a file or buffer data.

    Args:
        file_name (str): The name of the file to parse.
        xml_file (str): The XML file containing the data structures information.
        data_tag (str): The tag specifying the type of data to parse.
        multi_evt (int, optional): The number of events per packet. Defaults to None.
        multi_step (int, optional): The number of steps per event. Defaults to None.
        endian (str, optional): The endianness of the data. Defaults to 'MSB'.
        crc_check (bool, optional): Whether to perform CRC check. Defaults to True.
        bcc_check (bool, optional): Whether to perform BCC check. Defaults to True.
        data (ndarray, optional): The data stream to parse. Defaults to None.
            when use this parameter, specify file_name to '' or None.
        skip_et (list, optional): List of event types to skip. Defaults to [].
        packet_len (int, optional): The length of each packet. Defaults to None.

    Returns:
        tuple: A tuple containing the parsed data and the index of the packets.

    """
    if file_name not in [None,'']:
        if not os.path.exists(file_name):
            raise ValueError(f'cannot find file {file_name}')
    if not os.path.exists(xml_file):
        raise ValueError(f'cannot find xml file {xml_file}')

    data0, index, et_packet = get_frame_data(file_name=file_name, xml_file=xml_file, data_tag=data_tag, 
        endian=endian, data_stream=data, packet_len=packet_len)
    packet_num = len(data0)
    packet_len = len(data0[0])
    print('packet_num is ', packet_num, " ; packet_len is ", packet_len)

    if data_tag == 'ft_packet':
        multi_evt = 20 if multi_evt is None else multi_evt
        multi_step = 24 if multi_step is None else multi_step
    if data_tag == 'tl_packet':
        multi_evt = 15 if multi_evt is None else multi_evt
        multi_step = 16 if multi_step is None else multi_step
    if data_tag == 'catch_ft_packet':
        multi_evt = 40 if multi_evt is None else multi_evt
        multi_step = 12 if multi_step is None else multi_step
    if multi_evt is None:
        multi_evt = 1
        multi_step = 1

    # make low configuration computer can handle large file
    if (packet_num * packet_len > 1e9): 
        step = int(np.ceil(1e9/packet_len))
        p0,p1 = [],[]
        for i in range(np.ceil(index.shape[0]/step).astype(int)):
            index_max = min((i+1)*step,index.shape[0])
            tmp = parse_frame_single(data0[i*step:index_max,:], et_packet, multi_evt,
                    multi_step, endian, crc_check, bcc_check, skip_et)
            p0.append(tmp[0])
            p1.append(tmp[1])
        q0 = p0[0].copy()
        for k in q0.keys():
            for p in p0[1:]:
                q0[k] = np.r_[q0[k],p[k]]
        q1 = p1[0].copy()
        for k in q1.keys():
            for p in p1[1:]:
                q1[k] = np.r_[q1[k],p[k]]
        return (q0,index)
    else:
        return (parse_frame_single(data0, et_packet, multi_evt, multi_step, 
                    endian, crc_check, bcc_check, skip_et)[0],index)

def parse_frame_single(data_in, et_packet, multi_evt, multi_step, endian='MSB',
        crc_check=True, bcc_check=True, skip_et=[]):
    
    
    """
    Parses frame of data.

    Args:
        data_in (numpy.ndarray): Input data array with shape (packet_num, packet_len).
        et_packet (ElementTree.Element): ElementTree element containing packet information.
        multi_evt (int): Number of events.
        multi_step (int): byte size of each event.
        endian (str, optional): Endian format. Defaults to 'MSB'.
        crc_check (bool, optional): Flag to perform CRC check. Defaults to True.
        bcc_check (bool, optional): Flag to perform BCC check. Defaults to True.
        skip_et (list, optional): List of ET names to skip. Defaults to [].

    Returns:
        tuple: A tuple containing the parsed data and byte information.
    """
    
    packet_num = len(data_in)
    data_byte = {}
    data = {}
    tag_info = pd.DataFrame({'name':[], 'start':[], 'size':[], 'len':[]})

    for et in et_packet.findall('./'):
        name = et.tag
        if name in skip_et:
            continue
        start = int(et.find('start').text) 
        if 'vary_wf' in et.find('start').attrib: 
            pds = tag_info[tag_info['name']=='waveform_data']
            start = (start + int(pds.iloc[0]['start']) + 
                int(pds.iloc[0]['size']) * int(pds.iloc[0]['len']))
        if 'vary_repeat' in et.find('start').attrib:
            print(et.find('start').attrib)
            start = (start + int(et.find('start').attrib['base_start']) + multi_evt*multi_step)
        if 'vary_tag' in et.find('start').attrib:
            start_tag = et.find('start').attrib['vary_tag']
            pds = tag_info[tag_info['name']==start_tag]
            start = start + int(pds.iloc[0]['start']) + int(pds.iloc[0]['size']) * int(pds.iloc[0]['len'])
        size = int(et.find('size').text)
        length = int(et.find('len').text)
        if 'tag' in et.find('len').attrib:
            length_tag = et.find('len').attrib['tag']
            length_tmp = data[length_tag][0] if data[length_tag].shape else data[length_tag]
            if length_tmp < length:
                length = length_tmp
        if name == 'waveform_data':
            length = data['sample_length'][0]
        tag_info.loc[len(tag_info.index)] = [name, start, size, length] # type: ignore

        endian_bak = endian
        if 'endian' in et.attrib:
            endian_bak,endian = endian,et.attrib['endian']

        if 'repeat' in et.attrib:
            index = np.r_[[np.arange(start+i*multi_step,start+i*multi_step+length*size) for i in range(multi_evt)]]
            multi_dim = multi_evt
        else:
            index = np.arange(start,start+length*size)
            multi_dim = 1
        data_byte[name] = data_in[:,index].reshape(-1,multi_dim,length,size) 

        if 'multi' in et.attrib:
            data_byte[name] = np.repeat(data_byte[name],multi_evt,axis=1)

        data_byte[name] = data_byte[name].reshape(-1,length,size)
        data[name] = byte2int(data_byte[name],endian=endian)
        endian = endian_bak

        if 'incre' in et.attrib:
            data[name] = data[name].reshape(-1,multi_evt,length)
            data[name] = (data[name] + np.tile(np.arange(multi_evt),(data[name].shape[0],1))[...,np.newaxis]).reshape(-1,length).squeeze()

        if (name == 'CRC') & (crc_check):
            data_crc = data[name].reshape(packet_num,multi_evt)
            data['crc_check'] = np.zeros((packet_num,multi_evt),dtype=np.bool_)
            skip0 = int(et.attrib['skip0'])
            skip1 = int(et.attrib['skip1'])
            crc_type = et.attrib['type'] if 'type' in et.attrib else 'crc16_xmodem'
            for j in range(multi_dim):
                if (j==0): 
                    crc_index = np.arange(skip0,start-skip1).astype(int)
                else:
                    crc_index = np.r_[crc_index,np.arange(start+j*multi_step-(multi_step-size),start+j*multi_step-skip1)].astype(int) # type: ignore
                #for i in range(packet_num):
                #    data['crc_check'][i,j] = (crc16_xmodem(data0[i,crc_index]) == data_crc[i,j])
                if crc_type == 'crc16_xmodem':
                    data['crc_check'][:,j] = (crc16_xmodem_nd(data_in[:,crc_index]) == data_crc[:,j])
                elif crc_type == 'crc32-c':
                    data['crc_check'][:,j] = (crc32_c_nd(data_in[:,crc_index]) == data_crc[:,j])
            if (multi_dim==1) & (multi_evt>1):
                for j in range(1,multi_evt):
                    data['crc_check'][:,j] = data['crc_check'][:,0]
            data['crc_check'] = data['crc_check'].flatten()
            print('CRC done')
        if(name=='bcc') & (bcc_check):
            data_bcc = data[name].reshape(packet_num,multi_evt)
            data['bcc_check'] = np.zeros((packet_num,multi_evt),dtype=np.bool_)
            skip0 = int(et.attrib['skip0'])
            skip1 = int(et.attrib['skip1'])
            for j in range(multi_evt):
                if j==0: 
                    bcc_index = np.arange(skip0,start-skip1).astype(int)
                else:
                    bcc_index = np.r_[bcc_index,np.arange(start+j*multi_step-(multi_step-size),start+j*multi_step-skip1)].astype(int) # type: ignore
                data['bcc_check'][:,j] = (bcc_nd(data_in[:,bcc_index]) == data_bcc[:,j])
            data['bcc_check'] = data['bcc_check'].flatten()
            print('BCC done')
        if(name=='check_sum'):
            data_sum = data[name].reshape(packet_num,multi_evt)
            data['sum_check'] = np.zeros((packet_num,multi_evt),dtype=np.bool_)
            skip0 = int(et.attrib['skip0'])
            skip1 = int(et.attrib['skip1'])
            byte = int(et.attrib['byte'])
            for j in range(multi_evt):
                if j==0: 
                    sum_index = np.arange(skip0,start-skip1).astype(int)
                else:
                    sum_index = np.r_[sum_index,np.arange(start+j*multi_step-(multi_step-size),start+j*multi_step-skip1)].astype(int) # type: ignore
                data['sum_check'][:,j] = (np.sum(data_in[:,sum_index],axis=1).astype(np.uint16) == data_sum[:,j])
            data['sum_check'] = data['sum_check'].flatten()
    if data[name].shape[0]>1: #type: ignore
        print(tag_info)
    # count += 1
    # print(count)
    return (data,data_byte)



def byte2int(data,endian='MSB'):
    if endian == 'MSB':
        data = data[...,::-1]
    sp = data.shape
    if sp[-1] == 1:
        return np.atleast_1d(data.squeeze())
    elif sp[-1] <= 2:
        return np.atleast_1d((data @ 2**(8*np.arange(sp[-1], dtype=np.uint16))).squeeze())
    if sp[-1] <= 4:
        return np.atleast_1d((data @ 2**(8*np.arange(sp[-1], dtype=np.uint32))).squeeze())
    elif sp[-1] <= 8:
        return np.atleast_1d((data @ 2**(8*np.arange(sp[-1], dtype=np.uint64))).squeeze())
    else:
        return np.atleast_1d((data @ 2**(8*np.arange(sp[-1], dtype=object))).squezze())
    pass

def dict_to_hdf5(fh,data):
    for key,value in data.items():
        if type(value) is dict:
            dict_to_hdf5(fh,data=value)
        else:
            # TODO(liping): temporary treat
            if value.dtype == np.object_:
                dt = h5py.vlen_dtype(np.dtype(value[0].dtype))
                fh.create_dataset(key,data=value,dtype=dt)
            else:
                fh.create_dataset(key,data=value)

def pandas_to_hdf5(fh,data):
    for key,value in data.items():
        if (value.dtype == np.object_) & (type(value.iloc[0]) == np.ndarray):
            dt = h5py.vlen_dtype(np.dtype(value.iloc[0].dtype))
            fh.create_dataset(key,data=value,dtype=dt)
        elif (value.dtype == np.object_):
            dt = h5py.special_dtype(vlen=str)
            fh.create_dataset(key,data=value,dtype=dt)
        else:
            fh.create_dataset(key,data=value)

def save_hdf5(path,data):
    with h5py.File(path+'.hdf5','w') as fh:
        dict_to_hdf5(fh,data)