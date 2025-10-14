def print_hex_bytes(data, bytes_per_line=16):
    for offset in range(0, len(data), bytes_per_line):
        chunk = data[offset:offset + bytes_per_line]
        # 转换为十六进制字符串列表
        hex_bytes = [f"{byte:02X}" for byte in chunk]
        # 格式化输出
        print(f"{offset:08X}:  {' '.join(hex_bytes):<{bytes_per_line*3}}")
