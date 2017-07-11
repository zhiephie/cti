
 <script src="../static/underscore-min.js"></script>
 <script src="../static/zepto.min.js"></script>
 <script src="../static/jquery-1.10.2.min.js"></script>
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


      setTimeout(function(){
        var id=ambilCookie('cookie_id');
        var nm =ambilCookie('cookie_nm');
        var ext = ambilCookie('ext_number');
        var vdn = ambilCookie('vdn_group');
        var start = ambilCookie('start');
        if (id && (parseInt(id.length) > 0 && parseInt(nm.length) > 0) && start) {
            if(id.length<1){var id='0';var nm='login';}
            window.location = '/?room='+id+'&nick='+nm+'&ext='+ext+"&vdngroup="+vdn
        }
      },1000);

    // setTimeout(function(){
    //     send_text_msg('login', GetRoom);
    // })
    </script>
Waiting for login cti...
