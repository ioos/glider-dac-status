var DacStatus = (function init() {

    // Delta times for coloring rows and cells
    var delta6 = 60*60*6*1000;
    var delta12 = 60*60*12*1000;
    var delta24 = 60*60*24*1000;
    var delta36 = 60*60*36*1000;
    var delta72 = 60*60*72*1000;

    // JSON urls
    var status_url = './json/status.json';
    var meta_base_url = './json/deployments';
    
    // Data containers
    var status_datasets = [];
    var incomplete_datasets = [];
    var meta = {};
    var status_timestamp;

    // jQuery selections
    var $content = $('#content');
    var $clock = $("#load-time");
    var $statusMsg = $("#status-msg");

    // Mustache.js templates
    var status_template = $("#status-table").html();
    Mustache.parse(status_template);
    var deployment_template = $("#deployments-template").html();
    Mustache.parse(deployment_template);
    var institution_template = $("#institutions-template").html();
    Mustache.parse(institution_template);
    var operator_template = $("#operators-template").html();
    Mustache.parse(operator_template);
    var provider_template = $("#providers-template").html();
    Mustache.parse(provider_template);
    var wmo_template = $("#wmos-template").html();
    Mustache.parse(wmo_template);

    // Bootstrap popover options
    var popoverOptions = { selector : "i[rel='popover']",
        trigger : "hover",
        container : "body",
        html: true
    };
    
    // Delegate Bootstrap popovers
    $('body').popover(popoverOptions);

    // Start the clock
    ClockUtc.init('#utc-clock');

    function _init() {

        var now = moment().valueOf();

        // Fetch json_file
        var xhr = $.ajax({
            url: status_url,
            dataType: "json"
        });
        xhr.done(function(response) {
            // Store the status fetch time for display
            status_timestamp = response.meta.fetch_time;

            // Convert times to strings for display
            response.datasets.forEach(function(record) {
                if (record.created) {
	                // Set the bootstrap created-status contextual class to danger
	                // if either there is NO erddap or tds dataset available
	                record['created-status'] = 'bg-danger';
	                if (record.created > now-delta6) {
	                    record['created-status'] = 'bg-success';
	                }
	                else if (record.created > now-delta12) {
	                    record['created-status'] = 'bg-warning';
	                }
	                else if (record.created > now-delta24) {
	                    record['created-status'] = 'bg-danger';
	                }
                    record.created = moment.utc(record.created).format('YYYY-MM-DD<br />HH:mm');
                }
                if (record.updated) {
                    record.updated = moment.utc(record.updated).format('YYYY-MM-DD<br />HH:mm');
                }
                if (record.start) {
                    record.start = moment.utc(record.start).format('YYYY-MM-DD<br />HH:mm');
                }
                if (record.end) {
                    if (record.end > now-delta12) {
                        record['time-coverage-status'] = 'bg-success';
                    }
                    else if (record.end > now-delta24) {
                        record['time-coverage-status'] = 'bg-warning';
                    }
                    else if (record.end > now-delta36) {
                        record['time-coverage-status'] = 'bg-danger';
                    }
                    else if (record.end > now-delta72) {
                        record['time-coverage-status'] = 'bg-info';
                    }
                    else {
                        record['time-coverage-status'] = 'none';
                    }
                    record.end = moment.utc(record.end).format('YYYY-MM-DD<br />HH:mm');
                }
                // Set the bootstrap data-status contextual class to danger if
                // either there is NO erddap or tds dataset available
                record['data-status'] = null;
                if (record.tds === null || record.tabledap === null) {
                    record['data-status'] = 'bg-danger';
                }
            });
            // Sort the datasets by name and store
            status_datasets = _.sortBy(response.datasets, function(dataset) {
                return dataset.name.toLowerCase();
            });
            // Store the missing datasets
            incomplete_datasets = _.filter(status_datasets, function(dataset) {
                return dataset.tds === null || dataset.tabledap === null;
            });

            // Create the incomplete dataset table if there are incomplete
            // datasets
            var numMissing = incomplete_datasets.length;
            if (numMissing > 0) {
                $statusMsg.text(numMissing + ' Incomplete Datasets as of: ' + status_timestamp);
                $content.html(Mustache.render(status_template, incomplete_datasets));
                $.bootstrapSortable(false, 'reversed');
            }
            else {
	            var latest = _.sortBy(status_datasets, 'end').reverse().slice(0,15);
	            $statusMsg.text(latest.length + ' Latest Dataset Updates as of: ' + status_timestamp);
	            _createStatusTable(latest);
                var okMsg = '<div class="alert alert-success alert-dismissable center">';
                okMsg += '<button type="button" class="close" data-dismiss="alert" arial-label="Close">'
                okMsg += '<span aria-hidden="true">&times;</span></button>'
                okMsg += '<h3>All Datasets Are Complete</h3>'
                okMsg += 'ERDDAP and THREDDS end points exist for all registered deployments.  Have a nice day.';
                okMsg += '</div>';
                $content.prepend(okMsg);

            }

            // Get the list of institutions for which we have datasets and
            // remove null values
            var institutions = _.filter(_.uniq(_.map(status_datasets, function(dataset) {
                return dataset.institution;
            })), function(name) { return name !== null; });
            // Sort the result
            var sorted = _.sortBy(institutions, function(institution) {
                return institution;
            });
            // Fill in the Institutions nav dropdown
            $("#institutions-dropdown").html(Mustache.render(institution_template, sorted));

            // Get the list of operators for which we have datasets and
            // remove null values
            var operators = _.filter(_.uniq(_.map(status_datasets, function(dataset) {
                return dataset.operator;
            })), function(name) { return name !== null; });
            // Sort the result
            var sorted = _.sortBy(operators, function(institution) {
                return institution;
            });
            // Fill in the operators nav dropdown
            $("#operators-dropdown").html(Mustache.render(operator_template, sorted));

            // Get the list of data providers for which we have datasets and
            // remove null values
            var providers = _.filter(_.uniq(_.map(status_datasets, function(dataset) {
                return dataset.username;
            })), function(name) { return name !== null; });
            // Sort the result
            var sorted = _.sortBy(providers, function(institution) {
                return institution;
            });
            // Fill in the providers nav dropdown
            $("#providers-dropdown").html(Mustache.render(provider_template, sorted));

            // Get the list of wmo ids for which we have datasets and remove 
            // null values
            var wmo_ids = _.filter(_.uniq(_.map(status_datasets, function(dataset) {
                return dataset.wmo_id;
            })), function(name) { return name !== null; });
            // Sort the result
            var sorted = _.sortBy(wmo_ids, function(institution) {
                return institution;
            });
            // Fill in the providers nav dropdown
            $("#wmo-dropdown").html(Mustache.render(wmo_template, sorted));

        });

        // Delegate a.institution-link behavior
        $('body').on('click', 'a.institution,a.operator,a.provider,a.wmo-id', function(evt) {
            evt.preventDefault();
            var $link = $(this);
            // Get the target search name from the dropdown menu
            var target = $link.text();
            // Find all of the datasets for the selected link type
            if ($link.hasClass('institution')) {
                var datasets = _.filter(status_datasets, function(element) {
                    return element['institution'] == target
                });
            }
            else if ($link.hasClass('operator')) {
                var datasets = _.filter(status_datasets, function(element) {
                    return element['operator'] == target;
                });
            }
            else if ($link.hasClass('provider')) {
                var datasets = _.filter(status_datasets, function(element) {
                    return element['username'] == target;
                });
            }
            else if ($link.hasClass('wmo-id')) {
                var datasets = _.filter(status_datasets, function(element) {
                    return element['wmo_id'] == target;
                });
            }
            else {
                datasets = [];
            }

            // Create the table of all selected datasets
            if (datasets.length == 0) {
                return;
            }

            $statusMsg.text(datasets.length + ' Selected Datasets as of: ' + status_timestamp);
            _createStatusTable(datasets);

            // Set/remove .active on relevant navbar list-items
            $('ul.navbar-nav > li').removeClass('active');
            $('ul.dropdown-menu li, li.dropdown').removeClass('active');
            $link.closest('li.dropdown').addClass('active');
            $link.closest('li').addClass('active');

        });

        // Display incomplete datasets
        $('#incomplete-datasets').click(function(evt) {
            evt.preventDefault();
            // Set/remove .active on relevant navbar list-items
            $('ul.navbar-nav > li').removeClass('active');
            $(evt.target).parent().addClass('active');
            $('ul.dropdown-menu li, li.dropdown').removeClass('active');
            // Create the incomplete dataset table if there are incomplete
            // datasets
            var numMissing = incomplete_datasets.length;
            $statusMsg.text(numMissing + ' Incomplete Datasets as of: ' + status_timestamp);
            if (numMissing > 0) {
                $content.html(Mustache.render(status_template, incomplete_datasets));
                $.bootstrapSortable(false, 'reversed');
            }
            else {
                var okMsg = '<div class="alert alert-success alert-dismissable center">';
                okMsg += '<button type="button" class="close" data-dismiss="alert" arial-label="Close">'
                okMsg += '<span aria-hidden="true">&times;</span></button>'
                okMsg += '<h3>All Datasets Are Complete</h3>'
                okMsg += 'ERDDAP and THREDDS end points exist for all registered deployments.  Have a nice day.';
                okMsg += '</div>';
                $content.html(okMsg);
            }
        });

        // Display all datasets
        $('#all-datasets').click(function(evt) {
            evt.preventDefault();
            // Set/remove .active on relevant navbar list-items
            $('ul.navbar-nav > li').removeClass('active');
            $(evt.target).parent().addClass('active');
            $('ul.dropdown-menu li, li.dropdown').removeClass('active');
            $statusMsg.text(status_datasets.length + ' Selected Datasets as of: ' + status_timestamp);
            _createStatusTable(status_datasets);
        });

        // Display latest updated datasets
        $('#latest').click(function(evt) {
            evt.preventDefault();
            // Set/remove .active on relevant navbar list-items
            $('ul.navbar-nav > li').removeClass('active');
            $(evt.target).parent().addClass('active');
            $('ul.dropdown-menu li, li.dropdown').removeClass('active');
            var latest = _.sortBy(status_datasets, 'end').reverse().slice(0,15);
            $statusMsg.text(latest.length + ' Latest Dataset Updates as of: ' + status_timestamp);
            _createStatusTable(latest);
        });
    }

    function _createStatusTable(json) {
        $content.html(Mustache.render(deployment_template, json));
        $.bootstrapSortable(false, 'reversed');
    }

    return {
        init : _init,
        getStatusData : function() { return status_datasets; },
        getMetaData : function() { return meta; }
    }

})();

DacStatus.init();

