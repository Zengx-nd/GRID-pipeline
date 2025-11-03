import os
from astropy.io import fits
from astropy.time import Time
import numpy as np

import paths
import utils

def save_evt_files(detector): # temprorary, to be modified, only for GRID-11B
    path_pattern = os.path.join(detector.output_path, paths.path_events, '*.fits')
    
    processed_log = os.path.join(detector.output_path, paths.path_log, paths.log_processed_events)

    unprocessed_files = utils.find_unprocessed_files(path_pattern, processed_log)

    evt_output_path = os.path.join(detector.output_path, paths.path_evt_files)

    for filename in unprocessed_files:
        print('Saving evt files from ' + filename + '...')
        # Save evt files from file
        events_dict = {}
        with fits.open(filename) as hdu_list:
            for channel in detector.gagg_channels:
                channel_dict = {
                    'UTC': hdu_list['EVENTS' + str(channel)].data['UTC'],
                    'ENERGY': hdu_list['EVENTS' + str(channel)].data['ENERGY'],
                }
                events_dict[channel] = channel_dict
        utc_all = np.concatenate([events_dict[channel]['UTC'] for channel in detector.gagg_channels])
        utc_min = np.min(utc_all)
        utc_max = np.max(utc_all)
        utc_min_isot = Time(utc_min, format='unix', scale='utc').isot
        utc_max_isot = Time(utc_max, format='unix', scale='utc').isot
        
        header_standard = fits.Header()
        header_standard['DATE'] = Time.now().isot
        header_standard['FILE_VER'] = 'PRELIMINARY'
        header_standard['MISSION'] = 'GRID'
        header_standard['CUBESAT'] = 'GRID-GROUND'
        header_standard['DATE_OBS'] = utc_min_isot
        header_standard['DATE_END'] = utc_max_isot
        header_standard['DATE_REF'] = '2018-01-01T00:00:00.000'

        t_ref = Time('2018-01-01T00:00:00.000', format='isot', scale='utc')
        edges = np.load('G02_output_bound_v03.npy')

        all_hdus = [fits.PrimaryHDU()]
        
        ########## EXT Ebounds ##########
        col0 = fits.Column(name='Channel', format='I', array=np.arange(1, len(edges)))
        col1 = fits.Column(name='E_MIN', format='D', unit='keV', array=edges[:-1])
        col2 = fits.Column(name='E_MAX', format='D', unit='keV', array=edges[1:])
        hdu_ebounds = fits.BinTableHDU.from_columns([col0, col1, col2], name='EBOUNDS', header=header_standard)
        all_hdus.append(hdu_ebounds)

        ########## EXT GTI ##########
        start = np.array([utc_min - t_ref.unix])
        stop = np.array([utc_max - t_ref.unix])
        col0 = fits.Column(name='START', format='D', unit='s', array=start)
        col1 = fits.Column(name='STOP', format='D', unit='s', array=stop)
        hdu_gti = fits.BinTableHDU.from_columns([col0, col1], name='GTI', header=header_standard)
        all_hdus.append(hdu_gti)

        ########## EXT Events ##########
        for channel in detector.gagg_channels:
            channel_dict = events_dict[channel]
            t = np.array(channel_dict['UTC']) - t_ref.unix
            pi = np.digitize(channel_dict['ENERGY'], edges)
            col0 = fits.Column(name='TIME', format='D', unit='s', array=t)
            col1 = fits.Column(name='PI', format='I', array=pi)
            
            n = len(t)
            e_type = np.ones(n)
            N_bins = len(edges) - 1
            for i in range(n):
                if pi[i] <= 0:
                    pi[i] = 1
                    e_type[i] = 0
                elif pi[i] >= N_bins + 1:
                    pi[i] = N_bins
                    e_type[i] = 2
            dead_time = np.ones(n) * 4
            col2 = fits.Column(name='DEAD_TIME', format='B', unit='us', array=dead_time)
            col3 = fits.Column(name='EVT_TYPE', format='B', array=e_type)
            
            hdu_evt = fits.BinTableHDU.from_columns([col0, col1, col2, col3], name='EVENTS' + str(channel), header=header_standard)
            all_hdus.append(hdu_evt)
        
        save_path = os.path.join(detector.output_path, paths.path_evt_files, 'ground_test_evt_' + os.path.basename(filename)[8:]) 
        fits.HDUList(all_hdus).writeto(save_path, overwrite=True)

        print('fits_save_path: ', save_path)
        
        utils.record_processed_file(filename, processed_log)