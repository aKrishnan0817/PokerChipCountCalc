$(document).ready(function() {
    function displayScript(script) {
        $('#script-container').empty();
        $('#scene-list').empty();

        script.acts.forEach(act => {
            $('#scene-list').append(`<li class="act" data-act="${act.act}"><strong>Act ${act.act}</strong></li>`);
            act.scenes.forEach(scene => {
                let sceneId = `act-${act.act}-scene-${scene.scene}`;
                $('#scene-list').append(`<li class="scene" data-scene="${sceneId}" style="margin-left: 10px;">Scene ${scene.scene}: ${scene.title}</li>`);
                $('#script-container').append(`<h2 id="act-${act.act}" style="margin-bottom: 5px;">Act ${act.act}</h2>`);
                $('#script-container').append(`<h3 id="${sceneId}" style="margin-bottom: 5px;">Scene ${scene.scene}: ${scene.title}</h3>`);
                scene.lines.forEach(line => {
                    $('#script-container').append(`
                        <div class="speech" data-speaker="${line.speaker}" style="margin-bottom: 1px; padding-bottom: 1px; display: flex; flex-direction: column; position: relative;">
                            <div class="speaker-container" style="display: flex; align-items: center; gap: 3px;">
                                <span class="speaker" style="font-weight: bold;">${line.speaker}</span>
                                <button class="toggle-btn" data-state="visible" style="padding: 2px 4px; font-size: 10px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 3px;">👁</button>
                            </div>
                            <span class="line-text" style="display: block; margin-left: 5px; line-height: 1.1; margin-top: 1px;">${line.text}</span>
                        </div>
                    `);
                });
            });
        });
    }
    function scrollToElement(elementId) {
        $('html, body').animate({
            scrollTop: $(`#${elementId}`).offset().top
        }, 500);
    }

    $(document).on('click', '.act', function() {
        let actId = `act-${$(this).data('act')}`;
        scrollToElement(actId);
    });

    $(document).on('click', '.scene', function() {
        let sceneId = $(this).data('scene');
        scrollToElement(sceneId);
    });

    function toggleSpeakerLines(speaker) {
        $('.speech').each(function() {
            if ($(this).attr('data-speaker') === speaker) {
                let lineText = $(this).find('.line-text');
                let toggleBtn = $(this).find('.toggle-btn');
                if (toggleBtn.attr('data-state') === "visible") {
                    lineText.append('<div class="overlay" style="position: absolute; width: 100%; height: 100%; background: lightgreen; display: flex; align-items: center; justify-content: center;"><button class="mic-btn" data-line="' + lineText.text() + '" style="padding: 5px; border: none; background: white; border-radius: 50%; cursor: pointer;">🎤</button></div>');
                    toggleBtn.html('🚫👁').attr('data-state', 'hidden');
                } else {
                    lineText.find('.overlay').remove();
                    toggleBtn.html('👁').attr('data-state', 'visible');
                }
            }
        });
    }

    $(document).on('click', '.toggle-btn', function() {
        let speaker = $(this).closest('.speech').attr('data-speaker');
        toggleSpeakerLines(speaker);
    });

    $(document).on('click', '.mic-btn', function(event) {
        event.stopPropagation();
        let lineText = $(this).data('line');
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.start();

        let finalTranscript = "";
        let silenceTimeout;

        recognition.onresult = function(event) {
            clearTimeout(silenceTimeout);
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + " ";
                }
            }
            silenceTimeout = setTimeout(() => {
                recognition.stop();
            }, 2000);
        };

        recognition.onend = function() {
            $.ajax({
                url: '/check_speech',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ spoken_text: finalTranscript.trim(), correct_text: lineText }),
                success: function(response) {
                    alert(response.result);
                    if (response.correct) {
                        $(event.target).closest('.overlay').remove();
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error:", status, error);
                }
            });
        };

        recognition.onerror = function(event) {
            alert("Speech recognition error: " + event.error);
        };
    });

    $.post('/get_script', function(data) {
        displayScript(data);
    }, 'json');
});
