

    const contacts = document.querySelector('.contact-list'); 
    
    //--------- just toggle some ui for contact and message box
    function closeModal() {
        msg_modal_box.classList.remove('show');
    }
    function openModal() {
        msg_modal_box.classList.add('show');
    }

    function togglecontact(){
    contacts.classList.toggle('show');
    }

    function toggle_addsuser(){
        user_add_list.classList.toggle('show');
    }


    //----------contact name for contact message

    contact_msg_card.forEach(function(btn){
            btn.addEventListener('click',function(){
                contact_username_display.textContent = btn.dataset.contact_username;
                // toggle message modal
                msg_modal_box.classList.add('show'); 
            });
        });

    //-------------------search bar function for adding user
    searchbar.addEventListener('input',function(){
        const SearchTerm = this.value.toLowerCase();
        userobj.forEach(function(UserObj) {
            const name = UserObj.textContent.toLowerCase();
            UserObj.style.display = name.includes(SearchTerm) ? '' : 'none';
            
        });
    })

    //----------csrf helper thingy
    function getCookie(name){
        let cookieValue = null;
        if (document.cookie && document.cookie !== ''){
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++){
                const cookie = cookies[i].trim();
                if (cookie.substring(0,name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                } 
            }
        }
        return cookieValue;
    }
    

    //----adduser button logic
    Useraddbtn.forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        // The btn variable already refers to the button
        const userId = btn.getAttribute('data-user_id');
        console.log('CSRF Token Value:', getCookie('csrftoken'));

        fetch(`/contact/add/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
        .then(response => {
            if (response.ok) {
                btn.textContent = 'added!';
                btn.disabled = true;
            } else {
                alert('failed to add contact.');
            }
        });
    });
});