window.addEventListener("load", function () {
  var form = document.getElementById("tts_form");

  form.addEventListener("submit", function (event) {
    event.preventDefault(); // prevent form submission and reloading the page.
  });

  var form = document.getElementById("stt_form");
  form.addEventListener("submit", function (event) {
    event.preventDefault(); // prevent form submission and reloading the page.
  });
});

$(document).ready(function () {
  $('select').formSelect();
  $('.tabs').tabs();
  $('#loading_indicator').hide();
  $('textarea#text_input').characterCounter();
});

$("#inference_stt").on("click", function () {
  $(this).prop('disabled', true);
  var formData = new FormData(document.getElementById("stt_form"));
  $('#loading_indicator').show();
  $.ajax({
    url: '/inferencestt',
    method: 'post',
    cache: false,
    processData: false,
    contentType: false,
    enctype: 'multipart/form-data',
    data: formData,

    success: function (response) {
      $("#inference_text").text(response.inferenced_text);
    },

    error: function (response) {
      var errorMessage = JSON.parse(response.responseText).errormessage;
      alert(errorMessage);
      $('#loading_indicator').hide();
    $('#inference_stt').removeAttr('disabled');
    },

  }).done(function(){
    $('#loading_indicator').hide();
    $('#inference_stt').removeAttr('disabled');
  });
});

$("#inference_tts").on("click", function () {
  $(this).prop('disabled', true);
  var formData = new FormData(document.getElementById("tts_form"));
  $('#loading_indicator').show();
  $.ajax({
    beforeSend: function( xhr ) {
      xhr.overrideMimeType( "text/plain; charset=x-user-defined" );
    },
    url: '/inferencetts',
    method: 'post',
    cache: false,
    processData: false,
    contentType: false,
    data: formData,

    success: function (wavestring, _, jqXHR) {
      var wavString = wavestring;
      var len = wavString.length;
      var buf = new ArrayBuffer(len);
      var view = new Uint8Array(buf);
      for (var i = 0; i < len; i++) {
        view[i] = wavString.charCodeAt(i) & 0xff;
      }
      var blob = new Blob([view], {type: "audio/x-wav"});
      var audio = document.createElement("AUDIO");
      audio.src = URL.createObjectURL(new Blob([blob], { type: 'audio/x-wav'}));
      audio.setAttribute("controls", "controls");
      var waveName = jqXHR.getResponseHeader("content-disposition").replace("\"","").split("/").at(-1);
      var card = $("<div/>", {"class" : "card"});
      var cardContent = $("<div/>", {"class" : "card-content"});
      cardContent.append(audio);
      $.getJSON( "/getmetadata", {wav_identifier : waveName},  function(jsonData) {
        cardContent.append("<p>Input: "+formData.get("text_input")+"</p>");
        cardContent.append("<p>Teilwörter: "+jsonData["subwords"]+"</p>");
        cardContent.append("<p>Phonemisiert: "+jsonData["phonetic_sentence"]+"</p>");
      });
      card.append(cardContent);
      $("#tts_inferences").append(card);
      $('#loading_indicator').hide();
      
    },

    error: function (response) {
      //do something for error
      var errorMessage = JSON.parse(response.responseText).errormessage;
      alert(errorMessage);
      $('#loading_indicator').hide();
      $('#inference_tts').removeAttr('disabled');
    },

  }).done(function(){
    $('#loading_indicator').hide();
    $('#inference_tts').removeAttr('disabled');
  }
  );
});