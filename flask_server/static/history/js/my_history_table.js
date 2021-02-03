

$(document).ready(function() {
    $('#my_history_table').DataTable();


    $(document).on('click', '.updateButton', function() { 

        var member_id = $(this).attr('member_id');

        console.log(member_id)
    });



   
} );



