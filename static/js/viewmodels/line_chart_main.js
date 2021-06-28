var self = this;

var priceChangeSocket = null;
var el = document.querySelector('.odometer');

self.updateGraphToken = null;
self.watchListToken = null;
self.stockListToken = null;
self.activeListToken = null;

self.is_auth = is_auth;

self.share_total_int = share_total_int;

function getGainLoss() {
    if (self.is_auth) {
        $.ajax({
            url: "/accounts/dashboard/api/market_values/" + self.symbol,
            success: function(dat) {
                if (dat.values !== null && dat.values !== undefined) {
                    total_return_1 = dat.values.total_return;
                    if (dat.values.total_return !== null  && dat.values.total_return !== undefined) {
                        total_return = parseFloat(Math.abs(dat.values.total_return)).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                    } else {
                        total_return = "\u2014"
                    }

                    if (dat.values.total_return_percent !== null && dat.values.total_return_percent !== undefined) {
                        total_return_percent = parseFloat(Math.abs(dat.values.total_return_percent)).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                    } else {
                        total_return_percent = "\u2014"
                    }

                    if (total_return_1 < 0) {
                        total_return = "-₹" + total_return + " (-" + Math.abs(total_return_percent) + "%" + ")"
                    } else {
                        total_return = "+₹" + total_return + " (+" + total_return_percent + "%" + ")"
                    }

                    today_return_1 = dat.values.today_return;
                    if (dat.values.today_return !== null && dat.values.today_return !== undefined) {
                        today_return = parseFloat(Math.abs(dat.values.today_return)).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                    } else {
                        today_return = "\u2014"
                    }

                    if (dat.values.today_return_percent !== null && dat.values.today_return_percent !== undefined) {
                        today_return_percent = parseFloat(Math.abs(dat.values.today_return_percent)).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                    } else {
                        today_return_percent = "\u2014"
                    }

                    if (today_return_1 < 0) {
                        today_return = "-₹" + today_return + " (-" + today_return_percent + "%" + ")"
                    } else {
                        today_return = "+₹" + today_return + " (+" + today_return_percent + "%" + ")"
                    }

                    if (dat.values.share_total !== null && dat.values.share_total !== undefined) {
                        self.share_total_int = parseFloat(dat.values.share_total);
                        $(".inp-stock-num").val(self.share_total_int);
                        share_total = parseFloat(dat.values.share_total).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 0}
                        );
                    } else {
                        share_total = "\u2014"
                    }

                    if (dat.values.portfolio_diversity !== null && dat.values.portfolio_diversity !== undefined) {
                        portfolio_diversity = parseFloat(dat.values.portfolio_diversity).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                        portfolio_diversity = portfolio_diversity + "%"
                    } else {
                        portfolio_diversity = "\u2014"
                    }

                    if (dat.values.avg_cost !== null && dat.values.avg_cost !== undefined) {
                        avg_cost = parseFloat(dat.values.avg_cost).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                        avg_cost = "₹" + avg_cost;
                    } else {
                        avg_cost = "\u2014"
                    }

                    if (dat.values.cost !== null && dat.values.cost !== undefined) {
                        cost = parseFloat(dat.values.cost).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                        cost = "₹" + cost;
                    } else {
                        cost = "\u2014"
                    }

                    if (dat.values.market_value !== null && dat.values.market_value !== undefined) {
                        market_value = parseFloat(dat.values.market_value).toLocaleString(
                            "en-US",
                            {maximumFractionDigits: 2, minimumFractionDigits: 2}
                        );
                        market_value = "₹" + market_value
                    } else {
                        market_value = "\u2014"
                    }

                    $("#total_return").html(total_return);
                    // today return will be changed on web socket message reception.
                    // $("#today_return").html(today_return);
                    $("#avg_cost").html(avg_cost);
                    $("#cost").html(cost);
                    $("#market_value").html(market_value);
                    $("#share_count").html(share_total);
                    $("#portfolio_diversity").html(portfolio_diversity);
                }
            }
        })
    }
}

self.live_price = null;

changePlotColor = function(color) {
    var chart = Highcharts.charts[0];
    chart.update({
        plotOptions: {
            series: {
                color: color
            }
        }
    })
}

setTimeout(function() {
    $(".inp-stock-num").val(self.share_total_int);
    changePlotColor(init_intra_change.color);

    if (init_intra_change.color === "#00ff39") {
        self.color = "green"
    } else if (init_intra_change.color === "#ff5000") {
        self.color = "red"
    } else {
        self.color = "blue"
    }

    if (self.color == "red") {
        $("#btn_1d").removeClass("btn-range-green");
        $("#btn_1m").removeClass("btn-range-green");
        $("#btn_3m").removeClass("btn-range-green");
        $("#btn_6m").removeClass("btn-range-green");
        $("#btn_1y").removeClass("btn-range-green");
        $("#btn_5y").removeClass("btn-range-green");

        $("#btn_1d").addClass("btn-range-red");
        $("#btn_1m").addClass("btn-range-red");
        $("#btn_3m").addClass("btn-range-red");
        $("#btn_6m").addClass("btn-range-red");
        $("#btn_1y").addClass("btn-range-red");
        $("#btn_5y").addClass("btn-range-red");

    } else if (self.color == "green") {
        $("#btn_1d").removeClass("btn-range-red");
        $("#btn_1m").removeClass("btn-range-red");
        $("#btn_3m").removeClass("btn-range-red");
        $("#btn_6m").removeClass("btn-range-red");
        $("#btn_1y").removeClass("btn-range-red");
        $("#btn_5y").removeClass("btn-range-red");

        $("#btn_1d").addClass("btn-range-green");
        $("#btn_1m").addClass("btn-range-green");
        $("#btn_3m").addClass("btn-range-green");
        $("#btn_6m").addClass("btn-range-green");
        $("#btn_1y").addClass("btn-range-green");
        $("#btn_5y").addClass("btn-range-green");
    } else {
        $("#btn_1d").removeClass("btn-range-red");
        $("#btn_1m").removeClass("btn-range-red");
        $("#btn_3m").removeClass("btn-range-red");
        $("#btn_6m").removeClass("btn-range-red");
        $("#btn_1y").removeClass("btn-range-red");
        $("#btn_5y").removeClass("btn-range-red");

        $("#btn_1d").removeClass("btn-range-green");
        $("#btn_1m").removeClass("btn-range-green");
        $("#btn_3m").removeClass("btn-range-green");
        $("#btn_6m").removeClass("btn-range-green");
        $("#btn_1y").removeClass("btn-range-green");
        $("#btn_5y").removeClass("btn-range-green");
    }

    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");
    self.key = '1D'

    if (self.color === "green") {
        $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    } else if (self.color === "red") {
        $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
        $(".btn-change-color").addClass("btn-add-to-w-red");
        $(".btn-change-color").removeClass("btn-add-to-w");
    } else {
        $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    }

    $(".btn-change-color").css("background-color",init_intra_change.btn_color);
    $(".theme-color").val(init_intra_change.btn_color);
    $(".btn-change-color").css("border-color",init_intra_change.btn_color);
    $(".btn-change-color").css("color","#fff");

}, 20);

/*setTimeout(function() {
    $("#total_return").html("₹" + total_return + " (" + total_return_percent + "%" + ")");
    $("#today_return").html("₹" + today_return + " (" + today_return_percent + "%" + ")");
    $("#avg_cost").html("₹" + avg_cost);
    $("#cost").html("₹" + avg_cost);
    $("#market_value").html("₹" + market_value);
    $("#share_count").html(share_total);
    $("#portfolio_diversity").html(portfolio_diversity + "%");
}, 10);*/

self.updating = false;
self.key = '1D';
self.max = null;
self.min = min;
// self.live_price = lp;
// self.intraday_price = yVal;

// depicts whether market open today
self.is_market_open_today = is_market_open_today;
// depicts whether market open at current moment
self.is_market_open_now = is_market_open_now;

// $(".price_1D").val(self.intraday_price);

od = new Odometer({
    el: el,
    value: 0.00,

    format: '(,ddd).dd',
    theme: ''
});

od.update($(".stock_price").val());

var symbol = $("#stock_symbol").val()
self.symbol = symbol;
console.log("symbol ", symbol)
var data = [], time = (new Date()).getTime(), i;

self.dailyOpenValue = null;

function initializeIntraDayData() {
    $.ajax({
        url: '/accounts/dashboard/api/historical/',
        data: {
            "symbol": self.symbol,
            "interval": "1D"
        },
        type: 'GET',
        async: false,
        success: function (dat) {
            setTimeout(function() {
                changeAccentColors(init_intra_change);
            }, 1);

            data = dat.data;
            self.max = data[data.length - 1][0] + 100;
            self.dailyOpenValue = dat.open_value;
            // $(".price_1D").val(dat.open_value);
            var chart = Highcharts.charts[0], series = chart.series[0];

            var chart = Highcharts.charts[0];
            var series = chart.series[0];
            series.update({
                "data": dat.data
            }, true);
            chart.xAxis[0].update({
                max: self.max,
                min: self.min
            });
        }
    });
}

function initialiseBoxes() {
    $.ajax({
        url: '/singleton',
        type: "GET",
        async: false,
        error: function() {

        },
        success: function() {
            getGainLoss();
        }
    })
}

/*for (i = -19; i <= 0; i += 1) {
    data.push({
        x: time + i * 1000,
        y: Math.random()
    });
}*/

Highcharts.setOptions({
    time: {
        timezone: 'Asia/Kolkata'
    }
});

self.color = null;

updateGraphData = function(symbol, key, live_price, prev_price, retry) {
    // function to be called when the interval is changed.
    if (self.updateGraphToken !== null) {
        self.updateGraphToken.cancel();
        self.updateGraphToken = null;
    }
    self.key = key;
    self.updating = true;
    var chart = Highcharts.charts[0];
    var series = chart.series[0];

    series.update({
        "data": []
    });
    self.updateGraphToken = axios.CancelToken.source();

    axios.get(
        '/accounts/dashboard/api/historical/?symbol=' + symbol + "&interval=" + key, {
            cancelToken: self.updateGraphToken.token
        }
    ).then(function(data) {
        // Change the Graph
        chart_data = data.data.data;
        if (chart_data === null || chart_data === undefined) {
            updateGraphData(symbol, key, live_price, prev_price, retry);
        }
        var chart = Highcharts.charts[0];
        var series = chart.series[0];
        data = data.data;
        if (data.status === 200) {
            if (retry == 0) {
                series.update({
                    "data": []
                });
            }

            if (key !== "1D") {
                $(".price_"+key).val(data.open_value);
            }

            series.update({
                "data": chart_data
            });

            /*series.update({
                "data": chart_data
            });*/

            calculate_return_value2(self.live_price, $(".price_" + key).val())

            index = 0;
            if (key === "1D") {
                index = 0;
                chart.xAxis[0].update({
                    max: self.max,
                    min: self.min,
                    range: 24 * 3600 * 1000
                });
            }
            else if (key == "5y") {
                index = 5;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 5 * 370 * 24 * 3600 * 1000
                });
            }
            else if (key == "1y") {
                index = 4;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 1 * 370 * 24 * 3600 * 1000
                });
            }
            else if (key == "6m") {
                index = 3;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 6 * 31 * 24 * 3600 * 1000
                });
            }
            else if (key == "3m") {
                index = 2;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 3 * 31 * 24 * 3600 * 1000
                });
            }
            else if (key == "1m") {
                index = 1;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 1 * 31 * 24 * 3600 * 1000
                });
            }

            setTimeout(function() {
                self.updating = false;
            }, 2000);
            console.log("will retry? ", series.data.length !== chart_data.length);
            if (series.data.length !== chart_data.length && retry < 10) {
                // Recursive call to this function
                console.log("retry");
                updateGraphData(symbol, key, live_price, prev_price, retry + 1);
            } else {
                return;
            }

        } else {
            // don't change the graph at all and show a message.
        }
    });
    /*$.ajax({
        url: '/accounts/dashboard/api/historical/',
        type: 'GET',
        async: true,
        data: {
            'symbol': symbol,
            'interval': key
        },
        error: function() {
            self.updating = false;
        },
        success: function (data) {
            // Change the Graph
            chart_data = data.data;
            if (chart_data === null || chart_data === undefined) {
                updateGraphData(symbol, key, live_price, prev_price, retry);
            }
            var chart = Highcharts.charts[0];
            var series = chart.series[0];
            if (data.status === 200) {
                if (retry == 0) {
                    series.update({
                        "data": []
                    });
                }

                if (key !== "1D") {
                    $(".price_"+key).val(data.open_value);
                }

                series.update({
                    "data": chart_data
                });

                *//*series.update({
                    "data": chart_data
                });*//*

                calculate_return_value2(self.live_price, $(".price_" + key).val())

                index = 0;
                if (key === "1D") {
                    index = 0;
                    chart.xAxis[0].update({
                        max: self.max,
                        min: self.min,
                        range: 24 * 3600 * 1000
                    });
                }
                else if (key == "5y") {
                    index = 5;
                    chart.xAxis[0].update({
                        max: data.max,
                        min: data.min,
                        range: 5 * 370 * 24 * 3600 * 1000
                    });
                }
                else if (key == "1y") {
                    index = 4;
                    chart.xAxis[0].update({
                        max: data.max,
                        min: data.min,
                        range: 1 * 370 * 24 * 3600 * 1000
                    });
                }
                else if (key == "6m") {
                    index = 3;
                    chart.xAxis[0].update({
                        max: data.max,
                        min: data.min,
                        range: 6 * 31 * 24 * 3600 * 1000
                    });
                }
                else if (key == "3m") {
                    index = 2;
                    chart.xAxis[0].update({
                        max: data.max,
                        min: data.min,
                        range: 3 * 31 * 24 * 3600 * 1000
                    });
                }
                else if (key == "1m") {
                    index = 1;
                    chart.xAxis[0].update({
                        max: data.max,
                        min: data.min,
                        range: 1 * 31 * 24 * 3600 * 1000
                    });
                }

                setTimeout(function() {
                    self.updating = false;
                }, 2000);
                console.log("will retry? ", series.data.length !== chart_data.length);
                if (series.data.length !== chart_data.length && retry < 10) {
                    // Recursive call to this function
                    console.log("retry");
                    updateGraphData(symbol, key, live_price, prev_price, retry + 1);
                } else {
                    return;
                }

            } else {
                // don't change the graph at all and show a message.
            }
        },
        error: function(error) {
            console.log(error.responseJSON);
            self.key = "1D";

            var chart = Highcharts.charts[0];
            var series = chart.series[0];
            series.update({
                "data": data
            }, true);
            if (error.responseJSON.error) {
                // show toast message.
            }
        }
    });*/
}

// Create the chart

hour = moment().hour();
minute = moment().minute();

if (hour <= 9) {

} else {

}

chart = Highcharts.stockChart('container', {
    tooltip: {
        formatter: function() {
            ts = "";
            if (self.key === "1D") {
                ts = moment(this.x).format("HH:mm:ss");
            } else {
                ts = moment(this.x).format("DD MMM, YYYY");
            }

            formattedNumber = parseFloat(this.y).toLocaleString(
                "en-US",
                {maximumFractionDigits: 2, minimumFractionDigits: 2}
            )

            return "<b>" + ts + "<br>₹ " + formattedNumber + "</b>";
        }
    },
    xAxis: [{
        min: self.min,
        visible: false,
        max: new Date().getTime()+(3600 * 8),
        labels: {
            /*format: '%H:%M:%S',*/
            formatter: function() {
                if (self.key === "1D") {
                    return moment(this.value).format("HH:mm");
                } else if (self.key.includes("m")) {
                    return moment(this.value).format("DD MMM");
                }  else if (self.key.includes("y")) {
                    return moment(this.value).format("MMM YYYY");
                }
            }
        }
    }],
    chart: {
        animation: false,
        events: {
            load: function () {
                // set up the updating of the chart each second
                var series = this.series[0];
                var $this = this;

                if (symbol != undefined && symbol != "") {
                    /*setInterval(function () {
                        console.log(" key on load ", self.key);
                        if (self.key === "1D") {
                            current_date = new Date()
                            current_day_number = current_date.getDay()
                            if (parseInt(current_day_number) != 7 && parseInt(current_day_number) != 0) {
                                $.ajax({
                                    url: '/accounts/dashboard/api/stocks/',
                                    type: 'GET',
                                    async: true,
                                    data: {
                                        'type': 'get_stock_real_data',
                                        'symbol': symbol
                                    },
                                    success: function (dat) {
                                        if (dat.status) {
                                            yVal = dat.data
                                            console.log("yValyValyVal   ",yVal)
                                            $(".stock_price").val(yVal)
                                            //$(".odometer").html(yVal)
                                            od.update(yVal)
                                            var x = (new Date()).getTime(), // current time
                                                y = yVal;
                                            var series = $this.get('stock_series');
                                            // var series = $this.series[0];
                                            series.addPoint([x, y], true, true);

                                            $(".highcharts-button").each(function() {

                                                if($(this).hasClass("highcharts-button-pressed")) {
                                                    var key = $(this).find("text").html()
                                                    prev_price = $(".price_"+key).val()
                                                    live_price =  $(".stock_price").val()
                                                    get_price_change(symbol,key,live_price,prev_price)
                                                    return false;
                                                }

                                            })
                                            $this.redraw();

                                        }
                                    }
                                });
                            }
                        } else {
                            if (key == "5y") {
                                // show scrolling buttons
                            } else {
                                // hide scrolling buttons
                            }
                        }

                    }, 5000);*/
                }
                else{
                    setInterval(function () {
                        console.log("..............", $(".has_stock").val())
                        if ($(".has_stock").val() == "False") {
                            $.ajax({
                                url: '/accounts/latest-gain-loss/',
                                type: 'GET',
                                async: true,
                                success: function (dat) {
                                    if (dat.gl_status) {
                                        yVal = dat.gainloss_val
                                        // $(".stock_price").val(yVal)
                                        //$(".odometer").html(yVal)
                                        od.update(yVal)
                                        var x = (new Date()).getTime(), // current time
                                            y = yVal;
                                        var series = $this.get('stock_series');
                                        /*var series = $this.series[0];*/
                                        series.addPoint([x, y], true, true);
                                        console.log(">>><<<", series)
                                    }

                                    // $(".highcharts-button").each(function() {
                                    //
                                    //     if($(this).hasClass("highcharts-button-pressed")) {
                                    //         var key = $(this).find("text").html()
                                    //         prev_price = $(".price_"+key).val()
                                    //         live_price =  $(".stock_price").val()
                                    //         get_price_change(symbol,key,live_price,prev_price)
                                    //        return false;
                                    //     }
                                    //
                                    // })
                                    //$this.redraw();


                                }
                            })
                        }
                    }, 5000);
                }
            }
        }
    },

    rangeSelector: {
        // flag to enable/disable the button
        allButtonsEnabled: true,
        enabled: true,
        /*inputEnabled: true,*/
        buttonSpacing: 10,
        buttonTheme: { // styles for the buttons
            padding: 4,
            fill: '#131722',
            /*stroke: '#00ff39',
            'stroke-width': "1px",*/
            r: 8,
            style: {
                color: 'white',
                fontWeight: 'bold',
                fontSize: 14,
            },
            states: {
                hover: {
                    fill: '#131722',
                    stroke: "#5e81a7",
                    style: {
                        color: '#5e81a7'
                    }
                },
                select: {
                    stroke: "#5e81a7",
                    fill: '#131722',
                    style: {
                        color: '#5e81a7'
                    }
                }
                // disabled: { ... }
            }
        },
        buttonPosition: {
            align: 'left'
        },
        labelStyle: {
            display: 'none'
        },
        buttons: [
        {
            type: 'hour',
            count: 6,
            text: '1D',
            events: {
                click: function () {
                    if (self.key !== "1D") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");
                        self.key = '1D'
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        console.log("1D")
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price);
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                    }
                }
            }
        },
        {
            type: 'month',
            count: 1,
            text: '1m',
            events: {
                click: function(e) {
                    if (self.key !== "1m") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");
                        self.key = '1m'
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        console.log("1m")
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                    }
                }
            }
        },
        {
            type: 'month',
            count: 3,
            text: '3m',
            events: {
                click: function () {
                    if (self.key !== "3m") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");
                        self.key = '3m'
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        console.log("3m")
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                    }
                }
            }
        },
        {
            type: 'month',
            count: 6,
            text: '6m',
            events: {
                click: function () {
                    if (self.key !== "6m") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");
                        self.key = '6m'
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                    }
                }
            }
        },
        {
            type: 'year',
            count: 1,
            text: '1y',
            events: {
                click: function () {
                    if (self.key !== "1y") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");

                        self.key = '1y'
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        console.log("1y")
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                    }
                }
            }
        },
        {
            type: 'year',
            count: 1,
            text: '5y',
            events: {
                click: function () {
                    if (self.key !== "5y") {
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
                        $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");

                        self.key = '5y'
                        if (priceChangeSocket) {
                            priceChangeSocket.send(JSON.stringify({
                                "type": "subscribe", "symbol": $("#stock_symbol").val(), "interval": self.key
                            }));
                        }
                        console.log("5y")
                        if (self.color === "green") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-green");
                        } else if (self.color === "red") {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
                        } else {
                            $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
                        }
                        prev_price = $(".price_"+key).val()
                        live_price =  $(".stock_price").val()
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(symbol, key, live_price, prev_price, 0);
                    }
                }
            }
        },
        ],
        selected: 0     // by default select it to 1D
    },

    title: {
        text: ''
    },
    yAxis:{
         gridLineWidth:0
    },
    plotOptions: {
        series: {
            allowPointSelect: true,
            point: {
                events: {
                    mouseOver: function () {
                        /* var text = this.category + ': ' + this.y + ' was last selected',
                             chart = this.series.chart;
                        var value_text = "INR "
                         $(".graph-value").html(value_text)
                         if (!chart.lbl) {
                             chart.lbl = chart.renderer.label(text, 100, 70)
                                 .attr({
                                     padding: 10,
                                     r: 5,
                                     fill: Highcharts.getOptions().colors[1],
                                     zIndex: 5
                                 })
                                 .css({
                                     color: '#FFFFFF'
                                 })
                                 .add();
                         } else {
                             chart.lbl.attr({
                                 text: text
                             });
                         }*/
                    }
                }
            }
        }
    },
    series: [{
        id: "stock_series",
        name: 'stock',
        data: data
    }],
    time: {
        timezone: 'Asia/Kolkata'
    }
});

initializeIntraDayData();
initialiseBoxes();

function changeHighChartButtonTheme(color) {
    if (color === "red") {
        color = "#ff5000";
    } else if (color === "green") {
        color = "#00ff39";
    } else {
        color = "#5e81a7";
    }

    chart = Highcharts.charts[0];
    chart.rangeSelector.update({
        buttonTheme: {
            states: {
                select: {
                    stroke: color,
                    fill: '#131722',
                    style: {
                        color: color
                    }
                },
                hover: {
                    stroke: color,
                    fill: '#131722',
                    style: {
                        color: color
                    }
                }
                // disabled: { ... }
            }
        }
    });
}


function calculate_return_value2(live_price, initial) {
    console.log(live_price);
    if (typeof(live_price) === "number") {
    } else {
        live_price = live_price.replaceAll(",", "").replaceAll("₹", "");
        live_price = parseFloat(live_price)
    }
    difference = (live_price - initial);
    // Old Version
    // percentage = ((difference / initial) * 100);

    // New Version
    if (initial == 0) {
        percentage = 0.0;
    } else {
        percentage = ((difference / initial) * 100);
    }

    console.log("live_price ", live_price, "initial ", initial);
    console.log("difference ", difference, "percentage ", percentage);

    if (self.key === "1D" && self.share_total_int > 0) {
        // for intra day change the
        today_return_1 = difference * self.share_total_int;

        if (today_return_1 !== null && today_return_1 !== undefined) {
            today_return = parseFloat(Math.abs(today_return_1)).toLocaleString(
                "en-US",
                {maximumFractionDigits: 2, minimumFractionDigits: 2}
            );
        } else {
            today_return = "\u2014"
        }

        market_value = $("#market_value").html().replaceAll("₹", "").replaceAll(",", "");
        if (percentage !== null && percentage !== undefined) {
            today_return_percent = parseFloat((today_return_1 / market_value) * 100).toLocaleString(
                "en-US",
                {maximumFractionDigits: 2, minimumFractionDigits: 2}
            );
        } else {
            today_return_percent = "\u2014"
        }

        if (today_return_1 < 0) {
            today_return = "-₹" + today_return + " (-" + Math.abs(today_return_percent) + "%" + ")"
        } else {
            today_return = "+₹" + today_return + " (+" + today_return_percent + "%" + ")"
        }
        $("#today_return").html(today_return);
    }
    // console.log(live_price, initial);

    color = "#ff5000";
    btn_color = "#ff5000";
    scatter_s_color = "rgba(255, 80, 0, 0.58)";
    scatter_s_color_status = false;

    if (difference >= 0) {
        difference = "+₹" + difference.toFixed(2);
        percentage = "+" + percentage.toFixed(2);

        btn_color = "#28a745";
        color = "#00ff39";
        scatter_s_color = "rgba(40, 167, 69, 0.58)";
        scatter_s_color_status = false;
    } else {
        // modding the actual value and displaying the minus in the text
        difference = "-₹" + (-1 * difference).toFixed(2);
        percentage = "" + percentage.toFixed(2);
        color = "#ff5000";
        btn_color = "#ff5000";
        scatter_s_color = "rgba(255, 80, 0, 0.58)";
        scatter_s_color_status = false;
    }

    changePlotColor(color);

    changeAccentColors({
        color: color,
        btn_color: btn_color,
        scatter_s_color: scatter_s_color,
        scatter_s_color_status: scatter_s_color_status,
        percentage: percentage,
        difference: difference,
    });
}

function calculate_return_value(symbol, initial) {
    /*
        function to calculate the return value
    */

    /*if (!initial) {
        initial = 0;
    }
    current = $(".stock_price").val();
    delta = current - initial;


    return {"delta_percent": (delta / initial) * 100, "delta": delta}*/

    // console.log(self.symbol, self.key, $(".stock_price").val(), initial);
    // get_price_change()
    stock_price = $(".stock_price").val()
    if (stock_price && initial) {
        get_price_change(self.symbol, self.key, stock_price, initial)
    }
}


function update_Chart() {
    chart = Highcharts.charts[0];
    var series = chart.series[0];
    var yVal;

    console.log("singleton1")
    $.ajax({
        url: '/singleton',
        type: 'GET',
        async: true,
        success: function (dat) {
            let updateSocket;
            setTimeout(function reconnect() {
                current_date = new Date()
                current_day_number = current_date.getDay()
                if (parseInt(current_day_number) != 7 && parseInt(current_day_number) != 0) {
                    protocol = "wss://";
                    if (window.location.host.includes("localhost") || window.location.host.includes("127.0.0.1")
                        || window.location.host.includes("0.0.0.0")) {
                        protocol = "ws://";
                    }
                    updateSocket = new WebSocket(
                        protocol + window.location.host + '/ws/wbs2/' + $("#stock_symbol").val()
                    );

                    updateSocket.onmessage = function(e) {
                        var chart = Highcharts.charts[0]
                        var series = chart.series[0];
                        var obj = jQuery.parseJSON(event.data);

                        var x = obj.timestamp, // current time
                        y = parseFloat(obj.price);

                        self.live_price = y;

                        $("#market_value").html("₹" + parseFloat(y * self.share_total_int).toLocaleString("en-US", {
                            maximumFractionDigits: 2, minimumFractionDigits: 2
                        }));
                        document.getElementById("symbol_price").textContent=y;
                        document.getElementById("market-price-ws").textContent=y.toFixed(2);

                        $(".stock_price").val(y);
                        od.update(y);
                        if (self.key === "1D") {
                            // console.log(obj);
                            // update graphs only when intra-day is selected.
                            // updates the graph if the market is opened now
                            if (self.is_market_open_today && obj.is_market_open_now && !self.updating) {
                                setTimeout(function() {
                                    series.addPoint([x, y], false, false);
                                    // chart.series[0].addPoint(Math.random()*100, true, true);
                                    self.max = x;
                                    chart.xAxis[0].update({
                                        max: self.max,
                                        min: self.min,
                                        range: 24 * 3600 * 1000
                                    });
                                    chart.redraw();
                                }, 50)
                            }
                            calculate_return_value2(y, $(".price_1D").val());
                        } else {
                            // calculate_return_value(self.symbol, $(".price_" + self.key).val());
                            calculate_return_value2(y, $(".price_" + self.key).val());
                        }

                        $("#market_value").html("₹" + parseFloat(y * self.share_total_int).toLocaleString("en-US", {
                            maximumFractionDigits: 2, minimumFractionDigits: 2
                        }));
                        document.getElementById("symbol_price").textContent=y;
                        document.getElementById("market-price-ws").textContent=y.toFixed(2);
                    };

                    updateSocket.disconnect = function(e) {
                        console.log("disconnect");
                        updateSocket.disconnect;
                    };

                    updateSocket.onclose = function(e) {
                        console.log("closing");
                        updateSocket.close();
                    };

                    updateSocket.onopen = function(e) {
                        console.log("Socket connected; sending a ping");

                        // closing the WebSocket Connection before the page is unloaded.
                        window.onbeforeunload = function() {
                            updateSocket.close();
                        };
                    }
                }
            }, 10);
        }
    });
}


function update_Chart_demo() {
    setInterval(function () {
        chart = Highcharts.charts[0];
        var series = chart.series[0];
        var yVal;
        yVal = 150;
        var x = (new Date()).getTime()+19800, // current time
            y = 100;
        series.addPoint([100, 200], true,true);
        chart.series[0].addPoint(Math.random()*100, true, true);
        series.setData([129.2, 144.0],[ 176.0, 135.6], [148.5, 216.4], [194.1, 95.6], [54.4, 29.9], [71.5, 106.4]);
        //chart.redraw();
    }, 1000);
}

function set_price_change(data) {
    if (data.color === "#00ff39") {
        self.color = "green"
    } else if (data.color === "#ff5000") {
        self.color = "red"
    } else {
        self.color = "blue"
    }
    changePlotColor(data.color);
    changeHighChartButtonTheme(self.color);
    // remove all other classes from the selector buttons
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");

    // enable the relevant color
    $("#btn_" + self.key.toLowerCase()).addClass("highlight-" + self.color);
    difference = data.difference;
    percentage = data.percentage;
    $(".price-change").html(difference);
    $(".price-change-percentage").html(percentage);
    $(".price-change-percentage-content").show();

    $(".btn-change-color").css("background-color",data.btn_color);
    $(".theme-color").val(data.btn_color);
    $(".btn-change-color").css("border-color",data.btn_color);
    $(".btn-change-color").css("color","#fff");

    $(".highcharts-series.highcharts-series-0.highcharts-line-series.highcharts-color-0").
        find(".highcharts-graph").css("stroke",data.color);
    $(".highcharts-markers.highcharts-series-0.highcharts-scatter-series.highcharts-tracker")
        .find("path").each(function() {
            $(this).css("fill",data.color)
        });

    $(".highcharts-markers.highcharts-series-1.highcharts-scatter-series.highcharts-tracker").
        find("path").each(function() {
            $(this).css("fill",data.scatter_s_color)
        });
    $("#circle").css("background-color",data.color);
    if (data.scatter_s_color_status) {
        $("#diamond").addClass("diamond_green");
        $("#diamond").removeClass("diamond_red");
    } else{
        $("#diamond").removeClass("diamond_green");
        $("#diamond").addClass("diamond_red");
    }
    $(".loadingio-spinner-spinner-lzgp9tuxt9").hide();
    //$("#diamond").css("border-bottom-color",data.scatter_s_color)
}

function changeAccentColors(data) {
    if (data.color === "#00ff39") {
        self.color = "green"
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    } else if (data.color === "#ff5000") {
        self.color = "red"
        $(".btn-change-color").addClass("btn-add-to-w-red");
        $(".btn-change-color").removeClass("btn-add-to-w");
    } else {
        self.color = "blue"
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    }
    changePlotColor(data.color);
    changeHighChartButtonTheme(self.color);

    if (self.color == "red") {
        $("#btn_1d").removeClass("btn-range-green");
        $("#btn_1m").removeClass("btn-range-green");
        $("#btn_3m").removeClass("btn-range-green");
        $("#btn_6m").removeClass("btn-range-green");
        $("#btn_1y").removeClass("btn-range-green");
        $("#btn_5y").removeClass("btn-range-green");

        $("#btn_1d").addClass("btn-range-red");
        $("#btn_1m").addClass("btn-range-red");
        $("#btn_3m").addClass("btn-range-red");
        $("#btn_6m").addClass("btn-range-red");
        $("#btn_1y").addClass("btn-range-red");
        $("#btn_5y").addClass("btn-range-red");

    } else if (self.color == "green") {
        $("#btn_1d").removeClass("btn-range-red");
        $("#btn_1m").removeClass("btn-range-red");
        $("#btn_3m").removeClass("btn-range-red");
        $("#btn_6m").removeClass("btn-range-red");
        $("#btn_1y").removeClass("btn-range-red");
        $("#btn_5y").removeClass("btn-range-red");

        $("#btn_1d").addClass("btn-range-green");
        $("#btn_1m").addClass("btn-range-green");
        $("#btn_3m").addClass("btn-range-green");
        $("#btn_6m").addClass("btn-range-green");
        $("#btn_1y").addClass("btn-range-green");
        $("#btn_5y").addClass("btn-range-green");
    } else {
        $("#btn_1d").removeClass("btn-range-red");
        $("#btn_1m").removeClass("btn-range-red");
        $("#btn_3m").removeClass("btn-range-red");
        $("#btn_6m").removeClass("btn-range-red");
        $("#btn_1y").removeClass("btn-range-red");
        $("#btn_5y").removeClass("btn-range-red");

        $("#btn_1d").removeClass("btn-range-green");
        $("#btn_1m").removeClass("btn-range-green");
        $("#btn_3m").removeClass("btn-range-green");
        $("#btn_6m").removeClass("btn-range-green");
        $("#btn_1y").removeClass("btn-range-green");
        $("#btn_5y").removeClass("btn-range-green");
    }

    // remove all other classes from the selector buttons
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
    $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");

    // enable the relevant color
    $("#btn_" + self.key.toLowerCase()).addClass("highlight-" + self.color);
    difference = data.difference;
    percentage = data.percentage;
    $(".price-change").html(difference);
    $(".price-change-percentage").html(percentage);
    $(".price-change-percentage-content").show();

    $(".btn-change-color").css("background-color",data.btn_color);
    $(".theme-color").val(data.btn_color);
    $(".btn-change-color").css("border-color",data.btn_color);
    $(".btn-change-color").css("color","#fff");

    $(".highcharts-series.highcharts-series-0.highcharts-line-series.highcharts-color-0").
        find(".highcharts-graph").css("stroke",data.color);
    $(".highcharts-markers.highcharts-series-0.highcharts-scatter-series.highcharts-tracker")
        .find("path").each(function() {
            $(this).css("fill",data.color)
        });

    $(".highcharts-markers.highcharts-series-1.highcharts-scatter-series.highcharts-tracker").
        find("path").each(function() {
            $(this).css("fill",data.scatter_s_color)
        });
    $("#circle").css("background-color",data.color);
    if (data.scatter_s_color_status) {
        $("#diamond").addClass("diamond_green");
        $("#diamond").removeClass("diamond_red");
    } else{
        $("#diamond").removeClass("diamond_green");
        $("#diamond").addClass("diamond_red");
    }
    $(".loadingio-spinner-spinner-lzgp9tuxt9").hide();
    //$("#diamond").css("border-bottom-color",data.scatter_s_color)

    if (data.color === "#00ff39") {
        self.color = "green"
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    } else if (data.color === "#ff5000") {
        self.color = "red"
        $(".btn-change-color").addClass("btn-add-to-w-red");
        $(".btn-change-color").removeClass("btn-add-to-w");
    } else {
        self.color = "blue"
        $(".btn-change-color").removeClass("btn-add-to-w-red");
        $(".btn-change-color").addClass("btn-add-to-w");
    }
}

function get_price_change(symbol, key, live_price, prev_price) {
    $.ajax({
        url: '/accounts/dashboard/api/stocks/',
        type: 'GET',
        async: true,
        data: {
            'type': 'price_change',
            'key': key,
            'live_price': live_price,
            'prev_price': prev_price,
            'symbol': symbol
        },
        success: function (data) {
            if (data.color === "#00ff39") {
                self.color = "green"
            } else if (data.color === "#ff5000") {
                self.color = "red"
            } else {
                self.color = "blue"
            }
            changeHighChartButtonTheme(self.color);
            // remove all other classes from the selector buttons
            $("#btn_" + self.key.toLowerCase()).removeClass("highlight-blue");
            $("#btn_" + self.key.toLowerCase()).removeClass("highlight-red");
            $("#btn_" + self.key.toLowerCase()).removeClass("highlight-green");

            // enable the relevant color
            $("#btn_" + self.key.toLowerCase()).addClass("highlight-" + self.color);
            difference = data.difference;
            percentage = data.percentage;
            $(".price-change").html(difference);
            $(".price-change-percentage").html(percentage);
            $(".price-change-percentage-content").show();

            $(".btn-change-color").css("background-color",data.btn_color);
            $(".theme-color").val(data.btn_color);
            $(".btn-change-color").css("border-color",data.btn_color);
            $(".btn-change-color").css("color","#fff");

            $(".highcharts-series.highcharts-series-0.highcharts-line-series.highcharts-color-0").
                find(".highcharts-graph").css("stroke",data.color);
            $(".highcharts-markers.highcharts-series-0.highcharts-scatter-series.highcharts-tracker")
                .find("path").each(function() {
                    $(this).css("fill",data.color)
                });

            $(".highcharts-markers.highcharts-series-1.highcharts-scatter-series.highcharts-tracker").
                find("path").each(function() {
                    $(this).css("fill",data.scatter_s_color)
                });
            $("#circle").css("background-color",data.color);
            if (data.scatter_s_color_status) {
                $("#diamond").addClass("diamond_green");
                $("#diamond").removeClass("diamond_red");
            } else{
                $("#diamond").removeClass("diamond_green");
                $("#diamond").addClass("diamond_red");
            }
            $(".loadingio-spinner-spinner-lzgp9tuxt9").hide();
            //$("#diamond").css("border-bottom-color",data.scatter_s_color)
        }
    })
}

getUpcomingActivities = () => {
    if (self.is_auth == 1) {
        axios.get(
            "/accounts/dashboard/api/upcoming_activity/" + self.symbol
        ).then((res) => {
            console.log(res.data.count);
            console.log(res.data.upcoming);
            if (res.data.count > 0) {
                $("#upcoming_wrapper").css("display", "block");

                for (transaction of res.data.upcoming) {
                    html = '<tr style="color: white;"><td>' + transaction.symbol + '</td>' +
                        '<td>' + transaction.order_type + ' - ' + transaction.transaction_type + '</td>' +
                        '<td>' + transaction.expires + '</td>' +
                        '<td>₹' + transaction.limit_price.toLocaleString("en-US", {maximumFractionDigits: 2, minimumFractionDigits: 2}) + '</td>' +
                        '<td>' + transaction.size.toLocaleString("en-US", {maximumFractionDigits: 0, minimumFractionDigits: 0}) + '</td>' +
                        '<td>' + transaction.status + '</td></tr>';
                    $("#upcoming_table").append(html);
                }
            }
        }).catch((err) => {
        });
    }
}

self.getStockList = function(interval) {

    if (self.is_auth == 1) {
        if (self.stockListToken !== null) {
            self.stockListToken.cancel();
            self.stockListToken = null;
        }
        self.stockListToken = axios.CancelToken.source();
        axios.get(
            "/accounts/dashboard/api/stock_summary/", {
                cancelToken: self.stockListToken.token
            }
        ).then(function(data) {
            self.stockListToken = null;
            $("#stock_list").html("");
            for (stock of data.data.data) {
                percentage = stock.percentage.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                }) + "%";
                live_price = "₹" + stock.live_price.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                });
                html = "";
                if (stock.percentage >= 0) {
                    html = '<div class="stock-detail pb-2 pt-2" id="stock_' + stock.ticker + '"' + '>' +
                        '<div class="col-md-5 col-sm-4 padding-right-7"><div class="stock-name">' +
                            '<p>' + stock.ticker + '</p>' +
                            // '<a href="/accounts/dashboard/stocks/NSE:' + stock.ticker + '/" style="color: white;">'+ stock.ticker + '</a>' +
                            '<p class="num-of-shares">' + stock.shares + ' shares</p>' +
                        '</div></div>' +
                        '<div class="col-md-3 col-sm-4 padding-0"><div class="stock-graph"></div></div>' +
                        '<div class="col-md-4 col-sm-4 padding-left-7"><div class="stock-price">' +
                        '<p>' + live_price + '</p>' +
                        '<p class="trade-gain">' + percentage + '</p>' +
                        '</div></div>' +
                    '</div>';
                } else {
                    html = '<div class="stock-detail pb-2 pt-2" id="stock_' + stock.ticker + '"' + '>' +
                        '<div class="col-md-5 col-sm-4 padding-right-7"><div class="stock-name">' +
                            '<p>' + stock.ticker + '</p>' +
                            // '<a href="/accounts/dashboard/stocks/NSE:' + stock.ticker + '/" style="color: white;">'+ stock.ticker + '</a>' +
                            '<p class="num-of-shares">' + stock.shares + ' shares</p>' +
                        '</div></div>' +
                        '<div class="col-md-3 col-sm-4 padding-0"><div class="stock-graph"></div></div>' +
                        '<div class="col-md-4 col-sm-4 padding-left-7"><div class="stock-price">' +
                        '<p>' + live_price + '</p>' +
                        '<p class="trade-loss">' + percentage + '</p>' +
                        '</div></div>' +
                    '</div>';
                }
                $("#stock_list").append(html);
            }
        }).catch(function(err) {
            self.stockListToken = null;
        });
        if (interval) {
            setInterval(function() {
                self.getStockList(false);
            }, 10*1000);
        }
    }
}

self.getWatchList = function(interval) {
    if (self.is_auth == 1) {
        if (self.watchListToken !== null) {
            self.watchListToken.cancel();
            self.watchListToken = null;
        }
        self.watchListToken = axios.CancelToken.source();
        axios.get(
            "/accounts/dashboard/api/watchlist/", {
                cancelToken: self.watchListToken.token
            }
        ).then(function(data) {
            self.watchListToken = null;
            $("#watch_list").html("");
            for (stock of data.data.data) {
                percentage = stock.percentage.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                }) + "%";
                live_price = "₹" + stock.live_price.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                });
                html = "";
                console.log(stock.percentage >= 0);
                if (stock.percentage >= 0) {
                    html = '<div class="stock-detail pb-2 pt-2" id="watch_' + stock.ticker + '"' + '>' +
                        '<div class="col-md-5 col-sm-4 padding-right-7"><div class="stock-name">' +
                            '<p>' + stock.ticker + '</p>' +
                            // '<a href="/accounts/dashboard/stocks/NSE:' + stock.ticker + '/" style="color: white;">'+ stock.ticker + '</a>' +
                            '<p class="num-of-shares">' + "" + '</p>' +
                        '</div></div>' +
                        '<div class="col-md-3 col-sm-4 padding-0"><div class="stock-graph"></div></div>' +
                        '<div class="col-md-4 col-sm-4 padding-left-7"><div class="stock-price">' +
                        '<p>' + live_price + '</p>' +
                        '<p class="trade-gain">' + percentage + '</p>' +
                        '</div></div>' +
                    '</div>';
                } else {
                    html = '<div class="stock-detail pb-2 pt-2" id="watch_' + stock.ticker + '"' + '>' +
                        '<div class="col-md-5 col-sm-4 padding-right-7"><div class="stock-name">' +
                            '<p>' + stock.ticker + '</p>' +
                            // '<a href="/accounts/dashboard/stocks/NSE:' + stock.ticker + '/" style="color: white;">'+ stock.ticker + '</a>' +
                            '<p class="num-of-shares">' + "" + '</p>' +
                        '</div></div>' +
                        '<div class="col-md-3 col-sm-4 padding-0"><div class="stock-graph"></div></div>' +
                        '<div class="col-md-4 col-sm-4 padding-left-7"><div class="stock-price">' +
                        '<p>' + live_price + '</p>' +
                        '<p class="trade-loss">' + percentage + '</p>' +
                        '</div></div>' +
                    '</div>';
                }
                $("#watch_list").append(html);
            }
        }).catch(function(err) {
            self.watchListToken = null;
        });
        if (interval) {
            setInterval(function() {
                self.getWatchList(false);
            }, 10*1000);
        }
    }
}

self.getMostActive = function(interval) {
    if (self.activeListToken !== null) {
        self.activeListToken.cancel();
        self.activeListToken = null;
    }
    self.activeListToken = axios.CancelToken.source();

    axios.get(
        "/accounts/dashboard/api/most_active/", {
            cancelToken: self.activeListToken.token
        }
    ).then(function(data) {
        self.activeListToken = null;
        /*$("#watch_list").html("");*/
        for (stock of data.data.active) {
            percentage = stock.change.toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            }) + "%";
            live_price = "₹" + stock.price.toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
            html = "";
            if (percentage >= 0) {
                html = '';
            } else {
                html = '';
            }
            /*$("#watch_list").append(html);*/
        }
        if (data.data.count > 0) {
            // refresh the carousel
        }
    }).catch(function(err) {
        self.activeListToken = null;
    });
    if (interval) {
        setInterval(function() {
            self.getMostActive(false);
        }, 10*1000);
    }
}

function btn_d1() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[0].setState(3);
    chart.rangeSelector.buttonOptions[0].events.click()
    // chart.rangeSelector.clickButton(0, true);
}

function btn_m1() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[1].setState(3);
    chart.rangeSelector.buttonOptions[1].events.click()
    // chart.rangeSelector.clickButton(1, true);
}

function btn_m3() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[2].setState(3);
    chart.rangeSelector.buttonOptions[2].events.click()
    // chart.rangeSelector.clickButton(2, true);
}

function btn_m6() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[3].setState(3);
    chart.rangeSelector.buttonOptions[3].events.click()
    // chart.rangeSelector.clickButton(3, true);
}

function btn_y1() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[4].setState(3);
    chart.rangeSelector.buttonOptions[4].events.click()
    // chart.rangeSelector.clickButton(4, true);
}

function btn_y5() {
    chart = Highcharts.charts[0];
    chart.rangeSelector.buttons[5].setState(3);
    chart.rangeSelector.buttonOptions[5].events.click()
    // chart.rangeSelector.clickButton(5, true);
}

self.getStockList(true);
self.getWatchList(true);

$(document).ready(function() {
    // get data every 15 seconds
    // this api will be called only for the user who has bought the share
    $('.stock-detail-col').on('click', '.stock-detail', function() {
        // do something here
        stock = $(this).attr("id").replaceAll("watch_", "").replaceAll("stock_", "");
        window.location.href = "/accounts/dashboard/stocks/NSE:" + stock + "/";
    });
    getUpcomingActivities();
    /*self.getStockList(true);
    self.getWatchList(true);*/
    // self.getMostActive(false);
    if (share_total_int && share_total_int > 0) {
        setInterval(function() {
            getGainLoss();
        }, 10000);
    }
    if($("#stock_symbol").val().length) {
        update_Chart();
        //update_Chart_demo();
    }
})
