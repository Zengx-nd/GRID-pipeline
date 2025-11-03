import os
from astropy.io import fits

import numpy as np
import utils
import paths

from tqdm import tqdm

def extract_packets(detector):
    path_pattern = os.path.join(r'/data/GRIDSatFTP/11B/', r'JL1PT02A03_*', '*.dat')

    processed_log = os.path.join(detector.output_path, paths.path_log, paths.log_processed_raw_data)

    unprocessed_files = utils.find_unprocessed_files(path_pattern, processed_log)
    
    packet_output_path = os.path.join(detector.output_path, paths.path_packets)

    # unprocessed_files = []
    
    for filename in tqdm(unprocessed_files, desc="Extracting Packets", leave=False, ncols=100):
        # print('Extracting packets from ' + filename + '...')
        # Extract packets from file
        packets_all_info = detector.extract_packets(filename)
        
        # Save packets to path_packets
        packet_output_path = os.path.join(detector.output_path, paths.path_packets)
        
        save_filename = detector.short_name + '_pac_' + os.path.basename(filename).split('.')[0] + '.fits'
        save_packets_tmp(packets_all_info, packet_output_path, save_filename)

        utils.record_processed_file(filename, processed_log)

def save_packets_tmp(packets_all_info, packet_output_path, save_filename):
    # temprorary, to be modified, insert packets to files for each date
    hdu_primary = fits.PrimaryHDU()
    all_hdus = [hdu_primary]
    for packet_type in packets_all_info.keys(): # EVENTS, SPEC, HOUSEKEEPING
        packet_utc = packets_all_info[packet_type][0]
        packet_timestamp = packets_all_info[packet_type][1]
        packets = packets_all_info[packet_type][2]
        packet_length = packets_all_info[packet_type][3]

        if len(packets)==0:
            packet_utc = np.array([], dtype=np.int32)  # J 格式需要 int32
            packet_timestamp = np.array([], dtype=np.int64)  # K 格式需要 int64
            packets = np.array([], dtype=np.uint8).reshape(0, packet_length)  # 187B 格式
        else:
            packet_utc = np.array(packet_utc, dtype=np.int32)
            packet_timestamp = np.array(packet_timestamp, dtype=np.int64)
            packets = [
                np.frombuffer(p, dtype=np.uint8) for p in packets
            ]
            packets = np.array(packets, dtype=np.uint8)
        
        column_utc = fits.Column(name='UTC', format='J', unit='s', array=packet_utc)
        column_timestamp = fits.Column(name='TIMESTAMP', format='K', array=packet_timestamp)
        column_packet = fits.Column(name='PACKET', format='%dB'%(packet_length), array=packets)
        hdu_packet = fits.BinTableHDU.from_columns([column_utc, column_timestamp, column_packet], name=packet_type)

        all_hdus.append(hdu_packet)
    save_path = os.path.join(packet_output_path, save_filename)

    print('fits_save_path: ', save_path)
    fits.HDUList(all_hdus).writeto(save_path, overwrite=True)





