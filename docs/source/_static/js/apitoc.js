$(document).ready(function() {
  (function ($) {
    if (window.location.href.match("/api/pronto.*") !== null) {
      $(".nav-list")
        .children()
        .filter("li")
        .append("<ul id='apitoc' class='nav nav-list'></ul>");
      $( "dt" )
        .has( ".sig-name" )
        .slice(1)
        .each(function( index ) {
          var html = (
            "<li><a href='#"
            + $( this ).attr("id")
            + "'><code>"
            + $( this ).find(".sig-name").text()
            + "</code></a></li>"
          );
          $("#apitoc").append(html);
        });
    } else if (window.location.href.match("/api/warnings*") !== null) {
      $(".nav-list")
        .children()
        .filter("li")
        .append("<ul id='apitoc' class='nav nav-list'></ul>");
      $( "dt" )
        .each(function( index ) {
          var html = (
            "<li><a href='#"
            + $( this ).attr("id")
            + "'><code>"
            + $( this ).find(".sig-name").text()
            + "</code></a></li>"
          );
          $("#apitoc").append(html);
        });
    }
  })(window.$jqTheme || window.jQuery);
})
