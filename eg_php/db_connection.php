<?php
# FileName="Connection_php_mysql.htm"
# Type="MYSQL"
# HTTP="true"
//********************************** A modifier sites test et exploitation
$hostname_db = "localhost";
$username_db = "root";
$password_db = "root";
$db_connection = mysql_connect($hostname_db, $username_db, $password_db) or trigger_error(mysql_error(),E_USER_ERROR); 

?>
