(function() {
  var selectChoice = function () {
    console.log('clicked');
    updateAffection();
    clearDialogue();
    loadDialogue();
    return false;
  }

  var affection = 0.0;
  function updateAffection() {
    var incr = Math.random();
    if (affection > incr && Math.floor(Math.random() * 2) == 0) {
      incr = incr * -1;
    }
    affection += incr;
    console.log(affection);
  }

  function clearDialogue() {
    $('#dialogue').text('');
    $('ul').remove();
  }

  function createResponse() {
    var responseList = $('<ul>');
    $.each(data['you'], function(i) {
      // TODO: replace existing list on page
      // console.log(data['you'][i])
      var li = $('<li/>').appendTo(responseList);
      var ahref = $('<a/>')
        .on('click', selectChoice)
        .text(data['you'][i])
        .appendTo(li);
      });
    $('#dialogue-box').append(responseList);
  }

  function loadDialogue() {
    $.get('/babble', function (data) {
      // make text appear one letter at a time
      $('#dialogue').typed({
        strings: [data['them']],
        typeSpeed: 0,
        showCursor: false,
        contentType: 'text',
        callback: createResponse
      });
    });
  }

  function updateBackground() {
    var height = $(window).height();
    $('body').css('background-image', 'url(/static/images/school.jpg)');
    $('body').css('background-size', 'cover');
    $('body').height(height);
  }

  $(document).ready(function() {
    updateBackground();
    loadDialogue();
  });
})();
