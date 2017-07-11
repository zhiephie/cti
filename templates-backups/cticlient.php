<script src="/static/underscore-min.js"></script>
<script src="/static/zepto.min.js"></script>

<script>
    //get url
    function gup(name) {
        url = document.URL;
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp(regexS);
        var results = regex.exec(url);
        
        return results == null ? null : results[1];
    }
        var  GetUrl  = document.URL;
        var  GetRoom = gup('room');
        var  GetUser = gup('nick');

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
                login(GetRoom); 
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

        function login(userid) { 
            send_text_msg('login', userid);
        }

        function login_agent(userid) {
            send_text_msg('login_agent', userid);
        }

        function logout(userid) {
            send_text_msg('logout', userid);
        }

        function readyx(userid) { 
            // alert(userid); 
            send_text_msg('ready', userid);
        }

        function notready(userid) { 
            // alert(userid);
            send_text_msg('notready', userid);
        }

        function makecall(userid) {
            send_text_msg('makecall', userid);
        }

        function hangup(userid) {
            send_text_msg('hangup', userid);
        }

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

        function send_text_msg(command, userid, after=1) {
            text_msg_obj = {
                "msgtype":"text",
                "payload": command,
                "userid" : userid,
                "after": after
            };
            jmsg = JSON.stringify(text_msg_obj);
            console.log(jmsg);
            ws.send(jmsg);
        };

        function receive_message(wsevent) {
           console.log("received message: "+wsevent.data )
            msg_obj = wsevent.data;
            var url = "http://"+window.location.host+"/static/";
            switch (msg_obj.msgtype) {
                    case "login"     : $("#msgList").html("AUX"); break
                    case "ready"     : $("#msgList").html("READY"); break
                    case "not ready" : $("#msgList").html("Not Ready"); break
                    case "makecall"  : $("#msgList").html("Make Call"); break
                    case "incomming" : $("#msgList").html("Incomming"); break
                    case "connected" : $("#msgList").html("Conntected"); break
                    case "disconnect" : $("#msgList").html("Disconnect"); break
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
<span class="info">status : </span>
<div style="background-color:red;" id="msgList"></div>
<a href="#" onclick="logout(GetRoom);">logout</a>
<a href="#" onclick="login(GetRoom);">login</a>
<a href="#" onclick="login_agent(GetRoom);">login agent</a>
<a href="#" onclick="readyx(GetRoom);">ready</a>
<a href="#" onclick="notready(GetRoom);">Not Ready</a>
<a href="#" onclick="makecall(GetRoom);">Make Call</a>
<!--<a href="#" onclick="hangup(GetRoom);">Hangup Call</a>-->