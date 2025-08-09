const express = require('express');
const multer  = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();

// Make sure 'uploads' folder exists
const uploadDir = path.join(__dirname, 'uploadFiles');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const storage = multer.diskStorage({
  destination: function (req, file, cb) { cb(null, uploadDir); },
  filename: function (req, file, cb) { cb(null, file.originalname); }
});
const upload = multer({ storage: storage });

app.post('/uploadFiles', upload.array('files[]', 100), (req, res) => {
  res.send('Files uploaded successfully!');
});

app.use(express.static(__dirname));

app.listen(5000, () => { console.log('Server running at http://localhost:5000'); });
