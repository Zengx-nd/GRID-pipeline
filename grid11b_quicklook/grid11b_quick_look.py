import os, re, struct
import numpy as np # type: ignore
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fontdict = {'family':'WenQuanYi Zen Hei', 'size':16, 'color':'b'}


output_base_path = '/lime/GRID/quick_look/GRID-11B/quick_look'
if not os.path.exists(output_base_path):
    os.mkdir(output_base_path)

output_lc_dir = os.path.join(output_base_path, 'output_lightcurve')
output_lc_zm_dir = os.path.join(output_base_path, 'output_lightcurve', 'zoomed')
output_spec_dir = os.path.join(output_base_path, 'output_spectrum')
output_temp_dir = os.path.join(output_base_path, 'output_temperature')
output_cur_dir = os.path.join(output_base_path, 'output_current')
output_vol_dir = os.path.join(output_base_path, 'output_voltage')
output_log_file = os.path.join(output_base_path, 'log.txt')
output_lc_csv_dir = os.path.join(output_base_path, 'output_lc_csv')
output_consecutive_dir = os.path.join(output_base_path, 'consecutive_periods')

if not os.path.exists(output_lc_dir):
    os.makedirs(output_lc_dir)
if not os.path.exists(output_lc_zm_dir):
    os.makedirs(output_lc_zm_dir)
if not os.path.exists(output_spec_dir):
    os.makedirs(output_spec_dir)
if not os.path.exists(output_temp_dir):
    os.makedirs(output_temp_dir)
if not os.path.exists(output_cur_dir):
    os.makedirs(output_cur_dir)
if not os.path.exists(output_vol_dir):
    os.makedirs(output_vol_dir)
if not os.path.exists(output_log_file):
    with open(output_log_file, 'w') as f:
        f.write('')
if not os.path.exists(output_lc_csv_dir):
    os.makedirs(output_lc_csv_dir)
if not os.path.exists(output_consecutive_dir):
    os.makedirs(output_consecutive_dir)

sci_file_list = []
hk_file_list = []
iv_file_list = []
log_file_list = []
raw_data_path = '/lime/GRID/quick_look/GRID-11B'
for root, dirs, files in os.walk('/lime/GRID/quick_look/GRID-11B/'):
    for file in files:
        if file.endswith('.raw') and '_sci_' in file:
            sci_file_list.append(os.path.join(root, file))
        if file.endswith('.dat') and '_hk_' in file:
            hk_file_list.append(os.path.join(root, file))
        if file.endswith('.raw') and '_iv_' in file:
            iv_file_list.append(os.path.join(root, file))
        if file.endswith('.txt') and '_log_' in file:
            log_file_list.append(os.path.join(root, file))


# bin edges for long and short spectrums
bin_edges_long = [46,102,149,153,158,
                  163,172,177,185,191,
                  203,211,219,231,235,
                  241,250,265,277,284,
                  301,308,310,321,330,
                  332,337,342,347,352,
                  358,361,362,366,370,
                  373,378,380,385,388,
                  394,397,402,407,411,
                  424,428,433,442,455,
                  468,479,490,515,543,
                  558,606,651,739,851,
                  903,1031,1222,1323,1485,
                  1602,1793,1863,1959,2236,
                  2596,2822,2970,3086,3238,
                  3501,3818,4253,5144,11062,
                  13000,15000,np.inf]
bin_edges_short = [32,149,271,367,465,1528,2886,5259,np.inf]
# 计算 bin宽
bin_width_long = []
for i in range(len(bin_edges_long)-1):
    bin_width_long.append(bin_edges_long[i+1] - bin_edges_long[i])
bin_width_long = np.array(bin_width_long)
bin_width_short = []
for i in range(len(bin_edges_short)-1):
    bin_width_short.append(bin_edges_short[i+1] - bin_edges_short[i])
bin_width_short = np.array(bin_width_short)
# 计算 bin中点
bin_middle_long = []
for i in range(len(bin_edges_long)-1):
    bin_middle_long.append((bin_edges_long[i] + bin_edges_long[i+1]) / 2 - 0.5)
bin_middle_short = []
for i in range(len(bin_edges_short)-1):
    bin_middle_short.append((bin_edges_short[i] + bin_edges_short[i+1]) / 2 - 0.5)


# read processed files
quick_look_list = os.path.join(os.getcwd(), 'QUICK_LOOK_LIST.txt')
with open(quick_look_list, 'r') as f:
    processed_files = f.readlines()
    processed_files = [single_file.strip() for single_file in processed_files]


def scan_sci_from_file(filename):
    # 能谱模式
    pattern1_spec = re.compile(b'\\x3f\\x3f\\x44\\xcc')
    pattern2_spec = re.compile(b'\\x33\\xff\\xcc\\x44')
    # 特征量模式
    pattern1_ttl = re.compile(b'\\x1C\\x1C\\x22\\x88')
    pattern2_ttl = re.compile(b'\\xCC\\x11\\x88\\x22')
    with open(filename, 'rb') as f:
        print('>> Read File')
        data = f.read()
        print('<< Read File')
        print('>> Find TTE')
        sci_packs_tte = []
        start_indices = [m.start() for m in pattern1_ttl.finditer(data)]
        for i in range(len(start_indices)):
            if start_indices[i] >= len(data) - 528:
                continue
            if pattern2_ttl.match(data[start_indices[i]+524:start_indices[i]+528]):
                sci_packs_tte.append(data[start_indices[i]:start_indices[i]+528])
        print('<< Find TTE')
        print('>> Find SPEC')
        sci_packs_spec = []
        start_indices = [m.start() for m in pattern1_spec.finditer(data)]
        for i in range(len(start_indices)):
            if start_indices[i] >= len(data) - 528:
                continue
            if pattern2_spec.match(data[start_indices[i]+524:start_indices[i]+528]):
                sci_packs_spec.append(data[start_indices[i]:start_indices[i]+528])
        print('<< Find SPEC')
        print('Found %d SPEC packs' % len(sci_packs_spec))
        print('Found %d TTE packs' % len(sci_packs_tte))
    return sci_packs_tte, sci_packs_spec

def parse_sci_spec(pack):
    utc = struct.unpack('>I', pack[4:8])[0]
    channel = struct.unpack('>H', pack[20:22])[0]
    event_num = struct.unpack('>I', pack[22:26])[0]
    spectrum_long = []
    spectrum_shorts = []
    for i in range(82):
        spectrum_long.append(struct.unpack('>H', pack[38+2*i:38+2*i+2])[0])
    for i in range(20):
        spectrum_short = []
        for j in range(8):
            spectrum_short.append(struct.unpack('>H', pack[202+16*i+2*j:202+16*i+2*j+2])[0])
        spectrum_shorts.append(spectrum_short)
    return utc, channel, event_num, spectrum_long, spectrum_shorts

def parse_sci_tte(pack):
    utc = struct.unpack('>I', pack[4:8])[0]
    # 秒脉冲时间戳  总共 8 个字节 
    pps_stamp = struct.unpack('>Q', pack[12:20])[0]
    channel = struct.unpack('>H', pack[20:22])[0]
    event_num = struct.unpack('>I', pack[22:26])[0]
    particle_info = []
    for i in range(41):
        trig_stamp = struct.unpack('>I', pack[28+12*i:28+12*i+4])[0]
        wave_max = struct.unpack('>H', pack[32+12*i:32+12*i+2])[0]
        wave_base = struct.unpack('>H', pack[34+12*i:34+12*i+2])[0]
        wave_sum = struct.unpack('>I', pack[36+12*i:36+12*i+4])[0]
        
        particle_info.append((trig_stamp, wave_max, wave_base, wave_sum))
    particle_num = struct.unpack('>H', pack[26: 26+2])[0]
    return utc, pps_stamp, channel, event_num, particle_num, particle_info


# 绘制 高通量持续时间 分布直方图
def plot_time_periods(periods):
    durations = [(end - start).total_seconds() for start, end in periods]
    
    print(durations)
    plt.figure(figsize=(8, 4))
    plt.bar(range(len(periods)), durations, tick_label=None)
    
    plt.title('高通量模式持续时间', fontdict=fontdict)
    plt.xlabel('开启高通量模式的次数', fontdict=fontdict)
    plt.ylabel('持续时间（s）', fontdict=fontdict)
    
    plt.tight_layout()
    plt.show()
    plt.clf()



# 寻找 连续时间段， 要求 连续的长度 不小于 3
def find_consecutive_time_periods(time_series, min_length=3):
    time_series = [datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc) for time in time_series]
    
    consecutive_periods = []
    current_start = time_series[0]
    current_length = 1
    for i in range(1, len(time_series)):
        if time_series[i] == time_series[i-1]:
            continue
        if time_series[i] - time_series[i-1] == datetime.timedelta(seconds=1):
            current_length += 1
        else:
            if current_length >= min_length:
                consecutive_periods.append((current_start, time_series[i-1]))
            current_start = time_series[i]
            current_length = 1
    if current_length >= min_length:
        consecutive_periods.append((current_start, time_series[-1]))
    return consecutive_periods


def save_consecutive_periods(consecutive_periods, mode, base_time):
    if mode == 'spec':
        file = open(spec_log_path, 'w')
        print(f'\n\nGRID-11B {date_min} 至 {date_max} 高通量模式启用 的时间段\n\nNumber of Consecutive Periods = ', len(consecutive_periods), '\n', file=file)
        print('                  起始时间                     结束时间                 持续时间                 相对零点起始时间\n', file=file)
    if mode == 'tte':
        file = open(tte_log_path, 'w')
        print(f'\n\nGRID-11B {date_min} 至 {date_max} 特征量模式启用 的时间段\n\nNumber of Consecutive Periods = ', len(consecutive_periods), '\n', file=file)
        print('                  起始时间                     结束时间                 持续时间                 相对零点起始时间\n', file=file)
    index = 1
    for start_time, end_time in consecutive_periods:
        print(f"{index}\t:  {start_time.strftime('%m-%d %H:%M:%S')}  ==>  \
            {end_time.strftime('%m-%d %H:%M:%S')}      :      {end_time-start_time}           :              \
            {start_time-datetime.datetime.fromtimestamp(base_time, tz=datetime.timezone.utc)}", file=file)
        index += 1
    file.close()
    # plot_time_periods(consecutive_periods)
    return


for sci_file in sci_file_list:
    if sci_file in processed_files:
        continue

    print('==============> Processing SCI File')
    sci_packs_tte, sci_packs_spec = scan_sci_from_file(sci_file)

    cps_spec = [{}, {}, {}, {}]
    total_spectrum_long = np.zeros((4, 82), dtype=float)
    total_spectrum_short = np.zeros((4, 8), dtype=float)

    for pack in sci_packs_spec:
        utc, channel, event_num, spectrum_long, spectrum_shorts = parse_sci_spec(pack)
        
        spec_count_sum = 0
        for i in range(82):
            spec_count_sum += spectrum_long[i]
        if utc in cps_spec[channel]:
            cps_spec[channel][utc] += spec_count_sum
        else:
            cps_spec[channel][utc] = spec_count_sum
        
        for spec_ch in range(82):
            total_spectrum_long[channel][spec_ch] += spectrum_long[spec_ch]
        for spec_num in range(20):
            for spec_ch in range(8):
                total_spectrum_short[channel][spec_ch] += spectrum_shorts[spec_num][spec_ch]

    for channel in range(4):
        for spec_ch in range(82):
            total_spectrum_long[channel][spec_ch] /= bin_width_long[spec_ch]
        for spec_ch in range(8):
            total_spectrum_short[channel][spec_ch] /= bin_width_short[spec_ch]

    cps_tte = [{}, {}, {}, {}]
    # UTC = []
    # CHANNEL = []
    # EVNUM = []
    # TRIG_STAMP = []
    # WAVE_MAX = []
    # WAVE_BASE = []
    # WAVE_SUM = []
    # all_41 = True

    for pack in sci_packs_tte:
        utc, pps_stamp, channel, event_num, particle_num, info= parse_sci_tte(pack)
        if utc not in cps_tte[channel]:
            cps_tte[channel][utc] = 0
        cps_tte[channel][utc] += particle_num

        # UTC.append(utc)
        # CHANNEL.append(channel)
        # EVNUM.append(event_num)
        
        # if particle_num != 41:
        #     all_41 = False
        # for particle in info:
            # TRIG_STAMP.append(particle[0])
            # WAVE_MAX.append(particle[1])
            # WAVE_BASE.append(particle[2])
            # WAVE_SUM.append(particle[3])

    plt.clf()

    utc_min = min([min(cps_spec[channel].keys()) for channel in range(4)])
    utc_max = max([max(cps_spec[channel].keys()) for channel in range(4)])
    date_min = datetime.datetime.fromtimestamp(utc_min, tz=datetime.timezone.utc)
    date_max = datetime.datetime.fromtimestamp(utc_max, tz=datetime.timezone.utc)

    print(utc_min, utc_max)
    print(date_min, date_max)
    utc_in_filename = date_min.strftime('%Y%m%d%H%M') + '_' + date_max.strftime('%Y%m%d%H%M')
    spec_csv_file_path = os.path.join(output_lc_csv_dir, utc_in_filename + '_' + sci_file.split('/')[-1][:-4] + '_spec.csv')
    tte_csv_file_path = os.path.join(output_lc_csv_dir, utc_in_filename + '_' + sci_file.split('/')[-1][:-4] + '_tte.csv')

    cps_figure_path = os.path.join(output_lc_dir, sci_file.split('/')[-1] + '.png')
    print(utc_in_filename, '\n', spec_csv_file_path, '\n', cps_figure_path)

    all_utc = set()
    with open(spec_csv_file_path, 'w') as f:
        f.write('UTC,Channel,Counts\n')
        for channel in range(4):
            all_utc.update(cps_spec[channel].keys())
        all_utc = sorted(list(all_utc))
        for utc in all_utc:
            for channel in range(4):
                if utc in cps_spec[channel]:
                    f.write('%d,%d,%d\n' % (utc, channel, cps_spec[channel][utc]))
                else:
                    f.write('%d,%d,%d\n' % (utc, channel, 0))

    all_utc = set()
    with open(tte_csv_file_path, 'w') as f:
        f.write('UTC,Channel,Counts\n')
        for channel in range(4):
            all_utc.update(cps_tte[channel].keys())
        all_utc = sorted(list(all_utc))
        for utc in all_utc:
            for channel in range(4):
                if utc in cps_tte[channel]:
                    f.write('%d,%d,%d\n' % (utc, channel, cps_tte[channel][utc]))
                else:
                    f.write('%d,%d,%d\n' % (utc, channel, 0))



    spec_log_path = os.path.join(output_consecutive_dir, utc_in_filename + '_SPEC_TIME.txt')
    tte_log_path = os.path.join(output_consecutive_dir, utc_in_filename + '_TTE_TIME.txt')


    # 由于不方便同时画多个通道的双模式光变曲线， 所以目前仅用 一通道 的数据画光变
    channel = 1

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:00'))
    plt.gcf().autofmt_xdate()

    # spec
    utc_list = list(cps_spec[channel].keys())
    for i in range(len(utc_list)):
        if utc_list[i] < 1e8:
            utc_list[i] = np.nan

    consecutive_periods = find_consecutive_time_periods(utc_list)
    save_consecutive_periods(consecutive_periods, mode='spec', base_time=utc_list[0])
    tz_utc = datetime.timezone.utc
    for start_time, end_time in consecutive_periods:
        count_list = []
        date_list = []
        for utc in range(int(start_time.timestamp()), int(end_time.timestamp())+1):
            date_list.append(datetime.datetime.fromtimestamp(utc, tz=tz_utc))
            count_list.append(cps_spec[channel][utc])
        plt.step(date_list, count_list, where='pre', linewidth=0.5, color='red')


    # tte
    utc_list = list(cps_tte[channel].keys())
    for i in range(len(utc_list)):
        if utc_list[i] < 1e8:
            utc_list[i] = np.nan

    consecutive_periods = find_consecutive_time_periods(utc_list)
    save_consecutive_periods(consecutive_periods, mode='tte', base_time=utc_list[0])
    for start_time, end_time in consecutive_periods:
        count_list = []
        date_list = []
        for utc in range(int(start_time.timestamp()), int(end_time.timestamp())+1):
            date_list.append(datetime.datetime.fromtimestamp(utc, tz=tz_utc))
            count_list.append(cps_tte[channel][utc])
        plt.step(date_list, count_list, where='pre', linewidth=0.5, color='blue')

    plt.legend()
    plt.title('Light curves from file \"%s\"'%sci_file.split('/')[-1])
    plt.xlabel('UTC time')
    plt.ylabel('Counts per second')
    plt.yscale('log')
    plt.savefig(cps_figure_path)

    subfolder = os.path.join(output_lc_zm_dir, sci_file.split('/')[-1])
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H: %M'))
    plt.gcf().autofmt_xdate()

    counter = 0
    date_delta = datetime.timedelta(minutes=5)
    date_edge_delta = datetime.timedelta(seconds=10)
    while counter <= 300: # in case of too many plots
        lower_bound = date_min + counter * date_delta
        upper_bound = date_min + (counter + 1) * date_delta
        plt.xlim(lower_bound - date_edge_delta, upper_bound + date_edge_delta)
        plt.title('Light curves from file \"%s\", part %d'%(sci_file.split('/')[-1], counter + 1))
        plt.savefig(os.path.join(subfolder, '%d.png' % (counter + 1)))
        if upper_bound > date_max:
            break
        counter += 1
    plt.clf()

    for channel in range(4):
        plt.step(bin_edges_long[:-1], total_spectrum_long[channel], where='post', label='Channel %d' % channel, linewidth=0.5)
    plt.legend()
    plt.title('Spectra from file \"%s\"'%sci_file.split('/')[-1])
    plt.xlabel('ADC channel')
    plt.ylabel('Counts per ADC channel')
    plt.xscale('log')
    plt.yscale('log')
    plt.savefig(os.path.join(output_spec_dir, sci_file.split('/')[-1] + '.png'))

    plt.clf()

    with open(quick_look_list, 'a') as processed_list:
        print(sci_file, file=processed_list)