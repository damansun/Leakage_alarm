<?php
public function search(){
       $record=array();  //定义返回结果的数组
       $list = $this->search($this->keyword);//普通的根据关键词查询数据库的操作  代码就不用分享了
　　　　if(is_array($list)&&!empty($list)){
       foreach($list as $msg){
       	$record[]=array(
    //以下代码，将数据库中查询返回的数组格式化为微信返回消息能接收的数组形式，即title、description、picurl、url 详见微信官方的文档描述
                        'title' =>$msg['title'],
                        'description' =>$msg['discription'],
                        'picurl' => $msg['pic_url'],
                        'url' =>$msg['url']
                    );
       }
　　　　}
　　　　return $record;
}
?>