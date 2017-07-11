<script src="../static/underscore-min.js"></script>
<script src="../static/zepto.min.js"></script>

<script>
    //get url
    var createCookie = function(name, value, days) {
        var expires;
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toGMTString();
        }
        else {
            expires = "";
        }
        document.cookie = name + "=" + value + expires + "; path=/";
    }
    function gup(name) {
        url = document.URL;
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp(regexS);
        var results = regex.exec(url);

        return results == null ? null : results[1];
    }
        var  GetUrl  = document.URL;
        // var  GetRoom = gup('room');
        // var  GetUser = gup('nick');
        var  GetRoom = '1';
        var  GetUser = '202';

        // Check if typeof Zepto is "undefined"
        if((typeof Zepto !== "undefined") && ($ == null)) {
             $ = Zepto
        }

        // START WS
        var MAX_MSGS = 500;
        var ws;

        function ws_support() {
            ws = 'WebSocket' in window || 'MozWebSocket' in window;
            if (typeof(ws) == "undefined") { ws = false; }
            return ws;
        }

        if (!ws_support()) {
            window.location = "/drop";
        }

        $(function($){
            init_ws();
            window.onbeforeunload = function(e) {
                ws.close();
            };
        })

        function init_ws() {
            var url;
            url = "ws://"+window.location.host+ "/ws";
            ws = new WebSocket(url);

            ws.onopen  = function(event)  {
                // login(GetRoom);
                console.log("Socket opened");
                deleteCookie("ftc_cid")
            }
            ws.onclose = function() {
                console.log("WebSocket closed.");
            }
            ws.onerror = function(event) {
                console.log("ERROR opening WebSocket.");
                $('body').html("<h1>ERROR connecting to chat server</h1>");
            }
            ws.onmessage = receive_message;
        };


        function ready(fn) {
            if (document.readyState != 'loading') {
                fn();
            } else if (document.addEventListener) {
                document.addEventListener('DOMContentLoaded', fn);
            } else {
                document.attachEvent('onreadystatechange', function() {
                   if (document.readyState != 'loading')
                      fn();
                });
            }
        }

        function send_text_msg(command, userid,after=1,call='',busy=0,ring='') {
            text_msg_obj = {
                "msgtype": "text",
                "payload": command,
                "userid" : userid,
                "after"  : after,
                "callno" : call,
                "busy"   : busy,
                "ring"   : ring
            };
            jmsg = JSON.stringify(text_msg_obj);
            // console.log(jmsg);
            ws.send(jmsg);
        };

        var createCookie = function(name, value, days) {
            var expires;
            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = "; expires=" + date.toGMTString();
            }
            else {
                expires = "";
            }
            document.cookie = name + "=" + value + expires + "; path=/";
        }
        function ambilcookie(cname) {
            var name = cname + "=";
            var decodedCookie = decodeURIComponent(document.cookie);
            var ca = decodedCookie.split(';');
            for(var i = 0; i <ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) == ' ') {
                    c = c.substring(1);
                }
                if (c.indexOf(name) == 0) {
                    return c.substring(name.length, c.length);
                }
            }
            return "";
        }
        function deleteAllCookies(x) {
            for (var i = 0; i < x.length; i++) {
                var cookie = x[i];
                document.cookie = cookie + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;";
            }
        }

        function receive_message(wsevent) {
           console.log("received message: "+wsevent.data )
            msg_obj = wsevent.data;
            var url = "http://"+window.location.host+"/static/";

            var data=wsevent.data.split(';');
            if(data[1] ==121){
                createCookie('listen','yes',1);
                createCookie('after_status','login',1);
                createCookie('status_reason','Connected',1);
                console.log('Connected to cti server...');
            }
            // call order agent
            if (data[1] ==230){
                var sibuk=ambilcookie('sibuk');
                send_text_msg('busy', GetRoom,'','',data[5],'offered');
                createCookie('order','yes',1);
                createCookie('after_status','order',1);
                createCookie('start','yes',1);
                createCookie('caller_id',data[5],1);
                createCookie('timerbusy','start',1);
                createCookie('timerring','start',1);
                createCookie('acd','no',1);
                if(document.cookie.indexOf("sibuk=") <= 0){
                    createCookie('sibuk','yes',1);
                }else if(sibuk==='no'){
                    createCookie('sibuk','yes',1);
                }
                console.log('Incoming call...');
            }
            // close phone call
            if (data[1] ==226){
                send_text_msg('busy', GetRoom,'','',0,'retrieve');
                console.log('retrieve call...');
            }

            if (data[1] ==229){
                send_text_msg('busy', GetRoom,'','',0,'init');
            }
            // login agent pabx
            if (data[1] ==210){
                createCookie('after_status','loginagent',1);
                createCookie('status_reason','Login',1);
            }
            // hangup phone call
            if (data[1] ==201){
                var reason=ambilcookie('status_reason');
                createCookie('after_status','hangup',1);
                createCookie('sibuk','no',1);
                if(reason ==='melengkapi order'){
                    createCookie('status_reason','ready',1);
                }
                createCookie('start','yes',1);
            }
            // logout agent pabx
            if (data[1] ==124){
                createCookie('after_status','logoutagent',1);
                createCookie('start','yes',1);
            }

            if (data[1] ==211){
                createCookie('after_status','logoutagent',1);
                console.log('logout agent...');
            }
            if (data[1] ==231){
                send_text_msg('busy',GetRoom,'','',0,'originated');
                console.log('transfer call initiate...');
            }
            // answer call
            if (data[1] ==205){
                createCookie('after_status','answer',1);
                console.log('answered call...');
            }
            // do agent aux
            if (data[1] ==213){
                createCookie('after_status','aux',1);
                console.log('request aux status...');
            }
            // hold call
            if (data[1] ==225){
                send_text_msg('busy', GetRoom,'','',0,'hold');
                createCookie('status_reason','hold',1);
                console.log('agent hold call...');
            }
            if (data[1] ==232){
        				var busy=0;
        				var talk=0;
                var agen = ambilcookie('cookie_id');
                var busy = ambilcookie("busy_time_"+agen);
                var talk = ambilcookie("talk_time_"+agen);
                var acd  = ambilcookie('acd');
                createCookie('sibuk','no',1);

                if(acd === "no"){
                    send_text_msg('busy', GetRoom,'','',1,'abd');
                    console.log('abandoned call...');
                }else{
                    send_text_msg('busy', GetRoom,'','',1,'acd');
                    console.log('acd call...');
                }
                setTimeout(function(){
                    if(parseInt(busy)<1){var busy=0;}if(parseInt(talk)<1){var talk=0;}
                    send_text_msg('busy', GetRoom,'','',busy,'busy');
                    send_text_msg('busy', GetRoom,'','',talk,'talk');
                },200)
                send_text_msg('busy',GetRoom,'','',0,'disconnect');
                createCookie('after_status','hangup',1);
                createCookie('status_reason','ready',1);
                createCookie('timertalk','stop',1);
                createCookie('timerbusy','stop',1);
                createCookie('start','yes',1);
                console.log('disconencted call...');
            }
            if (data[1] ==228){
				        var ring=0;
                createCookie('acd','yes',1);
                createCookie('timerring','stop',1)
                createCookie('timertalk','start',1)
                var agen = ambilcookie('cookie_id');
                var ring = ambilcookie("ring_time_"+agen);

                console.log('ring='+ring);
                setTimeout(function(){
                    if(parseInt(ring)<1){var ring=0;}
                    send_text_msg('busy', GetRoom,'','',ring,'ring');
                },200)
                createCookie('after_status','answer',1);
            }
            if (data[1] ==212){
                createCookie('after_status','ready',1);
                createCookie('status_reason','ready',1);
            }
        }


        function getCookie(name){
            var pattern = RegExp(name + "=.[^;]*")
            matched = document.cookie.match(pattern)
            if(matched){
                var cookie = matched[0].split('=')
                return cookie[1]
            }
            return false
        }

        function deleteCookie(name, path, domain) {
            if (getCookie(name)) document.cookie = name + "=" +
                ((path) ? ";path=" + path : "") +
                ((domain) ? ";domain=" + domain : "" ) +
                ";expires=Thu, 01-Jan-1970 00:00:01 GMT";
        }

</script>
<style>
body{padding:0;margin:0;width:0;height:0;overflow: hidden;}
#call_list button{
    border:0;color:#fff;width:120px;height:35px;cursor:pointer;display: inline-block;margin-bottom:5px
}
#call_list #loginagent{background: #2a9c95;}
#call_list #ready{background: #19bad1;}
#call_list #makecall{background: #2a821f;}
#call_list #login:hover{background: #2fb6ae;}
#call_list #ready:hover{background: #53cbdd;}
#call_list #makecall:hover{background: #3fb330;}
#call_list_dv {width:100%;height:100%;background: #fff;position: absolute;top:0;left:0;z-index:99999}
</style>

<div class="col-sm-12" id="call_list">
  <div id="status"></div>
  <!-- <button class="btn btn-sm btn-danger" id="logins" onclick="parent.tes()">Login</button> -->
  <button class="btn btn-sm btn-danger" id="loginagent">Login Agent</button>
  <button class="btn btn-sm btn-danger" id="ready">Ready</button><span></span>
  <button class="btn btn-sm btn-danger" id="makecall">Make Call</button>
</div>
<input type="hidden" id="afterstatus" value=""/>
<script>


function ambilCookie(c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) {
                c_end = document.cookie.length;
            }
            return unescape(document.cookie.substring(c_start, c_end));
        }
    }
    return "";
}
// $("#afterstatus").val(ambilCookie('after_status'));

setInterval(function(){
  var cook=ambilCookie('after_status');
  var after=$("#afterstatus").val();
  var starts = ambilCookie('start');
  var reason = ambilCookie('status_reason');
  var hard = ambilCookie('hard');
  // if already login agent
  if(reason === 'login' && starts ==='yes'){
    if(cook !== after){
      send_text_msg('loginagent', GetRoom);
      $("#afterstatus").val('loginagent');
      createCookie('start','no',1);
      createCookie('after_status','',1);
    }
  }
  // if logout agent
  if(cook === 'logoutagent' && starts ==='yes'){
    if(cook !== after){
      send_text_msg('logout', GetRoom);
      createCookie('start','no',1);
      createCookie('after_status','',1);
    }
  }
  // if already ready status
  if(cook === 'ready' && starts ==='yes'){
    if(cook !== after){
      send_text_msg('ready', GetRoom);
      $("#afterstatus").val('ready');
      createCookie('start','no',1);
      createCookie('after_status','notready',1);
    }
  }
  if(cook === 'notready' && starts ==='yes'){
    if(cook !== after){
      var aux=ambilcookie('status_aux');
      send_text_msg('notready', GetRoom,aux);
      setTimeout(function(){
          send_text_msg('busy', GetRoom,'','',aux,'aux');
      })
      $("#afterstatus").val('notready');
      createCookie('start','no',1);
      createCookie('after_status','ready',1);
    }
  }
  // if makecall status
  // var makecal=false;
  if(cook === 'makecall' && starts ==='yes'){
    var phone = ambilcookie('phone');
    var after = ambilcookie('afterstatus');
    if(cook !== after && 'null'){
      // makecall=true;
      send_text_msg('makecall', GetRoom,after,phone);
      $("#afterstatus").val('makecall');
      createCookie('phone','',1);
      createCookie('start','no',1);
      createCookie('after_status','ready',1);
    }
  }

  if(cook === 'answer' && starts ==='yes'){
      send_text_msg('answer', GetRoom);
      createCookie('start','no',1);
      createCookie('after_status','hangup',1);
  }

  if(cook === 'hangup' && starts ==='yes'){
      send_text_msg('hangup', GetRoom);
      createCookie('start','no',1);
      createCookie('status_reason','hangup call',1);
      createCookie('after_status','loginagent',1);
  }

},1000)
setTimeout(function(){
  send_text_msg('login', GetRoom);
  var start=ambilcookie('start');
  var cook=ambilcookie('after_status');
  var reason = ambilcookie('status_reason');
  if(cook ==='loginagent' && (start ==='no' || start ==='yes')){setTimeout(function(){send_text_msg('loginagent', GetRoom);createCookie('status_aux','aux',1);},500)}
  if(cook ==='logoutagent'){createCookie('after_status','login',1);}
  if(cook ==='ready' || cook==='order' || reason ==='ready'){setTimeout(function(){send_text_msg('loginagent', GetRoom);setTimeout(function(){send_text_msg('ready', GetRoom);},500)},500);createCookie('after_status','ready',1);}
  if(cook ==='notready' || reason==='login'){setTimeout(function(){send_text_msg('loginagent', GetRoom);setTimeout(function(){send_text_msg('notready', GetRoom);},500)},500);}
  if(cook ==='aux'){setTimeout(function(){send_text_msg('loginagent', GetRoom);setTimeout(function(){var aux=ambilcookie('status_aux');send_text_msg('notready', GetRoom,aux);},500)},500);}
  if(cook ==='hangup'){setTimeout(function(){send_text_msg('loginagent', GetRoom);setTimeout(function(){send_text_msg('ready', GetRoom);},500)},500);}
  // createCookie('after_status','login',1);
},1000);
</script>
