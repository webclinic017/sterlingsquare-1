PositionTableViewModel = function() {
    var self = this;

    self.update_interval = 5 * 1000;
    self.transactionTable = null;

    self.columns = [
        {"data": "name", "title": "Asset Name", "sortable": true},
        {"data": "symbol", "title": "Symbol", "sortable": true},
        // units
        {
            "data": "size", "title": "Units", "sortable": true,
            "render": function(data) {
                return data.toLocaleString(
                    "en-US",
                    {maximumFractionDigits: 0, minimumFractionDigits: 0}
                );
            }
        },
        // current price
        {
            "data": "live_price", "title": "Current Price", "sortable": true,
            "render": function(data) {
                return "₹" + data.toLocaleString(
                    "en-US",
                    {maximumFractionDigits: 2, minimumFractionDigits: 2}
                );
            }
        },
        // unrealised gl
        {
            "data": "unrealised_gain_loss", "title": "Unrealised Gain/Loss", "sortable": true,
            "render": function(data) {
                if (data >= 0) {
                    return "₹" + data.toLocaleString(
                        "en-US",
                        {maximumFractionDigits: 2, minimumFractionDigits: 2}
                    );
                } else {
                    return "-₹" + Math.abs(data).toLocaleString(
                        "en-US",
                        {maximumFractionDigits: 2, minimumFractionDigits: 2}
                    );
                }
            }
        },
        // amount
        {
            "data": "avg_cost", "title": "Avg. Cost", "sortable": true,
            "render": function(data) {
                return "₹" + data.toLocaleString(
                    "en-US",
                    {maximumFractionDigits: 2, minimumFractionDigits: 2}
                );
            }
        },
        // amount
        {
            "data": "amount", "title": "Amount", "sortable": true,
            "render": function(data) {
                return "₹" + data.toLocaleString(
                    "en-US",
                    {maximumFractionDigits: 2, minimumFractionDigits: 2}
                );
            }
        },
    ];

    self.initTable = () => {
        self.transactionTable = $('#transactions').DataTable({
            "autoWidth": false,
            "paging": false,
            "info": false,
            "serverSide": true,
            "columns": self.columns,
            "ajax": {
                "url": "/accounts/dashboard/api/transactions/",
            },
            "order": [[4, "desc"]],
            "initComplete": function(settings, json) {
                code = setInterval(() => {
                    // abort previous API call if it's still in progress.
                    xhr = self.transactionTable.settings()[0].jqXHR
                    if (xhr) {
                        xhr.abort();
                    }
                    self.transactionTable.ajax.reload();
                }, self.update_interval);
            }
        });
    }

    self.init = () => {
        $.fn.dataTableExt.sErrMode = 'throw';
        self.initTable();
    }
}
