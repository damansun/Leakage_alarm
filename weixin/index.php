<?php
/**
  * wechat php test
  */
header("Content-type: php; charset=utf-8");
include_once('weClass.php');
//define your token
define("TOKEN", "weixin");
define('DEBUG', true);
define('APPID', 'wx746f544f9eff0cf8');
define('APPSECRET', 'a1d9d4a3a1611d8b48f46221e0d6e05b');
$weixin = new Weixin(TOKEN, DEBUG, APPID, APPSECRET);//instance
// [Coulson]: $weixin->valid(); //Just for first verification.Please comment it after it is passed apply for Weinxin verification.
$weixin->getMsg();
$type = $weixin->msgtype;//msg type
$event = strtolower($weixin->msg['Event']);
$username = $weixin->msg['FromUserName'];
switch ($type) {
    case 'text':
        $keyword = $weixin->msg['Content'];
        if (!empty($keyword)) {
            //Save user info in user_list.json
            $filename = "./user_list.json";
            $file = file_get_contents($filename,true);
            $data = json_decode($file,true);
            if ($weixin->msg['Content']=== "博砚电子") {//TODO 换成正则表达式
                if ($data['openid']=== NULL){
                    $data['openid'] = array($username);
                } elseif (in_array($username, $data['openid'])){
                    $weixin->write_log('用户名已经存在');
                    $reply = $weixin->makeText("用户已存在， 请勿重复注册！");
                } else {
                    $reply = $weixin->makeText("欢迎关注博砚电子，您将收到系统推送！");
                    array_push($data['openid'],$username);
                }
                $jsonStr = json_encode($data);
                file_put_contents($filename, $jsonStr);
            } else {
                $reply = $weixin->makeText("Hello World!!!");
            }
        } else {
            echo "Input something ...";
        }
        break;
    case 'event':
        if ($event=== 'subscribe') {
            $reply = $weixin->makeText("欢迎来到广砚科技");
        } elseif ($event=== 'unsubscribe') {
            $reply = $weixin->makeText("广砚科技！");
        } elseif($event=== 'templatesendjobfinish') {
            if ($weixin->msg['Status']=== 'success') {
                $weixin->write_log('send msg successfully');
                return true;
            }
        }
        break;
    case 'zigbee':
        $filename = "./user_list.json";
        $file = file_get_contents($filename,true);
        $data = json_decode($file,true);
        //遍历发送到博砚电子的工作人员
        foreach ($data['openid'] as $d) {
            $weixin->write_log('userid : '.$d);
            $weixin->sendMessage($d, $weixin->msg['NodeId'], $weixin->msg['SensorWays'], $weixin->msg['Status']);
        }
        break;
    default:
        # code...
        break;
}

$weixin->reply($reply);

/*[Coulson]>>>
        include_once("search.php");//文本消息 调用查询程序
        $chaxun= new chaxun(DEBUG,$keyword,$username);
        $results['items'] =$chaxun->search();//查询的代码
        $reply = $weixin->makeNews($results);
[Coulson]<<<*/
/*[Coulson]>>>
}elseif ($type=== 'event') {
    if 
    $reply = $weixin->makeText('Welcome follow, great day for you');
}elseif ($type==='location') {

}elseif ($type==='image') {

}elseif ($type==='voice') {

}
[Coulson]<<<*/
?>


