import packet_extractor as pe
import data_unpacker as du
import event_reconstructor as er
import file_formatter as ff

payload_number = '11'
# payload_number = 'ground'

if payload_number == '11':
    from detectors.detector_grid_11b import GRID11BDetector
    detector = GRID11BDetector()

if payload_number == 'ground':
    from detectors.detector_grid_ground import GRIDGroundDetector
    detector = GRIDGroundDetector()


if __name__ == '__main__':
    print(50*'$', '\n', 50*'$', '\nExtracting packets...')
    pe.extract_packets(detector)
    print(50*'$', '\n', 50*'$', '\nUnpacking data...')
    du.unpack_data(detector)
    print(50*'$', '\n', 50*'$', '\nReconstructing events...')
    er.reconstruct_events(detector)
    print(50*'$', '\n', 50*'$', '\nFormatting files...')
    ff.save_evt_files(detector)
    print(50*'$', '\n', 50*'$', '\nProcess complete.')


    