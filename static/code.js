$(function() {
    // search txt enter event
    $('#txtTvShowName').keypress(function(event) {
        if (event.which == 13) $('#btnSearch').click();
    });
    
    // tv show search handling
    $('#btnSearch').click(function() {
        $('#imgAjaxLoaderSearch').show();
        requestCrossDomain('http://www.thetvdb.com/api/GetSeries.php?seriesname=' + encodeURIComponent($('#txtTvShowName').val()),
            function(data) {
                $('#imgAjaxLoaderSearch').hide();
                data = data.query.results;
                var html = '';
                if (data && data.Data && data.Data != '\n') {
                    var shows = data.Data.Series;
                    if (!shows.length) {
                        shows = [shows];
                    }
                    for (var i = 0; i < shows.length; i++) {
                        html += '<div><a href="javascript:void(null)" onclick="addShow(' + shows[i].id + ', this)">' + shows[i].SeriesName + '</a></div>';
                    }
                } else {
                    html = 'No shows found';
                }
                modal.show(html);
            });
    });
    
    // start focus on tv show search
    $('#txtTvShowName').focus();
});

// allows to make a cross-domain ajax request using YQL as a proxy
function requestCrossDomain(url, successCallback) {
    $.getJSON(
        'http://query.yahooapis.com/v1/public/yql?format=json&callback=?&q=' +
            encodeURIComponent('select * from xml where url="' + url + '"'), successCallback);
}

// this is the modal that shows TV shows search results
var modal = {
    container: null,
    show: function(html) {
        $('#modal-inner-content').html(html);
        $('#modal-content')
            .modal({
                overlayId: 'overlay',
                containerId: 'container',
                closeHTML: null,
                minHeight: 300,
                opacity: 65, 
                position: ['0',],
                overlayClose: true,
                onOpen: modal.open,
                onClose: modal.close
            });
    },
    open: function(d) {
        var self = this;
        self.container = d.container[0];
        d.overlay.fadeIn('slow', function () {
            $('#modal-content', self.container).show();
            var title = $('#modal-title', self.container);
            title.show();
            d.container.slideDown('slow', function () {
                var h = 300;
                d.container.animate(
                    {height: h}, 
                    100,
                    function () {
                        $('div.close', self.container).show();
                        $('#modal-data', self.container).show();
                    }
                );
            });
        })
    },
    close: function (d) {
        var self = this; // this = SimpleModal object
        d.container.animate(
            {top:'-' + (d.container.height() + 20)},
            100,
            function () {
                self.close(); // or $.modal.close();
            }
        );
    }
};

// add the show to the list
function addShow(id, elem) {
    $('.simplemodal-close').click();
    // check if the show is already added
    if ($('#show_' + id.toString()).length > 0) {
        alert('The show is already added.');
        $('#txtTvShowName').val('');
        $('#txtTvShowName').focus();
        return;
    }
    $('#imgAjaxLoaderSearch').show();
    var show_name = $(elem).text();
    // get show episodes
    $.getJSON('/show_data/' + id.toString() + '/' + show_name,
        function(show_data) {
            episodes = show_data.episodes;
            
            // add show container
            var show = $('#show_template')
                .clone()
                .show()
                .attr('id', 'show_' + id.toString())
                .appendTo('#shows_container');
            
            $('.title', show).html(show_data.show_name);
            // remove show event
            $('.remove_button', show).click(function() {
                    $.ajax('/remove_show/' + id.toString());
                    show.remove();
                });
            
            // add each episode to the container
            for (var i = 0; i < episodes.length; i++) {
                var episode_data = episodes[i];
                
                var episode = $('#episode_template')
                    .clone()
                    .show()
                    .removeAttr('id')
                    .appendTo(show);
                
                if (episode_data.episode_id != -1) {
                    $('.title', episode).html(episode_data.title);
                    $('.date', episode).html(episode_data.air_date);
                    var season_and_episode = 'S';
                    if (episode_data.season_number < 10) {
                        season_and_episode += '0' + episode_data.season_number.toString();
                    } else {
                        season_and_episode += episode_data.season_number.toString();
                    }
                    season_and_episode += 'E';
                    if (episode_data.episode_number < 10) {
                        season_and_episode += '0' + episode_data.episode_number.toString();
                    } else {
                        season_and_episode += episode_data.episode_number.toString();
                    }
                    $('.season_and_episode', episode).html(season_and_episode);
                    if (episode_data.rating) {
                        $('.rating', episode).html('Rating: ' + episode_data.rating.toString());
                    }
                    $('.overview', episode).html(episode_data.overview);
                } else {
                    $('.ep_data_top', episode).html('All episodes up to this day have already aired.');
                    episode.addClass('today');
                    $('.ep_data_bottom', episode).remove();
                    $('.overview', episode).remove();
                }
            }
            
            $('#imgAjaxLoaderSearch').hide();
            $('#txtTvShowName').val('');
            $('#txtTvShowName').focus();
        });
}