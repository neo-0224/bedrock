(function() {
    'use strict';

    var client = window.Mozilla.Client;

    if (client._isFirefox() === true && client._getFirefoxMajorVersion() >= '70') {
        document.querySelector('.for-firefox-69-and-below').remove();
        document.querySelector('.for-non-firefox-users').remove();  
    }
    else if ( client._isFirefox() === true && client._getFirefoxMajorVersion() < '70' ) {
        document.querySelector('.for-firefox-70-and-above').remove();
        document.querySelector('.for-non-firefox-users').remove();
    }
    else if ( client._isFirefox() === false ){
        document.querySelector('.for-firefox-69-and-below').remove();
        document.querySelector('.for-firefox-70-and-above').remove();
    } else {
        document.querySelector('.for-firefox-70-and-above').remove();
        document.querySelector('.for-firefox-69-and-below').remove();
        document.querySelector('.for-non-firefox-users').remove();
    }

    document.querySelector('#lockwise-button').addEventListener('click', function() {
        Mozilla.UITour.showHighlight('logins');
    });
})();