import glob
import numpy as np

def find_unprocessed_files(path_pattern, processed_log):
    processed_files = []
    with open(processed_log, 'r') as f:
        processed_files = f.readlines()
    processed_files = [f.strip() for f in processed_files]
    # print(processed_files)
    files = glob.glob(path_pattern)
    # print(files)
    unprocessed_files = np.sort([f for f in files if f not in processed_files])
    return unprocessed_files

def record_processed_file(file_path, processed_log):
    with open(processed_log, 'a') as f:
        f.write(file_path + '\n')