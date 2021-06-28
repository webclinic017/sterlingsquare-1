var self = this;

self.portfolioWebSocket = null;
self.grey = "#b2b2b2"
self.grey_rgb = "rgba(178, 178, 178)"
self.empty_graph = false;

self.updateGraphToken = null;
self.watchListToken = null;
self.stockListToken = null;
self.activeListToken = null;

self.buying_power = buying_power;

self.m1_greyed = false;
self.m3_greyed = false;
self.m6_greyed = false;
self.y1_greyed = false;
self.y5_greyed = false;

var el = document.querySelector('.odometer');

// self.share_total_int = share_total_int;

function getGainLoss() {
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

self.live_price = lp;


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
    // $(".inp-stock-num").val(self.share_total_int);
    $("#buying_power").html("₹" + parseFloat(self.buying_power).toLocaleString("en-US", {
        maximumFractionDigits: 2, minimumFractionDigits: 2
    }));
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
    } else if (self.color === "red") {
        $("#btn_" + self.key.toLowerCase()).addClass("highlight-red");
    } else {
        $("#btn_" + self.key.toLowerCase()).addClass("highlight-blue");
    }

    difference = parseFloat(init_intra_change.difference.replaceAll(",", "").replaceAll("₹", ""));
    percentage = parseFloat(init_intra_change.percentage.replaceAll("+", ""));

    if (difference >= 0) {
        difference = "+₹" + difference.toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
        if (percentage >= 0) {
            percentage = "+" + Math.abs(percentage).toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
        } else {
            percentage = "-" + Math.abs(percentage).toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
        }
    } else {
        difference = "-₹" + (-1 * difference).toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
        percentage = "" + percentage.toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
    }

    $(".price-change").html(difference);
    $(".price-change-percentage").html(percentage);
    $(".price-change-percentage-content").show();

    console.log(open_values);
    // initial values
    $(".price_1D").val(open_values['1D']);
    $(".price_1m").val(open_values['1m']);
    $(".price_3m").val(open_values['3m']);
    $(".price_6m").val(open_values['6m']);
    $(".price_1y").val(open_values['1y']);
    $(".price_5y").val(open_values['5y']);

    console.log(portfolio_values)

    $(".price_port_value_1D").val(portfolio_values['1D']);
    $(".price_port_value_1m").val(portfolio_values['1m']);
    $(".price_port_value_3m").val(portfolio_values['3m']);
    $(".price_port_value_6m").val(portfolio_values['6m']);
    $(".price_port_value_1y").val(portfolio_values['1y']);
    $(".price_port_value_5y").val(portfolio_values['5y']);
}, 10);

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

init_stock_price = parseFloat($(".stock_price").val()).toLocaleString(
    "en-US",
    {maximumFractionDigits: 2, minimumFractionDigits: 2}
);
od.update(init_stock_price);

var symbol = $("#stock_symbol").val()
self.symbol = symbol;
var data = [], time = (new Date()).getTime(), i;

self.dailyOpenValue = null;

function setupWebSocket(latest_time_stamp) {
    if (self.portfolioWebSocket) {
        return null;
    }

    protocol = "wss://";
    if (window.location.host.includes("localhost") || window.location.host.includes("127.0.0.1")
        || window.location.host.includes("0.0.0.0")) {
        protocol = "ws://";
    }

    self.portfolioWebSocket = new WebSocket(
        protocol + window.location.host + '/ws/portfolio/'
    );

    self.portfolioWebSocket.onmessage = function(e) {
        data = JSON.parse(event.data);
        self.is_market_open_now = data.is_market_open_now;
        if (data.count && data.count > 0) {
            var chart = Highcharts.charts[0]
            var series = chart.series[0];
            // var series2 = chart.series[1];
            points = data.data_points;
            // only add points if the data is returned by the ws, and graph is on "1D" mode
            // and the market is opened right now
            if (points.length > 0 && self.key === "1D" && self.is_market_open_now) {
                for (point of points) {
                    series.addPoint([point[0], point[2]], false, false);
                    //series2.addPoint([point[0], point[2]], false, false);
                }
                chart.xAxis[0].update({
                    max: self.max,
                    min: self.min,
                    range: 24 * 3600 * 1000
                });
                chart.redraw();
            }
            od.update(data.portfolio_value);
            self.live_price = data.gl_value;
            if (self.key === "1D") {
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
            } else {
                if (!self.empty_graph) {
                    calculate_return_value2(
                        self.live_price, parseFloat($(".price_" + self.key).val()),
                        parseFloat($(".price_port_value_" + self.key).val())
                    );
                } else {
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
                /*if (self.key === "1m" && !self.m1_greyed) {
                    calculate_return_value2(self.live_price, parseFloat($(".price_" + self.key).val()));
                } else if (self.key === "1m" && self.m1_greyed) {
                    // calculate_return_value2(self.live_price, parseFloat($(".price_" + self.key).val()));
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
                if (self.key === "3m" && !self.m3_greyed) {
                    // calculate_return_value2(self.live_price, parseFloat($(".price_" + self.key).val()));
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
                if (self.key === "6m" && !self.m6_greyed) {
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
                if (self.key === "1y" && !self.y1_greyed) {
                    // calculate_return_value2(self.live_price, parseFloat($(".price_" + self.key).val()));
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
                if (self.key === "5y" && !self.y5_greyed) {
                    // calculate_return_value2(self.live_price, parseFloat($(".price_" + self.key).val()));
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }*/
            }
        }
    }

    self.portfolioWebSocket.onopen = function() {
        // closing the WebSocket Connection before the page is unloaded.
        console.log("connected", moment(last_time_stamp).format("HH:mm:ss"));
        window.onbeforeunload = function() {
            self.portfolioWebSocket.close();
        };
        self.portfolioWebSocket.send(JSON.stringify({
            "last": moment(last_time_stamp).format("HH:mm:ss")
        }));
    }

    self.portfolioWebSocket.disconnect = function(e) {
        console.log("disconnect");
        self.portfolioWebSocket.disconnect();
    };

    self.portfolioWebSocket.onclose = function(e) {
        console.log("closing");
        self.portfolioWebSocket.close();
    };
}

function initializeIntraDayData() {
    axios.get(
        "/accounts/dashboard/api/portfolio/historical/?interval=1D"
    ).then(function(data) {
        dat = data.data;

        setTimeout(function() {
            difference = parseFloat(init_intra_change.difference.replaceAll(",", "").replaceAll("₹", ""));
            if (difference >= 0) {
                changeHighChartButtonTheme('green');
            } else {
                changeHighChartButtonTheme('red');
            }
        }, 1);

        /*setTimeout(function() {
            changeAccentColors(init_intra_change);
        }, 1);*/

        data = dat.data;
        self.max = data[data.length - 1][0] + 100;
        self.dailyOpenValue = dat.open_value;
        // $(".price_1D").val(dat.open_value);
        var chart = Highcharts.charts[0], series = chart.series[0];

        var chart = Highcharts.charts[0];
        var series = chart.series[0];
        // var series2 = chart.series[1];
        series.update({
            /*"data": dat.data*/
            "data": dat.data2
        }, true);
        /*series2.update({
            "data": dat.data2
        }, true);*/
        chart.xAxis[0].update({
            max: self.max,
            min: self.min
        });

        // after the chart has been rendered, setup the web socket.
        last_time_stamp = dat.data[dat.data.length - 1][0];
        setupWebSocket(last_time_stamp);
    }).catch(function() {
    });
}

function initialiseBoxes() {
    axios.get("/singleton").then((res) => {
        getGainLoss();
    }).catch((err) => {
        getGainLoss();
    });

    /*$.ajax({
        url: '/singleton',
        type: "GET",
        async: false,
        error: function() {

        },
        success: function() {
            getGainLoss();
        }
    })*/
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

updateGraphData = function(key, live_price, prev_price, retry) {
    // function to be called when the interval is changed.
    if (self.updateGraphToken !== null) {
        self.updateGraphToken.cancel();
        self.updateGraphToken = null;
    }
    self.key = key;
    self.updating = true;
    var chart = Highcharts.charts[0];
    var series = chart.series[0];
    // var series2 = chart.series[1];

    series.update({
        "data": []
    });
    /*series2.update({
        "data": []
    });*/
    self.updateGraphToken = axios.CancelToken.source();
    axios.get(
        "/accounts/dashboard/api/portfolio/historical/?interval=" + self.key, {
            cancelToken: self.updateGraphToken.token
        }
    ).then(function(dat) {
        self.updateGraphToken = null;
        data = dat.data;
        chart_data = data.data;

        empty = false;
        if (data.empty) {
            empty = data.empty;
        } else {
            empty = false;
        }
        self.empty_graph = empty;

        if (chart_data === null || chart_data === undefined) {
            updateGraphData(key, live_price, prev_price, retry);
        }
        var chart = Highcharts.charts[0];
        var series = chart.series[0];

        if (data.status === 200 && chart_data.length > 0) {
            series.update({
                /*"data": chart_data*/
                "data": data.data2
            });
            /*series2.update({
                "data": data.data2
            }, true);*/

            self.live_price = data.live_gl;
            console.log("self.live_price ", self.live_price);

            index = 0;
            if (key === "1D") {
                index = 0;
                chart.xAxis[0].update({
                    max: self.max,
                    min: self.min,
                    range: 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
            }
            else if (key == "5y") {
                index = 5;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 5 * 370 * 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
                if (empty) {
                    self.y5_greyed = data.greyed_out;
                    if (data.greyed_out) {
                        changePlotColor(self.grey);
                        changeAccentColors({
                            color: self.grey,
                            btn_color: self.grey,
                            scatter_s_color: self.grey_rgb,
                            scatter_s_color_status: true,
                            percentage: null,
                            difference: null,
                        });
                    }
                }
            }
            else if (key == "1y") {
                index = 4;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 1 * 370 * 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
                if (empty) {
                    self.y1_greyed = data.greyed_out;
                    if (data.greyed_out) {
                        changePlotColor(self.grey);
                    }
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
            }
            else if (key == "6m") {
                index = 3;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 6 * 31 * 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
                if (empty) {
                    self.m6_greyed = data.greyed_out;
                    if (data.greyed_out) {
                        changePlotColor(self.grey);
                    }
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
            }
            else if (key == "3m") {
                index = 2;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 3 * 31 * 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
                if (empty) {
                    self.m3_greyed = data.greyed_out;
                    if (data.greyed_out) {
                        changePlotColor(self.grey);
                    }
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
            }
            else if (key == "1m") {
                index = 1;
                chart.xAxis[0].update({
                    max: data.max,
                    min: data.min,
                    range: 1 * 31 * 24 * 3600 * 1000
                });
                calculate_return_value2(
                    self.live_price, parseFloat($(".price_" + self.key).val()),
                    parseFloat($(".price_port_value_" + self.key).val())
                );
                if (empty) {
                    self.m1_greyed = data.greyed_out;
                    if (data.greyed_out) {
                        changePlotColor(self.grey);
                    }
                    changeAccentColors({
                        color: self.grey,
                        btn_color: self.grey,
                        scatter_s_color: self.grey_rgb,
                        scatter_s_color_status: true,
                        percentage: null,
                        difference: null,
                    });
                }
            }

            setTimeout(function() {
                self.updating = false;
            }, 2000);
            console.log("will retry? ", series.data.length !== chart_data.length);
            changeHighChartButtonTheme(self.color);
            if (series.data.length !== chart_data.length && retry < 10) {
                // Recursive call to this function
                console.log("retry");
                changeHighChartButtonTheme(self.color);
                updateGraphData(key, live_price, prev_price, retry + 1);
            } else {
                changeHighChartButtonTheme(self.color);
                return;
            }
            changeHighChartButtonTheme(self.color);
        }
    }).catch(function() {
        self.updateGraphToken = null;
    });
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

            /*y2 = this.points[1].y;*/
            formattedNumber = parseFloat(this.y).toLocaleString(
                "en-US",
                {maximumFractionDigits: 2, minimumFractionDigits: 2}
            )
            /*formattedNumber2 = parseFloat(y2).toLocaleString(
                "en-US",
                {maximumFractionDigits: 2, minimumFractionDigits: 2}
            )*/
            /*return "<b>" + ts + "<br>Value: ₹ " + formattedNumber + "<br>Gain/Loss: ₹ " + formattedNumber2 + "</b>";*/
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
                    stroke: '#5e81a7',
                    fill: '#131722',
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
                        updateGraphData(key, live_price, prev_price, 0);
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
                        updateGraphData(key, live_price, prev_price, 0);
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
                        updateGraphData(key, live_price, prev_price, 0);
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
                        /*if ($(".has_stock").val() == "True") {
                            get_price_change(symbol, key, live_price, prev_price)
                        }*/
                        updateGraphData(key, live_price, prev_price, 0);
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
                        updateGraphData(key, live_price, prev_price, 0);
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
                        updateGraphData(key, live_price, prev_price, 0);
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
    }, /*{
        id: "stock_series_2",
        name: 'stock2',
        data: []
    }*/],
    time: {
        timezone: 'Asia/Kolkata'
    }
});

initializeIntraDayData();
// initialiseBoxes();

function changeHighChartButtonTheme(color) {
    if (color === "red") {
        color = "#ff5000";
    } else if (color === "green") {
        color = "#00ff39";
    } else if (color === "grey") {
        color = self.grey;
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


function calculate_return_value2(live_price, initial, denominator) {
    console.log(live_price, initial, denominator);
    difference = (live_price - initial);
    // old logic before 02-Mar-2020
    /*if (initial != 0) {
        percentage = ((difference / initial) * 100);
    } else {
        percentage = 0.0;
    }*/

    // new logic 02-Mar-2020
    if (denominator && denominator != 0) {
        percentage = ((difference / denominator) * 100);
    } else {
        percentage = 0.0;
    }
    console.log("===>> ", difference, percentage, denominator)

    /*if (self.key === "1D" && self.share_total_int > 0) {
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

        if (percentage !== null && percentage !== undefined) {
            today_return_percent = parseFloat(Math.abs(percentage)).toLocaleString(
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
        $("#today_return").html(today_return);
    }*/
    // console.log(live_price, initial);

    color = "#ff5000";
    btn_color = "#ff5000";
    scatter_s_color = "rgba(255, 80, 0, 0.58)";
    scatter_s_color_status = false;

    if (difference >= 0) {
        // difference = "+₹" + difference.toFixed(2);
        difference = "+₹" + difference.toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
        // percentage = "+" + percentage.toFixed(2);
        if (percentage >= 0) {
            percentage = "+" + Math.abs(percentage).toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
        } else {
            percentage = "-" + Math.abs(percentage).toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
        }

        btn_color = "#28a745";
        color = "#00ff39";
        scatter_s_color = "rgba(40, 167, 69, 0.58)";
        scatter_s_color_status = false;
    } else {
        // modding the actual value and displaying the minus in the text
        // difference = "-₹" + (-1 * difference).toFixed(2);
        difference = "-₹" + (-1 * difference).toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
        // percentage = "" + percentage.toFixed(2);
        percentage = "" + percentage.toLocaleString("en-US", {
            maximumFractionDigits: 2, minimumFractionDigits: 2
        });
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


function changeAccentColors(data) {
    if (data.color === "#00ff39") {
        self.color = "green"
    } else if (data.color === "#ff5000") {
        self.color = "red"
    } else if (data.color === self.grey) {
        self.color = "grey"
    } else {
        self.color = "blue"
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

    if (data.difference && data.percentage) {
        difference = data.difference;
        percentage = data.percentage;
        $(".price-change").html(difference);
        $(".price-change-percentage").html(percentage);
        $(".price-change-percentage-content").show();
    }

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

self.getStockList = function(interval) {

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

self.getWatchList = function(interval) {
    console.log("self.getWatchList self.getWatchListself.getWatchList")
    if (self.watchListToken !== null) {
        self.watchListToken.cancel();
        self.watchListToken = null;
    }
    self.watchListToken = axios.CancelToken.source();
    console.log("getWatchList ", interval)
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
            console.log(stock.percentage >= 0)
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
    console.log("interval ", interval)
    if (interval) {
        code = setInterval(function() {
            self.getWatchList(false);
        }, 10*1000);
        console.log("watchlist code ", code);
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
    /*self.getStockList(true);
    self.getWatchList(true);*/
    // self.getMostActive(false);

    $('.stock-detail-col').on('click', '.stock-detail', function() {
        // do something here
        stock = $(this).attr("id").replaceAll("watch_", "").replaceAll("stock_", "");
        window.location.href = "/accounts/dashboard/stocks/NSE:" + stock + "/";
    });
})
