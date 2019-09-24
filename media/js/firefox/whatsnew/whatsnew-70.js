/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

(function() {
    'use strict';

    var client = Mozilla.Client;

    var lockwiseCTA = document.getElementById('lockwise-cta-link');
    var protectionCTA = document.getElementById('protection-cta');

    lockwiseCTA.addEventListener('click', openLogins);
    protectionCTA.addEventListener('click', openProtectionReport);

    function openLogins() {
        Mozilla.UITour.showHighlight('logins');
    }

    function openProtectionReport(){
        Mozilla.UITour.showProtectionReport();
    }

    function checkUpToDate() {
        if (client.isFirefoxDesktop) {
            console.log('up to date');
        }
    }

    Mozilla.UITour.ping(function() {
        checkUpToDate();
    });

})();
