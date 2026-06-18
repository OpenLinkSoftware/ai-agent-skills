<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, shrink-to-fit=no">

!!{use_opal_widget}
<script src="//code.jquery.com/jquery-3.7.0.min.js"></script>
<link href="//cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="//cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.11/clipboard.min.js"></script>
!!.

<link rel="describes" href="%{card_ident_url}" title="Describes" />
<link rev="describedby" href="%{card_ident_url}" title="Described By" />

<link rel="related" href="%{cert_url}" title="Related Document" type="text/turtle" />
<link rel="related" href="%{card_url}" title="Related Document"  type="text/html" />
<link rel="related" href="%{jsonld_prof_url}" title="Related Document" type="application/json+ld" />
<link rel="http://xmlns.com/foaf/0.1/primaryTopic" href="%{rdfa_prof_url}#identity" title="This Document's Primary Topic" />
!{pdp_url_head}
<!-- RelMeAuth Relations Start -->
!!{rel_header_html}
%{rel_header_html}
<!-- RelMeAuth Relations End -->
!!.

!!{em_indie_idp}
<!-- IndieAuth Relations Start -->
<!-- URIBurner IdP -->
<link rel="indieauth-metadata" href="%{em_indie_idp}/indieauth/indieauth_metadata">
<link rel="authorization_endpoint" href="%{em_indie_idp}/indieauth/indieauth_authorize">
<link rel="token_endpoint" href="%{em_indie_idp}/indieauth/indieauth_token">
<!-- IndieAuth Relations End -->
!!.

!!{pim_storage}
<link rel="http://www.w3.org/ns/pim/space#storage" href="%{pim_storage}" title="Default (Preferred) Storage Location (Address)" />
!!.

<link rel="alternate" href="%{jsonld_prof_url}" title="Identity Card (JSON-LD Format)" type="application/json+ld" />
<link rel="alternate" href="vcard.vcf" title="Identity Card (vCard Format)" type="text/vcard" />
<link rel="alternate" href="%{pubkey_pem_url}" title="Identity Card (PKIX X.509 Certificate Format)" type="application/x-x509-ca-cert" />
!{ca_cert_url} <link rel="alternate" href="%{ca_cert_url}" title="Issuer Public Key (PKIX X.509 Certificate Format)" type="application/x-x509-ca-cert" />

<title>Profile RDFa for %{subj_name}</title>

<link href="style.css" rel="stylesheet" type="text/css">
!!{use_opal_widget}
<link href="style_opal.css" rel="stylesheet" type="text/css">
!!.

<script type="text/javascript" src="./qrcode.js"></script>

</head>
<body>

        <div class="xcard cardWrapper">
        
          <div class="xcard cardHeader border">
            <h1>Your Web-Scale Verifiable Digital Identity Card</h1>
          </div><!-- end cardHeader -->
            
          <div class="cardBody">

            <div>
              <div class="xcard">
                <img src="%{photo_url}" class="cardPic" alt="User Photo">
              </div><!-- end cardPic -->
!!{relList_html}
              <div class="rel_block">
%{relList_html}
              </div>
!!.
            </div>
            <div class="cardDetails">
                      <p class="xcard fieldName">Common Name</p>
                      <p class="xcard fieldContent"><a href="%{webid}">%{subj_name}</a></p>
                   
                      <p class="xcard fieldName">Organization</p>
                      <p class="xcard fieldContent">%{subj_org}</p>
                    
                      <p class="xcard fieldName">Country</p>
                      <p class="xcard fieldContent">%{subj_country}</p>
                    
                      <p class="xcard fieldName">State/Province</p>
                      <p class="xcard fieldContent">%{subj_state}</p>
                   
                      <p class="xcard fieldName">Email Address</p>
                      <p class="xcard fieldContent">%{subj_email_mailto_href}</p>
!!{pdp_url}
                      <p class="xcard fieldName">Web Page</p>
                      <p class="xcard fieldContent"><a href="%{pdp_url}">%{pdp_url}</a></p>
!!.
                      <p class="xcard fieldName">Issued</p>
                      <p class="xcard fieldContent">%{date_before}</p>
                        
                      <p class="xcard fieldName">Expiry</p>
                      <p class="xcard fieldContent">%{date_after}</p>
            </div>

            <div class="xcard cardQr">
                	%{qr_card_img}
            </div>
            <!-- end cardQr -->

          </div>

          <div class="cardBottom">
                 <div class="xcard cardYouIdIcn">
                	<a class="aimg" href="http://youid.openlinksw.com"><img src="youid_logo-35px.png" width="35" height="30" alt="YouID"></a>
                	<a href="http://youid.openlinksw.com">Get&nbsp;Your&nbsp;ID&nbsp;Card</a>
                 </div><!-- end cardYouIdIcn -->

                 <div class="xcard vCard">
                	<a class="aimg" href="vcard.vcf"><img src="addrbook.png" width="32" height="34" alt="Add to Contacts"></a>
                	<a href="vcard.vcf">Add&nbsp;to&nbsp;Contacts</a>
                 </div><!-- end vCard -->

                 <div class="xcard pKey">
                	<a class="aimg" href="%{pubkey_pem_url}"><img src="lock.png" width="38" height="38" alr="Certificate (.pem)"></a>
                	<a href="%{pubkey_pem_url}">Certificate&nbsp;(.pem)</a>
                	<a href="%{pubkey_der_url}">Certificate&nbsp;(.crt)</a>
                 </div><!-- end pKey -->

!!{ca_cert_url}
                 <div class="xcard caKey">
                    <a class="aimg" href="%{ca_cert_url}"><img src="lock.png" width="38" height="38" alt="CA Certificate (.pem)"></a>
                    <a href="%{ca_cert_url}">CA&nbsp;Certificate&nbsp;(.pem)</a>
                 </div>
!!.
!!{use_opal_widget}
                 <div class="xcard agent open-button">
                    <a class="aimg open-button" href="javascript:void(0)"><img src="chatbot-32px.png" width="32" height="32" alt="AI Agent"></a>
                    <a class="open-button" href="javascript:void(0)">AI&nbsp;Agent</a>
                 </div>
!!.
          </div>
          <!-- end cardBottom -->
        
        </div><!-- end cardWrapper -->

<!-- rdfa -->
%{rdfa}
<!-- end rdfa -->

<!-- profile turtles -->
<!-- end profile turtles -->

<!-- profile json_ld -->
<script type="application/ld+json">
%{json_ld}
</script> 
<!-- end profile json_ld -->

<script>
(function () {

  function create_qrcode(text) 
  {
    var errorCorrectionLevel = 'M';
    var typeNumber = 12;
    qrcode.stringToBytes = qrcode.stringToBytesFuncs['default'];

    var qr = qrcode(typeNumber, errorCorrectionLevel);
    qr.addData(text, 'Byte');
    qr.make();

    return qr.createImgTag(2, 2, 'QR code');
  }


  document.addEventListener('DOMContentLoaded', 
    function()
    {
       var el = document.querySelector('.cardQr');
       if (el)
         el.innerHTML = create_qrcode(location.href);
    });

})();
</script>


!!{use_opalx}
<!-- OPALX -->

<div id="snackbar">
    <div id="msg"></div>
</div>


<div class="image-upload-template">
    <div class="user-image">
        <div class="user-img-zoom-in"><img src="svg/zoom-in.svg"/></div>
        <div class="user-img-zoom-out"><img src="svg/zoom-out.svg"/></div>
        <img src="" class="user-img-src"/>
        <div class="user-img-remove"><img src="svg/x-circle.svg"/></div>
    </div>
</div>

<textarea id="clipboard-text"></textarea>
<div class="chat-popup" id="opal-form">
  <div class="form-container">
    <div class="form-header">
      <div class="form-header-title">
        <h1>Talk with OPAL</h1>
        <span id="info" style="margin-left:10px; color:yellow; display:none">Connecting</span>
      </div>
      <div class="form-header-btn">
        <span type="button" title="Copy" class="header-btn clipboard-btn" data-clipboard-target="#clipboard-text"><img src="svg/clipboard.svg"/></span>
        <span type="button" title="Share" class="header-btn share-btn"><img src="svg/paperclip.svg"/></span>
!{use_oauth}        <span class="header-btn loggedin-btn"> <a data-placement="bottom" target="_blank" href="" title=""><img id="uid-icon" src="svg/person-fill-check.svg"></a></span>
!{use_oauth}        <button type="button" title="Logout" id="logoutID" class="d-none btn log-btn"><img src="logout.svg"/></button>
!{use_oauth}        <button type="button" title="Login" id="loginID" class="d-none btn log-btn"><img src="login.svg"/></button>
        <span type="button" title="Close" class="header-btn close-btn"><img src="svg/x-circle.svg"/></span>
      </div>
    </div>
    <div class="messages">
      <div class="questions">
!{w_prompt1}        <button type="button" class="prompt">%{w_prompt1}</button>
!{w_prompt2}        <button type="button" class="prompt">%{w_prompt2}</button>
!{w_prompt3}        <button type="button" class="prompt">%{w_prompt3}</button>
!{w_prompt4}        <button type="button" class="prompt">%{w_prompt4}</button>
      </div>
    </div>
    <div class="input_wrapper">
      <div style="flex:1">
        <label id="assistant-id"></label>
        <textarea placeholder="Type message.." id="message_input" required></textarea>
        <div id="suggestions"></div>
      </div>
      <div class="input_btns">
        <input type="file" style="display:none;" multiple id="img-upload"/>
        <button type="button" id="image-upload" class="image-btn"><img src="svg/paperclip.svg"/></span></button>
        <button type="button" class="send"><img src="svg/send.svg"/></button>
        <button type="button" class="stop d-none"><img src="svg/dash-circle.svg"/></button>
      </div>
    </div>
  </div>
  <div style="display:flex; flex-direction:row-reverse;">
    <img class="resizer" src="data:image/gif;base64,R0lGODlhCgAKAJEAAAAAAP///6CgpP///yH5BAEAAAMALAAAAAAKAAoAAAIRnI+JosbN3hryRDqvxfp2zhUAOw==" alt="Resize" width="15" height="15"/>
  </div>
</div>


<!-- these two have to be included in order Opal() to work, the rest about jQuery/Bootstrap/design is deveoper choice -->
!{use_bearer}<script src="auth.js"></script>
!{use_oauth}<script src="solid-client-authn.bundle.js"></script>
<script src="opalx.js"></script>
<script src="win.js"></script>
<script>
const md = window.markdownit({
                               html:true,
                               breaks:true,
                               linkify:true,
                               langPrefix:'language-',
                               quotes: '“”‘’',
    });

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const hrefIndex = tokens[idx].attrIndex('href');
  const href = hrefIndex >= 0 ? tokens[idx].attrs[hrefIndex][1] : '';

  if (href && href.startsWith('#')) {
    return self.renderToken(tokens, idx, options);
  }

  const targetIndex = tokens[idx].attrIndex('target');
  if (targetIndex < 0) tokens[idx].attrPush(['target', '_blank']);
  else tokens[idx].attrs[targetIndex][1] = '_blank';

  const relIndex = tokens[idx].attrIndex('rel');
  if (relIndex < 0) tokens[idx].attrPush(['rel', 'noopener noreferrer']);
  else tokens[idx].attrs[relIndex][1] = 'noopener noreferrer';

  return self.renderToken(tokens, idx, options);
};


var clipboard = new ClipboardJS('.clipboard-btn');

async function showInfo (text) {
    const tm = 3000;
    $('#msg').html(text);
    $('#snackbar').show();
    setTimeout(function () {  $('#snackbar').hide(); }, tm);
}

async function showNotice (text) {
    const tm = 3000;
    $('#info').html(text);
    $('#info').show();
    setTimeout(function () {  $('#info').hide(); }, tm);
}

clipboard.on('success', (e) => {
  showNotice('Copied.')
})

$(function () {

    const baseUrl = "%{w_opl_endpoint}";
    const hostname = new URL(baseUrl).hostname;
    // OIDC client variable
!{use_oauth}    var authClient = solidClientAuthentication.default;
!{use_bearer}    var authClient = new AuthClient('%{w_opl_api_key}');
    var session = authClient.getDefaultSession();
    // OPAL interface, params: OIDC client var, backend host&port, callbacks for incoming message and error callback 
    // if callbacks not given behaviour is not defined
    var opal = new OpalX(authClient, hostname, receiveMessage, errorHandler, {
!{w_model}        model: '%{w_model}', // next three are to calibrate model, look at OpenAI docs.
!{w_funcs}        functions: [%{w_funcs}], // backend registered functions, can be added unless not given otherwise via module
        top_p: %{w_top_p},
        temperature: %{w_temperature},
        assistant: '%{w_assistant}' // assistant to use
    });
    var $currentMessage = undefined; // keep DOM element of the receiving message as it coming on chunks
    var currentText = undefined;
    var $messages = $('.messages'); // the messages list, shortcut

    function receiveMessage(role, chunk) { // this is a handler see above Opal() to draw incoming messages
        if (role === 'function' || role === 'tool' || role === 'function_response' || role === 'info' || role === 'message_id') {
            // in this demo we do not print functions & response from them
            return;
        }
       if (role === 'notice') {
           showNotice (chunk);
           return;
       }
       if (chunk === '[DONE]' || chunk === '[LENGTH]') { // standart markers of backend when stops sending data 
          $currentMessage = undefined;
           currentText = undefined;
           $messages.find('.cursor').remove();
           $('.stop').toggleClass('d-none', true);
           $('.send').toggleClass('d-none', false);
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           // optionally we can enable the predefined prompts here
           $('.prompt').on ('click', sendPredefinedPrompt);
       } else if (!$currentMessage) { // this is first chunk of the answer
           currentText = chunk;
           $currentMessage = $('<div class="agent-message"></div>');
           $currentMessage.html(md.render(currentText));
           $messages.append($currentMessage);
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           $('<span class="cursor"></span>').insertAfter($currentMessage);
           $('.stop').toggleClass('d-none', false);
           $('.send').toggleClass('d-none', true);
           $('#clipboard-text').val($('#clipboard-text').val() + '\nassistant: ' + chunk);
       } else { // next chunk
           currentText = currentText + chunk;
           currentText = currentText.replace(/【[0-9:]+†[\w+\.-]+】/g, '');
           $currentMessage.html(md.render(currentText));
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           $('#clipboard-text').val($('#clipboard-text').val()+chunk);
       }
    }

    function errorHandler (error) { // error handler, called by Opal() if something f goes wrong
        let $message = $('<div class="agent-message">'+error+'</div>');
        $messages.append($message);
    }

    $('.open-button').on('click', function(e) {  // to open chat popup 
        $('.open-button').hide();
        $('#opal-form').fadeIn();
    });
    $('.close-btn').on('click', function(e) { // self evident
        $('#opal-form').hide();
        $('.open-button').show();
    });

    $('.share-btn').on('click', function () { opal.share(); });

    $('#message_input').keypress(function (e) { // enter or shift + enter 
        if (!e.shiftKey && e.which === 13) {
            let text = $('#message_input').val().trim();
            e.preventDefault();
            sendPrompt(text);
        }
    });

    $('.stop').on('click', function(e) {
        opal.stop();
     });
    $('.send').on('click', function(e) { // see above, doing same thing
        let $messages = $('.chat-popup .messages');
        let text = $('#message_input').val().trim();
        sendPrompt(text);
     });

    // simple wait function to allow socket to connect etc.
    async function waitConnect() {
        while (!opal.thread_id) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

     // wrapper to draw message and call OPAL widget
     async function sendPrompt (text) {
        if (text.length) {
            if (!session.info.isLoggedIn) {
                localStorage.setItem('prompt0', text);
                $messages.append ($(`<div class="user-message"><pre style="color:red">You need to Login</pre></div>`));
                await sleep(300);
                $('#loginID').click();
                return;
            }
        }
        if (text.length && !opal.thread_id) {
            opal.connect(); // open a WebSocket and init session
            // however bind() the onOpen can't be detected synchronously, so we need to wait on timeout
            await waitConnect();
            $('.stop').on ('click', function () { opal.stop(); });
        }
        if (text.length) {
            $messages.append ($(`<div class="user-message"><p>${text}</p></div>`));
            $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
            $('.prompt').off();
            await opal.send (text);
            $('.questions').hide();
            $('#message_input').val('');
            $('#clipboard-text').val($('#clipboard-text').val() + '\nuser: ' + text);
        }
     }

    // wrapper to handle predefined prompts
    async function sendPredefinedPrompt(e) {
        let text = e.target.innerHTML;
        if ($('.open-button:visible').length > 0) {
            $('.open-button').hide();
            $('#opal-form').fadeIn();
        }
        // disable the predefined promps, can enable once this one complete
        sendPrompt (text);
    }


    $('.image-btn').on('click', function(){ $('#img-upload').trigger('click'); });

    $('#img-upload').on('change', function(e) {
        var $messages = $(".messages");
        for (const file of e.currentTarget.files) {
            let imgURL = URL.createObjectURL(file);
            let $div = $($('.image-upload-template').clone().html());
            let $img = $div.find('.user-img-src');

            $img.on('load', async function () {
                const r = await fetch($(this).attr('src'));
                const blob = await r.blob();
                const file_id = await opal.addFile(file.name, file.type, blob, file.type.startsWith('image/') ? 'vision' : 'assistants');
                $(this).attr('id', file_id);
            });

            $img.attr("src", imgURL);

            $div.find('.user-img-remove').on('click', function (e) {
                const file_id = $($div).find('.user-img-src').attr('id');
                opal.deleteFile(file_id).then(() => { $($div).remove(); });
            });

            if (file?.type.startsWith('image/')) {
                $div.find('.user-img-zoom-in').on('click', function (e) {
                    let $img = $(this).siblings('.user-img-src');
                    let height = $img.height();
                    height += 50;
                    if (height >= 480) return;
                    $img.height(height);
                });

                $div.find('.user-img-zoom-out').on('click', function (e) {
                    let $img = $(this).siblings('.user-img-src');
                    let height = $img.height();
                    height -= 50;
                    if (height <= 120) return;
                    $img.height(height);
                });
            }

            $div.show();
            $messages.append($div);
        }
        $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
        $('#img-upload').val('');
    });

    /* Assistant suggestions */
    var assistants = [];
    opal.loadAssistants().then(() => { assistants = opal.getAssistants() });
    var $suggestions = $('#suggestions').hide();

    $suggestions.on('click', '.autocomplete-suggestion', function() {
        let $mentionInput = $('#message_input');
        let selectedAssistant = $(this).text();
        let text = $mentionInput.val();
        let caretPos = $mentionInput[0].selectionStart;
        let beforeCaret = text.substring(0, caretPos).replace(/@\w*$/, '@' + selectedAssistant + ' ');
        let afterCaret = text.substring(caretPos);
        opal.setAssistant($(this).attr('data-assist-id'));
        $mentionInput.val(afterCaret);
        $('#assistant-id').text(beforeCaret).show();
        $mentionInput.css('text-indent', Math.round($('#assistant-id').width()) + 15);
        $mentionInput.focus();
        $suggestions.hide();
    });

    $(document).click(function(e) {
        if (!$(e.target).closest('#suggestions').length) {
            $suggestions.hide();
        }
    });

    function selectSuggestion(direction) {
        let $options = $suggestions.find('.autocomplete-suggestion');
        let $selected = $options.filter('.selected');
        let index = $options.index($selected);


        if (40 == direction) {
            index = (index + 1) % $options.length;
        } else if (38 == direction) {
            index = (index - 1 + $options.length) % $options.length;
        }
        $options.removeClass('selected');
        $options.eq(index).addClass('selected');

        let selectedOption = $options.eq(index)[0];
        let popupHeight = $suggestions.height();
        let popupScrollTop = $suggestions.scrollTop();
        let optionTop = selectedOption.offsetTop;
        let optionHeight = selectedOption.offsetHeight;

        if (optionTop < popupScrollTop) {
            $suggestions.scrollTop(optionTop);
        } else if (optionTop + optionHeight > popupScrollTop + popupHeight) {
            $suggestions.scrollTop(optionTop + optionHeight - popupHeight);
        }
    }

    $('#message_input').on('keydown', function(e) {
        if ($suggestions.is(':visible')) {
            if (38 == e.keyCode || 40 == e.keyCode) {
                selectSuggestion(e.keyCode);
                e.preventDefault();
            } else if (13 == e.keyCode) {
                $('#suggestions .autocomplete-suggestion.selected').trigger('click');
                e.preventDefault();
            } else if (27 == e.keyCode) {
                $suggestions.hide();
            }
        }
    });

    $('#message_input').on('keyup', function(e) {
        if ($suggestions.is(':visible') && (38 == e.keyCode || 40 == e.keyCode || 13 == e.keyCode || 27 == e.keyCode)) {
            e.preventDefault();
            return;
        }
        let caretPos = this.selectionStart;
        let $mentionInput = $('#message_input');
        let text = this.value.trim();
        if (text.split(/\s+/).length === 1 && text.match(/^@\w*$/)) {
            let query = text.substring(1).toLowerCase();
            let matches = assistants.filter(function(item) {
                return item.name.toLowerCase().startsWith(query);
            });
            e.preventDefault();
            if (matches.length > 0) {
                var suggestionsHtml = matches.map(function(item) {
                    return `<div class="autocomplete-suggestion" data-assist-id="${item.id}">${item.name}</div>`;
                }).join('');
                $suggestions.html(suggestionsHtml).show();
                /*
                $suggestions.css({
                                 bottom: $mentionInput.position().top + $mentionInput.outerHeight() + 15,
                                 left: $mentionInput.position().left + 10
                });
                */
            } else {
                $suggestions.hide();
            }
        } else {
            $suggestions.hide();
        }
        if (0 === text.length && 8 === e.keyCode) {
            $('#assistant-id').text('').hide();
            $mentionInput.css('text-indent', 0);
        }
    });
    /* end suggestions */

    /* replace images with location from OPAL installation */
    try {
        var imgBase = new URL("/chat/", baseUrl).toString();
        $('img').each(function() {
            let src = $(this).attr('src');
            if (0 === src.indexOf('svg/'))
                $(this).attr('src', new URL(src, imgBase).href);
        });
        $('.prompt').on ('click', sendPredefinedPrompt);
    } catch(_) {}

    const opal_win = document.querySelector('#opal-form');
    dragElement(opal_win, document.querySelector('div.form-header-title'))
    makeResizable(opal_win, document.querySelector('#opal-form .resizer'), 405, 585)

!{use_bearer}/***
     // the below is code to login/logout with OIDC client, can see more examples of it in SPA, OPAL etc.
     // the only specific thing is call to Opal().connect after login see vvv 
     $('#loginID').click(authLogin);
     $('#logoutID').click(authLogout);
     
     async function authLogout() {
        let url = new URL(window.location.href);
        url.search = '';
        await authClient.logout();
        location.replace(url.toString());
    }

    async function authLogin() {
        let url = new URL(window.location.href);
        url.hash = '';
        localStorage.setItem('login', 1);
        authClient.login({
                         oidcIssuer: baseUrl,
                         redirectUrl: url.toString(),
                         tokenType: 'DPoP',
                         clientName: 'OpenLink Demo'
        });
    }

    authClient.handleIncomingRedirect({restorePreviousSession: false}).then(async (info) => {
        loggedIn = info?.isLoggedIn;
        $('#loginID').toggleClass('d-none', loggedIn);
        $('#logoutID').toggleClass('d-none', !loggedIn);
        const is_login = localStorage.getItem('login');
        localStorage.removeItem('login');
        const prompt = localStorage.getItem('prompt0');
        localStorage.removeItem('prompt0');
	
        if (info?.webId != null) {
            $('.loggedin-btn').show();
            $('.loggedin-btn').attr('href', info.webId);
            $('.loggedin-btn').attr('title', info.webId);
            $('.loggedin-btn').tooltip({container: 'body'});
            // here we after OIDC login succeed we call Opal.connect() it does what it does and then send() can be used
            // for details see code in opal.js
            await opal.connect();
            // end of connecting Opal
            // $('.prompt').on ('click', sendPredefinedPrompt);
            if (is_login) {
              $('.open-button').click()
              if (prompt)
                sendPrompt(prompt);
            }
        }
    }).catch ((e) => {
        errorHandler (e.toString());
    });
!{use_bearer}***/
});
</script>
!!.


!!{use_opal}
<!-- OPAL -->

<div id="snackbar">
    <div id="msg"></div>
</div>


<textarea id="clipboard-text"></textarea>
<div class="chat-popup" id="opal-form">
  <div class="form-container">
    <div class="form-header">
      <div class="form-header-title">
        <h1>Talk with OPAL</h1>
        <span id="info" style="margin-left:10px; color:yellow; display:none">Connecting</span>
      </div>
      <div class="form-header-btn">
        <span type="button" title="Copy" class="header-btn clipboard-btn" data-clipboard-target="#clipboard-text"><img src="svg/clipboard.svg"/></span>
        <span type="button" title="Share" class="header-btn share-btn"><img src="svg/paperclip.svg"/></span>
!{use_oauth}        <span class="header-btn loggedin-btn"> <a data-placement="bottom" target="_blank" href="" title=""><img id="uid-icon" src="svg/person-fill-check.svg"></a></span>
!{use_oauth}        <button type="button" title="Logout" id="logoutID" class="d-none btn log-btn"><img src="logout.svg"/></button>
!{use_oauth}        <button type="button" title="Login" id="loginID" class="d-none btn log-btn"><img src="login.svg"/></button>
        <span type="button" title="Close" class="header-btn close-btn"><img src="svg/x-circle.svg"/></span>
      </div>
    </div>
    <div class="messages">
      <div class="questions">
!{w_prompt1}        <button type="button" class="prompt">%{w_prompt1}</button>
!{w_prompt2}        <button type="button" class="prompt">%{w_prompt2}</button>
!{w_prompt3}        <button type="button" class="prompt">%{w_prompt3}</button>
!{w_prompt4}        <button type="button" class="prompt">%{w_prompt4}</button>
      </div>
    </div>
    <div class="input_wrapper">
      <div style="flex:1">
        <textarea placeholder="Type message.." id="message_input" required></textarea>
      </div>
      <div class="input_btns">
        <button type="button" class="send"><img src="svg/send.svg"/></button>
        <button type="button" class="stop d-none"><img src="svg/dash-circle.svg"/></button>
      </div>
    </div>
  </div>
  <div style="display:flex; flex-direction:row-reverse;">
    <img class="resizer" src="data:image/gif;base64,R0lGODlhCgAKAJEAAAAAAP///6CgpP///yH5BAEAAAMALAAAAAAKAAoAAAIRnI+JosbN3hryRDqvxfp2zhUAOw==" alt="Resize" width="15" height="15"/>
  </div>
</div>


<!-- these two have to be included in order Opal() to work, the rest about jQuery/Bootstrap/design is deveoper choice -->
!{use_bearer}<script src="auth.js"></script>
!{use_oauth}<script src="solid-client-authn.bundle.js"></script>
<script src="opal.js"></script>
<script src="win.js"></script>
<script>
const md = window.markdownit({
                               html:true,
                               breaks:true,
                               linkify:true,
                               langPrefix:'language-',
                               quotes: '“”‘’',
    });

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const hrefIndex = tokens[idx].attrIndex('href');
  const href = hrefIndex >= 0 ? tokens[idx].attrs[hrefIndex][1] : '';

  if (href && href.startsWith('#'))
    return self.renderToken(tokens, idx, options);

  const targetIndex = tokens[idx].attrIndex('target');
  if (targetIndex < 0) 
    tokens[idx].attrPush(['target', '_blank']);
  else 
    tokens[idx].attrs[targetIndex][1] = '_blank';

  const relIndex = tokens[idx].attrIndex('rel');
  if (relIndex < 0) 
    tokens[idx].attrPush(['rel', 'noopener noreferrer']);
  else 
    tokens[idx].attrs[relIndex][1] = 'noopener noreferrer';

  return self.renderToken(tokens, idx, options);
};


var clipboard = new ClipboardJS('.clipboard-btn');

async function showInfo (text) {
    const tm = 3000;
    $('#msg').html(text);
    $('#snackbar').show();
    setTimeout(function () {  $('#snackbar').hide(); }, tm);
}

async function showNotice (text) {
    const tm = 3000;
    $('#info').html(text);
    $('#info').show();
    setTimeout(function () {  $('#info').hide(); }, tm);
}

clipboard.on('success', (e) => {
  showNotice('Copied.')
})

$(function () {

    const baseUrl = "%{w_opl_endpoint}";
    const hostname = new URL(baseUrl).hostname;
    // OIDC client variable
!{use_oauth}    var authClient = solidClientAuthentication.default;
!{use_bearer}    var authClient = new AuthClient('%{w_opl_api_key}');
    var session = authClient.getDefaultSession();
    // OPAL interface, params: OIDC client var, backend host&port, callbacks for incoming message and error callback 
    // if callbacks not given behaviour is not defined
    var opal = new Opal(authClient, hostname, receiveMessage, errorHandler, {
!{w_model}        model: '%{w_model}', // next three are to calibrate model, look at OpenAI docs.
!{w_funcs}        functions: [%{w_funcs}], // backend registered functions, can be added unless not given otherwise via module
        top_p: %{w_top_p},
        temperature: %{w_temperature},
        module: '%{w_module}' // fine-tune module to init session, e.g. data-twingler-config, chat-help et.c see docs.
    });
    var $currentMessage = undefined; // keep DOM element of the receiving message as it coming on chunks
    var currentText = undefined;
    var $messages = $('.messages'); // the messages list, shortcut

    function receiveMessage(role, chunk) { // this is a handler see above Opal() to draw incoming messages
        if (role === 'function' || role === 'tool' || role === 'function_response') {
            // in this demo we do not print functions & response from them
            return;
        }
       if (role === 'notice') {
           showNotice (chunk);
           return;
       }
       if (chunk === '[DONE]' || chunk === '[LENGTH]') { // standart markers of backend when stops sending data 
          $currentMessage = undefined;
           currentText = undefined;
           $messages.find('.cursor').remove();
           $('.stop').toggleClass('d-none', true);
           $('.send').toggleClass('d-none', false);
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           // optionally we can enable the predefined prompts here
           $('.prompt').on ('click', sendPredefinedPrompt);
       } else if (!$currentMessage) { // this is first chunk of the answer
           currentText = chunk;
           $currentMessage = $('<div class="agent-message"></div>');
           $currentMessage.html(md.render(currentText));
           $messages.append($currentMessage);
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           $('<span class="cursor"></span>').insertAfter($currentMessage);
           $('.stop').toggleClass('d-none', false);
           $('.send').toggleClass('d-none', true);
           $('#clipboard-text').val($('#clipboard-text').val() + '\nassistant: ' + chunk);
       } else { // next chunk
           currentText = currentText + chunk;
           currentText = currentText.replace(/【[0-9:]+†[\w+\.-]+】/g, '');
           $currentMessage.html(md.render(currentText));
           $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
           $('#clipboard-text').val($('#clipboard-text').val()+chunk);
       }
    }

    function errorHandler (error) { // error handler, called by Opal() if something f goes wrong
        let $message = $('<div class="agent-message">'+error+'</div>');
        $messages.append($message);
    }

    function sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }

    function connect()
    {
      const tm_sleep = 250;
      const cnt = 10000 / tm_sleep;
      return new Promise(async (resolve) => {
        if (opal.getChatId())
          resolve(1);
        $('#info').html('Connecting...')
        $('#info').show();
        try {
          if (!opal.isConnecting())
            await opal.connect();

          for(var i=0; i < cnt; i++) {
            if (opal.getChatId()) {
              resolve(1);
              break;
            }
            await sleep(tm_sleep);
          }
          resolve(0)
        } catch(_) {
        } finally {
          $('#info').hide();
        }
      })
    }

    $('.open-button').on('click', function(e) {  // to open chat popup 
!{use_bearer}        connect();
        $('.open-button').hide();
        $('#opal-form').fadeIn();
    });
    $('.close-btn').on('click', function(e) { // self evident
        $('#opal-form').hide();
        $('.open-button').show();
    });

    $('.share-btn').on('click', function(e) {
        opal.share();
     });

    $('#message_input').keypress(function (e) { // enter or shift + enter 
        if (!e.shiftKey && e.which === 13) {
            let text = $('#message_input').val().trim();
            e.preventDefault();
            sendPrompt(text);
        }
    });

    $('.stop').on('click', function(e) {
        opal.stop();
     });
    $('.send').on('click', function(e) { // see above, doing same thing
        let $messages = $('.chat-popup .messages');
        let text = $('#message_input').val().trim();
        sendPrompt(text);
     });

     // wrapper to draw message and call OPAL widget
     async function sendPrompt (text) {
        if (text.length) {
            if (!session.info.isLoggedIn) {
                localStorage.setItem('prompt0', text);
                $messages.append ($(`<div class="user-message"><pre style="color:red">You need to Login</pre></div>`));
                await sleep(300);
                $('#loginID').click();
                return;
            }
            if (!opal.getChatId())
                await connect();
            $messages.append ($(`<div class="user-message"><pre>${text}</pre></div>`));
            $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 0);
            $('.prompt').off();
            await opal.send (text);
            $('.questions').hide();
            $('#message_input').val('');
            $('#clipboard-text').val($('#clipboard-text').val() + '\nuser: ' + text);
        }
     }

    // wrapper to handle predefined prompts
    async function sendPredefinedPrompt(e) {
        let text = e.target.innerHTML;
        if ($('.open-button:visible').length > 0) {
            $('.open-button').hide();
            $('#opal-form').fadeIn();
        }
        // disable the predefined promps, can enable once this one complete
        sendPrompt (text);
    }

    /* replace images with location from OPAL installation */
    try {
        var imgBase = new URL("/chat/", baseUrl).toString();
        $('img').each(function() {
            let src = $(this).attr('src');
            if (0 === src.indexOf('svg/'))
                $(this).attr('src', new URL(src, imgBase).href);
        });
        $('.prompt').on ('click', sendPredefinedPrompt);
    } catch(_) {}

    const opal_win = document.querySelector('#opal-form');
    dragElement(opal_win, document.querySelector('div.form-header-title'))
    makeResizable(opal_win, document.querySelector('#opal-form .resizer'), 405, 585)

!{use_bearer}/***
     // the below is code to login/logout with OIDC client, can see more examples of it in SPA, OPAL etc.
     // the only specific thing is call to Opal().connect after login see vvv 
     $('#loginID').click(authLogin);
     $('#logoutID').click(authLogout);
     
     async function authLogout() {
        let url = new URL(window.location.href);
        url.search = '';
        await authClient.logout();
        location.replace(url.toString());
    }

    async function authLogin() {
        let url = new URL(window.location.href);
        url.hash = '';
        localStorage.setItem('login', 1);
        authClient.login({
                         oidcIssuer: baseUrl,
                         redirectUrl: url.toString(),
                         tokenType: 'DPoP',
                         clientName: 'OpenLink Demo'
        });
    }

    authClient.handleIncomingRedirect({restorePreviousSession: false}).then(async (info) => {
        loggedIn = info?.isLoggedIn;
        $('#loginID').toggleClass('d-none', loggedIn);
        $('#logoutID').toggleClass('d-none', !loggedIn);
        const is_login = localStorage.getItem('login');
        localStorage.removeItem('login');
        const prompt = localStorage.getItem('prompt0');
        localStorage.removeItem('prompt0');

        if (info?.webId != null) {
            $('.loggedin-btn').show();
            $('.loggedin-btn').attr('href', info.webId);
            $('.loggedin-btn').attr('title', info.webId);
            $('.loggedin-btn').tooltip({container: 'body'});
            // here we after OIDC login succeed we call Opal.connect() it does what it does and then send() can be used
            // for details see code in opal.js
            await opal.connect();
            // end of connecting Opal
            // $('.prompt').on ('click', sendPredefinedPrompt);
            if (is_login) {
              $('.open-button').click()
              if (prompt)
                sendPrompt(prompt);
            }
        }
    }).catch ((e) => {
        errorHandler (e.toString());
    });
!{use_bearer}***/
});
</script>
!!.


</body>
</html>