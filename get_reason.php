<?php
$kon = parse_ini_file('config.conf',true);

$host = $kon['smartcenter']['host'];
$user = $kon['smartcenter']['user'];
$pass = $kon['smartcenter']['pass'];
$dbnm = $kon['smartcenter']['dbnm'];

$con = mysqli_connect($host,$user,$pass,$dbnm);

if(isset($_GET['get_reason'])){
    $query = mysqli_query($con,"select*from reasons");
    $data=[];
    while($row = mysqli_fetch_assoc($query)){
        $data[]=array(
            'id'=>$row['reason_id'],
            'reason'=>$row['reason_desc']
        );
    }
    echo json_encode($data);
}

 ?>
