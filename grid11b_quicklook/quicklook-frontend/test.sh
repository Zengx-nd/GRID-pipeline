#!/bin/bash

# 接收参数
start_time=$1
end_time=$2
data_type=$3

# 提取参数值 (使用 sed 来提取参数值)
start_time_value=$(echo "$start_time" | sed 's/--start-time=//g')
end_time_value=$(echo "$end_time" | sed 's/--end-time=//g')
data_type_value=$(echo "$data_type" | sed 's/--data-type=//g')

# 模拟数据查询 (你需要替换为你的实际查询逻辑)
if [[ "$data_type_value" == "raw" ]]; then
  data='[{"time":"'$start_time_value'", "value":10}, {"time":"'$end_time_value'", "value":20}]'
elif [[ "$data_type_value" == "processed" ]]; then
  data='[{"time":"'$start_time_value'", "value":30}, {"time":"'$end_time_value'", "value":40}]'
else
  data='[{"time":"'$start_time_value'", "value":50}, {"time":"'$end_time_value'", "value":60}]'
fi

# 返回 JSON 格式的数据
echo "$data"