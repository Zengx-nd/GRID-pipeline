import os
from astropy.io import fits
from astropy.time import Time
import numpy as np

import paths
import utils

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def reconstruct_events(detector):

    # path_pattern = detector.source_path_pattern
    path_pattern = os.path.join(detector.output_path, paths.path_unpacked_data, '*.fits')

    processed_log = os.path.join(detector.output_path, paths.path_log, paths.log_processed_unpacked_data)
    unprocessed_files = utils.find_unprocessed_files(path_pattern, processed_log)

    events_output_path = os.path.join(detector.output_path, paths.path_events)


    for filename in tqdm(unprocessed_files, desc="Reconstructing Energy", leave=False, ncols=100):
        print('Reconstructing events from ' + filename + '...')
        # Reconstructing events from file
        
        events = []
        for channel in range(4):
            events_dict = {
                'UTC': [],
                'ENERGY': [],
                'ADC_VALUE': [],
                'ADC_CALIBRATED': []
            }
            events.append(events_dict)

        with fits.open(filename) as hdu_list:
            print(hdu_list['EVENTS'].data)
            events_hdu           =      hdu_list['EVENTS']
            utcs                 =      np.array(events_hdu.data['UTC'])
            timestamp_refs       =      np.array(events_hdu.data['TIMESTAMP_REF'])
            timestamp_trig       =      np.array(events_hdu.data['TIMESTAMP_OFFSET'])
            channels             =      np.array(events_hdu.data['CHANNEL'])
            adc_values           =      np.array(events_hdu.data['ADC_VALUE'])
        
        print('read hdu file complete')
        print('num of utc = ', len(utcs))
        print(utcs[:100])
        print(channels[:100])
        print(adc_values[:100])
        # pps_for_utc_stamp = get_utc_pps(timestamp_refs)
        # second_delta_stamp = [(pps_for_utc_stamp[ind] - pps_for_utc_stamp[ind-1]) 
        #                             for ind in range(1, len(pps_for_utc_stamp))]
        
        # mean_value 为 晶振频率
        mean_value = 99998665
        # threshold = 400
        # filtered_lst = [x for x in second_delta_stamp
        #                     if (mean_value - threshold) <= x <= (mean_value + threshold)]
        # mean_value = np.mean(filtered_lst)

        utc_accurate = utcs + timestamp_trig / mean_value

        detector.read_ec_coef()

        # for i in range(len(utcs)):
        for i in tqdm(range(len(utcs)), desc="Processing events", ncols=100):
            adc_calibrated = detector.calibrate_adc(adc_values[i], channels[i])
            energy = detector.adc_to_energy(adc_calibrated, channels[i])
            
            events[channels[i]]['UTC']             .append(utc_accurate[i])
            events[channels[i]]['ENERGY']          .append(energy)
            events[channels[i]]['ADC_VALUE']       .append(adc_values[i])
            events[channels[i]]['ADC_CALIBRATED']  .append(adc_calibrated)
        
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def process_event(i):
            adc_calibrated = detector.calibrate_adc(adc_values[i], channels[i])
            energy = detector.adc_to_energy(adc_calibrated, channels[i])
            
            # 将结果保存到 events 中
            return (i, channels[i], utc_accurate[i], energy, adc_values[i], adc_calibrated)

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_event, i) for i in range(len(utcs))]
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing events", ncols=100):
                i, channel, utc, energy, adc_value, adc_calibrated = future.result()
                events[channel]['UTC'].append(utc)
                events[channel]['ENERGY'].append(energy)
                events[channel]['ADC_VALUE'].append(adc_value)
                events[channel]['ADC_CALIBRATED'].append(adc_calibrated)

        
        print('energy calibrate complete')
        
        utc_all = np.concatenate([events[channel]['UTC'] for channel in range(4)])
        print(utc_all[:100])
        isot_min = Time(np.min(utc_all), format='unix', scale='utc').isot
        isot_max = Time(np.max(utc_all), format='unix', scale='utc').isot
        filename_time = isot_to_time_str(isot_min) + '_' + isot_to_time_str(isot_max)
        
        # Save reconstructed events to path_events
        events_output_path = os.path.join(detector.output_path, paths.path_events)
        save_filename = detector.short_name + '_tte_' + filename_time + '_preliminary.fits'
        save_path = os.path.join(events_output_path, save_filename)
        save_events(events, save_path)
        utils.record_processed_file(filename, processed_log)


def get_utc_pps(timestamp_refs):
    ind = 0
    ans = timestamp_refs[0]
    pps_for_utc_stamp = []
    while True:
        pps_for_utc_stamp.append(ans)
        while timestamp_refs[ind] == ans:
            ind += 1
            if ind == len(timestamp_refs):
                return pps_for_utc_stamp
        ans = timestamp_refs[ind]

def isot_to_time_str(isot):
    return isot[2:4] + isot[5:7] + isot[8:10] + isot[11:13] + isot[14:16]

def save_events(events, save_path):
    hdu_primary = fits.PrimaryHDU()
    all_hdus = [hdu_primary]
    for channel in range(4):
        column_utc = fits.Column(name='UTC', format='D', unit='s', array=events[channel]['UTC'])
        column_energy = fits.Column(name='ENERGY', format='D', unit='keV', array=events[channel]['ENERGY'])
        column_adc_value = fits.Column(name='ADC_VALUE', format='I', array=events[channel]['ADC_VALUE'])
        column_adc_calibrated = fits.Column(name='ADC_CALIBRATED', format='D', array=events[channel]['ADC_CALIBRATED'])
        hdu_events = fits.BinTableHDU.from_columns([column_utc, column_energy, column_adc_value, column_adc_calibrated], name='EVENTS' + str(channel))
        all_hdus.append(hdu_events)

    print('fits_save_path: ', save_path)
    
    fits.HDUList(all_hdus).writeto(save_path, overwrite=True)