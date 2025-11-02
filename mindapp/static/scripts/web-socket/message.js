var connector = 'ws://' + window.location.host ;
var message_endpoint = connector + '/ws/chat/' ; 
var room_check_endpoint = connector + '/ws/room_checker/' ;
var notification_endpoint = connector + '/ws/notifications/';

function message_input(room_id,text_content,sender,receiver,chat_log){
    const users = '/' + sender + '/' + receiver + '/';
    const socket = new WebSocket( message_endpoint + room_id + users );
    
    socket.onopen = function(){
        console.log(text_content);
    
        socket.send(JSON.stringify({
        'message':text_content       
        }));
    };

    socket.onmessage = function(e){
        const data = JSON.parse(e.data);
        console.log('received message:', data.message); // Log the received message
        if (!chat_log) return;

        const item = document.createElement('div')
        item.className = data.sender 
    };

     
};

    
function established_connection(room_id,sender,receiver,chat_log){

    const users = '/' + sender + '/' + receiver + '/';
    const socket = new WebSocket( message_endpoint + room_id + users);

    socket.onopen = function(){
        console.log('connecttion established');
        // --- FIX: Enable the form now that the connection is open ---
        //messageInput.disabled = false;
        //sendButton.disabled = false;
        //messageInput.placeholder = "Type your message here...";
    };

    socket.onmessage = function(e){
        const data = JSON.parse(e.data);
        console.log('receive data', data);

        if (!chat_log) return;

        append_message_to_log(data,sender,chat_log);
        
        chat_log.scrollTop = chat_log.scrollHeight;
    
    };

        
    socket.onclose = function(e){
        console.error('chat were cooked')
    };
    //message_socket.onmessage = function(e) {
    //        const data = JSON.parse(e.data);
            //meesage log is id for textarea
    //        message_in.value += (data.message + '\n');
    //    };
    return socket;
};

/////////////////////////////////////////////////////////////////////

function checkroom(user_1, user_2, callback){
    const room_socket = new WebSocket( room_check_endpoint + user_1 + '/' + user_2 + '/')
    let room_id = null;

    room_socket.onmessage = function(e){
        const data = JSON.parse(e.data);
        if (data.type === 'room_id_init'){
             room_id = data.room_id;
            //console.log('room id :' + room_id);

            if (typeof callback === "function"){
                callback(room_id);
            }

            room_socket.close();
            
        }
    }

    console.log('room out' + room_socket.onmessage);

    room_socket.onopen = function() {
        console.log("WebSocket connection established.");
    };

    room_socket.onclose = function() {
        console.log("WebSocket connection removed.");
    };
    room_socket.onerror = function(error) {
        console.error("WebSocket Error:", error);
    };
};

////////////////////////////////////////////////////////////////

function notified_user(){
    return notification_endpoint
};

////////////////////////////////////////////////////////////////


function append_message_to_log(data,request_user_id, chat_log){
    const messageElement = document.createElement('div');

    const senderId = data.sender__who__id || data.sender_id;
    const sender_name = data.sender__full_name || data.sender_name;
    const content = data.content || data.message;
    
    const messageClass = parseInt(senderId) === parseInt(request_user_id) ? 'message-sent' : 'message-received';
        messageElement.classList.add('message', messageClass);

     messageElement.textContent = `${content}`;

        chat_log.appendChild(messageElement);

}

function to_load_message(room_id, request_user_id,chat_log){

    fetch(`/api/messages/${room_id}/`)
        .then(Response => Response.json())
        .then(data => {
            data.forEach( msg => {

                append_message_to_log(msg, request_user_id,chat_log);
                
            });

            chat_log.scrollTop = chat_log.scrollHeight;
        })
        .catch(error => console.error('hello, message not to be appearing?', error));
}