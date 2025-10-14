from os.path import join
from os import getenv, getcwd

path_packets = 'packets'
path_unpacked_data = 'unpacked_data'
path_events = 'events'
path_evt_files = 'evt_files'

path_log = 'log'
log_processed_raw_data = 'processed_raw_data.log'
log_processed_packets = 'processed_packets.log'
log_processed_unpacked_data = 'processed_unpacked_data.log'
log_processed_events = 'processed_events.log'


base_dir = getcwd()
source_dir = join(
    base_dir,
    'testfiles',
    'source'
    # 'data'
)

output_dir = join(
    base_dir,
    # 'testfiles',
    'output'
)

env = getenv("PIPELINE_ENV", "development")
if env == 'production':
    source_dir = join(
        'data',
        'GRIDSatFTP'
    )
    output_dir = join(
        'srv',
        'gridftp',
        'GRID_temporary_pipeline',
        'output'
    )
