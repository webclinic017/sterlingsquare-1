var self = this;

self.searchToken = null;
$(document).ready(function(){
    // var yVal = {{stockprice}}
    // console.log(yVal)
    var has_pos = $(".has_position").val()
    // console.log({{has_position}})
    if (has_pos)
    {
        //$("#container").empty()

        $(".loadingio-spinner-spinner-lzgp9tuxt9").show()
        setTimeout(function() {
            $(".highcharts-button").each(function () {

                if ($(this).hasClass("highcharts-button-pressed")) {
                    var key = $(this).find("text").html()
                    prev_price = $(".price_" + key).val()
                    live_price = $(".stock_price").val()
                    get_price_change(symbol, key, live_price, prev_price)
                    return false;
                }

            })

        },500)
        updateWatchlist()

    }
})

function highlight_letter(keyword) {
    $(".s-result-code").each(function () {
        var word = keyword
        element = $(this)
        var rgxp = new RegExp(word, 'g');
        var repl = '<span class="highlighted">' + word + '</span>';
        // element.innerHTML = element.innerHTML.replace(rgxp, repl);
        old_val = $(this).html();
        new_val = old_val.replace(rgxp, repl)
        $(this).html(new_val)
    })
}

$(document).on("keyup", ".stock-search", function () {
    var keyword = $(".stock-search").val().trim()
    $("#stock-auto-search").empty()
    if (keyword) {
        if (self.searchToken !== null) {
            self.searchToken.cancel();
            self.searchToken = null;
        }
        self.searchToken = axios.CancelToken.source();
        axios.get(
            "/accounts/dashboard/stock-search/?symbol="+keyword, {
                cancelToken: self.searchToken.token
            }
        ).then((res) => {
            self.searchToken = null;
            data = res.data;
            $("#stock-auto-search").empty()
            console.log(data.stock_list)
            for (var i = 0, l = data.stock_list.length; i < l; i++) {
                var symbol = data.stock_list[i]['symbol']
                var name = data.stock_list[i]['name']
                var html = '<div class="row search-result"><div class="col-sm-4"><p class="s-result-code name_id">' + symbol + '</p></div><div class="col-sm-8"><p class="s-result-name name_id">' + name + '</p></div></div>'
                $(".dropdown-content").append(html)
                $(".dropdown-content").show()
            }
        });

        /*$.ajax({
            url: '/accounts/dashboard/stock-search/',
            type: 'GET',
            async: true,
            data: {
                'symbol': keyword
            },
            success: function (data) {
                $("#stock-auto-search").empty()
                console.log(data.stock_list)
                for (var i = 0, l = data.stock_list.length; i < l; i++) {
                    var symbol = data.stock_list[i]['symbol']
                    var name = data.stock_list[i]['name']
                    var html = '<div class="row search-result"><div class="col-sm-4"><p class="s-result-code name_id">' + symbol + '</p></div><div class="col-sm-8"><p class="s-result-name name_id">' + name + '</p></div></div>'
                    $(".dropdown-content").append(html)
                    $(".dropdown-content").show()

                }
            }
        })*/

    } else {
        $(".dropdown-content").hide()
    }
})

$(document).on("click", ".dash-right-col-title-arrow", function () {
    $(".dash-right-col-dropdown").toggleClass("show")
})

$(document).on("click", ".dash-right-col-title-arrow-2", function () {
    $(".dash-right-col-dropdown-2").toggleClass("show")
})


$(document).on("click", ".s-result-code", function () {
  console.log("called");
    symbol = $(this).html()
        $(".loadingio-spinner-spinner-lzgp9tuxt9").show()
             $(".dropdown-content").hide()
            $("#stock-auto-search").empty()
  window.location.href='/accounts/dashboard/stocks/NSE:'+`${symbol}/`;
// setTimeout(function(){
//     // window.location.href='/accounts/dashboard/stocks/NSE:'+`${symbol}/`;
//     $.ajax({
//                 url:'/accounts/dashboard/stocks/NSE:'+`${symbol}/`,
//                 type:'GET',
//                 // data:{
//                 //     'type':'get_stock_details',
//                 //     'symbol':symbol
//                 // },
//                 success:function(data){
//                 if (data.has_history == "True"){
//                 console.log("data.has_history    ",data.has_history)
//                                         $("#container").empty()
//
//                     $(".top-g-con").show()
//
//
//                     $(".line-chart-main").replaceWith(data.line_chart_html)
//                     $(".scatter_plot_con").replaceWith(data.scatter_plot_html)
//                     $(".market-pairs").replaceWith(data.stock_market_settings_html)
//                     $(".company_info").replaceWith(data.company_info_html)
//                     $(".has_stock").val("True")
//                     $(".highcharts-series.highcharts-series-0.highcharts-line-series.highcharts-color-0").find(".highcharts-graph").css("stroke",data.color)
//                     AddReadMore();
//                     $(".price_1D").val(data.prev_day_price)
//                     $(".price_1m").val(data.prev_month_price)
//                     $(".price_3m").val(data.prev_3m_price)
//                     $(".price_6m").val(data.prev_6m_price)
//                     $(".price_1y").val(data.prev_y_price)
//                     $(".highcharts-button").each(function(){
//
//                         if($(this).hasClass("highcharts-button-pressed")){
//                             var key = $(this).find("text").html()
//                             prev_price = $(".price_"+key).val()
//                             live_price = $(".stock_price").val()
//                             get_price_change(symbol,key,live_price,prev_price)
//                            return false;
//                         }
//
//                     })
//                     if (data.tr_status == "True"){
//                         $(".ua-content").replaceWith(data.up_activity_html)
//                         $(".ua-content").show()
//                     }
//                     $(".pos-tabl-details-content").replaceWith(data.pos_table_details_html)
//                     $(".pos-tabl-details-content").show()
//   $('.dataTables_length').addClass('bs-select');
//                     $(".inp-stock-num").val(data.stock_num)
//                             $(".loadingio-spinner-spinner-lzgp9tuxt9").hide()
//
//
//                 }else{
//                  console.log("data.h______________    ",data.has_history)
//                 alert("Stock has no data")
//                 location.reload()
//                 }
//                 }
//
//             })
//             }, 500);
})

$(document).on("keyup", ".share-num", function () {
    var num = $(this).val()
    if (num != "") {
        price = $("#market-price-ws").text()
        total = parseFloat(price) * parseFloat(num)
        $(".total-market-price").html(total.toFixed(2))
    }else{
        $(".total-market-price").html("0.00")
    }
})


function AddReadMore() {
    //This limit you can set after how much characters you want to show Read More.
    var carLmt = 280;
    // Text to show when text is collapsed
    var readMoreTxt = " ... Read More";
    // Text to show when text is expanded
    var readLessTxt = " Read Less";


    //Traverse all selectors with this class and manupulate HTML part to show Read More
    $(".addReadMore").each(function () {
        if ($(this).find(".firstSec").length)
            return;

        var allstr = $(this).text();
        if (allstr.length > carLmt) {
            var firstSet = allstr.substring(0, carLmt);
            var secdHalf = allstr.substring(carLmt, allstr.length);
            var strtoadd = firstSet + "<span class='SecSec'>" + secdHalf + "</span><span style='color: #fff;font-weight: 800' class='readMore'  title='Click to Show More'>" + readMoreTxt + "</span><span style='color: #fff;font-weight: 800' class='readLess' title='Click to Show Less'>" + readLessTxt + "</span>";
            $(this).html(strtoadd);

        }

    });
    //Read More and Read Less Click Event binding

}

//$(function() {
//    //Calling function after Page Load
//    AddReadMore();
//});
//$(".readMore").click(function(){

$(document).on("click", ".readMore,.readLess", function () {

    $(this).closest(".addReadMore").toggleClass("showlesscontent showmorecontent");
    $(".show-staff-details").toggle()

        $(".show-staff-details").toggle()
        $(".read-more").toggle();


});
$(document).on("click", ".show-more-content", function () {

    $(this).toggleClass("show-less-content")
    $(".show-staff-details").toggle()

});

//



function updateWatchlist() {
    var w_symbols = []
            $(".w_s_s").each(function () {
                w_symbols.push($(this).text())
                $.ajax({
                    // url:'/accounts/dashboard/',
                    url: '/accounts/dashboard/api/stocks/',
                    type:'GET',
                    async:true,
                    data:{
                        'type':'get_watched_stock_real_data',
                        'symbols':w_symbols
                    },
                    success:function(data){
                        for(var i=0; i<data.data.length; i++) {
                            $(".w_s_s_"+data.data[i].symbol).html(data.data[i].price)
                            $(".w_s_s").closest(".row").show()
                            $(".w_s_s_d"+data.data[i].symbol).html(data.data[i].difference)
                            $(".w_s_s_d"+data.data[i].symbol).css("color",data.data[i].color)
                            $(".w_s_s_label"+data.data[i].symbol).show()
                        }
                    }
                })
            })

}

getWatchList = function(interval) {
    axios.get(
        "/accounts/dashboard/api/watchlist/"
    ).then(function(data) {
        $("#watch_list").html("");
        for (stock of data.data.data) {
            percentage = stock.percentage.toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            }) + "%";
            live_price = "₹" + stock.live_price.toLocaleString("en-US", {
                maximumFractionDigits: 2, minimumFractionDigits: 2
            });
            html = "";
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

    });
}

$(document).on("click", ".btn-add-to-w", function () {
    $this = $(this)
    // symbol = $(".stock-symbol-span").text()
    symbol = $("#symbol").text().replaceAll(" ", "").replaceAll("\n", "");
    $.ajax({
        // url: '/accounts/dashboard/',
        url: '/accounts/dashboard/api/stocks/',
        type: 'GET',
        data: {
            'type': 'add-to-watchlist',
            'symbol': symbol
        },
        success: function (data) {
            window.location.reload();
            /*if (data.status == "added") {
                $this.html("Remove from Watchlist")
                // $(".stock-added-success").fadeIn(500);
                // $(".stock-added-success").fadeOut(500);

            } else {
                $this.html("Add to Watchlist")
                // $(".stock-added-success").html("Stock already added");
                // $(".stock-added-success").fadeIn(500);
                // $(".stock-added-success").fadeOut(500);

            }
            getWatchList();*/
        }
    })
})


$(document).on("click", ".btn-add-to-w-red", function () {
    $this = $(this)
    // symbol = $(".stock-symbol-span").text()
    symbol = $("#symbol").text().replaceAll(" ", "").replaceAll("\n", "");
    $.ajax({
        // url: '/accounts/dashboard/',
        url: '/accounts/dashboard/api/stocks/',
        type: 'GET',
        data: {
            'type': 'add-to-watchlist',
            'symbol': symbol
        },
        success: function (data) {
            window.location.reload();
            /*if (data.status == "added") {
                $this.html("Remove from Watchlist")
                // $(".stock-added-success").fadeIn(500);
                // $(".stock-added-success").fadeOut(500);

            } else {
                $this.html("Add to Watchlist")
                // $(".stock-added-success").html("Stock already added");
                // $(".stock-added-success").fadeIn(500);
                // $(".stock-added-success").fadeOut(500);

            }
            getWatchList();*/
        }
    })
})


$(document).on("click", ".order-select", function () {
    $(this).closest(".dropdown-menu").removeClass("show")
    if ($(this).attr("data-attr") == "limit_order") {
        $(".limit-price-content").show()
    } else {
        $(".limit-price-content").hide()
    }
    $(".info-message").html("")
    $(".share-num").val("")
    $(".total-market-price").val("0.00")
    $(".order_type").val($(this).attr("data-attr"))
})

$(document).on("click", ".btn-buy-order", function () {
    var share_num = $(".share-num").val()
    var current_price = $("#market-price-ws").text()
    console.log(current_price)
    var order_type = $(".order_type").val()
    var symbol = $(".stock-symbol-span").html()
    if (share_num != "") {
        $(".err-label").hide()
        var limit_price;
        var expires = "1";
        var flag = 0;
        if (order_type == "limit_order") {
            limit_price = $(".inp-limit-price").val()
            if (limit_price != "") {
                $(".err-label").hide()
            } else {
                $(".err-label").show()
                $(".err-label").html("Enter a valid limit price")
                flag = 1;
            }
            expires = $(".inp-expires").val()
        }
        if (flag == 0) {
            $.ajax({
                // url: '/accounts/dashboard/',
                url: '/accounts/dashboard/api/stocks/',
                type: 'GET',
                data: {
                    'type': 'buy_stock',
                    'share': share_num,
                    'current_price': current_price,
                    'order_type': order_type,
                    'symbol': symbol,
                    'expires':expires,
                    'limit_price': limit_price
                },
                success: function (data) {
                    alert("SUCCESS")
                    $(".err-label").hide()
                    location.reload();
                }
            })
        }


    }else{
                $(".err-label").show()
                $(".err-label").html("Enter a valid share number")
            }
})

function initializeOdoometer(){

/*! odometer 0.4.6 */
(function () {
    var a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, A, B, C, D, E, F, G = [].slice;
    q = '<span class="odometer-value"></span>', n = '<span class="odometer-ribbon"><span class="odometer-ribbon-inner">' + q + "</span></span>", d = '<span class="odometer-digit"><span class="odometer-digit-spacer">8</span><span class="odometer-digit-inner">' + n + "</span></span>", g = '<span class="odometer-formatting-mark"></span>', c = "(,ddd).dd", h = /^\(?([^)]*)\)?(?:(.)(d+))?$/, i = 30, f = 2e3, a = 20, j = 2, e = .5, k = 1e3 / i, b = 1e3 / a, o = "transitionend webkitTransitionEnd oTransitionEnd otransitionend MSTransitionEnd", y = document.createElement("div").style, p = null != y.transition || null != y.webkitTransition || null != y.mozTransition || null != y.oTransition, w = window.requestAnimationFrame || window.mozRequestAnimationFrame || window.webkitRequestAnimationFrame || window.msRequestAnimationFrame, l = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver, s = function (a) {
        var b;
        return b = document.createElement("div"), b.innerHTML = a, b.children[0]
    }, v = function (a, b) {
        return a.className = a.className.replace(new RegExp("(^| )" + b.split(" ").join("|") + "( |$)", "gi"), " ")
    }, r = function (a, b) {
        return v(a, b), a.className += " " + b
    }, z = function (a, b) {
        var c;
        return null != document.createEvent ? (c = document.createEvent("HTMLEvents"), c.initEvent(b, !0, !0), a.dispatchEvent(c)) : void 0
    }, u = function () {
        var a, b;
        return null != (a = null != (b = window.performance) ? "function" == typeof b.now ? b.now() : void 0 : void 0) ? a : +new Date
    }, x = function (a, b) {
        return null == b && (b = 0), b ? (a *= Math.pow(10, b), a += .5, a = Math.floor(a), a /= Math.pow(10, b)) : Math.round(a)
    }, A = function (a) {
        return 0 > a ? Math.ceil(a) : Math.floor(a)
    }, t = function (a) {
        return a - x(a)
    }, C = !1, (B = function () {
        var a, b, c, d, e;
        if (!C && null != window.jQuery) {
            for (C = !0, d = ["html", "text"], e = [], b = 0, c = d.length; c > b; b++) a = d[b], e.push(function (a) {
                var b;
                return b = window.jQuery.fn[a], window.jQuery.fn[a] = function (a) {
                    var c;
                    return null == a || null == (null != (c = this[0]) ? c.odometer : void 0) ? b.apply(this, arguments) : this[0].odometer.update(a)
                }
            }(a));
            return e
        }
    })(), setTimeout(B, 0), m = function () {
        function a(b) {
            var c, d, e, g, h, i, l, m, n, o, p = this;
            if (this.options = b, this.el = this.options.el, null != this.el.odometer) return this.el.odometer;
            this.el.odometer = this, m = a.options;
            for (d in m) g = m[d], null == this.options[d] && (this.options[d] = g);
            null == (h = this.options).duration && (h.duration = f), this.MAX_VALUES = this.options.duration / k / j | 0, this.resetFormat(), this.value = this.cleanValue(null != (n = this.options.value) ? n : ""), this.renderInside(), this.render();
            try {
                for (o = ["innerHTML", "innerText", "textContent"], i = 0, l = o.length; l > i; i++) e = o[i], null != this.el[e] && !function (a) {
                    return Object.defineProperty(p.el, a, {
                        get: function () {
                            var b;
                            return "innerHTML" === a ? p.inside.outerHTML : null != (b = p.inside.innerText) ? b : p.inside.textContent
                        }, set: function (a) {
                            return p.update(a)
                        }
                    })
                }(e)
            } catch (q) {
                c = q, this.watchForMutations()
            }
        }

        return a.prototype.renderInside = function () {
            return this.inside = document.createElement("div"), this.inside.className = "odometer-inside", this.el.innerHTML = "", this.el.appendChild(this.inside)
        }, a.prototype.watchForMutations = function () {
            var a, b = this;
            if (null != l) try {
                return null == this.observer && (this.observer = new l(function () {
                    var a;
                    return a = b.el.innerText, b.renderInside(), b.render(b.value), b.update(a)
                })), this.watchMutations = !0, this.startWatchingMutations()
            } catch (c) {
                a = c
            }
        }, a.prototype.startWatchingMutations = function () {
            return this.watchMutations ? this.observer.observe(this.el, {childList: !0}) : void 0
        }, a.prototype.stopWatchingMutations = function () {
            var a;
            return null != (a = this.observer) ? a.disconnect() : void 0
        }, a.prototype.cleanValue = function (a) {
            var b;
            return "string" == typeof a && (a = a.replace(null != (b = this.format.radix) ? b : ".", "<radix>"), a = a.replace(/[.,]/g, ""), a = a.replace("<radix>", "."), a = parseFloat(a, 10) || 0), x(a, this.format.precision)
        }, a.prototype.bindTransitionEnd = function () {
            var a, b, c, d, e, f, g = this;
            if (!this.transitionEndBound) {
                for (this.transitionEndBound = !0, b = !1, e = o.split(" "), f = [], c = 0, d = e.length; d > c; c++) a = e[c], f.push(this.el.addEventListener(a, function () {
                    return b ? !0 : (b = !0, setTimeout(function () {
                        return g.render(), b = !1, z(g.el, "odometerdone")
                    }, 0), !0)
                }, !1));
                return f
            }
        }, a.prototype.resetFormat = function () {
            var a, b, d, e, f, g, i, j;
            if (a = null != (i = this.options.format) ? i : c, a || (a = "d"), d = h.exec(a), !d) throw new Error("Odometer: Unparsable digit format");
            return j = d.slice(1, 4), g = j[0], f = j[1], b = j[2], e = (null != b ? b.length : void 0) || 0, this.format = {
                repeating: g,
                radix: f,
                precision: e
            }
        }, a.prototype.render = function (a) {
            var b, c, d, e, f, g, h, i, j, k, l, m;
            for (null == a && (a = this.value), this.stopWatchingMutations(), this.resetFormat(), this.inside.innerHTML = "", g = this.options.theme, b = this.el.className.split(" "), f = [], i = 0, k = b.length; k > i; i++) c = b[i], c.length && ((e = /^odometer-theme-(.+)$/.exec(c)) ? g = e[1] : /^odometer(-|$)/.test(c) || f.push(c));
            for (f.push("odometer"), p || f.push("odometer-no-transitions"), f.push(g ? "odometer-theme-" + g : "odometer-auto-theme"), this.el.className = f.join(" "), this.ribbons = {}, this.digits = [], h = !this.format.precision || !t(a) || !1, m = a.toString().split("").reverse(), j = 0, l = m.length; l > j; j++) d = m[j], "." === d && (h = !0), this.addDigit(d, h);
            return this.startWatchingMutations()
        }, a.prototype.update = function (a) {
            var b, c = this;
            return a = this.cleanValue(a), (b = a - this.value) ? (v(this.el, "odometer-animating-up odometer-animating-down odometer-animating"), b > 0 ? r(this.el, "odometer-animating-up") : r(this.el, "odometer-animating-down"), this.stopWatchingMutations(), this.animate(a), this.startWatchingMutations(), setTimeout(function () {
                return c.el.offsetHeight, r(c.el, "odometer-animating")
            }, 0), this.value = a) : void 0
        }, a.prototype.renderDigit = function () {
            return s(d)
        }, a.prototype.insertDigit = function (a, b) {
            return null != b ? this.inside.insertBefore(a, b) : this.inside.children.length ? this.inside.insertBefore(a, this.inside.children[0]) : this.inside.appendChild(a)
        }, a.prototype.addSpacer = function (a, b, c) {
            var d;
            return d = s(g), d.innerHTML = a, c && r(d, c), this.insertDigit(d, b)
        }, a.prototype.addDigit = function (a, b) {
            var c, d, e, f;
            if (null == b && (b = !0), "-" === a) return this.addSpacer(a, null, "odometer-negation-mark");
            if ("." === a) return this.addSpacer(null != (f = this.format.radix) ? f : ".", null, "odometer-radix-mark");
            if (b) for (e = !1; ;) {
                if (!this.format.repeating.length) {
                    if (e) throw new Error("Bad odometer format without digits");
                    this.resetFormat(), e = !0
                }
                if (c = this.format.repeating[this.format.repeating.length - 1], this.format.repeating = this.format.repeating.substring(0, this.format.repeating.length - 1), "d" === c) break;
                this.addSpacer(c)
            }
            return d = this.renderDigit(), d.querySelector(".odometer-value").innerHTML = a, this.digits.push(d), this.insertDigit(d)
        }, a.prototype.animate = function (a) {
            return p && "count" !== this.options.animation ? this.animateSlide(a) : this.animateCount(a)
        }, a.prototype.animateCount = function (a) {
            var c, d, e, f, g, h = this;
            if (d = +a - this.value) return f = e = u(), c = this.value, (g = function () {
                var i, j, k;
                return u() - f > h.options.duration ? (h.value = a, h.render(), void z(h.el, "odometerdone")) : (i = u() - e, i > b && (e = u(), k = i / h.options.duration, j = d * k, c += j, h.render(Math.round(c))), null != w ? w(g) : setTimeout(g, b))
            })()
        }, a.prototype.getDigitCount = function () {
            var a, b, c, d, e, f;
            for (d = 1 <= arguments.length ? G.call(arguments, 0) : [], a = e = 0, f = d.length; f > e; a = ++e) c = d[a], d[a] = Math.abs(c);
            return b = Math.max.apply(Math, d), Math.ceil(Math.log(b + 1) / Math.log(10))
        }, a.prototype.getFractionalDigitCount = function () {
            var a, b, c, d, e, f, g;
            for (e = 1 <= arguments.length ? G.call(arguments, 0) : [], b = /^\-?\d*\.(\d*?)0*$/, a = f = 0, g = e.length; g > f; a = ++f) d = e[a], e[a] = d.toString(), c = b.exec(e[a]), e[a] = null == c ? 0 : c[1].length;
            return Math.max.apply(Math, e)
        }, a.prototype.resetDigits = function () {
            return this.digits = [], this.ribbons = [], this.inside.innerHTML = "", this.resetFormat()
        }, a.prototype.animateSlide = function (a) {
            var b, c, d, f, g, h, i, j, k, l, m, n, o, p, q, s, t, u, v, w, x, y, z, B, C, D, E;
            if (s = this.value, j = this.getFractionalDigitCount(s, a), j && (a *= Math.pow(10, j), s *= Math.pow(10, j)), d = a - s) {
                for (this.bindTransitionEnd(), f = this.getDigitCount(s, a), g = [], b = 0, m = v = 0; f >= 0 ? f > v : v > f; m = f >= 0 ? ++v : --v) {
                    if (t = A(s / Math.pow(10, f - m - 1)), i = A(a / Math.pow(10, f - m - 1)), h = i - t, Math.abs(h) > this.MAX_VALUES) {
                        for (l = [], n = h / (this.MAX_VALUES + this.MAX_VALUES * b * e), c = t; h > 0 && i > c || 0 > h && c > i;) l.push(Math.round(c)), c += n;
                        l[l.length - 1] !== i && l.push(i), b++
                    } else l = function () {
                        E = [];
                        for (var a = t; i >= t ? i >= a : a >= i; i >= t ? a++ : a--) E.push(a);
                        return E
                    }.apply(this);
                    for (m = w = 0, y = l.length; y > w; m = ++w) k = l[m], l[m] = Math.abs(k % 10);
                    g.push(l)
                }
                for (this.resetDigits(), D = g.reverse(), m = x = 0, z = D.length; z > x; m = ++x) for (l = D[m], this.digits[m] || this.addDigit(" ", m >= j), null == (u = this.ribbons)[m] && (u[m] = this.digits[m].querySelector(".odometer-ribbon-inner")), this.ribbons[m].innerHTML = "", 0 > d && (l = l.reverse()), o = C = 0, B = l.length; B > C; o = ++C) k = l[o], q = document.createElement("div"), q.className = "odometer-value", q.innerHTML = k, this.ribbons[m].appendChild(q), o === l.length - 1 && r(q, "odometer-last-value"), 0 === o && r(q, "odometer-first-value");
                return 0 > t && this.addDigit("-"), p = this.inside.querySelector(".odometer-radix-mark"), null != p && p.parent.removeChild(p), j ? this.addSpacer(this.format.radix, this.digits[j - 1], "odometer-radix-mark") : void 0
            }
        }, a
    }(), m.options = null != (E = window.odometerOptions) ? E : {}, setTimeout(function () {
        var a, b, c, d, e;
        if (window.odometerOptions) {
            d = window.odometerOptions, e = [];
            for (a in d) b = d[a], e.push(null != (c = m.options)[a] ? (c = m.options)[a] : c[a] = b);
            return e
        }
    }, 0), m.init = function () {
        var a, b, c, d, e, f;
        if (null != document.querySelectorAll) {
            for (b = document.querySelectorAll(m.options.selector || ".odometer"), f = [], c = 0, d = b.length; d > c; c++) a = b[c], f.push(a.odometer = new m({
                el: a,
                value: null != (e = a.innerText) ? e : a.textContent
            }));
            return f
        }
    }, null != (null != (F = document.documentElement) ? F.doScroll : void 0) && null != document.createEventObject ? (D = document.onreadystatechange, document.onreadystatechange = function () {
        return "complete" === document.readyState && m.options.auto !== !1 && m.init(), null != D ? D.apply(this, arguments) : void 0
    }) : document.addEventListener("DOMContentLoaded", function () {
        return m.options.auto !== !1 ? m.init() : void 0
    }, !1), "function" == typeof define && define.amd ? define(["jquery"], function () {
        return m
    }) : typeof exports === !1 ? module.exports = m : window.Odometer = m
}).call(this);
}


$(document).on("click",".btn-review-order",function(){
    var share_num = $(".share-num").val()
    var current_price = $(".market-price-val").val()
    var user_buyingpower = $(".user-buyingpower").val()
    var total_market_price = $(".total-market-price").html()
    var order_type = $(".order_type").val()
    var symbol = $(".stock-symbol-span").html()
    var expires = $(".inp-expires").val()
    var expires_txt = $(".inp-expires option:selected").text()
    date = new Date()
    var order_type_txt = "market order"
    if (order_type == "limit_order") {
        order_type_txt = "limit order"
    }
    var str = "You are placing a "+expires_txt+" "+order_type_txt+" to buy "+share_num+" share of "+symbol+"."
    var message = "Temporary message. For developement purpose."; // what should be shown if clicks on review order when market is opened.
    if (share_num != "") {
        $(".err-label").hide()
        var limit_price;
        expires = "1";
        var flag = 0;
        if (parseFloat(user_buyingpower) >= parseFloat(total_market_price)){
            if (order_type == "limit_order") {
                limit_price = $(".inp-limit-price").val()
                if (limit_price != "") {
                    $(".err-label").hide()
                    message = str+" Your pending order if executed,will execute at $"+limit_price+" per share or better."
                $(".info-message").html(message)
                $(".review-order-content").hide()
                $(".buy-order-content").show()
                } else {
                    $(".err-label").show()
                    $(".err-label").html("Enter a valid limit price")
                    flag = 1;
                }


            }else{
                var hours = parseInt(date.getHours())
                var minutes = parseInt(date.getMinutes())
                var statusflag = 0
                if (hours < 15){
                    statusflag = 1
                }else if(hours == 15){
                    if (minutes <=30){
                        statusflag = 1
                    }
                }
                if (statusflag == 0) {
                    message = str + " Your order will be placed  after the market opens and executed at the best available price."
                }
                $(".info-message").html(message)
                $(".review-order-content").hide()
                $(".buy-order-content").show()
            }
        }else{
            $(".err-label").show()
            $(".err-label").html("Enter enough buying power. Enter money into the account.")
        }
    }else{
            $(".err-label").show()
            $(".err-label").html("Enter a valid share number")
          }
})

$(document).on("click",".btn-paginate",function(){
    var symbol = $("#stock_symbol").val()
    $.ajax({
                // url:'/accounts/dashboard/',
                url: '/accounts/dashboard/api/stocks/',
                type:'GET',
                data:{
                    'type':'table_paginate',
                    'symbol':symbol,
                    'page':$(this).attr("data-attr")
                },
                success:function(data){
                    if (data.tr_status == "True"){
                        $(".ua-content").replaceWith(data.up_activity_html)
                        $(".ua-content").show()
                    }else{
                        $(".ua-content").hide()
                    }
                }
    })

})

$(document).on("click",".cancel-transact",function(){
    var id = $(this).attr("data-attr")
    $this = $(this)
    $.ajax({
                // url:'/accounts/dashboard/',
                url: '/accounts/dashboard/api/stocks/',
                type:'GET',
                data:{
                    'type':'delete_transaction_data',
                    'id':id,
                },
                success:function(data){
                    $this.closest("tr").remove()
                }
    })

})

$(document).on("click",".show-pos-table",function(){
    $.ajax({
                // url:'/accounts/dashboard/',
                url: '/accounts/dashboard/api/stocks/',
                type:'GET',
                data:{
                    'type':'get_position_table_list',
                },
                success:function(data){
                   $(".container-fluid").replaceWith(data.position_table_html)
                }
    })

})

$(document).on("click",".open-sell-content",function(){
    $(this).css("color",$(".theme-color").val())
    $(".open-buy-content").css("color","#fff")
    $(".buy-stock-content").hide()
    $(".sell-order-content").show()
})

$(document).on("click",".open-buy-content",function(){
    $(this).css("color",$(".theme-color").val())
    $(".open-sell-content").css("color","#fff")
    $(".buy-stock-content").show()
    $(".sell-order-content").hide()
    $(".buy-order-content").hide()
    $(".limit-price-content").hide()
})

$(document).on("click",".btn-sell-order",function(){

    var share_num = $(".share-num").val()
    var current_price = $("#market-price-ws").text()
    var order_type = $(".order_type").val()
    var symbol = $(".stock-symbol-span").html()
    var limit_price = $(".inp-limit-price").val()

    var share_total = $(".inp-stock-num").val()

    console.log(share_num, current_price, order_type, symbol, limit_price, share_total);

    if (share_num != "") {
        $(".err-label").hide()
        var limit_price;
        var expires = "1";
        var flag = 0;
        if (order_type == "limit_order") {
            limit_price = $(".inp-limit-price").val()
            if (limit_price != "") {
                $(".err-label").hide()
            } else {
                $(".err-label").show()
                $(".err-label").html("Enter a valid limit price")
                flag = 1;
            }
            expires = $(".inp-expires").val()
        }
        console.log(flag, parseInt(share_num) <= parseInt(share_total));
        if (flag == 0) {
            //
            if (parseInt(share_num) <= parseInt(share_total)) {
                $(".err-label").html("")
                $this = $(this)
                $.ajax({
                    // url:'/accounts/dashboard/',
                    url: '/accounts/dashboard/api/stocks/',
                    type:'GET',
                    data:{
                        'type': 'sell-stock',
                        'symbol': symbol,
                        'share_num': share_num,
                        'order_type': order_type,

                        'current_price': current_price,
                        'expires':expires,
                        'limit_price': limit_price
                    },
                    success:function(data){
                       alert("SUCCESS")
                       location.reload();
                    }
                });
            } else {
                $(".err-label").html("You only have "+share_total+" shares for this stock");
            }
            /*$.ajax({
                // url: '/accounts/dashboard/',
                url: '/accounts/dashboard/api/stocks/',
                type: 'GET',
                data: {
                    'type': 'buy_stock',
                    'share': share_num,
                    'current_price': current_price,
                    'order_type': order_type,
                    'symbol': symbol,
                    'expires':expires,
                    'limit_price': limit_price
                },
                success: function (data) {
                    alert("SUCCESS")
                    $(".err-label").hide()
                    location.reload();
                }
            })*/
        }


    } else{
        $(".err-label").show()
        $(".err-label").html("Enter a valid share number")
    }

    // Old Approach ...
    /*if (parseInt(share_num) <= parseInt(share_total)){
        $(".err-label").html("")
        $this = $(this)
        $.ajax({
            // url:'/accounts/dashboard/',
            url: '/accounts/dashboard/api/stocks/',
            type:'GET',
            data:{
                'type':'sell-stock',
                'symbol':symbol,
                'share_num':share_num,
            },
            success:function(data){
               alert("SUCCESS")
               location.reload();
            }
        })
    }else{
        $(".err-label").html("You only have "+share_total+" shares for this stock")
    }*/


     // click on search input and change color of search icon
    $(document).on('click', function(e) {
        clicked_id = e.target.id;
        if(clicked_id === 'search_input_stock')
        {
            console.log('iifff')
            $('#search_input_stock').closest('div').find('i').css('color','#fff')
        }
        else{
            console.log('else')
            $('#search_input_stock').closest('div').find('i').css('color','#495057')
        }
    });
})
