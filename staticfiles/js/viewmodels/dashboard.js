Dashboard = function() {
    var self = this;

    self.activeListToken = null;

    self.postRendering = () => {
        $(".carousel-item").first().addClass("active");
        $('#recipeCarousel').carousel({
            interval: 10000
        });

        $('.carousel .carousel-item').each(function() {
            var minPerSlide = 3;
            var next = $(this).next();
            if (!next.length) {
                next = $(this).siblings(':first');
            }
            // next.children(':first-child').clone().appendTo($(this));

            for (var i=0; i < minPerSlide; i++) {
                next = next.next();
                if (!next.length) {
                    next = $(this).siblings(':first');
                }
                next.children(':first-child').clone().appendTo($(this));
            }
        });

        $(document).on('click', '.markets-capital-item', function() {
            symbol = $(this).attr("id").replaceAll("active_", "");
            window.open('/accounts/dashboard/stocks/NSE:'+`${symbol}/`);
        })

        /*$(document).on("click", ".s-result", function () {
            symbol = $(this).html()
            symbol = symbol.trim()
            console.log(symbol);
            window.open('/accounts/dashboard/stocks/NSE:'+`${symbol}/`);
        });*/

        $("#top_gainers").css("display", "block");
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
            $("#carousel-item-wrapper").html("");
            for (stock of data.data.active) {
                percentage = stock.change.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                }) + "%";
                live_price = "₹" + stock.price.toLocaleString("en-US", {
                    maximumFractionDigits: 2, minimumFractionDigits: 2
                });
                html = "";
                if (stock.change >= 0) {
                    html = '<div class="carousel-item">' +
                        '<div class="col-md-3 col-sm-2 top-stocks">' +
                        '<div class="markets-capital-item" id="active_' + stock.symbol + '">' +
                        '<h6><span><p class="s-result name_id">' + stock.symbol +
                        '</h6></span></p>' +
                        '<div><h6 class="s-ltp">'+ live_price + '</h6>' +
                            '<h5 class="green">' + percentage + '<i class="icon ion-md-arrow-up"></i></h5>' +
                        '</div>' +
                    '</div></div></div>';
                } else {
                    html = '<div class="carousel-item">' +
                        '<div class="col-md-3 col-sm-2 top-stocks">' +
                        '<div class="markets-capital-item" id="active_' + stock.symbol + '">' +
                        '<h6><span><p class="s-result name_id">' + stock.symbol +
                        '</h6></span></p>' +
                        '<div class="markets-capital-details"><h6 class="s-ltp">'+ live_price + '</h6>' +
                        '<h5 class="red">' + percentage + '<i class="icon ion-md-arrow-down"></i></h5>' +
                        '</div>' +
                    '</div></div></div>';
                }
                $("#carousel-item-wrapper").append(html);
            }
            if (data.data.count > 0) {
                // refresh the carousel
                self.postRendering();
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

    self.init = () => {
        self.getMostActive(false);
    }
}
