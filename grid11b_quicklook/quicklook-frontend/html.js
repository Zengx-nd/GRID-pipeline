
// 11B 载荷 dat 原始数据的文件列表
const payload_type = document.getElementById('payload-type').value
const get_dat_Button = document.getElementById('get-dat-button');
const datResultsDiv = document.getElementById('dat-results');        
const datlistSelection = document.getElementById('dat-list-selection');
let dat_list = [];
get_dat_Button.addEventListener('click', async () => {

    const Data = await get_dat_list(payload_type);
    dat_list = Data;

    if (Data.length === 0) {
        datResultsDiv.innerHTML = '<p class="text-red-500 dark:text-red-400">未找到符合条件的数据。</p>';
        datlistSelection.innerHTML = '<option value="">请先查询数据</option>';
    } else {
        datResultsDiv.innerHTML = `<p class="text-green-500 dark:text-green-400">查询成功，找到 ${Data.length} 条数据。</p>`;
        datlistSelection.innerHTML = Data.map((item, index) => `<option value="${item}">文件 ${index} :  ${item}</option>`).join('');
    }
});



const get_unpack_log_Button = document.getElementById('get-unpacklog-button');
const unpacklogTextDiv = document.getElementById('unpack-log');

const unpackedResultsDiv = document.getElementById('unpacked-results');
const unpackedlistSelection = document.getElementById('unpacked-list-selection');

get_unpack_log_Button.addEventListener('click', async() => {
    const filename = datlistSelection.value;

    const Data_1 = await get_unpack_log(filename);

    if (Data_1.length === 0) {
        unpacklogTextDiv.value = '未查询到该文件的解包日志';
    } else {
        unpacklogTextDiv.value = Data_1;
    }

    const Data_2 = await get_unpacked_list(filename);
    
    console.log(Data_2);

    if (Data_2.length === 0) {
        unpackedResultsDiv.innerHTML = '<p class="text-red-500 dark:text-red-400">未查询到该文件的解包结果</p>';
    } else {
        unpackedResultsDiv.innerHTML = `<p class="text-red-500 dark:text-red-400">查询成功，找到 ${Data_2.length} 条数据</p>`;
        unpackedlistSelection.innerHTML = Data_2.map((item, index) => `<option value="${item}">data ${index} : ${item}</option>`).join('');
    }
});



const get_unpacked_info_Button = document.getElementById('get-unpacked-info-button');
const unpackedInfoTextDiv = document.getElementById('unpacked-file-info');

get_unpacked_info_Button.addEventListener('click', async() => {
    const dirname = datlistSelection.value;
    const filename = unpackedlistSelection.value;

    const Data = await get_unpackedFile_info(dirname, filename);
    
    if (Data_2.length === 0) {
        unpackedInfoTextDiv.innerText = '<p class="text-red-500 dark:text-red-400">未查询到该文件的信息</p>';
    } else {
        unpackedResultsDiv.innerText = Data;
    }

});

async function get_dat_list(payload) {

    try {
        const response = await fetch(`/api/datlist?payload=${payload}`);

        // 检查响应是否成功
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        // 解析 JSON 格式的响应数据
        const data = await response.json();
        return data; // 返回获取到的数据
    } catch (error) {
        console.error("获取数据时发生错误:", error);
        // 在页面上显示错误信息
        queryResultsDiv.innerHTML = `<p class="text-red-500 dark:text-red-400">获取数据失败: ${error.message}</p>`;
        return []; // 发生错误时返回空数组
    }
}



async function get_unpack_log(filename) {

    try {
        const response = await fetch(`/api/unpacklog?filename=${filename}`);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.text();
        return data; // 返回获取到的数据
    } catch (error) {
        console.error("获取数据时发生错误:", error);
        // 在页面上显示错误信息
        // queryResultsDiv.innerHTML = `<p class="text-red-500 dark:text-red-400">获取数据失败: ${error.message}</p>`;
        return data; // 发生错误时返回空数组
    }
}

async function get_unpacked_list(filename) {

    try {
        const response = await fetch(`/api/unpackedlist?filename=${filename}`);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.json();
        return data; // 返回获取到的数据
    } catch (error) {
        console.error("获取数据时发生错误:", error);
        // 在页面上显示错误信息
        // queryResultsDiv.innerHTML = `<p class="text-red-500 dark:text-red-400">获取数据失败: ${error.message}</p>`;
        return data; // 发生错误时返回空数组
    }
}
