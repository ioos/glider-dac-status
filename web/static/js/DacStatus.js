(function() {
  var DacStatus = function(templates) {
    // Delta times for coloring rows and cells
    this.delta6 = 60*60*6*1000;
    this.delta12 = 60*60*12*1000;
    this.delta24 = 60*60*24*1000;
    this.delta36 = 60*60*36*1000;
    this.delta72 = 60*60*72*1000;

    // JSON urls
    this.status_url = 'static/json/status.json';
    this.meta_base_url = 'static/json/deployments';

    // Data containers
    this.status_datasets = [];
    this.incomplete_datasets = [];
    this.meta = {};
    this.status_timestamp = null;

    // jQuery selections
    this.$content = $('#content');
    this.$clock = $("#load-time");
    this.$statusMsg = $("#status-msg");

    // Mustache.js templates
    this.status_template = templates['StatusTable.html'];
    Mustache.parse(this.status_template);

    this.deployment_template = templates['DeploymentsTable.html'];
    Mustache.parse(this.deployment_template);

    this.blacklisted_alert = templates['BlacklistedAlert.html'];
    Mustache.parse(this.blacklisted_alert);

    this.institution_template = $("#institutions-template").html();
    Mustache.parse(this.institution_template);

    this.operator_template = $("#operators-template").html();
    Mustache.parse(this.operator_template);

    this.provider_template = $("#providers-template").html();
    Mustache.parse(this.provider_template);

    this.wmo_template = $("#wmos-template").html();
    Mustache.parse(this.wmo_template);

    // Bootstrap popover options
    this.popoverOptions = { selector : "i[rel='popover']",
      trigger : "hover",
      container : "body",
      html: true
    };

    // Delegate Bootstrap popovers
    $('body').popover(this.popoverOptions);

    // Start the clock
    ClockUtc.init('#utc-clock');
  };


  DacStatus.prototype.load = function() {
    this.now = moment().valueOf();
    // Fetch json_file
    var xhr = $.ajax({
      url: this.status_url,
      dataType: "json"
    });
    xhr.done(this.onLoad.bind(this));

    // Delegate a.institution-link behavior
    $('body').on('click', 'a.institution,a.operator,a.provider,a.wmo-id', this.onClickInstitution.bind(this));

    // Display incomplete datasets
    $('#incomplete-datasets').click(this.onClickIncompleteDatasets.bind(this));

    // Display all datasets
    $('#all-datasets').click(this.onClickAllDatasets.bind(this));

    // Display latest updated datasets
    $('#latest').click(this.onClickLatest.bind(this));

    // Display blacklisted deployments
    $('#blacklisted').click(this.onClickBlacklisted.bind(this));
  };


  DacStatus.prototype.onLoad = function(response) {
    // Store the status fetch time for display
    this.status_timestamp = response.meta.fetch_time;

    // Convert times to strings for display
    response.datasets.forEach(this._convertTimes.bind(this));

    // Sort the datasets by name and store
    this.status_datasets = _.sortBy(response.datasets, function(dataset) {
      return dataset.name.toLowerCase();
    });
    // Store the missing datasets
    this.incomplete_datasets = _.filter(this.status_datasets, function(dataset) {
      return dataset.tds === null || dataset.tabledap === null;
    });

    this.onClickIncompleteDatasets();
    var sorted;

    // Get the list of institutions for which we have datasets and
    // remove null values
    var institutions = _.filter(_.uniq(_.map(this.status_datasets, function(dataset) {
      return dataset.institution;
    })), function(name) { return name !== null; });
    // Sort the result
    var sortedInstitutions = _.sortBy(institutions, function(institution) {
      return institution;
    });
    // Fill in the Institutions nav dropdown
    $("#institutions-dropdown").html(Mustache.render(this.institution_template, sortedInstitutions));

    // Get the list of operators for which we have datasets and
    // remove null values
    var operators = _.filter(_.uniq(_.map(this.status_datasets, function(dataset) {
      return dataset.operator;
    })), function(name) { return name !== null; });
    // Sort the result
    var sortedOperators = _.sortBy(operators, function(operator) {
      return operator;
    });
    // Fill in the operators nav dropdown
    $("#operators-dropdown").html(Mustache.render(this.operator_template, sortedOperators));

    // Get the list of data providers for which we have datasets and
    // remove null values
    var providers = _.filter(_.uniq(_.map(this.status_datasets, function(dataset) {
      return dataset.username;
    })), function(name) { return name !== null; });
    // Sort the result
    var sortedProviders = _.sortBy(providers, function(provider) {
      return provider;
    });
    // Fill in the providers nav dropdown
    $("#providers-dropdown").html(Mustache.render(this.provider_template, sortedProviders));

    // Get the list of wmo ids for which we have datasets and remove
    // null values
    var wmo_ids = _.filter(_.uniq(_.map(this.status_datasets, function(dataset) {
      return dataset.wmo_id;
    })), function(name) { return name !== null; });
    // Sort the result
    var sortedWMOIDs = _.sortBy(wmo_ids, function(wmo_id) {
      return wmo_id;
    });
    // Fill in the providers nav dropdown
    $("#wmo-dropdown").html(Mustache.render(this.wmo_template, sortedWMOIDs));

  };


  DacStatus.prototype.onClickInstitution = function(event) {
    event.preventDefault();
    var $link = $(event.target);
    // Get the target search name from the dropdown menu
    var target = $link.text();
    var datasets;
    // Find all of the datasets for the selected link type
    if ($link.hasClass('institution')) {
      datasets = _.filter(this.status_datasets, function(element) {
        return element.institution == target;
      });
    }
    else if ($link.hasClass('operator')) {
      datasets = _.filter(this.status_datasets, function(element) {
        return element.operator == target;
      });
    }
    else if ($link.hasClass('provider')) {
      datasets = _.filter(this.status_datasets, function(element) {
        return element.username == target;
      });
    }
    else if ($link.hasClass('wmo-id')) {
      datasets = _.filter(this.status_datasets, function(element) {
        return element.wmo_id == target;
      });
    }
    else {
      datasets = [];
    }

      // Create the table of all selected datasets
    if (datasets.length === 0) {
      return;
    }

    this.$statusMsg.text(datasets.length + ' Selected Datasets as of: ' + this.status_timestamp);
    this.render(datasets);

    // Set/remove .active on relevant navbar list-items
    $('ul.navbar-nav > li').removeClass('active');
    $('ul.dropdown-menu li, li.dropdown').removeClass('active');
    $link.closest('li.dropdown').addClass('active');
    $link.closest('li').addClass('active');

  };


  DacStatus.prototype.onClickIncompleteDatasets = function(event) {
    if(typeof event !== "undefined") {
      event.preventDefault();
      // Set/remove .active on relevant navbar list-items
      $('ul.navbar-nav > li').removeClass('active');
      $(event.target).parent().addClass('active');
      $('ul.dropdown-menu li, li.dropdown').removeClass('active');
      // Create the incomplete dataset table if there are incomplete
      // datasets
    }
    // Create the incomplete dataset table if there are incomplete
    // datasets
    var numMissing = this.incomplete_datasets.length;
    if (numMissing > 0) {
      this.$statusMsg.text(numMissing + ' Incomplete Datasets as of: ' + this.status_timestamp);
      this.$content.html(Mustache.render(this.status_template, this.incomplete_datasets));
      $.bootstrapSortable(false, 'reversed');
    }
    else {
      var latest = _.sortBy(this.status_datasets, 'end').reverse().slice(0,15);
      this.$statusMsg.text(latest.length + ' Latest Dataset Updates as of: ' + this.status_timestamp);
      this.render(latest);
      var okMsg = '<div class="alert alert-success alert-dismissable center">';
      okMsg += '<button type="button" class="close" data-dismiss="alert" arial-label="Close">';
      okMsg += '<span aria-hidden="true">&times;</span></button>';
      okMsg += '<h3>All Datasets Are Complete</h3>';
      okMsg += 'ERDDAP and THREDDS end points exist for all registered deployments.  Have a nice day.';
      okMsg += '</div>';
      this.$content.prepend(okMsg);
    }
  };

  DacStatus.prototype.onClickAllDatasets = function(event) {
    event.preventDefault();
    // Set/remove .active on relevant navbar list-items
    $('ul.navbar-nav > li').removeClass('active');
    $(event.target).parent().addClass('active');
    $('ul.dropdown-menu li, li.dropdown').removeClass('active');
    this.$statusMsg.text(this.status_datasets.length + ' Selected Datasets as of: ' + this.status_timestamp);
    this.render(this.status_datasets);
  };

  DacStatus.prototype.onClickLatest = function(event) {
    event.preventDefault();
    // Set/remove .active on relevant navbar list-items
    $('ul.navbar-nav > li').removeClass('active');
    $(event.target).parent().addClass('active');
    $('ul.dropdown-menu li, li.dropdown').removeClass('active');
    var latest = _.sortBy(this.status_datasets, 'end').reverse().slice(0,15);
    this.$statusMsg.text(latest.length + ' Latest Dataset Updates as of: ' + this.status_timestamp);
    this.render(latest);
  };

  DacStatus.prototype.onClickBlacklisted = function(event) {
    event.preventDefault();
    $('ul.navbar-nav > li').removeClass('active');
    $(event.target).parent().addClass('active');
    $('ul.dropdown-menu li, li.dropdown').removeClass('active');
    this.render(_.where(this.status_datasets, {archive_safe: false}));
    this.$content.prepend(Mustache.render(this.blacklisted_alert));
  };

  DacStatus.prototype.getStatusData = function() {
    return this.status_datasets;
  };

  DacStatus.prototype.getMetaData = function () {
    return this.meta;
  };

  DacStatus.prototype.render = function(json) {
    this.$content.html(Mustache.render(this.deployment_template, json));
    $.bootstrapSortable(false, 'reversed');
  };

  DacStatus.prototype._convertTimes = function(record) {
    if (record.created) {
      // Set the bootstrap created-status contextual class to danger
      // if either there is NO erddap or tds dataset available
      record['created-status'] = 'bg-danger';
      if (record.created > (this.now - this.delta6)) {
        record['created-status'] = 'bg-success';
      }
      else if (record.created > (this.now - this.delta12)) {
        record['created-status'] = 'bg-warning';
      }
      else if (record.created > (this.now - this.delta24)) {
        record['created-status'] = 'bg-danger';
      }
      record.created = moment.utc(record.created).format('YYYY-MM-DD<br />HH:mm');
    }
    if (record.updated) {
      record.updated = moment.utc(record.updated).format('YYYY-MM-DD<br />HH:mm');
    }
    if (record.nc_file_last_update) {
      record.nc_file_last_update = moment.utc(record.nc_file_last_update).format('YYYY-MM-DD<br />HH:mm');
    }
    if (record.start) {
      record.start = moment.utc(record.start).format('YYYY-MM-DD<br />HH:mm');
    }
    if (record.end) {
      if (record.end > (this.now - this.delta12)) {
        record['time-coverage-status'] = 'bg-success';
      }
      else if (record.end > (this.now - this.delta24)) {
        record['time-coverage-status'] = 'bg-warning';
      }
      else if (record.end > (this.now - this.delta36)) {
        record['time-coverage-status'] = 'bg-danger';
      }
      else if (record.end > (this.now - this.delta72)) {
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
  };

  window.DacStatus = DacStatus;
})();
