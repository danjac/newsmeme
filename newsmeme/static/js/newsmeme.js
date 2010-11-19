var newsmeme = {

    ajax_post : function(url, params, on_success){
    
        var _callback = function(response){
            if (response.success) {
                if (response.redirect_url){
                    window.location.href = response.redirect_url;
                } else if (response.reload){
                    window.location.reload(); 
                } else if (on_success) {
                    return on_success(response);
                }
            } else  {
                return newsmeme.message(response.error, "error");
            }
        }

        $.post(url, params, _callback, "json");

    },
    
    message : function(message, category){
        $('ul#messages').html('<li class="' + category + '">' + message + '</li>').fadeOut();
    },

    delete_comment : function(url) {
        var callback = function(response){
            $('#comment-' + response.comment_id).fadeOut();
        }   
        newsmeme.ajax_post(url, null, callback);
    },

    vote_post : function(url){
        var callback = function(response){
            $('#vote-' + response.post_id).hide();
            $('#score-' + response.post_id).text(response.score);
        }

        newsmeme.ajax_post(url, null, callback);
    },


    vote_comment : function(url){
        var callback = function(response){
            $('#vote-comment-' + response.comment_id).hide();
            $('#score-comment-' + response.comment_id).text(response.score);
        }

        newsmeme.ajax_post(url, null, callback);
    }

}
