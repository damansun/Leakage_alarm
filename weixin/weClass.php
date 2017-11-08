<?php

class Weixin
{
    public $token = '';//token
    public $appid = '';
    public $appsecret = '';
    public $debug =  false;//debug mode
    public $setFlag = false;
    public $msgtype = 'text';   //('text','image','location')
    public $msg = array();
    public function __construct($token,$debug, $appid, $appsecret)
    {
        $this->token = $token;
        $this->debug = $debug;
        $this->appid = $appid;
        $this->appsecret = $appsecret;
    }
    //get user information
    public function getMsg()
    {
        $postStr = $GLOBALS["HTTP_RAW_POST_DATA"];
        if ($this->debug) {
            $this->write_log($postStr);
        }
        if (!empty($postStr)) {
            $this->msg = (array)simplexml_load_string($postStr, 'SimpleXMLElement', LIBXML_NOCDATA);
            $this->msgtype = strtolower($this->msg['MsgType']);
        }
    }
    public function makeText($text='')
    {
        $CreateTime = time();
        $FuncFlag = $this->setFlag ? 1 : 0;
        $textTpl = "<xml>
            <ToUserName><![CDATA[{$this->msg['FromUserName']}]]></ToUserName>
            <FromUserName><![CDATA[{$this->msg['ToUserName']}]]></FromUserName>
            <CreateTime>{$CreateTime}</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[%s]]></Content>
            <FuncFlag>%s</FuncFlag>
            </xml>";
        return sprintf($textTpl,$text,$FuncFlag);
    }
    //
    public function makeNews($newsData=array())
    {
        $CreateTime = time();
        $FuncFlag = $this->setFlag ? 1 : 0;
        $newTplHeader = "<xml>
            <ToUserName><![CDATA[{$this->msg['FromUserName']}]]></ToUserName>
            <FromUserName><![CDATA[{$this->msg['ToUserName']}]]></FromUserName>
            <CreateTime>{$CreateTime}</CreateTime>
            <MsgType><![CDATA[news]]></MsgType>
            <Content><![CDATA[%s]]></Content>
            <ArticleCount>%s</ArticleCount><Articles>";
        $newTplItem = "<item>
            <Title><![CDATA[%s]]></Title>
            <Description><![CDATA[%s]]></Description>
            <PicUrl><![CDATA[%s]]></PicUrl>
            <Url><![CDATA[%s]]></Url>
            </item>";
        $newTplFoot = "</Articles>
            <FuncFlag>%s</FuncFlag>
            </xml>";
        $Content = '';
        $itemsCount = count($newsData['items']);
        $itemsCount = $itemsCount < 10 ? $itemsCount : 10;//It is a limits which not over 10
        if ($itemsCount) {
            foreach ($newsData['items'] as $key => $item) {
                if ($key<=9) {
                    $Content .= sprintf($newTplItem,$item['title'],$item['description'],$item['picurl'],$item['url']);
                }
            }
        }
        $header = sprintf($newTplHeader,$newsData['content'],$itemsCount);
        $footer = sprintf($newTplFoot,$FuncFlag);
        return $header . $Content . $footer;
    }
    public function reply($data)
    {
        // [Coulson]: $this->getToken();
        if ($this->debug) {
            $this->write_log($data);
        }
        echo $data;
    }
    public function valid()
    {
        $echoStr = $_GET["echostr"];
        $this->write_log("Start verify ...");
        $result = $this->checkSignature();
        $this->write_log("result : ".$result);
        if ($result) {
            echo $echoStr;
            exit;
        }else{
            $this->write_log('Check signature failed, try again ...');
            exit;
        }
    }

    private function checkSignature()
    {
        $signature = $_GET["signature"];
        $timestamp = $_GET["timestamp"];
        $nonce = $_GET["nonce"];
        $tmpArr = array($this->token, $timestamp, $nonce);
        sort($tmpArr);
        $tmpStr = implode( $tmpArr );
        $tmpStr = sha1( $tmpStr );
        $this->write_log("tmpStr:".$tmpStr);
        $this->write_log("signature:".$signature);

        if( $tmpStr == $signature ){
            $this->write_log("true");
            return true;
        }else{
            $this->write_log("false");
            return false;
        }
    }

    public function sendMessage($openid, $nodeid, $sensorways, $status) {
        date_default_timezone_set('PRC'); 
        $time = date("Y-m-d H:i:s")."\r\n";
        $token = $this->getToken();
        $url="https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=".$token;
        $post_data = array(
            "touser"=>$openid,
            "template_id"=>"ybpEOTXZIrpup4efxzXTQgLHT0hnk-xRN5mJfYuRURs",
            "url"=>"http://www.brovantek.com",
            "data"=> array(
                    "NodeID" => array(
                            "value"=>$nodeid,
                            "color"=>"#173177"
                    ),
                    "SensorWays" => array(
                            "value"=>$sensorways,
                            "color"=>"#173177"
                    ),
                    "Status"=>array(
                            "value"=>$status,
                            "color"=>"#EA0000"
                    ),
                    "Time"=>array(
                            "value"=>$time,
                            "color"=>"#173177"
                    ),
            )
        );

        $post_data = json_encode($post_data);
        $data = $this->https_request($url, 1, $post_data);
        $this->write_log("errorcode : ".$data['errcode'].' erromsg : '.$data['errmsg'].' msgid : '.$data['msgid']);
        if ($data['errcode']=== 0) {
            $this->write_log('success');
            return $data;
        } else {
            $this->write_log('Something was broken, please contact administrator right now ... ');
        }
    }
    //获取模板信息-行业信息（参考，示例未使用）
/*[Coulson]>>>
    function getHangye(){
        //用户同意授权后，会传过来一个code
        $token = $this->get_token();
        $url = "https://api.weixin.qq.com/cgi-bin/template/get_industry?access_token=".$token;
        //请求token，get方式
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL,$url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER,1);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER,0);
        $data = curl_exec($ch);
        curl_close($ch);
        $data = json_decode($data,true); //将json数据转成数组
        //return $data["access_token"];
        return $data;
　　}
}
[Coulson]<<<*/

//推送模板信息给置业顾问
/*[Coulson]>>>
$send = new Oauth();　　//实例化类
$send->sendMessage($zhiyeguwen,$clientName,$tel,$product);　　//调用方法

[Coulson]<<<*/
    public function getToken(){
        $filename = "./access_token.json";
        $this->write_log("I am here");
        $file = file_get_contents($filename,true);
        $result = json_decode($file,true);
        if (time() > $result['expires']){
            $data = array();
            $data['access_token'] = $this->getNewToken($this->appid,$this->appsecret);
            $data['expires']=time()+7000;
            $jsonStr = json_encode($data);
            $fp = fopen($filename, "w");
            fwrite($fp, $jsonStr);
            fclose($fp);
            $this->write_log('access_token : '.$access_token);
            return $data['access_token'];
        }else{
            $this->write_log('That is not necessary, access_token has been stored in access_token.json');
            return $result['access_token'];
        }
    }

    private function getNewToken($appid,$appsecret){
        $url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$appid&secret=$appsecret";
        $access_token_Arr = $this->https_request($url);
        // [Coulson]: $this->write_log("expires_in : ".$jsoninfo['expires_in']);
        return $access_token_Arr['access_token'];
    }

    public function https_request ($url, $isPost = false, $post_data = NULL){
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_POST, $isPost);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);

        $output = curl_exec($ch);
        curl_close($ch);
        return json_decode($output,true);
    }
    
    public function write_log($log){
        //record debug log
        date_default_timezone_set('PRC');
        $filename = "wexinlog.txt";
        $content = date("Y-m-d H:i:s")."  ".$log."\r\n";
        if (filesize($filename) > 1024 * 1024 * 5) { //5Mb
            file_put_contents($filename, $content);
        } else {
            file_put_contents($filename, $content, FILE_APPEND);
        }
    }
}
?>