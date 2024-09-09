// Functions active on templates thread.html and base_thread_reply.html

/*
  Handles the 'Reply' button for the thread's replies
*/
function setReplyTo(replyId) {
    document.getElementById('reply_to_id').value = replyId
    window.scrollTo(0, 0);
}

/**
    On the page load sets the interval that periodically (currently 1 minute) checks
    whether the thread has been updated (by invoking an appropriate view via Ajax).
    If the thread has been changed it will display a message and clear the interval.
**/
window.onload = function () {

    let update_interval = setInterval(function () {
        const check_update_data = JSON.parse(document.getElementById('check-update-data').textContent);
        let thread_page_time = check_update_data.thread_page_time
        const request = new XMLHttpRequest();
        request.open('GET', check_update_data.url);

        request.onreadystatechange = function () {
            if (this.readyState === 4 && this.status === 200) {
                if (this.responseText > thread_page_time) {
                    new bootstrap.Toast(document.getElementById("updateToast")).show();
                    clearInterval(update_interval)
                }
            }
        };
        request.send();
    }, 60000);

}

/*
    Shows dialog for message edit with the message from the given thread
*/
function showEditModal(threadId) {
    document.getElementById('editThreadIdField').value = threadId
    document.getElementById('editMessageField').value = document.getElementById('message' + threadId).innerHTML
    document.getElementById('editMessageError').hidden = true
    new bootstrap.Modal(document.getElementById('editMessageModal'), {}).show()
}

/*
    Triggers thread's message edit by invoking a proper view via Ajax
*/
function editMessage(threadId) {
    let updateId = document.getElementById('editThreadIdField').value
    let newMessage = document.getElementById('editMessageField').value
    let replyId = updateId === threadId ? '' : updateId

    const update_message_data = JSON.parse(document.getElementById('edit-message-data').textContent);

    fetch(update_message_data.url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": update_message_data.csrf_token,
        },
        body: JSON.stringify({ replyId: replyId, newMessage: newMessage })
    })
        .then(function (response) {
            if (response.status == 204) {
                bootstrap.Modal.getInstance(document.getElementById('editMessageModal')).hide()
                document.getElementById('message' + updateId).innerHTML = newMessage
            } else {
                document.getElementById('editMessageError').hidden = false
                console.error(response)
            }
        })
}