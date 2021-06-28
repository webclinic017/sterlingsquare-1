
    function highlight_letter(keyword) {
        $(".s-result-code").each(function () {
            var word = keyword
            element = $(this)
            var rgxp = new RegExp(word, 'g');
            var repl = '<span class="highlighted">' + word + '</span>';
            // element.innerHTML = element.innerHTML.replace(rgxp, repl);
            old_val = $(this).html();
            new_val = old_val.replace(rgxp,repl)
            $(this).html(new_val)
        })
    }

    $(document).on("keyup", ".stock-search", function () {
        var keyword = $(".stock-search").val()
//        $(".search-result").remove()
        $("#stock-auto-search").empty()
        if(keyword){
            $.ajax({
                url:'/accounts/dashboard/stock-search/',
                type:'GET',
                async:false,
                data:{
                    'type':'stock_search',
                    'keyword':keyword
                },
                success:function(data){
                    $("#stock-auto-search").empty()
                    console.log(data.stock_list)
                    for ( var i = 0, l = data.stock_list.length; i < l; i++ ) {
                        var symbol = data.stock_list[ i ]['symbol']
                        var name = data.stock_list[ i ]['name']
                        var html = '<div class="row search-result"><div class="col-sm-4"><p class="s-result-code name_id">'+symbol+'</p></div><div class="col-sm-8"><p class="s-result-name name_id">'+name+'</p></div></div>'
                        $(".dropdown-content").append(html)
                        $(".dropdown-content").show()

                    }
                }
            })

        }
        else{
            $(".dropdown-content").hide()
        }
    })

    $(document).on("click",".dash-right-col-title-arrow",function () {
        $(".dash-right-col-dropdown").toggleClass("show")
    })


$(document).on("click",".s-result-code",function(){
    symbol = $(this).html()
    $(".loadingio-spinner-spinner-lzgp9tuxt9").show()

    $.ajax({
                url:'/accounts/dashboard/',
                type:'GET',
                data:{
                    'type':'get_stock_details',
                    'symbol':symbol
                },
                success:function(data){
                if (data.has_history == "True"){
                    $("#stock-auto-search").empty()
                    $(".dropdown-content").hide()
                    $(".line-chart-main").replaceWith(data.line_chart_html)
                    $(".scatter_plot_con").replaceWith(data.scatter_plot_html)
                    $(".market-pairs").replaceWith(data.stock_market_settings_html)
                    $(".company_info").replaceWith(data.company_info_html)
                    $(".has_stock").val("True")
                    $(".highcharts-series.highcharts-series-0.highcharts-line-series.highcharts-color-0").find(".highcharts-graph").css("stroke",data.color)
                    $(".pos-tabl-details-content").replaceWith(data.pos_table_details_html)
                    $(".pos-tabl-details-content").show()
                    $(".open-buy-content").trigger("click")
                    $(".loadingio-spinner-spinner-lzgp9tuxt9").hide()
                }else{
                alert("Stock has no data")
                location.reload()
                }
                }
            })


})

$(document).on("keyup",".share-num",function(){

    num = $(this).val()
    price = $("#market-price-ws").text()
    console.log(price);
    total = parseFloat(price)*parseFloat(num)
    total = 99.00
    document.getElementByClass("total-market-price").textContent=total;
})