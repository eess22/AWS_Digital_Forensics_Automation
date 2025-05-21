<?php
$logUploadDir = "upload/info/";

$logFileName = $_FILES["logToUpload"]["name"];
$logFileTmpName = $_FILES["logToUpload"]["tmp_name"];

$logFileExtension = strtolower(pathinfo($logFileName, PATHINFO_EXTENSION));
$newLogFileName = uniqid() . "." . $logFileExtension;
$logUploadPath = $logUploadDir . $newLogFileName;

// 파일 이동
if (move_uploaded_file($logFileTmpName, $logUploadPath)) {
    echo "파일 업로드 성공: " . $newLogFileName;
} else {
    echo "파일 업로드 실패.";
}
?>
