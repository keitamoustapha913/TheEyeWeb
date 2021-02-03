

$(document).ready(function() {
   

    $(document).on('click', '.view_data', function(){
        var employee_id = $(this).attr("id");
        console.log(employee_id);
        var edit_row_id = $(this).attr('row_id');
        console.log(edit_row_id);

    });

   
} );