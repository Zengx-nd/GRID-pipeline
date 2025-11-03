const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 5500;

app.use(express.static(__dirname)); // 假设 index.html 和 style.css 在同一个目录下

app.get('/api/datlist', (req, res) => {
    const { payload } = req.query;

    const sshCommand = `ssh -i C:\\Users\\zeng-\\.ssh\\id_rsa zx21@166.111.32.56 -p 2222 "python /home/zx21/WEB_11B/test.py --operation='raw_dat' --payload=${payload}"`;
    
    exec(sshCommand, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            res.status(500).send(stderr);
            return;
        }
        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            res.send(stdout);
        }
    });
});

app.get('/api/unpacklog', (req, res) => {
    const {filename} = req.query

    const sshCommand = `ssh -i C:\\Users\\zeng-\\.ssh\\id_rsa zx21@166.111.32.56 -p 2222 "python /home/zx21/WEB_11B/test.py --operation='unpack_log' --unpacklogfile=${filename} "`;
    
    exec(sshCommand, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            res.status(500).send(stderr);
            return;
        }
        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            res.send(stdout);
        }
    });
});

app.get('/api/unpackedlist', (req, res) => {
    const {filename} = req.query

    const sshCommand = `ssh -i C:\\Users\\zeng-\\.ssh\\id_rsa zx21@166.111.32.56 -p 2222 "python /home/zx21/WEB_11B/test.py --operation='unpacked_list' --unpacklogfile=${filename} "`;
    console.log(filename)
    exec(sshCommand, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            res.status(500).send(stderr);
            return;
        }
        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            res.send(stdout);
        }
    });
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});